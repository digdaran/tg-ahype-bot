"""
Онлайн-платёж.

Финализация платежа идемпотентна: повторный webhook с тем же
provider_payment_id / idempotency_key не приводит к повторной выдаче
номерков (см. app/services/payment_service.py).
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid
from app.models.enums import PaymentProviderEnum, PaymentStatusEnum

if TYPE_CHECKING:
    from app.models.participant import Participant
    from app.models.giveaway import Giveaway
    from app.models.ticket import Ticket


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id"), nullable=False, index=True)
    giveaway_id: Mapped[str] = mapped_column(ForeignKey("giveaways.id"), nullable=False, index=True)

    provider: Mapped[PaymentProviderEnum] = mapped_column(Enum(PaymentProviderEnum, native_enum=False), nullable=False)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)

    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum, native_enum=False), default=PaymentStatusEnum.PENDING, nullable=False
    )

    payment_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Идемпотентность: уникальный ключ финализации (напр. provider+provider_payment_id)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(191), unique=True, nullable=True)

    raw_webhook_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    participant: Mapped["Participant"] = relationship(back_populates="payments")
    giveaway: Mapped["Giveaway"] = relationship(back_populates="payments")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="payment")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Payment {self.order_id} {self.status}>"
