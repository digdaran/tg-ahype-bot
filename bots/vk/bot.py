"""
Точка входа VK-бота (vkbottle, long polling).

Как и Telegram-бот, работает с общим пакетом app/* напрямую (та же БД).
Уведомления после подтверждения оплаты отправляются backend'ом напрямую
через VK API (app/services/notification_service.py), поэтому не зависят
от того, запущен ли процесс этого бота.

Выключатель: VK_ENABLED=false в .env — процесс запускается (контейнер
остаётся "healthy"), но к VK не подключается и ничего не делает. Чтобы
контейнер вообще не запускался — уберите профиль "vk" из COMPOSE_PROFILES
(см. .env.example и docker-compose.yml). Флаг — вторая линия защиты на
случай, если контейнер всё же поднят.

Запуск: python -m bots.vk.bot
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from vkbottle.bot import Bot

from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from bots.vk.handlers import help as help_handler
from bots.vk.handlers import payment_check, purchase, start, tickets

settings = get_settings()
configure_logging(settings.app_env)
logger = get_logger(__name__)


def main() -> None:
    if not settings.vk_enabled:
        logger.info("vk_bot_disabled")
        # Намеренно не выходим (иначе Docker с restart:unless-stopped будет
        # бесконечно перезапускать контейнер) — просто ничего не делаем.
        import time

        while True:
            time.sleep(3600)

    if not settings.vk_group_token:
        logger.error("vk_group_token_missing")
        raise SystemExit("VK_GROUP_TOKEN не задан в .env")

    bot = Bot(token=settings.vk_group_token)

    start.register(bot)
    purchase.register(bot)
    payment_check.register(bot)
    tickets.register(bot)
    help_handler.register(bot)

    logger.info("vk_bot_starting")
    bot.run_forever()


if __name__ == "__main__":
    main()
