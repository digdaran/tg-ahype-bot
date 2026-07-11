"""Прямые вызовы VK API по HTTP (без vkbottle) — для уведомлений из backend."""
from __future__ import annotations

import random
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()

_API_URL = "https://api.vk.com/method"


async def send_message(user_id: int, text: str, random_id: Optional[int] = None) -> bool:
    if not settings.vk_group_token:
        return False
    async with httpx.AsyncClient(timeout=10, proxy=settings.vk_proxy_url or None) as client:
        try:
            response = await client.post(
                f"{_API_URL}/messages.send",
                data={
                    "access_token": settings.vk_group_token,
                    "user_id": user_id,
                    "message": text,
                    "random_id": random_id or random.randint(1, 2_000_000_000),
                    "v": "5.199",
                },
            )
            data = response.json()
            return "response" in data
        except httpx.HTTPError:
            return False
