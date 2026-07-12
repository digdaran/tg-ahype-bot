"""
Централизованная конфигурация приложения.
Все настройки читаются из переменных окружения (.env).
"""
from functools import lru_cache
from typing import List, Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Общие
    app_env: str = "production"
    app_secret_key: str = "insecure-dev-key"
    app_timezone: str = "Europe/Moscow"
    app_base_url: str = "http://localhost:8000"

    # БД
    database_url: str = "sqlite+aiosqlite:///./data/db.sqlite3"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 30
    jwt_refresh_ttl_days: int = 14

    # Telegram
    # Общий выключатель интеграции: если False — бот-процесс (bots/telegram/bot.py)
    # запускается, но ничего не делает (не подключается к Telegram), а backend
    # (уведомления после оплаты, рассылки) не пытается слать через Telegram,
    # даже если у участника есть привязанный telegram_user_id. Основной способ
    # реально не запускать контейнер бота — переменная COMPOSE_PROFILES (см.
    # .env.example и docker-compose.yml); этот флаг — второй уровень защиты на
    # случай, если контейнер всё же запущен.
    telegram_enabled: bool = True
    telegram_bot_token: str = ""
    # Прокси для связи бота с api.telegram.org (если Telegram недоступен напрямую
    # с сервера). Формат: http://user:pass@host:port или socks5://user:pass@host:port
    telegram_proxy_url: Optional[str] = None

    # VK
    # Аналогично telegram_enabled — общий выключатель VK-интеграции.
    vk_enabled: bool = True
    vk_group_token: str = ""
    # Строка, а не число: vkbottle сам определяет группу по VK_GROUP_TOKEN,
    # это поле нигде не используется как число — принимаем как есть, в любом
    # формате, как его показывает сам VK (например "club4237650"), чтобы не
    # ловить ValidationError на реальных значениях, скопированных из URL группы.
    vk_group_id: str = ""
    # Прокси для VK API — обычно не требуется (VK не блокируется в РФ),
    # но поддержан на случай блокировок исходящего трафика с хостинга.
    vk_proxy_url: Optional[str] = None

    # Платёжный провайдер
    payment_provider: Literal["tbank", "vtb"] = "tbank"

    tbank_terminal_key: str = ""
    tbank_secret_key: str = ""
    tbank_api_url: str = "https://securepay.tinkoff.ru/v2"

    vtb_merchant_id: str = ""
    vtb_secret_key: str = ""
    vtb_api_url: str = "https://api.vtb.ru/acquiring/v1"

    # Первичный супер-админ
    initial_superadmin_login: str = "superadmin"
    initial_superadmin_password: str = "change-me"

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
