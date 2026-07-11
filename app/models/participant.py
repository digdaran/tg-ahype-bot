"""
Участник розыгрыша.

Главный идентификатор — номер телефона (уникален, обязателен).
Telegram и VK ID — вторичные, необязательные, привязываются автоматически
при первом запуске бота с уже известным номером телефона.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.ticket import Ticket
    from app.models.manual_registration import ManualRegistration


class Participant(Base, TimestampMixin):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)

    # Главный идентификатор
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)

    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Вторичные идентификаторы
    telegram_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    vk_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    vk_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    payments: Mapped[list["Payment"]] = relationship(back_populates="participant")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="participant")
    manual_registrations: Mapped[list["ManualRegistration"]] = relationship(back_populates="participant")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Participant {self.phone}>"
