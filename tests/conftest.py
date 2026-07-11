"""
Общие фикстуры для тестов.

Тесты работают на изолированной in-memory SQLite (StaticPool держит одно
и то же соединение живым на всё время теста — иначе in-memory SQLite
"исчезает" между операциями, т.к. каждое новое соединение видело бы пустую
БД). Это не требует поднятого docker/Postgres и не трогает реальный
data/db.sqlite3 — тесты полностью изолированы от dev/prod окружения.
"""
from __future__ import annotations

import os
from typing import AsyncIterator

os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Импортируем app.models (не только app.database), чтобы вся metadata Base
# была заполнена перед create_all — иначе часть таблиц не создастся.
import app.models  # noqa: F401
from app.database import Base


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as s:
        yield s
