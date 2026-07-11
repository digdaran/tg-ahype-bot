"""Репозиторий глобальных настроек платформы (singleton, id=1)."""
from __future__ import annotations

from app.models.settings import PlatformSettings
from app.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[PlatformSettings]):
    model = PlatformSettings

    async def get_or_create(self) -> PlatformSettings:
        instance = await self.session.get(PlatformSettings, 1)
        if instance is None:
            instance = PlatformSettings(id=1)
            self.session.add(instance)
            await self.session.flush()
        return instance
