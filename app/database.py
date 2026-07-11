"""
Настройка асинхронного подключения к БД через SQLAlchemy 2.x.

Архитектура намеренно не зависит от конкретной СУБД: сейчас используется
SQLite (aiosqlite), переход на PostgreSQL (asyncpg) выполняется исключительно
изменением DATABASE_URL в .env — ни модели, ни репозитории, ни сервисы
менять не требуется.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: сессия БД на один запрос."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Контекстный менеджер для использования вне FastAPI (боты, скрипты)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
