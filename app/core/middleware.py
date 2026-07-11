"""
HTTP-middleware уровня приложения:

- RequestIDMiddleware — генерирует (или принимает от reverse-proxy)
  X-Request-ID, привязывает его к structlog contextvars на время обработки
  запроса и возвращает тем же заголовком в ответе. Это позволяет находить
  все лог-записи одного запроса (в т.ч. через несколько сервисов/логов)
  по одному идентификатору.
- SecurityHeadersMiddleware — добавляет стандартный набор защитных
  заголовков ответа. TLS сам по себе терминируется на reverse-proxy
  (см. docker/Caddyfile), поэтому Strict-Transport-Security здесь тоже
  проставляется — Caddy проксирует заголовки backend'а как есть.
"""
from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

_REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        incoming_id = request.headers.get(_REQUEST_ID_HEADER)
        request_id = incoming_id or uuid.uuid4().hex

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()

        response.headers[_REQUEST_ID_HEADER] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Базовые защитные заголовки. Админ-панель — SPA, обращающаяся к этому API
    через Authorization-заголовок (без cookies), поэтому CSP здесь намеренно
    не задаёт ограничений на сам SPA (он отдаётся отдельным nginx-сервисом,
    см. docker/nginx.conf) — только на ответы самого API.
    """

    _HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
        # Работает, только если запрос действительно пришёл по HTTPS
        # (через Caddy) — для прямых http-запросов в dev-режиме браузер
        # этот заголовок просто проигнорирует.
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    }

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for key, value in self._HEADERS.items():
            response.headers.setdefault(key, value)
        return response
