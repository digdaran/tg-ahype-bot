"""
Сервис отчётов: продажи по дням/месяцам, онлайн/офлайн продажи, отчёты по
операторам/администраторам/платёжным системам, по выданным номеркам,
по участникам, финансовые отчёты. Экспорт в CSV/XLSX выполняется в
app/admin_api/routers/reports.py поверх данных, возвращаемых этим сервисом.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ManualRegistrationStatusEnum, PaymentStatusEnum, TicketSourceEnum
from app.models.manual_registration import ManualRegistration
from app.models.panel_user import PanelUser
from app.models.participant import Participant
from app.models.payment import Payment
from app.models.ticket import Ticket


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _succeeded_payments(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> list[Payment]:
        """
        Возвращает оплаченные платежи для группировки по дате.

        Группировка выполняется в Python, а не через SQL date()/strftime() —
        так проще и не завязано на конкретный диалект (сейчас только SQLite,
        см. README).
        """
        stmt = select(Payment).where(Payment.status == PaymentStatusEnum.SUCCEEDED)
        if date_from:
            stmt = stmt.where(Payment.confirmed_at >= date_from)
        if date_to:
            stmt = stmt.where(Payment.confirmed_at <= date_to)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def sales_by_day(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> list[dict[str, Any]]:
        payments = await self._succeeded_payments(date_from, date_to)
        buckets: dict[str, dict[str, Any]] = {}
        for p in payments:
            if not p.confirmed_at:
                continue
            key = p.confirmed_at.strftime("%Y-%m-%d")
            bucket = buckets.setdefault(key, {"day": key, "count": 0, "amount": 0.0})
            bucket["count"] += 1
            bucket["amount"] += float(p.amount)
        return [buckets[k] for k in sorted(buckets.keys())]

    async def sales_by_month(self) -> list[dict[str, Any]]:
        payments = await self._succeeded_payments()
        buckets: dict[str, dict[str, Any]] = {}
        for p in payments:
            if not p.confirmed_at:
                continue
            key = p.confirmed_at.strftime("%Y-%m")
            bucket = buckets.setdefault(key, {"month": key, "count": 0, "amount": 0.0})
            bucket["count"] += 1
            bucket["amount"] += float(p.amount)
        return [buckets[k] for k in sorted(buckets.keys())]

    async def online_vs_offline(self) -> dict[str, Any]:
        online_result = await self.session.execute(
            select(func.count()).select_from(Ticket).where(Ticket.source == TicketSourceEnum.ONLINE)
        )
        offline_result = await self.session.execute(
            select(func.count()).select_from(Ticket).where(Ticket.source == TicketSourceEnum.MANUAL)
        )
        return {"online_tickets": online_result.scalar_one(), "offline_tickets": offline_result.scalar_one()}

    async def by_operator(self) -> list[dict[str, Any]]:
        stmt = (
            select(
                PanelUser.login,
                func.count(ManualRegistration.id).label("registrations"),
                func.coalesce(func.sum(ManualRegistration.quantity), 0).label("tickets"),
            )
            .join(ManualRegistration, ManualRegistration.operator_id == PanelUser.id)
            .where(ManualRegistration.status == ManualRegistrationStatusEnum.CONFIRMED)
            .group_by(PanelUser.login)
            .order_by(func.count(ManualRegistration.id).desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [{"operator": r.login, "registrations": r.registrations, "tickets": r.tickets} for r in rows]

    async def by_payment_provider(self) -> list[dict[str, Any]]:
        stmt = (
            select(
                Payment.provider,
                func.count(Payment.id).label("count"),
                func.coalesce(func.sum(Payment.amount), 0).label("amount"),
            )
            .where(Payment.status == PaymentStatusEnum.SUCCEEDED)
            .group_by(Payment.provider)
        )
        rows = (await self.session.execute(stmt)).all()
        return [{"provider": r.provider.value, "count": r.count, "amount": float(r.amount)} for r in rows]

    async def tickets_issued_report(self) -> list[dict[str, Any]]:
        stmt = (
            select(Ticket.giveaway_id, Ticket.source, func.count(Ticket.id).label("count"))
            .group_by(Ticket.giveaway_id, Ticket.source)
        )
        rows = (await self.session.execute(stmt)).all()
        return [{"giveaway_id": r.giveaway_id, "source": r.source.value, "count": r.count} for r in rows]

    async def participants_report(self, limit: int = 100) -> list[dict[str, Any]]:
        stmt = (
            select(
                Participant.phone,
                Participant.full_name,
                func.count(Ticket.id).label("tickets"),
            )
            .outerjoin(Ticket, Ticket.participant_id == Participant.id)
            .group_by(Participant.id)
            .order_by(func.count(Ticket.id).desc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [{"phone": r.phone, "full_name": r.full_name, "tickets": r.tickets} for r in rows]

    async def financial_summary(self) -> dict[str, Any]:
        total_result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatusEnum.SUCCEEDED)
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(Payment).where(Payment.status == PaymentStatusEnum.SUCCEEDED)
        )
        total = float(total_result.scalar_one())
        count = count_result.scalar_one()
        return {
            "total_revenue": total,
            "successful_payments": count,
            "average_check": (total / count) if count else 0.0,
        }
