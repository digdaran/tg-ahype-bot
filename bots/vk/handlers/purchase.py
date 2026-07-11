"""Покупка номерков в VK-боте: выбор розыгрыша -> количество -> ссылка на оплату."""
from __future__ import annotations

from vkbottle import GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from app.core.exceptions import GiveawayLockedError, ValidationError
from app.database import session_scope
from app.services.giveaway_service import GiveawayService
from app.services.payment_service import PaymentService
from bots.vk.keyboards import BTN_BUY, giveaways_keyboard, payment_link_keyboard, quantity_keyboard
from bots.vk.utils import require_participant

MAX_QUANTITY_OPTION = 20


def register(bot: Bot) -> None:
    @bot.on.private_message(text=[BTN_BUY, "Купить номерки"])
    async def start_purchase(message: Message) -> None:
        participant = await require_participant(message)
        if participant is None:
            return

        async with session_scope() as session:
            giveaways = await GiveawayService(session).list_open_for_participants()

        if not giveaways:
            await message.answer("Сейчас нет активных розыгрышей для покупки номерков. Загляните позже 🙏")
            return

        if len(giveaways) == 1:
            g = giveaways[0]
            max_available = min(g.tickets_remaining, MAX_QUANTITY_OPTION)
            await message.answer(
                f"Розыгрыш «{g.name}»\nЦена номерка: {g.ticket_price} ₽\n"
                f"Свободно номерков: {g.tickets_remaining}\n\nСколько номерков купить?",
                keyboard=quantity_keyboard(g.id, max_available),
            )
            return

        await message.answer(
            "Выберите розыгрыш:",
            keyboard=giveaways_keyboard([(g.id, g.name) for g in giveaways]),
        )

    @bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent, func=lambda e: e.payload.get("cmd") == "giveaway")
    async def choose_giveaway(event: MessageEvent) -> None:
        giveaway_id = event.payload["id"]
        async with session_scope() as session:
            giveaway = await GiveawayService(session).get(giveaway_id)

        if giveaway is None or giveaway.is_locked or not giveaway.is_registration_open:
            await event.show_snackbar("Розыгрыш недоступен")
            return

        max_available = min(giveaway.tickets_remaining, MAX_QUANTITY_OPTION)
        await event.send_message(
            f"Розыгрыш «{giveaway.name}»\nЦена номерка: {giveaway.ticket_price} ₽\n"
            f"Свободно номерков: {giveaway.tickets_remaining}\n\nСколько номерков купить?",
            keyboard=quantity_keyboard(giveaway.id, max_available),
        )

    @bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent, func=lambda e: e.payload.get("cmd") == "qty")
    async def choose_quantity(event: MessageEvent) -> None:
        giveaway_id = event.payload["giveaway_id"]
        quantity = int(event.payload["qty"])

        async with session_scope() as session:
            from app.services.registration_service import RegistrationService

            participant = await RegistrationService(session).find_by_vk_id(event.user_id)
            if participant is None:
                await event.show_snackbar("Сначала подтвердите телефон")
                return

            giveaway_service = GiveawayService(session)
            giveaway = await giveaway_service.get(giveaway_id)
            if giveaway is None:
                await event.show_snackbar("Розыгрыш не найден")
                return

            payment_service = PaymentService(session)
            try:
                payment = await payment_service.create_payment(participant, giveaway, quantity)
            except (ValidationError, GiveawayLockedError) as exc:
                await event.show_snackbar(str(exc))
                return

        await event.send_message(
            f"Заказ {payment.order_id}\nК оплате: {payment.amount} ₽ за {quantity} номерков.\n\n"
            "Нажмите кнопку ниже, чтобы перейти к оплате. После оплаты номерки будут выданы автоматически.",
            keyboard=payment_link_keyboard(payment.payment_url, payment.order_id),
        )
