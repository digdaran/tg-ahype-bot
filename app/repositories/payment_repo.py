"""Репозиторий онлайн-платежей."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select

from app.models.enums import PaymentProviderEnum, PaymentStatusEnum
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        result = await self.session.execute(select(Payment).where(Payment.order_id == order_id))
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        result = await self.session.execute(select(Payment).where(Payment.idempotency_key == key))
        return result.scalar_one_or_none()

    async def get_by_provider_payment_id(self, provider_payment_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        return result.scalar_one_or_none()

    async def get_locked_for_update_by_order_id(self, order_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.order_id == order_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_locked_for_update(self, payment_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_by_participant(self, participant_id: str) -> list[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.participant_id == participant_id).order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_filtered(
        self,
        status: Optional[PaymentStatusEnum] = None,
        provider: Optional[PaymentProviderEnum] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Payment], int]:
        stmt = select(Payment)
        count_stmt = select(func.count()).select_from(Payment)

        if status is not None:
            stmt = stmt.where(Payment.status == status)
            count_stmt = count_stmt.where(Payment.status == status)
        if provider is not None:
            stmt = stmt.where(Payment.provider == provider)
            count_stmt = count_stmt.where(Payment.provider == provider)
        if date_from is not None:
            stmt = stmt.where(Payment.created_at >= date_from)
            count_stmt = count_stmt.where(Payment.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Payment.created_at <= date_to)
            count_stmt = count_stmt.where(Payment.created_at <= date_to)

        stmt = stmt.order_by(Payment.created_at.desc()).limit(limit).offset(offset)
        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def sum_succeeded_amount(self) -> float:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatusEnum.SUCCEEDED
            )
        )
        return float(result.scalar_one())

    async def count_succeeded(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Payment).where(Payment.status == PaymentStatusEnum.SUCCEEDED)
        )
        return result.scalar_one()
