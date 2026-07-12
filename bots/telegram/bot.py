"""
Точка входа Telegram-бота (aiogram 3, long polling).

Бот использует общий пакет app/* (модели, репозитории, сервисы) напрямую —
он работает с той же базой данных, что и веб-панель/backend, без
промежуточного HTTP API. Уведомления после подтверждения оплаты (в т.ч. если
webhook пришёл, пока бот был выключен) отправляются backend'ом напрямую через
Telegram Bot API (см. app/services/notification_service.py) — поэтому
работоспособность оплаты не зависит от того, запущен ли процесс бота.

Если сервер не имеет прямого доступа к api.telegram.org (блокировки и т.п.),
задайте TELEGRAM_PROXY_URL в .env — бот пойдёт через HTTP(S) или SOCKS5
прокси (см. AiohttpSession ниже). Без этой переменной прокси не используется.

Выключатель: TELEGRAM_ENABLED=false в .env — процесс запускается (контейнер
остаётся "healthy"), но к Telegram не подключается и ничего не делает. Чтобы
контейнер вообще не запускался — уберите профиль "telegram" из
COMPOSE_PROFILES (см. .env.example и docker-compose.yml). Флаг — вторая
линия защиты на случай, если контейнер всё же поднят.

Запуск: python -m bots.telegram.bot
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from bots.telegram.handlers import help as help_handler
from bots.telegram.handlers import payment_check, purchase, start, tickets

settings = get_settings()
configure_logging(settings.app_env)
logger = get_logger(__name__)


def _build_session() -> AiohttpSession | None:
    """
    Если задан TELEGRAM_PROXY_URL — создаёт сессию с прокси (HTTP/HTTPS/SOCKS5,
    с авторизацией или без). Требует пакет aiohttp-socks (уже в
    requirements/telegram.txt). Если переменная не задана — возвращает None,
    и aiogram использует обычное прямое соединение.
    """
    if not settings.telegram_proxy_url:
        return None
    logger.info("telegram_bot_using_proxy", proxy=_mask_proxy(settings.telegram_proxy_url))
    return AiohttpSession(proxy=settings.telegram_proxy_url)


def _mask_proxy(proxy_url: str) -> str:
    """Прячет логин/пароль прокси при логировании."""
    if "@" not in proxy_url:
        return proxy_url
    scheme_and_auth, _, host_part = proxy_url.rpartition("@")
    scheme = scheme_and_auth.split("://", 1)[0]
    return f"{scheme}://***:***@{host_part}"


async def main() -> None:
    if not settings.telegram_enabled:
        logger.info("telegram_bot_disabled")
        # Намеренно не выходим (иначе Docker с restart:unless-stopped будет
        # бесконечно перезапускать контейнер) — просто ничего не делаем.
        await asyncio.Event().wait()
        return

    if not settings.telegram_bot_token:
        logger.error("telegram_bot_token_missing")
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан в .env")

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=_build_session(),
    )
    dispatcher = Dispatcher()

    dispatcher.include_router(start.router)
    dispatcher.include_router(purchase.router)
    dispatcher.include_router(payment_check.router)
    dispatcher.include_router(tickets.router)
    dispatcher.include_router(help_handler.router)

    logger.info("telegram_bot_starting")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
