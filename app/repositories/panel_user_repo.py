"""Репозиторий пользователей веб-панели."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.models.panel_user import PanelUser
from app.repositories.base import BaseRepository


class PanelUserRepository(BaseRepository[PanelUser]):
    model = PanelUser

    async def get_by_login(self, login: str) -> Optional[PanelUser]:
        result = await self.session.execute(select(PanelUser).where(PanelUser.login == login))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[PanelUser]:
        result = await self.session.execute(select(PanelUser).order_by(PanelUser.created_at.desc()))
        return list(result.scalars().all())
