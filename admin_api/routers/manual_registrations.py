"""Раздел «Ручные регистрации»: создание, выдача номерков, отмена до подтверждения."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.core.exceptions import GiveawayLockedError, ValidationError
from app.models.enums import ManualRegistrationStatusEnum
from app.models.panel_user import PanelUser
from app.schemas.manual_registration import (
    ManualRegistrationCreateRequest,
    ManualRegistrationListResponse,
    ManualRegistrationOut,
)
from app.services.manual_registration_service import ManualRegistrationService

router = APIRouter(prefix="/api/manual-registrations", tags=["manual_registrations"])


@router.get("", response_model=ManualRegistrationListResponse)
async def list_manual_registrations(
    status_filter: Optional[ManualRegistrationStatusEnum] = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("manual_registration.view")),
) -> ManualRegistrationListResponse:
    service = ManualRegistrationService(session)
    items, total = await service.list_filtered(status=status_filter, limit=limit, offset=offset)
    return ManualRegistrationListResponse(items=[ManualRegistrationOut.model_validate(i) for i in items], total=total)


@router.post("", response_model=ManualRegistrationOut, status_code=status.HTTP_201_CREATED)
async def create_manual_registration(
    payload: ManualRegistrationCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("manual_registration.create")),
) -> ManualRegistrationOut:
    service = ManualRegistrationService(session)
    try:
        registration = await service.create(
            phone=payload.phone,
            giveaway_id=payload.giveaway_id,
            quantity=payload.quantity,
            operator_id=current_user.id,
            operator_label=current_user.login,
            comment=payload.comment,
        )
        await session.commit()
    except (ValidationError, GiveawayLockedError) as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ManualRegistrationOut.model_validate(registration)


@router.post("/{registration_id}/confirm", response_model=ManualRegistrationOut)
async def confirm_manual_registration(
    registration_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("manual_registration.create")),
) -> ManualRegistrationOut:
    service = ManualRegistrationService(session)
    try:
        registration = await service.confirm_and_issue_tickets(
            registration_id, operator_id=current_user.id, operator_label=current_user.login
        )
        await session.commit()
    except ValidationError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ManualRegistrationOut.model_validate(registration)


@router.post("/{registration_id}/cancel", response_model=ManualRegistrationOut)
async def cancel_manual_registration(
    registration_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("manual_registration.cancel")),
) -> ManualRegistrationOut:
    service = ManualRegistrationService(session)
    try:
        registration = await service.cancel(
            registration_id, operator_id=current_user.id, operator_label=current_user.login
        )
        await session.commit()
    except ValidationError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ManualRegistrationOut.model_validate(registration)
