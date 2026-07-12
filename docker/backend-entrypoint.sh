#!/bin/sh
set -e

echo "[backend] проверка/создание таблиц БД (SQLite, create_all)..."
python -m scripts.init_db

echo "[backend] ensuring initial Super Admin exists..."
python -m scripts.create_superadmin || true

echo "[backend] starting: $@"
exec "$@"
