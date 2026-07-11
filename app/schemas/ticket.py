from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import TicketSourceEnum


class TicketOut(BaseModel):
    id: str
    giveaway_id: str
    number: int
    full_code: str
    participant_id: str
    source: TicketSourceEnum
    payment_id: Optional[str] = None
    manual_registration_id: Optional[str] = None
    issued_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: list[TicketOut]
    total: int
