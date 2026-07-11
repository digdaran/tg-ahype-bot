"""Раздел «Продажи»: онлайн-платежи, статусы, экспорт."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.models.enums import PaymentProviderEnum, PaymentStatusEnum
from app.models.panel_user import PanelUser
from app.repositories.payment_repo import PaymentRepository
from app.schemas.payment import PaymentListResponse, PaymentOut

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("", response_model=PaymentListResponse)
async def list_sales(
    status_filter: Optional[PaymentStatusEnum] = Query(default=None, alias="status"),
    provider: Optional[PaymentProviderEnum] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("sales.view")),
) -> PaymentListResponse:
    repo = PaymentRepository(session)
    items, total = await repo.list_filtered(
        status=status_filter, provider=provider, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
    return PaymentListResponse(items=[PaymentOut.model_validate(i) for i in items], total=total)


@router.get("/export")
async def export_sales(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("sales.export")),
) -> StreamingResponse:
    repo = PaymentRepository(session)
    items, _ = await repo.list_filtered(limit=100000, offset=0)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["order_id", "participant_id", "provider", "amount", "currency", "status", "created_at", "confirmed_at"])
    for p in items:
        writer.writerow(
            [p.order_id, p.participant_id, p.provider.value, float(p.amount), p.currency, p.status.value,
             p.created_at.isoformat(), p.confirmed_at.isoformat() if p.confirmed_at else ""]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_export.csv"},
    )
