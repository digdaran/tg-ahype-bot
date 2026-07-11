"""Регистрация участника VK: запрос и подтверждение телефона текстом."""
from __future__ import annotations

import re

from vkbottle.bot import Bot, Message
from vkbottle.dispatch.rules.base import FuncRule

from app.core.exceptions import ValidationError
from app.database import session_scope
from app.services.registration_service import RegistrationService
from bots.vk.keyboards import main_menu_keyboard
from bots.vk.state import clear_awaiting_phone, is_awaiting_phone, mark_awaiting_phone

_PHONE_RE = re.compile(r"[\d+][\d\s\-()]{6,}")


def _looks_like_phone_and_awaiting(message: Message) -> bool:
    return is_awaiting_phone(message.from_id) and bool(_PHONE_RE.search(message.text or ""))


def register(bot: Bot) -> None:
    @bot.on.private_message(text=["начать", "Начать", "start", "меню", "Меню"])
    async def start_handler(message: Message) -> None:
        async with session_scope() as session:
            participant = await RegistrationService(session).find_by_vk_id(message.from_id)

        if participant:
            await message.answer(
                f"С возвращением, {participant.full_name or participant.phone}! 👋",
                keyboard=main_menu_keyboard(),
            )
            return

        mark_awaiting_phone(message.from_id)
        await message.answer(
            "Добро пожаловать в бот розыгрышей цифровых постеров! 🎨\n\n"
            "Чтобы продолжить, отправьте номер телефона в формате +7XXXXXXXXXX — "
            "это ваш главный идентификатор как участника розыгрыша."
        )

    @bot.on.private_message(FuncRule(_looks_like_phone_and_awaiting))
    async def phone_handler(message: Message) -> None:
        async with session_scope() as session:
            service = RegistrationService(session)
            try:
                await service.link_vk(
                    phone=message.text,
                    vk_user_id=message.from_id,
                    vk_username=None,
                )
            except ValidationError as exc:
                await message.answer(f"⚠️ {exc}")
                return

        clear_awaiting_phone(message.from_id)
        await message.answer(
            "Телефон подтверждён ✅\n\nТеперь вам доступны покупка номерков, "
            "просмотр своих номерков и истории покупок.",
            keyboard=main_menu_keyboard(),
        )
