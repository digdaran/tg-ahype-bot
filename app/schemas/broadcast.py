from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.enums import BroadcastChannelEnum, BroadcastStatusEnum


class BroadcastCreateRequest(BaseModel):
    title: str
    message_text: str
    channel: BroadcastChannelEnum
    audience: str = "all"  # all|paid|unpaid|offline|online
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_tickets: Optional[int] = None
    max_tickets: Optional[int] = None


class BroadcastOut(BaseModel):
    id: str
    title: str
    message_text: str
    channel: BroadcastChannelEnum
    status: BroadcastStatusEnum
    created_by_id: str
    sent_at: Optional[datetime] = None
    stats: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
