from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GiveawayCreateRequest(BaseModel):
    name: str
    prefix: str = Field(min_length=1, max_length=16)
    ticket_price: float = Field(gt=0)
    max_tickets: int = Field(gt=0)


class GiveawayUpdateRequest(BaseModel):
    name: Optional[str] = None
    ticket_price: Optional[float] = Field(default=None, gt=0)
    max_tickets: Optional[int] = Field(default=None, gt=0)


class GiveawayOut(BaseModel):
    id: str
    name: str
    prefix: str
    ticket_price: float
    max_tickets: int
    tickets_issued: int
    tickets_remaining: int
    is_registration_open: bool
    is_locked: bool
    is_immutable: bool
    opened_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    digital_poster_file_id: Optional[str] = None
    digital_poster_caption: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
