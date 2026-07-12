"""
Создаёт таблицы БД, если их ещё нет.

Проект осознанно не использует Alembic — только SQLite, схема создаётся
напрямую через SQLAlchemy `Base.metadata.create_all()`. create_all()
идемпотентен (создаёт только отсутствующие таблицы) и безопасен запускать
при каждом старте контейнера, но НЕ умеет менять уже существующие таблицы
(добавлять/удалять колонки и т.п.) — если модели поменяются, для сервера с
реальными данными такое изменение нужно будет применить вручную (написать
разовый ALTER TABLE) или начать с чистой БД. Такое упрощение архитектуры —
осознанный выбор в пользу простоты для проекта на одной SQLite-базе без
Postgres (см. README).

Запуск: python -m scripts.init_db
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401 — регистрирует все модели в Base.metadata
from app.database import Base, engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы БД проверены/созданы (create_all).")


if __name__ == "__main__":
    asyncio.run(main())
