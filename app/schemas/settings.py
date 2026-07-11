from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.models.enums import PaymentProviderEnum


class SettingsOut(BaseModel):
    payment_provider_override: Optional[PaymentProviderEnum] = None
    active_payment_provider: PaymentProviderEnum
    support_contact: Optional[str] = None
    poster_settings_note: Optional[str] = None

    model_config = {"from_attributes": True}


class SettingsUpdateRequest(BaseModel):
    payment_provider_override: Optional[PaymentProviderEnum] = None
    clear_payment_provider_override: bool = False
    support_contact: Optional[str] = None
    poster_settings_note: Optional[str] = None
