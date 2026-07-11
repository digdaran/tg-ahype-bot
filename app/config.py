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
    telegram_bot_token: str = ""
    # Прокси для связи бота с api.telegram.org (если Telegram недоступен напрямую
    # с сервера). Формат: http://user:pass@host:port или socks5://user:pass@host:port
    telegram_proxy_url: Optional[str] = None

    # VK
    vk_group_token: str = ""
    vk_group_id: int = 0
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
