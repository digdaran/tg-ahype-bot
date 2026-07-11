"""Репозиторий рассылок."""
from __future__ import annotations

from sqlalchemy import select

from app.models.broadcast import Broadcast
from app.repositories.base import BaseRepository


class BroadcastRepository(BaseRepository[Broadcast]):
    model = Broadcast

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Broadcast]:
        result = await self.session.execute(
            select(Broadcast).order_by(Broadcast.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
