"""Общие вспомогательные функции хендлеров VK-бота."""
from __future__ import annotations

from typing import Optional

from vkbottle.bot import Message

from app.database import session_scope
from app.models.participant import Participant
from app.services.registration_service import RegistrationService
from bots.vk.state import mark_awaiting_phone


async def get_participant(vk_user_id: int) -> Optional[Participant]:
    async with session_scope() as session:
        service = RegistrationService(session)
        return await service.find_by_vk_id(vk_user_id)


async def require_participant(message: Message) -> Optional[Participant]:
    participant = await get_participant(message.from_id)
    if participant is None:
        mark_awaiting_phone(message.from_id)
        await message.answer(
            "Сначала нужно подтвердить номер телефона. Отправьте его в формате +7XXXXXXXXXX."
        )
        return None
    return participant
