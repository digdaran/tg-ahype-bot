#!/usr/bin/env bash
#
# Резервное копирование базы данных платформы.
#
# Поддерживает оба варианта хранилища:
#   - SQLite  (по умолчанию) — бэкап через "sqlite3 ... VACUUM INTO", что
#     даёт консистентный снимок без остановки backend'а (в отличие от
#     простого cp файла, который рискует зацепить файл в момент записи).
#   - PostgreSQL — обычный pg_dump в сжатом custom-формате.
#
# Что делает:
#   1. Определяет тип БД по DATABASE_URL в .env.
#   2. Снимает дамп в BACKUP_DIR (по умолчанию ./backups) с меткой времени.
#   3. Удаляет бэкапы старше BACKUP_RETENTION_DAYS (по умолчанию 14 дней).
#   4. Пишет лог в logs/backup.log.
#
# Запуск (обычно по расписанию, см. docs/BACKUP.md):
#   ./scripts/backup_db.sh
#
# Восстановление — см. docs/BACKUP.md (там же примеры cron/systemd).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/backup.log"

mkdir -p "$LOG_DIR"

log() {
    echo "$(date '+%F %T') [backup] $*" | tee -a "$LOG_FILE"
}

# Безопасно достаёт значение переменной из .env (не падает под set -e, если
# переменной/файла нет — см. аналогичный приём в scripts/auto_update.sh).
get_env_var() {
    local key="$1"
    if [ -f "$ENV_FILE" ]; then
        grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- || printf ''
    else
        printf ''
    fi
}

DATABASE_URL="$(get_env_var DATABASE_URL)"
BACKUP_DIR="$(get_env_var BACKUP_DIR)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
RETENTION_DAYS="$(get_env_var BACKUP_RETENTION_DAYS)"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"

cd "$PROJECT_ROOT"

if [[ "$DATABASE_URL" == sqlite* ]]; then
    # DATABASE_URL вида sqlite+aiosqlite:///./data/db.sqlite3
    DB_PATH="${DATABASE_URL#*:///}"
    if [ ! -f "$DB_PATH" ]; then
        # Backend обычно работает внутри Docker (docker-compose), а этот
        # скрипт — на хосте; типовой путь внутри volume для sqlite_data.
        DB_PATH="$PROJECT_ROOT/data/db.sqlite3"
    fi
    if [ ! -f "$DB_PATH" ]; then
        log "ОШИБКА: файл БД не найден ни по '$DATABASE_URL', ни по '$DB_PATH'."
        log "Если backend работает в Docker, экспортируйте volume вручную или запускайте бэкап внутри контейнера."
        exit 1
    fi

    OUT_FILE="$BACKUP_DIR/db_${TIMESTAMP}.sqlite3"
    if command -v sqlite3 >/dev/null 2>&1; then
        # VACUUM INTO делает консистентный снимок без блокировки записи в оригинал.
        sqlite3 "$DB_PATH" "VACUUM INTO '$OUT_FILE'"
    else
        log "sqlite3 CLI не найден — делаю обычную копию файла (может быть неконсистентной при активной записи)"
        cp "$DB_PATH" "$OUT_FILE"
    fi
    gzip -f "$OUT_FILE"
    log "готово: $OUT_FILE.gz"

elif [[ "$DATABASE_URL" == postgresql* ]]; then
    # postgresql+asyncpg://user:pass@host:port/dbname -> обычный postgres:// для pg_dump
    PG_URL="$(echo "$DATABASE_URL" | sed -E 's#postgresql\+[a-z0-9]+://#postgresql://#')"
    if ! command -v pg_dump >/dev/null 2>&1; then
        log "ОШИБКА: pg_dump не найден в PATH. Установите postgresql-client или запускайте бэкап из контейнера с ним."
        exit 1
    fi
    OUT_FILE="$BACKUP_DIR/db_${TIMESTAMP}.dump"
    pg_dump --format=custom --file="$OUT_FILE" "$PG_URL"
    gzip -f "$OUT_FILE"
    log "готово: $OUT_FILE.gz"

else
    log "ОШИБКА: не удалось распознать тип БД по DATABASE_URL='$DATABASE_URL'"
    exit 1
fi

# --- Ротация старых бэкапов ---
DELETED=0
while IFS= read -r -d '' old_file; do
    rm -f "$old_file"
    DELETED=$((DELETED + 1))
done < <(find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'db_*.sqlite3.gz' -o -name 'db_*.dump.gz' \) -mtime "+${RETENTION_DAYS}" -print0)

if [ "$DELETED" -gt 0 ]; then
    log "удалено старых бэкапов (старше ${RETENTION_DAYS} дн.): $DELETED"
fi

log "бэкап завершён успешно"
