"""Раздел «Рассылки»: всем / оплатившим / неоплатившим / офлайн / онлайн / по датам / по кол-ву номерков."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.models.panel_user import PanelUser
from app.schemas.broadcast import BroadcastCreateRequest, BroadcastOut
from app.services.broadcast_service import BroadcastService

router = APIRouter(prefix="/api/broadcasts", tags=["broadcasts"])


@router.get("", response_model=list[BroadcastOut])
async def list_broadcasts(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("broadcasts.view")),
) -> list[BroadcastOut]:
    service = BroadcastService(session)
    items = await service.list_all()
    return [BroadcastOut.model_validate(i) for i in items]


@router.post("", response_model=BroadcastOut, status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    payload: BroadcastCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("broadcasts.send")),
) -> BroadcastOut:
    service = BroadcastService(session)
    audience_filter = {
        "audience": payload.audience,
        "date_from": payload.date_from,
        "date_to": payload.date_to,
        "min_tickets": payload.min_tickets,
        "max_tickets": payload.max_tickets,
    }
    broadcast = await service.create_draft(
        title=payload.title,
        message_text=payload.message_text,
        audience_filter=audience_filter,
        channel=payload.channel,
        created_by_id=current_user.id,
        created_by_label=current_user.login,
    )
    await session.commit()
    return BroadcastOut.model_validate(broadcast)


@router.post("/{broadcast_id}/send", response_model=BroadcastOut)
async def send_broadcast(
    broadcast_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("broadcasts.send")),
) -> BroadcastOut:
    service = BroadcastService(session)
    try:
        broadcast = await service.send(broadcast_id, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BroadcastOut.model_validate(broadcast)
