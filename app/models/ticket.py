"""
Номерок (билет участника розыгрыша).

full_code = <prefix розыгрыша><порядковый номер>, например HYPE2026-000123.
Номерки всегда принадлежат участнику (Participant), а не Telegram/VK ID.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import gen_uuid
from app.models.enums import TicketSourceEnum

if TYPE_CHECKING:
    from app.models.participant import Participant
    from app.models.giveaway import Giveaway
    from app.models.payment import Payment
    from app.models.manual_registration import ManualRegistration


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    giveaway_id: Mapped[str] = mapped_column(ForeignKey("giveaways.id"), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    full_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id"), nullable=False, index=True)

    source: Mapped[TicketSourceEnum] = mapped_column(
        Enum(TicketSourceEnum, native_enum=False), nullable=False
    )

    payment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("payments.id"), nullable=True, index=True)
    manual_registration_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("manual_registrations.id"), nullable=True, index=True
    )

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    giveaway: Mapped["Giveaway"] = relationship(back_populates="tickets")
    participant: Mapped["Participant"] = relationship(back_populates="tickets")
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="tickets")
    manual_registration: Mapped[Optional["ManualRegistration"]] = relationship(back_populates="tickets")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Ticket {self.full_code}>"
