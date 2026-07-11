"""Пользователь веб-панели администратора (Super Admin / Administrator / Operator)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid
from app.models.enums import PanelRoleEnum


class PanelUser(Base, TimestampMixin):
    __tablename__ = "panel_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    login: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role: Mapped[PanelRoleEnum] = mapped_column(Enum(PanelRoleEnum, native_enum=False), nullable=False)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PanelUser {self.login} ({self.role})>"
