"""Сервис журнала аудита. Логируются все значимые действия платформы."""
from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditActorTypeEnum
from app.repositories.audit_log_repo import AuditLogRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        action: str,
        actor_type: AuditActorTypeEnum = AuditActorTypeEnum.SYSTEM,
        actor_id: Optional[str] = None,
        actor_label: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details, ensure_ascii=False, default=str) if details is not None else None,
            ip_address=ip_address,
        )
        return await self.repo.add(entry)
