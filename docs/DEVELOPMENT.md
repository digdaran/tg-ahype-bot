# Локальная разработка без Docker

## Backend (admin_api)

```bash
python3 -m venv .venv-backend
source .venv-backend/bin/activate
pip install -r requirements/backend.txt

cp .env.example .env   # отредактировать при необходимости

python -m alembic upgrade head
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

## VK-бот

```bash
python3 -m venv .venv-vk
source .venv-vk/bin/activate
pip install -r requirements/vk.txt

python -m bots.vk.bot
```

> Обратите внимание: `aiogram` и `vkbottle` требуют разные версии `aiohttp`,
> поэтому backend/telegram-бот/vk-бот должны использовать РАЗНЫЕ виртуальные
> окружения — так же, как в Docker-образах.

## Фронтенд

```bash
cd admin-frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

## Новая миграция после изменения моделей

```bash
python -m alembic revision --autogenerate -m "описание изменения"
python -m alembic upgrade head
```
