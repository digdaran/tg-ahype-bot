#!/usr/bin/env bash
#
# Обновление платформы на сервере: git pull + пересборка и перезапуск
# Docker-сервисов.
#
# Первый запуск после `git clone` — вручную:
#   cp .env.example .env   # и отредактировать
#   docker compose up -d --build
#
# Каждое следующее обновление — просто:
#   ./deploy.sh
#
# Что делает:
#   1. Проверяет, что в рабочей копии нет незакоммиченных изменений
#      (иначе останавливается, чтобы их не потерять).
#   2. git fetch + git pull --ff-only (ветка — из .env AUTO_UPDATE_BRANCH,
#      по умолчанию main; можно передать явно: ./deploy.sh other-branch).
#   3. docker compose build + docker compose up -d --remove-orphans.
#   4. docker image prune -f — чистит старые слои образов.
#
# Миграции Alembic и создание Super Admin выполняются автоматически при
# старте контейнера backend (docker/backend-entrypoint.sh) — здесь их
# отдельно запускать не нужно.
#
# Отличие от scripts/auto_update.sh: тот же принцип действий, но
# scripts/auto_update.sh предназначен для автозапуска по расписанию
# (cron/systemd timer, тихо завершается, если обновлений нет, шлёт
# уведомление в Telegram) — см. docs/AUTO_UPDATE.md. deploy.sh — для
# ручного запуска командой одной рукой, когда вы сами знаете, что хотите
# обновиться прямо сейчас.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE="$SCRIPT_DIR/.env"

# Безопасно достаёт значение переменной из .env (не падает под set -e, если
# переменной/файла нет — см. тот же приём в scripts/auto_update.sh).
get_env_var() {
    local key="$1"
    if [ -f "$ENV_FILE" ]; then
        grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- || printf ''
    else
        printf ''
    fi
}

BRANCH="${1:-}"
if [ -z "$BRANCH" ]; then
    BRANCH="$(get_env_var AUTO_UPDATE_BRANCH)"
fi
BRANCH="${BRANCH:-main}"

if [ ! -d .git ]; then
    echo "ОШИБКА: $SCRIPT_DIR — не git-репозиторий (нет .git)." >&2
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "ОШИБКА: в рабочей копии есть незакоммиченные изменения — деплой остановлен, чтобы их не потерять." >&2
    echo "Проверьте 'git status', закоммитьте или спрячьте изменения (git stash) и запустите ./deploy.sh снова." >&2
    exit 1
fi

echo "==> git fetch/pull (ветка: $BRANCH)"
git fetch origin "$BRANCH"

LOCAL_REV="$(git rev-parse HEAD)"
REMOTE_REV="$(git rev-parse "origin/$BRANCH")"

if [ "$LOCAL_REV" = "$REMOTE_REV" ]; then
    echo "Обновлений нет (HEAD уже на ${LOCAL_REV:0:7}). Пересобираю и перезапускаю всё равно —"
    echo "полезно, если менялся .env или локальные Docker-образы устарели по другой причине."
else
    echo "Найдены новые коммиты: ${LOCAL_REV:0:7} -> ${REMOTE_REV:0:7}"
fi

if ! git pull --ff-only origin "$BRANCH"; then
    echo "ОШИБКА: git pull --ff-only не удался (расхождение истории веток?). Разберитесь вручную." >&2
    exit 1
fi

echo "==> docker compose build"
docker compose build

echo "==> docker compose up -d"
docker compose up -d --remove-orphans

echo "==> docker image prune -f"
docker image prune -f || true

echo "==> готово. Статус сервисов:"
docker compose ps
