"""Раздел «Номерки»: поиск, кому принадлежат, история выдачи."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.models.panel_user import PanelUser
from app.repositories.ticket_repo import TicketRepository
from app.schemas.ticket import TicketListResponse, TicketOut

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=TicketListResponse)
async def search_tickets(
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("tickets.view")),
) -> TicketListResponse:
    repo = TicketRepository(session)
    items, total = await repo.search(query=q, limit=limit, offset=offset)
    return TicketListResponse(items=[TicketOut.model_validate(i) for i in items], total=total)


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("tickets.view")),
) -> TicketOut:
    repo = TicketRepository(session)
    ticket = await repo.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Номерок не найден")
    return TicketOut.model_validate(ticket)
