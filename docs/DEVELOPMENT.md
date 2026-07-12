# Локальная разработка без Docker

## Backend (admin_api)

```bash
python3 -m venv .venv-backend
source .venv-backend/bin/activate
pip install -r requirements/backend.txt

cp .env.example .env   # отредактировать при необходимости

python -m scripts.init_db
python -m scripts.create_superadmin

uvicorn admin_api.main:app --reload --port 8000
```

## Telegram-бот

```bash
python3 -m venv .venv-telegram
source .venv-telegram/bin/activate
pip install -r requirements/telegram.txt

python -m bots.telegram.bot
```

> Backend и Telegram-бот используют разные `requirements/*.txt` (у FastAPI и
> aiogram разные зависимости) — используйте РАЗНЫЕ виртуальные окружения,
> так же, как в Docker-образах.

## Фронтенд

```bash
cd admin-frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

## Изменение схемы БД

Проект не использует Alembic (только SQLite, см. README раздел «База
данных»). После изменения моделей на чистой БД схема просто создастся
заново через `python -m scripts.init_db`. Если БД уже существует и в ней
есть данные — новую колонку/таблицу нужно добавить вручную (`ALTER TABLE`
через `sqlite3`), т.к. `create_all()` не умеет менять уже существующие
таблицы.
