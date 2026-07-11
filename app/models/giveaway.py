"""
Розыгрыш.

Архитектура поддерживает несколько независимых и одновременных розыгрышей.
Каждый розыгрыш имеет уникальный префикс, добавляемый к номеркам, чтобы
исключить пересечение номеров между розыгрышами.

Как только розыгрыш открыт (opened_at заполнен), его ключевые параметры
(prefix, ticket_price, max_tickets) становятся неизменяемыми — это
проверяется в сервисном слое (GiveawayImmutableError).

Блокировка (is_locked=True) запрещает выдачу новых номерков, но не влияет
на уже выданные номерки.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid

if TYPE_CHECKING:
    from app.models.ticket import Ticket
    from app.models.payment import Payment


class Giveaway(Base, TimestampMixin):
    __tablename__ = "giveaways"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)

    ticket_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_tickets: Mapped[int] = mapped_column(Integer, nullable=False)
    tickets_issued: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_registration_open: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Цифровой постер, выдаваемый после онлайн-оплаты
    digital_poster_file_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    digital_poster_caption: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="giveaway")
    payments: Mapped[list["Payment"]] = relationship(back_populates="giveaway")

    @property
    def is_immutable(self) -> bool:
        return self.opened_at is not None

    @property
    def tickets_remaining(self) -> int:
        return max(self.max_tickets - self.tickets_issued, 0)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Giveaway {self.prefix} ({self.name})>"
