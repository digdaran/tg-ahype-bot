"""Раздел «Настройки»: платёжный провайдер (override), контакты, постеры.
Стоимость/лимит номерков задаются на уровне конкретного розыгрыша (см. giveaways.py)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.config import get_settings as get_app_settings
from app.models.enums import AuditActorTypeEnum
from app.models.panel_user import PanelUser
from app.payments.factory import available_providers
from app.schemas.settings import SettingsOut, SettingsUpdateRequest
from app.services.audit_service import AuditService
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("settings.view")),
) -> SettingsOut:
    service = SettingsService(session)
    settings_row = await service.get()
    active_provider = await service.get_active_payment_provider()
    return SettingsOut(
        payment_provider_override=settings_row.payment_provider_override,
        active_payment_provider=active_provider,
        support_contact=settings_row.support_contact,
        poster_settings_note=settings_row.poster_settings_note,
    )


@router.get("/payment-providers")
async def list_payment_providers(_: PanelUser = Depends(require_permission("settings.view"))) -> dict:
    return {"providers": available_providers(), "env_default": get_app_settings().payment_provider.value}


@router.patch("", response_model=SettingsOut)
async def update_settings(
    payload: SettingsUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("settings.edit")),
) -> SettingsOut:
    service = SettingsService(session)
    if payload.clear_payment_provider_override:
        await service.set_payment_provider_override(None)
    elif payload.payment_provider_override is not None:
        await service.set_payment_provider_override(payload.payment_provider_override)

    settings_row = await service.update(
        support_contact=payload.support_contact,
        poster_settings_note=payload.poster_settings_note,
    )

    await AuditService(session).log(
        action="settings.updated",
        actor_type=AuditActorTypeEnum.PANEL_USER,
        actor_id=current_user.id,
        actor_label=current_user.login,
        entity_type="platform_settings",
        details=payload.model_dump(exclude_none=True),
    )
    await session.commit()

    active_provider = await service.get_active_payment_provider()
    return SettingsOut(
        payment_provider_override=settings_row.payment_provider_override,
        active_payment_provider=active_provider,
        support_contact=settings_row.support_contact,
        poster_settings_note=settings_row.poster_settings_note,
    )
