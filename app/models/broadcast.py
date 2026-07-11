"""Рассылки участникам (всем / оплатившим / неоплатившим / офлайн / онлайн / по датам / по кол-ву номерков)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid
from app.models.enums import BroadcastChannelEnum, BroadcastStatusEnum


class Broadcast(Base, TimestampMixin):
    __tablename__ = "broadcasts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON-строка с фильтром аудитории: {"audience": "all|paid|unpaid|offline|online",
    # "date_from": ..., "date_to": ..., "min_tickets": ..., "max_tickets": ...}
    audience_filter: Mapped[str] = mapped_column(Text, nullable=False)

    channel: Mapped[BroadcastChannelEnum] = mapped_column(Enum(BroadcastChannelEnum, native_enum=False), nullable=False)
    status: Mapped[BroadcastStatusEnum] = mapped_column(
        Enum(BroadcastStatusEnum, native_enum=False), default=BroadcastStatusEnum.DRAFT, nullable=False
    )

    created_by_id: Mapped[str] = mapped_column(ForeignKey("panel_users.id"), nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # JSON-строка со статистикой отправки: {"sent": N, "failed": N, "total": N}
    stats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped["object"] = relationship("PanelUser")
