"""
Глобальные настройки платформы (singleton-запись, id=1).

Стоимость номерка и максимум задаются на уровне конкретного розыгрыша
(app/models/giveaway.py) — это позволяет вести несколько розыгрышей
одновременно с разными параметрами.

Здесь хранятся сквозные, не привязанные к конкретному розыгрышу настройки:
переопределение платёжного провайдера (по умолчанию берётся из .env),
контакты поддержки, глобальные заметки по постерам.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import PaymentProviderEnum


class PlatformSettings(Base, TimestampMixin):
    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Если задано — переопределяет PAYMENT_PROVIDER из .env без передеплоя.
    payment_provider_override: Mapped[Optional[PaymentProviderEnum]] = mapped_column(
        Enum(PaymentProviderEnum, native_enum=False), nullable=True
    )

    support_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    poster_settings_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
