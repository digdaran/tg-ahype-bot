"""
Сервис регистрации участников.

Главный идентификатор — номер телефона. Telegram ID — вторичный,
привязывается автоматически при первом запуске бота, если участник с таким
телефоном уже существует.

VK-интеграция полностью удалена из проекта (вернёмся к ней отдельно позже) —
если понадобится восстановить привязку по VK, смотрите git-историю этого
файла (методы link_vk/find_by_vk_id).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.enums import AuditActorTypeEnum
from app.models.participant import Participant
from app.repositories.participant_repo import ParticipantRepository
from app.services.audit_service import AuditService

try:
    import phonenumbers
except ImportError:  # pragma: no cover
    phonenumbers = None


def normalize_phone(raw_phone: str) -> str:
    """Приводит номер телефона к формату +7XXXXXXXXXX."""
    raw_phone = raw_phone.strip()
    if phonenumbers is not None:
        try:
            parsed = phonenumbers.parse(raw_phone, "RU")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass
    digits = "".join(c for c in raw_phone if c.isdigit())
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) != 11:
        raise ValidationError(f"Некорректный номер телефона: {raw_phone}")
    return "+" + digits


class RegistrationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.participants = ParticipantRepository(session)
        self.audit = AuditService(session)

    async def get_or_create_by_phone(self, phone: str, full_name: Optional[str] = None) -> tuple[Participant, bool]:
        normalized = normalize_phone(phone)
        participant = await self.participants.get_by_phone(normalized)
        if participant:
            return participant, False

        participant = Participant(phone=normalized, full_name=full_name)
        await self.participants.add(participant)
        await self.audit.log(
            action="participant.registered",
            actor_type=AuditActorTypeEnum.SYSTEM,
            entity_type="participant",
            entity_id=participant.id,
            details={"phone": normalized, "full_name": full_name},
        )
        return participant, True

    async def link_telegram(self, phone: str, telegram_user_id: int, telegram_username: Optional[str]) -> Participant:
        """
        Привязывает Telegram ID к участнику по номеру телефона.
        Если участник уже существовал (например, ранее купил номерки офлайн)
        — Telegram ID подключается к его существующей записи.
        """
        participant, created = await self.get_or_create_by_phone(phone)

        existing_by_tg = await self.participants.get_by_telegram_id(telegram_user_id)
        if existing_by_tg and existing_by_tg.id != participant.id:
            raise ValidationError("Этот Telegram-аккаунт уже привязан к другому номеру телефона")

        participant.telegram_user_id = telegram_user_id
        participant.telegram_username = telegram_username
        await self.session.flush()

        await self.audit.log(
            action="participant.telegram_linked",
            actor_type=AuditActorTypeEnum.BOT,
            entity_type="participant",
            entity_id=participant.id,
            details={"telegram_user_id": telegram_user_id, "telegram_username": telegram_username, "new": created},
        )
        return participant

    async def find_by_telegram_id(self, telegram_user_id: int) -> Optional[Participant]:
        return await self.participants.get_by_telegram_id(telegram_user_id)
