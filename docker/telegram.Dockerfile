FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements/base.txt requirements/telegram.txt requirements/
RUN pip install --no-cache-dir -r requirements/telegram.txt

COPY app ./app
COPY bots/telegram ./bots/telegram
COPY bots/__init__.py ./bots/__init__.py

RUN mkdir -p /app/data

CMD ["python", "-m", "bots.telegram.bot"]
