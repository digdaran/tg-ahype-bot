"""Раздел «Розыгрыши»: создание, открытие/закрытие регистрации, блокировка."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.core.exceptions import GiveawayImmutableError, ValidationError
from app.models.panel_user import PanelUser
from app.schemas.giveaway import GiveawayCreateRequest, GiveawayOut, GiveawayUpdateRequest
from app.services.giveaway_service import GiveawayService

router = APIRouter(prefix="/api/giveaways", tags=["giveaways"])


@router.get("", response_model=list[GiveawayOut])
async def list_giveaways(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("giveaways.view")),
) -> list[GiveawayOut]:
    service = GiveawayService(session)
    giveaways = await service.list_all()
    return [GiveawayOut.model_validate(g) for g in giveaways]


@router.post("", response_model=GiveawayOut, status_code=status.HTTP_201_CREATED)
async def create_giveaway(
    payload: GiveawayCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("giveaways.create")),
) -> GiveawayOut:
    service = GiveawayService(session)
    try:
        giveaway = await service.create(
            name=payload.name,
            prefix=payload.prefix,
            ticket_price=payload.ticket_price,
            max_tickets=payload.max_tickets,
            actor_id=current_user.id,
            actor_label=current_user.login,
        )
        await session.commit()
    except ValidationError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return GiveawayOut.model_validate(giveaway)


@router.get("/{giveaway_id}", response_model=GiveawayOut)
async def get_giveaway(
    giveaway_id: str,
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("giveaways.view")),
) -> GiveawayOut:
    service = GiveawayService(session)
    giveaway = await service.get(giveaway_id)
    if giveaway is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Розыгрыш не найден")
    return GiveawayOut.model_validate(giveaway)


@router.patch("/{giveaway_id}", response_model=GiveawayOut)
async def update_giveaway(
    giveaway_id: str,
    payload: GiveawayUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("giveaways.edit")),
) -> GiveawayOut:
    service = GiveawayService(session)
    try:
        giveaway = await service.update_params(
            giveaway_id,
            name=payload.name,
            ticket_price=payload.ticket_price,
            max_tickets=payload.max_tickets,
            actor_id=current_user.id,
            actor_label=current_user.login,
        )
        await session.commit()
    except GiveawayImmutableError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GiveawayOut.model_validate(giveaway)


@router.post("/{giveaway_id}/open", response_model=GiveawayOut)
async def open_registration(
    giveaway_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("giveaways.lock")),
) -> GiveawayOut:
    service = GiveawayService(session)
    try:
        giveaway = await service.open_registration(giveaway_id, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GiveawayOut.model_validate(giveaway)


@router.post("/{giveaway_id}/close", response_model=GiveawayOut)
async def close_registration(
    giveaway_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("giveaways.lock")),
) -> GiveawayOut:
    service = GiveawayService(session)
    try:
        giveaway = await service.close_registration(giveaway_id, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GiveawayOut.model_validate(giveaway)


@router.post("/{giveaway_id}/lock", response_model=GiveawayOut)
async def lock_giveaway(
    giveaway_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("giveaways.lock")),
) -> GiveawayOut:
    service = GiveawayService(session)
    try:
        giveaway = await service.set_locked(giveaway_id, True, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GiveawayOut.model_validate(giveaway)


@router.post("/{giveaway_id}/unlock", response_model=GiveawayOut)
async def unlock_giveaway(
    giveaway_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("giveaways.lock")),
) -> GiveawayOut:
    service = GiveawayService(session)
    try:
        giveaway = await service.set_locked(giveaway_id, False, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GiveawayOut.model_validate(giveaway)
