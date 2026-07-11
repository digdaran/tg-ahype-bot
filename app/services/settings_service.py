"""Сервис глобальных настроек платформы."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import PaymentProviderEnum
from app.models.settings import PlatformSettings
from app.repositories.settings_repo import SettingsRepository

app_settings = get_settings()


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SettingsRepository(session)

    async def get(self) -> PlatformSettings:
        return await self.repo.get_or_create()

    async def get_active_payment_provider(self) -> PaymentProviderEnum:
        """
        Активный платёжный провайдер.

        Приоритет: ручной override в панели администратора (Настройки) →
        иначе значение переменной окружения PAYMENT_PROVIDER.
        """
        settings_row = await self.get()
        if settings_row.payment_provider_override is not None:
            return settings_row.payment_provider_override
        # app_settings.payment_provider - это Literal["tbank","vtb"] (обычная строка),
        # приводим к PaymentProviderEnum, чтобы вызывающий код (PaymentService и т.д.)
        # всегда получал единый тип, а не "то enum, то строку" в зависимости от того,
        # задан ли override в БД.
        return PaymentProviderEnum(app_settings.payment_provider)

    async def set_payment_provider_override(self, provider: Optional[PaymentProviderEnum]) -> PlatformSettings:
        settings_row = await self.get()
        settings_row.payment_provider_override = provider
        await self.session.flush()
        return settings_row

    async def update(
        self,
        support_contact: Optional[str] = None,
        poster_settings_note: Optional[str] = None,
    ) -> PlatformSettings:
        settings_row = await self.get()
        if support_contact is not None:
            settings_row.support_contact = support_contact
        if poster_settings_note is not None:
            settings_row.poster_settings_note = poster_settings_note
        await self.session.flush()
        return settings_row
