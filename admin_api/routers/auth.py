"""Аутентификация пользователей веб-панели."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_client_ip, get_current_user, get_db
from app.core.exceptions import AuthError, UserBlockedError
from app.models.panel_user import PanelUser
from app.schemas.auth import LoginRequest, PanelUserOut, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(session)
    try:
        access_token, refresh_token, _ = await service.authenticate(
            payload.login, payload.password, ip_address=get_client_ip(request)
        )
        await session.commit()
    except AuthError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserBlockedError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: PanelUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = AuthService(session)
    await service.logout(current_user, ip_address=get_client_ip(request))
    await session.commit()
    return {"ok": True}


@router.get("/me", response_model=PanelUserOut)
async def me(current_user: PanelUser = Depends(get_current_user)) -> PanelUser:
    return current_user
