"""
Прямые вызовы Telegram Bot API по HTTP (без aiogram).

Используется backend'ом (рассылки, автоматические уведомления после оплаты),
чтобы не тянуть aiogram в зависимости веб-панели и не зависеть от того,
запущен ли процесс телеграм-бота в данный момент.

Если TELEGRAM_PROXY_URL задан в .env — все вызовы идут через этот прокси
(HTTP/HTTPS/SOCKS5), так же как и у самого бота (см. bots/telegram/bot.py).
"""
from __future__ import annotations

from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()

_BASE_URL = "https://api.telegram.org/bot{token}"


def _client(timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, proxy=settings.telegram_proxy_url or None)


async def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None) -> bool:
    if not settings.telegram_bot_token:
        return False
    url = f"{_BASE_URL.format(token=settings.telegram_bot_token)}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with _client(10) as client:
        try:
            response = await client.post(url, json=payload)
            return response.status_code == 200 and response.json().get("ok", False)
        except httpx.HTTPError:
            return False


async def send_photo(chat_id: int, photo: str, caption: Optional[str] = None) -> bool:
    """photo — это либо file_id (уже загруженный в Telegram), либо публичный URL картинки."""
    if not settings.telegram_bot_token:
        return False
    url = f"{_BASE_URL.format(token=settings.telegram_bot_token)}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    async with _client(15) as client:
        try:
            response = await client.post(url, json=payload)
            return response.status_code == 200 and response.json().get("ok", False)
        except httpx.HTTPError:
            return False
