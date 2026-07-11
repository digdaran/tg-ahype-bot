#!/usr/bin/env bash
#
# Автообновление платформы из Git-репозитория.
#
# Что делает:
#   1. git fetch — проверяет, есть ли новые коммиты в удалённой ветке.
#   2. Если новых коммитов нет — тихо завершается (ничего не трогает).
#   3. Если есть — делает git pull --ff-only, пересобирает и перезапускает
#      Docker-сервисы (docker compose build + up -d).
#   4. Пишет лог в logs/auto_update.log.
#   5. Если заданы TELEGRAM_BOT_TOKEN и AUTO_UPDATE_NOTIFY_CHAT_ID в .env —
#      шлёт уведомление об успехе/ошибке в Telegram администратору.
#
# Запуск (обычно по расписанию, см. docs/AUTO_UPDATE.md):
#   ./scripts/auto_update.sh
#
# Требования: git, docker (с плагином compose), curl. Скрипт НЕ требует
# Python/venv — намеренно, чтобы работать даже если приложение сейчас лежит.
set -euo pipefail

# --- Пути ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/auto_update.log"
LOCK_FILE="$PROJECT_ROOT/.auto_update.lock"
ENV_FILE="$PROJECT_ROOT/.env"

mkdir -p "$LOG_DIR"

# --- Не даём двум запускам пересечься (если cron сработает раньше, чем
# предыдущий update+rebuild закончился) ---
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "$(date '+%F %T') [auto_update] уже выполняется другой процесс — выходим" >> "$LOG_FILE"
    exit 0
fi

log() {
    echo "$(date '+%F %T') [auto_update] $*" | tee -a "$LOG_FILE"
}

# Безопасно достаёт значение переменной из .env. Если переменной нет или
# .env отсутствует — возвращает пустую строку и НЕ падает (важно под set -e).
get_env_var() {
    local key="$1"
    if [ -f "$ENV_FILE" ]; then
        grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- || printf ''
    else
        printf ''
    fi
}

# --- Настройки ---
BRANCH="${AUTO_UPDATE_BRANCH:-main}"
ENV_BRANCH="$(get_env_var AUTO_UPDATE_BRANCH)"
if [ -n "$ENV_BRANCH" ]; then
    BRANCH="$ENV_BRANCH"
fi
TELEGRAM_BOT_TOKEN="$(get_env_var TELEGRAM_BOT_TOKEN)"
AUTO_UPDATE_NOTIFY_CHAT_ID="$(get_env_var AUTO_UPDATE_NOTIFY_CHAT_ID)"

notify() {
    # notify <text> — отправка администратору в Telegram, если настроено.
    # Не прерывает скрипт при ошибке отправки.
    local text="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$AUTO_UPDATE_NOTIFY_CHAT_ID" ]; then
        curl -s -m 10 \
            -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${AUTO_UPDATE_NOTIFY_CHAT_ID}" \
            -d "text=${text}" \
            -d "parse_mode=HTML" > /dev/null 2>&1 || true
    fi
}

cd "$PROJECT_ROOT"

if [ ! -d .git ]; then
    log "ОШИБКА: $PROJECT_ROOT — не git-репозиторий (нет .git). Автообновление невозможно."
    exit 1
fi

log "проверка обновлений (ветка: $BRANCH)..."
if ! git fetch --quiet origin "$BRANCH" 2>>"$LOG_FILE"; then
    log "ОШИБКА: git fetch не удался (сеть/доступ к репозиторию?)"
    notify "⚠️ Raffle Platform: автообновление — git fetch не удался, см. logs/auto_update.log"
    exit 1
fi

LOCAL_REV="$(git rev-parse HEAD)"
REMOTE_REV="$(git rev-parse "origin/$BRANCH")"

if [ "$LOCAL_REV" = "$REMOTE_REV" ]; then
    log "обновлений нет (HEAD уже на $LOCAL_REV)"
    exit 0
fi

log "найдены новые коммиты: $LOCAL_REV -> $REMOTE_REV"

# --- Не перезаписываем локальные изменения, если кто-то правил файлы руками ---
if [ -n "$(git status --porcelain)" ]; then
    log "ОШИБКА: в рабочей копии есть незакоммиченные изменения — автообновление остановлено, чтобы их не потерять."
    notify "⚠️ Raffle Platform: автообновление остановлено — есть локальные незакоммиченные изменения. Разберитесь вручную (git status)."
    exit 1
fi

if ! git pull --ff-only origin "$BRANCH" >>"$LOG_FILE" 2>&1; then
    log "ОШИБКА: git pull --ff-only не удался (расхождение веток?)"
    notify "⚠️ Raffle Platform: автообновление — git pull не удался (возможен конфликт истории), см. logs/auto_update.log"
    exit 1
fi

log "код обновлён, пересобираю и перезапускаю Docker-сервисы..."
if ! docker compose build >>"$LOG_FILE" 2>&1; then
    log "ОШИБКА: docker compose build не удался"
    notify "❌ Raffle Platform: сборка после обновления не удалась, см. logs/auto_update.log"
    exit 1
fi

if ! docker compose up -d --remove-orphans >>"$LOG_FILE" 2>&1; then
    log "ОШИБКА: docker compose up -d не удался"
    notify "❌ Raffle Platform: запуск после обновления не удался, см. logs/auto_update.log"
    exit 1
fi

# Не обязательно, но полезно: убрать старые неиспользуемые образы, чтобы
# диск не забивался после каждого обновления.
docker image prune -f >>"$LOG_FILE" 2>&1 || true

log "готово: обновлено до $REMOTE_REV, сервисы перезапущены"
notify "✅ Raffle Platform обновлена: <code>${LOCAL_REV:0:7}</code> → <code>${REMOTE_REV:0:7}</code>"
