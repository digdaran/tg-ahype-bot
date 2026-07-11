"""Резервная (ручная) проверка статуса оплаты — используется, только если webhook не пришёл."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.core.exceptions import ValidationError
from app.database import session_scope
from app.models.enums import PaymentStatusEnum
from app.services.payment_service import PaymentService
from bots.telegram.keyboards import BTN_CHECK_PAYMENT
from bots.telegram.utils import require_participant

router = Router(name="payment_check")


def _status_text(status: PaymentStatusEnum) -> str:
    return {
        PaymentStatusEnum.PENDING: "⏳ Платёж пока не подтверждён банком. Попробуйте проверить чуть позже.",
        PaymentStatusEnum.SUCCEEDED: "✅ Оплата подтверждена! Номерки уже выданы — посмотрите в разделе «Мои номерки».",
        PaymentStatusEnum.FAILED: "❌ Платёж отклонён банком. Попробуйте купить номерки заново.",
        PaymentStatusEnum.CANCELED: "❌ Платёж отменён.",
    }[status]


@router.callback_query(F.data.startswith("check:"))
async def check_specific_payment(callback: CallbackQuery) -> None:
    order_id = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        service = PaymentService(session)
        try:
            payment = await service.reserve_check(order_id)
        except ValidationError as exc:
            await callback.answer(str(exc), show_alert=True)
            return

    await callback.answer(_status_text(payment.status), show_alert=True)


@router.message(F.text == BTN_CHECK_PAYMENT)
async def check_latest_payment(message: Message) -> None:
    participant = await require_participant(message)
    if participant is None:
        return

    async with session_scope() as session:
        service = PaymentService(session)
        payments = await service.list_by_participant(participant.id)
        pending = [p for p in payments if p.status == PaymentStatusEnum.PENDING]
        if not pending:
            await message.answer("У вас нет ожидающих подтверждения платежей.")
            return

        latest = pending[0]
        payment = await service.reserve_check(latest.order_id)

    await message.answer(_status_text(payment.status))
