FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/backend.txt requirements/
RUN pip install --no-cache-dir -r requirements/backend.txt

COPY app ./app
COPY admin_api ./admin_api
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN mkdir -p /app/data

COPY docker/backend-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "admin_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
