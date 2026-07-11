FROM python:3.11-slim AS base

WORKDIR /app

# procps даёт pgrep, используемый в healthcheck (см. docker-compose.yml) —
# у бота нет HTTP-эндпоинта, поэтому healthcheck проверяет, что процесс жив.
RUN apt-get update && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/telegram.txt requirements/
RUN pip install --no-cache-dir -r requirements/telegram.txt

COPY app ./app
COPY bots/telegram ./bots/telegram
COPY bots/__init__.py ./bots/__init__.py

RUN mkdir -p /app/data

# Непривилегированный пользователь — см. пояснение в backend.Dockerfile.
RUN groupadd -r app && useradd -r -g app -d /app -s /usr/sbin/nologin app \
    && chown -R app:app /app
USER app

CMD ["python", "-m", "bots.telegram.bot"]
