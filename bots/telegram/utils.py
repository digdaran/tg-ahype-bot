"""Общие вспомогательные функции хендлеров Telegram-бота."""
from __future__ import annotations

from typing import Optional

from aiogram.types import Message

from app.database import session_scope
from app.models.participant import Participant
from app.services.registration_service import RegistrationService
from bots.telegram.keyboards import phone_request_keyboard


async def get_participant(telegram_user_id: int) -> Optional[Participant]:
    async with session_scope() as session:
        service = RegistrationService(session)
        return await service.find_by_telegram_id(telegram_user_id)


async def require_participant(message: Message) -> Optional[Participant]:
    participant = await get_participant(message.from_user.id)
    if participant is None:
        await message.answer(
            "Сначала нужно подтвердить номер телефона — нажмите /start.",
            reply_markup=phone_request_keyboard(),
        )
        return None
    return participant
