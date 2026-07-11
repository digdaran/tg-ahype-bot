"""Репозиторий участников. Номер телефона — главный идентификатор."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select

from app.models.participant import Participant
from app.repositories.base import BaseRepository


class ParticipantRepository(BaseRepository[Participant]):
    model = Participant

    async def get_by_phone(self, phone: str) -> Optional[Participant]:
        result = await self.session.execute(select(Participant).where(Participant.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[Participant]:
        result = await self.session.execute(
            select(Participant).where(Participant.telegram_user_id == telegram_user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_vk_id(self, vk_user_id: int) -> Optional[Participant]:
        result = await self.session.execute(select(Participant).where(Participant.vk_user_id == vk_user_id))
        return result.scalar_one_or_none()

    async def search(
        self,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Participant], int]:
        stmt = select(Participant)
        count_stmt = select(func.count()).select_from(Participant)

        if query:
            like = f"%{query}%"
            condition = or_(
                Participant.phone.ilike(like),
                Participant.full_name.ilike(like),
                Participant.telegram_username.ilike(like),
                Participant.vk_username.ilike(like),
            )
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        stmt = stmt.order_by(Participant.created_at.desc()).limit(limit).offset(offset)

        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Participant))
        return result.scalar_one()
