"""Репозиторий ручных регистраций (офлайн-продажи)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from app.models.enums import ManualRegistrationStatusEnum
from app.models.manual_registration import ManualRegistration
from app.repositories.base import BaseRepository


class ManualRegistrationRepository(BaseRepository[ManualRegistration]):
    model = ManualRegistration

    async def list_by_participant(self, participant_id: str) -> list[ManualRegistration]:
        result = await self.session.execute(
            select(ManualRegistration)
            .where(ManualRegistration.participant_id == participant_id)
            .order_by(ManualRegistration.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_filtered(
        self,
        status: Optional[ManualRegistrationStatusEnum] = None,
        operator_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ManualRegistration], int]:
        stmt = select(ManualRegistration)
        count_stmt = select(func.count()).select_from(ManualRegistration)
        if status is not None:
            stmt = stmt.where(ManualRegistration.status == status)
            count_stmt = count_stmt.where(ManualRegistration.status == status)
        if operator_id is not None:
            stmt = stmt.where(ManualRegistration.operator_id == operator_id)
            count_stmt = count_stmt.where(ManualRegistration.operator_id == operator_id)
        stmt = stmt.order_by(ManualRegistration.created_at.desc()).limit(limit).offset(offset)
        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total
