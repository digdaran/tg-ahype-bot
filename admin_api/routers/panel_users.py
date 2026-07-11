"""Раздел «Пользователи панели»: создание, блокировка, смена пароля, роли."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.core.exceptions import ValidationError
from app.schemas.auth import PanelUserCreateRequest, PanelUserOut, PasswordChangeRequest
from app.models.panel_user import PanelUser
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/panel-users", tags=["panel_users"])


@router.get("", response_model=list[PanelUserOut])
async def list_panel_users(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("panel_users.view")),
) -> list[PanelUserOut]:
    service = AuthService(session)
    users = await service.list_all()
    return [PanelUserOut.model_validate(u) for u in users]


@router.post("", response_model=PanelUserOut, status_code=status.HTTP_201_CREATED)
async def create_panel_user(
    payload: PanelUserCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("panel_users.manage")),
) -> PanelUserOut:
    service = AuthService(session)
    try:
        user = await service.create_user(
            login=payload.login,
            password=payload.password,
            role=payload.role,
            full_name=payload.full_name,
            actor_id=current_user.id,
            actor_label=current_user.login,
        )
        await session.commit()
    except ValidationError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return PanelUserOut.model_validate(user)


@router.post("/{user_id}/block", response_model=PanelUserOut)
async def block_panel_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("panel_users.manage")),
) -> PanelUserOut:
    service = AuthService(session)
    try:
        user = await service.set_blocked(user_id, True, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PanelUserOut.model_validate(user)


@router.post("/{user_id}/unblock", response_model=PanelUserOut)
async def unblock_panel_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("panel_users.manage")),
) -> PanelUserOut:
    service = AuthService(session)
    try:
        user = await service.set_blocked(user_id, False, actor_id=current_user.id, actor_label=current_user.login)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PanelUserOut.model_validate(user)


@router.post("/{user_id}/change-password", response_model=PanelUserOut)
async def change_password(
    user_id: str,
    payload: PasswordChangeRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("panel_users.manage")),
) -> PanelUserOut:
    service = AuthService(session)
    try:
        user = await service.change_password(
            user_id, payload.new_password, actor_id=current_user.id, actor_label=current_user.login
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PanelUserOut.model_validate(user)
