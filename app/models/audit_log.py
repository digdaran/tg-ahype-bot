"""
Журнал аудита. Логируются абсолютно все значимые действия:
вход/выход, изменение настроек, регистрация участников, платежи,
выдача номерков, ручная регистрация, рассылки, изменения пользователей,
действия операторов, ошибки API.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import gen_uuid
from app.models.enums import AuditActorTypeEnum


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    actor_type: Mapped[AuditActorTypeEnum] = mapped_column(
        Enum(AuditActorTypeEnum, native_enum=False), nullable=False
    )
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    actor_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-строка
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog {self.action} by {self.actor_label}>"
