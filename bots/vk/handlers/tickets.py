"""Просмотр своих номерков и истории покупок в VK-боте."""
from __future__ import annotations

from vkbottle.bot import Bot, Message

from app.database import session_scope
from app.models.enums import ManualRegistrationStatusEnum
from app.repositories.giveaway_repo import GiveawayRepository
from app.repositories.manual_registration_repo import ManualRegistrationRepository
from app.services.payment_service import PaymentService
from app.services.ticket_service import TicketService
from bots.vk.keyboards import BTN_HISTORY, BTN_MY_TICKETS
from bots.vk.utils import require_participant


def register(bot: Bot) -> None:
    @bot.on.private_message(text=[BTN_MY_TICKETS, "Мои номерки"])
    async def my_tickets(message: Message) -> None:
        participant = await require_participant(message)
        if participant is None:
            return

        async with session_scope() as session:
            tickets = await TicketService(session).list_for_participant(participant.id)
            giveaway_repo = GiveawayRepository(session)
            giveaway_names = {}
            for t in tickets:
                if t.giveaway_id not in giveaway_names:
                    g = await giveaway_repo.get(t.giveaway_id)
                    giveaway_names[t.giveaway_id] = g.name if g else t.giveaway_id

        if not tickets:
            await message.answer("У вас пока нет номерков. Самое время купить первый! 🎟")
            return

        by_giveaway: dict[str, list[str]] = {}
        for t in tickets:
            by_giveaway.setdefault(giveaway_names[t.giveaway_id], []).append(t.full_code)

        lines = [f"Ваши номерки ({len(tickets)} шт.):\n"]
        for name, codes in by_giveaway.items():
            lines.append(f"{name}:")
            lines.extend(f"  🎟 {code}" for code in codes)
            lines.append("")

        await message.answer("\n".join(lines))

    @bot.on.private_message(text=[BTN_HISTORY, "История покупок"])
    async def purchase_history(message: Message) -> None:
        participant = await require_participant(message)
        if participant is None:
            return

        async with session_scope() as session:
            payments = await PaymentService(session).list_by_participant(participant.id)
            manual_regs = await ManualRegistrationRepository(session).list_by_participant(participant.id)

        if not payments and not manual_regs:
            await message.answer("История покупок пуста.")
            return

        lines = ["🧾 История покупок:\n"]
        for p in payments:
            lines.append(
                f"• Онлайн, заказ {p.order_id}: {p.quantity} шт. на {p.amount} ₽ — статус: {p.status.value} "
                f"({p.created_at.strftime('%d.%m.%Y %H:%M')})"
            )
        for r in manual_regs:
            if r.status == ManualRegistrationStatusEnum.CANCELLED:
                continue
            lines.append(
                f"• Офлайн-регистрация: {r.quantity} шт. — статус: {r.status.value} "
                f"({r.created_at.strftime('%d.%m.%Y %H:%M')})"
            )

        await message.answer("\n".join(lines))
