"""
Сервис онлайн-платежей.

Webhook - основной способ подтверждения оплаты, ручная (резервная) проверка
используется только как запасной механизм, если webhook не пришёл.

Финализация платежа полностью идемпотентна: статус платежа меняется из
PENDING только один раз (строка блокируется SELECT ... FOR UPDATE на время
транзакции), повторные вызовы с тем же результатом - no-op.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicatePaymentError,
    GiveawayLockedError,
    ValidationError,
)
from app.models.enums import AuditActorTypeEnum, PaymentStatusEnum, TicketSourceEnum
from app.models.giveaway import Giveaway
from app.models.participant import Participant
from app.models.payment import Payment
from app.payments.base import WebhookVerificationResult
from app.payments.factory import get_provider
from app.repositories.giveaway_repo import GiveawayRepository
from app.repositories.payment_repo import PaymentRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.settings_service import SettingsService
from app.services.ticket_service import TicketService


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.payments = PaymentRepository(session)
        self.giveaways = GiveawayRepository(session)
        self.tickets = TicketService(session)
        self.settings = SettingsService(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService()

    async def create_payment(self, participant: Participant, giveaway: Giveaway, quantity: int) -> Payment:
        if quantity < 1:
            raise ValidationError("Количество номерков должно быть положительным")
        if giveaway.is_locked or not giveaway.is_registration_open:
            raise GiveawayLockedError(f"Розыгрыш '{giveaway.name}' недоступен для покупки")
        if giveaway.tickets_remaining < quantity:
            raise ValidationError(f"Недостаточно свободных номерков: доступно {giveaway.tickets_remaining}")

        provider_enum = await self.settings.get_active_payment_provider()
        provider = get_provider(provider_enum)

        order_id = f"{giveaway.prefix}-{uuid.uuid4().hex[:12]}"
        amount = float(giveaway.ticket_price) * quantity

        payment = Payment(
            order_id=order_id,
            participant_id=participant.id,
            giveaway_id=giveaway.id,
            provider=provider_enum,
            quantity=quantity,
            amount=amount,
            status=PaymentStatusEnum.PENDING,
        )
        await self.payments.add(payment)

        init_result = await provider.create_payment(
            order_id=order_id,
            amount=amount,
            currency="RUB",
            description=f"Оплата {quantity} номерков «{giveaway.name}» ({order_id})",
            return_url="https://t.me/",
        )
        payment.provider_payment_id = init_result.provider_payment_id
        payment.payment_url = init_result.payment_url
        await self.session.flush()

        await self.audit.log(
            action="payment.created",
            actor_type=AuditActorTypeEnum.SYSTEM,
            entity_type="payment",
            entity_id=payment.id,
            details={"order_id": order_id, "amount": amount, "quantity": quantity, "provider": provider_enum.value},
        )
        return payment

    async def _apply_terminal_status(
        self,
        payment: Payment,
        status: PaymentStatusEnum,
        provider_payment_id: Optional[str],
        raw_payload: Optional[dict],
        actor_label: str,
    ) -> Payment:
        """Единая точка перехода PENDING -> {SUCCEEDED|FAILED}. Идемпотентна по построению."""
        if payment.status != PaymentStatusEnum.PENDING:
            await self.audit.log(
                action="payment.duplicate_finalization_ignored",
                actor_type=AuditActorTypeEnum.SYSTEM,
                entity_type="payment",
                entity_id=payment.id,
                details={"current_status": payment.status.value, "attempted_status": status.value, "source": actor_label},
            )
            return payment

        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id
        if raw_payload is not None:
            payment.raw_webhook_payload = json.dumps(raw_payload, ensure_ascii=False, default=str)

        if status == PaymentStatusEnum.SUCCEEDED:
            payment.status = PaymentStatusEnum.SUCCEEDED
            payment.confirmed_at = datetime.now(timezone.utc)
            payment.idempotency_key = f"{payment.provider.value}:{payment.provider_payment_id or payment.order_id}"
            await self.session.flush()

            participant = await self.session.get(Participant, payment.participant_id)
            giveaway = await self.giveaways.get(payment.giveaway_id)
            issued_tickets = await self.tickets.issue_tickets(
                giveaway_id=payment.giveaway_id,
                participant=participant,
                quantity=payment.quantity,
                source=TicketSourceEnum.ONLINE,
                payment=payment,
                actor_type=AuditActorTypeEnum.SYSTEM,
                actor_label=actor_label,
            )
            if giveaway is not None:
                await self.notifications.notify_online_purchase(participant, giveaway, issued_tickets)
            await self.audit.log(
                action="payment.succeeded",
                actor_type=AuditActorTypeEnum.SYSTEM,
                entity_type="payment",
                entity_id=payment.id,
                details={"order_id": payment.order_id, "source": actor_label},
            )
        elif status == PaymentStatusEnum.FAILED:
            payment.status = PaymentStatusEnum.FAILED
            payment.failure_reason = "Отклонён платёжной системой"
            await self.session.flush()
            await self.audit.log(
                action="payment.failed",
                actor_type=AuditActorTypeEnum.SYSTEM,
                entity_type="payment",
                entity_id=payment.id,
                details={"order_id": payment.order_id, "source": actor_label},
            )

        return payment

    async def finalize_from_webhook(self, verification: WebhookVerificationResult, provider_name: str) -> Optional[Payment]:
        """Вызывается из webhook-роутера конкретного банка после проверки подписи."""
        if not verification.is_valid:
            await self.audit.log(
                action="payment.webhook_invalid_signature",
                actor_type=AuditActorTypeEnum.SYSTEM,
                details={"provider": provider_name, "error": verification.error, "raw": verification.raw},
            )
            return None

        if not verification.order_id:
            return None

        payment = await self.payments.get_locked_for_update_by_order_id(verification.order_id)
        if payment is None:
            await self.audit.log(
                action="payment.webhook_unknown_order",
                actor_type=AuditActorTypeEnum.SYSTEM,
                details={"provider": provider_name, "order_id": verification.order_id},
            )
            return None

        return await self._apply_terminal_status(
            payment,
            status=verification.status,
            provider_payment_id=verification.provider_payment_id,
            raw_payload=verification.raw,
            actor_label=f"webhook:{provider_name}",
        )

    async def reserve_check(self, order_id: str) -> Payment:
        """Резервная (ручная) проверка статуса - используется, только если webhook не пришёл."""
        payment = await self.payments.get_by_order_id(order_id)
        if payment is None:
            raise ValidationError(f"Платёж {order_id} не найден")
        if payment.status != PaymentStatusEnum.PENDING:
            return payment

        provider = get_provider(payment.provider)
        if not payment.provider_payment_id:
            return payment

        check_result = await provider.check_status(payment.provider_payment_id)
        return await self._apply_terminal_status(
            payment,
            status=check_result.status,
            provider_payment_id=payment.provider_payment_id,
            raw_payload=check_result.raw,
            actor_label="reserve_check",
        )

    async def list_by_participant(self, participant_id: str) -> list[Payment]:
        return await self.payments.list_by_participant(participant_id)
