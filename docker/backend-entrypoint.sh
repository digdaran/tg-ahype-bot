#!/bin/sh
set -e

echo "[backend] applying Alembic migrations..."
python -m alembic upgrade head

echo "[backend] ensuring initial Super Admin exists..."
python -m scripts.create_superadmin || true

echo "[backend] starting: $@"
exec "$@"
