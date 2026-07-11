from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ParticipantOut(BaseModel):
    id: str
    phone: str
    full_name: Optional[str] = None
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    vk_user_id: Optional[int] = None
    vk_username: Optional[str] = None
    is_blocked: bool
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParticipantUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    comment: Optional[str] = None
    is_blocked: Optional[bool] = None


class ParticipantListResponse(BaseModel):
    items: list[ParticipantOut]
    total: int
