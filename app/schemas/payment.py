from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import PaymentProviderEnum, PaymentStatusEnum


class PaymentOut(BaseModel):
    id: str
    order_id: str
    participant_id: str
    giveaway_id: str
    provider: PaymentProviderEnum
    provider_payment_id: Optional[str] = None
    quantity: int
    amount: float
    currency: str
    status: PaymentStatusEnum
    payment_url: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    items: list[PaymentOut]
    total: int
