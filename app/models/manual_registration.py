"""
Ручная регистрация (офлайн-продажа физического постера оператором).

При ручной продаже бот ничего не отправляет — постер физический,
выдаётся оператором лично. Хранится, кто и когда зарегистрировал,
для отмены до подтверждения и истории изменений.

Поток статусов: PENDING (создана) -> CONFIRMED (номерки выданы)
                                   -> CANCELLED (отменена до подтверждения)
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid
from app.models.enums import ManualRegistrationStatusEnum

if TYPE_CHECKING:
    from app.models.participant import Participant
    from app.models.giveaway import Giveaway
    from app.models.panel_user import PanelUser
    from app.models.ticket import Ticket


class ManualRegistration(Base, TimestampMixin):
    __tablename__ = "manual_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id"), nullable=False, index=True)
    giveaway_id: Mapped[str] = mapped_column(ForeignKey("giveaways.id"), nullable=False, index=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    status: Mapped[ManualRegistrationStatusEnum] = mapped_column(
        Enum(ManualRegistrationStatusEnum, native_enum=False),
        default=ManualRegistrationStatusEnum.PENDING,
        nullable=False,
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    operator_id: Mapped[str] = mapped_column(ForeignKey("panel_users.id"), nullable=False, index=True)
    cancelled_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("panel_users.id"), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    participant: Mapped["Participant"] = relationship(back_populates="manual_registrations")
    giveaway: Mapped["Giveaway"] = relationship()
    operator: Mapped["PanelUser"] = relationship(foreign_keys=[operator_id])
    cancelled_by: Mapped[Optional["PanelUser"]] = relationship(foreign_keys=[cancelled_by_id])
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="manual_registration")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ManualRegistration {self.id} qty={self.quantity}>"
