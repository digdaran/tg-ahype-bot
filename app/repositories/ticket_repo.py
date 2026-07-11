"""Репозиторий номерков."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from app.models.ticket import Ticket
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    model = Ticket

    async def get_by_full_code(self, full_code: str) -> Optional[Ticket]:
        result = await self.session.execute(select(Ticket).where(Ticket.full_code == full_code))
        return result.scalar_one_or_none()

    async def list_by_participant(self, participant_id: str) -> list[Ticket]:
        result = await self.session.execute(
            select(Ticket).where(Ticket.participant_id == participant_id).order_by(Ticket.issued_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_giveaway(self, giveaway_id: str, limit: int = 100, offset: int = 0) -> list[Ticket]:
        result = await self.session.execute(
            select(Ticket)
            .where(Ticket.giveaway_id == giveaway_id)
            .order_by(Ticket.number.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def max_number_for_giveaway(self, giveaway_id: str) -> int:
        result = await self.session.execute(
            select(func.max(Ticket.number)).where(Ticket.giveaway_id == giveaway_id)
        )
        value = result.scalar_one_or_none()
        return value or 0

    async def search(self, query: Optional[str] = None, limit: int = 50, offset: int = 0) -> tuple[list[Ticket], int]:
        stmt = select(Ticket)
        count_stmt = select(func.count()).select_from(Ticket)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(Ticket.full_code.ilike(like))
            count_stmt = count_stmt.where(Ticket.full_code.ilike(like))
        stmt = stmt.order_by(Ticket.issued_at.desc()).limit(limit).offset(offset)
        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total
