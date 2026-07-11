"""Раздел помощи VK-бота."""
from __future__ import annotations

from vkbottle.bot import Bot, Message

from app.database import session_scope
from app.services.settings_service import SettingsService
from bots.vk.keyboards import BTN_HELP, main_menu_keyboard


def register(bot: Bot) -> None:
    @bot.on.private_message(text=[BTN_HELP, "Помощь"])
    async def help_handler(message: Message) -> None:
        async with session_scope() as session:
            settings_row = await SettingsService(session).get()

        support = settings_row.support_contact or "поддержка появится позже"
        await message.answer(
            "ℹ️ Как это работает:\n\n"
            "1. Подтвердите номер телефона — это ваш главный идентификатор.\n"
            "2. Купите номерки в разделе «Купить номерки».\n"
            "3. После оплаты номерки выдаются автоматически, вы получите цифровой постер.\n"
            "4. Если оплата прошла, а номерки не пришли — нажмите «Проверить оплату».\n\n"
            f"Поддержка: {support}",
            keyboard=main_menu_keyboard(),
        )
