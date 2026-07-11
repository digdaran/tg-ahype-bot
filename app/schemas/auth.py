from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import PanelRoleEnum


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PanelUserOut(BaseModel):
    id: str
    login: str
    full_name: Optional[str] = None
    role: PanelRoleEnum
    is_blocked: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PanelUserCreateRequest(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None
    role: PanelRoleEnum


class PasswordChangeRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
