FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements/base.txt requirements/vk.txt requirements/
RUN pip install --no-cache-dir -r requirements/vk.txt

COPY app ./app
COPY bots/vk ./bots/vk
COPY bots/__init__.py ./bots/__init__.py

RUN mkdir -p /app/data

CMD ["python", "-m", "bots.vk.bot"]
