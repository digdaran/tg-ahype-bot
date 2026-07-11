"""Резервная (ручная) проверка статуса оплаты в VK-боте."""
from __future__ import annotations

from vkbottle import GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from app.core.exceptions import ValidationError
from app.database import session_scope
from app.models.enums import PaymentStatusEnum
from app.services.payment_service import PaymentService
from bots.vk.keyboards import BTN_CHECK_PAYMENT
from bots.vk.utils import require_participant


def _status_text(status: PaymentStatusEnum) -> str:
    return {
        PaymentStatusEnum.PENDING: "⏳ Платёж пока не подтверждён банком. Попробуйте проверить чуть позже.",
        PaymentStatusEnum.SUCCEEDED: "✅ Оплата подтверждена! Номерки уже выданы — посмотрите в разделе «Мои номерки».",
        PaymentStatusEnum.FAILED: "❌ Платёж отклонён банком. Попробуйте купить номерки заново.",
        PaymentStatusEnum.CANCELED: "❌ Платёж отменён.",
    }[status]


def register(bot: Bot) -> None:
    @bot.on.raw_event(
        GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent, func=lambda e: e.payload.get("cmd") == "check"
    )
    async def check_specific_payment(event: MessageEvent) -> None:
        order_id = event.payload["order_id"]
        async with session_scope() as session:
            service = PaymentService(session)
            try:
                payment = await service.reserve_check(order_id)
            except ValidationError as exc:
                await event.show_snackbar(str(exc))
                return
        await event.show_snackbar(_status_text(payment.status))

    @bot.on.private_message(text=[BTN_CHECK_PAYMENT, "Проверить оплату"])
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
            payment = await service.reserve_check(pending[0].order_id)

        await message.answer(_status_text(payment.status))
