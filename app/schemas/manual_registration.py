from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import ManualRegistrationStatusEnum


class ManualRegistrationCreateRequest(BaseModel):
    phone: str
    giveaway_id: str
    quantity: int = Field(gt=0)
    comment: Optional[str] = None


class ManualRegistrationOut(BaseModel):
    id: str
    participant_id: str
    giveaway_id: str
    quantity: int
    comment: Optional[str] = None
    status: ManualRegistrationStatusEnum
    operator_id: str
    cancelled_by_id: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ManualRegistrationListResponse(BaseModel):
    items: list[ManualRegistrationOut]
    total: int
