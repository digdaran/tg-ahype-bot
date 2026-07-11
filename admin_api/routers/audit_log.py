"""Раздел «Журнал аудита»."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.models.panel_user import PanelUser
from app.repositories.audit_log_repo import AuditLogRepository
from app.schemas.audit_log import AuditLogListResponse, AuditLogOut

router = APIRouter(prefix="/api/audit-log", tags=["audit_log"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_log(
    action: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("audit_log.view")),
) -> AuditLogListResponse:
    repo = AuditLogRepository(session)
    items, total = await repo.list_filtered(action=action, actor_id=actor_id, entity_type=entity_type, limit=limit, offset=offset)
    return AuditLogListResponse(items=[AuditLogOut.model_validate(i) for i in items], total=total)
