"""Раздел «Отчёты»: продажи по дням/месяцам, онлайн/офлайн, операторы, администраторы,
платёжные системы, номерки, участники, финансовые отчёты, экспорт CSV/XLSX."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.models.panel_user import PanelUser
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/sales-by-day")
async def sales_by_day(
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> list[dict]:
    return await ReportService(session).sales_by_day(date_from, date_to)


@router.get("/sales-by-month")
async def sales_by_month(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> list[dict]:
    return await ReportService(session).sales_by_month()


@router.get("/online-vs-offline")
async def online_vs_offline(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> dict:
    return await ReportService(session).online_vs_offline()


@router.get("/by-operator")
async def by_operator(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> list[dict]:
    return await ReportService(session).by_operator()


@router.get("/by-payment-provider")
async def by_payment_provider(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> list[dict]:
    return await ReportService(session).by_payment_provider()


@router.get("/tickets-issued")
async def tickets_issued(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> list[dict]:
    return await ReportService(session).tickets_issued_report()


@router.get("/participants")
async def participants_report(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> list[dict]:
    return await ReportService(session).participants_report()


@router.get("/financial-summary")
async def financial_summary(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> dict:
    return await ReportService(session).financial_summary()


@router.get("/participants/export")
async def export_participants(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("reports.view")),
) -> StreamingResponse:
    rows = await ReportService(session).participants_report(limit=100000)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["phone", "full_name", "tickets"])
    for r in rows:
        writer.writerow([r["phone"], r["full_name"] or "", r["tickets"]])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=participants_report.csv"},
    )
