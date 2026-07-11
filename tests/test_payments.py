"""
Тесты идемпотентности финализации платежа (app/services/payment_service.py):
повторный webhook с тем же результатом верификации не должен приводить к
повторной выдаче номерков — это ключевое требование ТЗ (webhook может
прийти от банка более одного раза).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PaymentProviderEnum, PaymentStatusEnum
from app.models.giveaway import Giveaway
from app.models.participant import Participant
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.payments.base import WebhookVerificationResult
from app.services.payment_service import PaymentService


async def _make_giveaway(session: AsyncSession, **overrides) -> Giveaway:
    defaults = dict(name="Тестовый розыгрыш", prefix="PAY", ticket_price=100, max_tickets=50)
    defaults.update(overrides)
    giveaway = Giveaway(**defaults)
    session.add(giveaway)
    await session.flush()
    return giveaway


async def _make_participant(session: AsyncSession, phone: str = "+79990000002") -> Participant:
    participant = Participant(phone=phone)
    session.add(participant)
    await session.flush()
    return participant


async def _make_pending_payment(
    session: AsyncSession, giveaway: Giveaway, participant: Participant, quantity: int = 2
) -> Payment:
    payment = Payment(
        order_id="PAY-order-1",
        participant_id=participant.id,
        giveaway_id=giveaway.id,
        provider=PaymentProviderEnum.TBANK,
        quantity=quantity,
        amount=float(giveaway.ticket_price) * quantity,
        status=PaymentStatusEnum.PENDING,
    )
    session.add(payment)
    await session.flush()
    return payment


async def test_webhook_finalization_is_idempotent(session: AsyncSession):
    giveaway = await _make_giveaway(session)
    participant = await _make_participant(session)
    payment = await _make_pending_payment(session, giveaway, participant, quantity=2)

    service = PaymentService(session)
    verification = WebhookVerificationResult(
        is_valid=True,
        order_id=payment.order_id,
        provider_payment_id="tbank-ext-123",
        status=PaymentStatusEnum.SUCCEEDED,
        raw={"ok": True},
    )

    result_1 = await service.finalize_from_webhook(verification, provider_name="tbank")
    assert result_1 is not None
    assert result_1.status == PaymentStatusEnum.SUCCEEDED

    tickets_after_first = (
        (await session.execute(select(Ticket).where(Ticket.payment_id == payment.id))).scalars().all()
    )
    assert len(tickets_after_first) == 2, "после первого webhook должно быть выдано ровно 2 номерка"

    # Повторная доставка того же webhook банком (типичный сценарий retry).
    result_2 = await service.finalize_from_webhook(verification, provider_name="tbank")
    assert result_2 is not None
    assert result_2.status == PaymentStatusEnum.SUCCEEDED

    tickets_after_second = (
        (await session.execute(select(Ticket).where(Ticket.payment_id == payment.id))).scalars().all()
    )
    assert len(tickets_after_second) == 2, "повторный webhook НЕ должен выдавать номерки повторно"

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 2


async def test_webhook_finalization_unknown_order_returns_none(session: AsyncSession):
    service = PaymentService(session)
    verification = WebhookVerificationResult(
        is_valid=True,
        order_id="does-not-exist",
        provider_payment_id="tbank-ext-999",
        status=PaymentStatusEnum.SUCCEEDED,
        raw={},
    )
    result = await service.finalize_from_webhook(verification, provider_name="tbank")
    assert result is None


async def test_webhook_finalization_invalid_signature_returns_none(session: AsyncSession):
    giveaway = await _make_giveaway(session)
    participant = await _make_participant(session)
    payment = await _make_pending_payment(session, giveaway, participant, quantity=1)

    service = PaymentService(session)
    verification = WebhookVerificationResult(
        is_valid=False,
        order_id=payment.order_id,
        provider_payment_id=None,
        status=PaymentStatusEnum.SUCCEEDED,
        raw={},
        error="bad signature",
    )
    result = await service.finalize_from_webhook(verification, provider_name="tbank")
    assert result is None

    await session.refresh(payment)
    assert payment.status == PaymentStatusEnum.PENDING, "платёж не должен финализироваться при неверной подписи"


async def test_webhook_finalization_failed_status_no_tickets(session: AsyncSession):
    giveaway = await _make_giveaway(session)
    participant = await _make_participant(session)
    payment = await _make_pending_payment(session, giveaway, participant, quantity=3)

    service = PaymentService(session)
    verification = WebhookVerificationResult(
        is_valid=True,
        order_id=payment.order_id,
        provider_payment_id="tbank-ext-fail",
        status=PaymentStatusEnum.FAILED,
        raw={},
    )
    result = await service.finalize_from_webhook(verification, provider_name="tbank")
    assert result is not None
    assert result.status == PaymentStatusEnum.FAILED

    tickets = (await session.execute(select(Ticket).where(Ticket.payment_id == payment.id))).scalars().all()
    assert len(tickets) == 0

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 0
