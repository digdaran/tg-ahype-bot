"""
Rate-limiter в оперативной памяти процесса для критичных публичных
эндпоинтов: логин панели администратора (защита от перебора пароля) и
webhook'и банков (защита от флуда/DoS на публичный URL).

Реализован как FastAPI-зависимость (Depends) — обычная async-функция,
а не декоратор и не bound-method класса. Пробовали оба альтернативных
варианта:
  1) декоратор slowapi — ломает резолвинг forward-ref аннотаций Pydantic в
     модулях с `from __future__ import annotations` (стиль всего проекта),
     т.к. __globals__ обёртки указывают на модуль slowapi;
  2) экземпляр класса с __call__ в качестве Depends(...) — FastAPI падает с
     той же PydanticUndefinedAnnotation при резолве аннотации `Request` у
     bound-метода.
Обычная функция, созданная фабрикой `_make_limiter`, не имеет этих проблем:
её __globals__ корректно указывают на этот модуль.

Хранилище — в памяти (fixed window, per-ключ "путь+IP"). Подходит для
типового деплоя из одного backend-контейнера. При горизонтальном
масштабировании backend'а на несколько реплик нужно перевести на общее
хранилище (Redis) — точка использования (Depends(login_rate_limiter) и т.п.)
при этом не меняется.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable, Coroutine

from fastapi import HTTPException, Request, status


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _make_limiter(times: int, seconds: int) -> Callable[[Request], Coroutine[None, None, None]]:
    """Фабрика: не более `times` запросов за `seconds` секунд на ключ (путь+IP)."""
    hits: dict[str, deque[float]] = defaultdict(deque)
    lock = Lock()

    async def _dependency(request: Request) -> None:
        key = f"{request.url.path}:{_client_ip(request)}"
        now = time.monotonic()
        with lock:
            bucket = hits[key]
            while bucket and now - bucket[0] > seconds:
                bucket.popleft()
            if len(bucket) >= times:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Слишком много запросов, попробуйте позже",
                )
            bucket.append(now)

    return _dependency


# Отдельные лимитеры на логин (строже — брутфорс пароля) и на вебхуки
# (мягче — банк может слать много уведомлений легитимно).
login_rate_limiter = _make_limiter(times=10, seconds=60)
webhook_rate_limiter = _make_limiter(times=60, seconds=60)
