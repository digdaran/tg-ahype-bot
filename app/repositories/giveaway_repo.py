"""Репозиторий розыгрышей."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.models.giveaway import Giveaway
from app.repositories.base import BaseRepository


class GiveawayRepository(BaseRepository[Giveaway]):
    model = Giveaway

    async def get_by_prefix(self, prefix: str) -> Optional[Giveaway]:
        result = await self.session.execute(select(Giveaway).where(Giveaway.prefix == prefix))
        return result.scalar_one_or_none()

    async def list_open_unlocked(self) -> list[Giveaway]:
        """Розыгрыши, доступные для покупки номерков прямо сейчас (несколько параллельно)."""
        result = await self.session.execute(
            select(Giveaway).where(Giveaway.is_registration_open.is_(True), Giveaway.is_locked.is_(False))
        )
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Giveaway]:
        result = await self.session.execute(
            select(Giveaway).order_by(Giveaway.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_locked_for_update(self, giveaway_id: str) -> Optional[Giveaway]:
        """Блокирующее чтение строки розыгрыша для атомарной выдачи номерков."""
        result = await self.session.execute(
            select(Giveaway).where(Giveaway.id == giveaway_id).with_for_update()
        )
        return result.scalar_one_or_none()
