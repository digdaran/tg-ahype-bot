"""
Точка входа FastAPI-приложения: веб-панель администратора (REST API) +
webhook-эндпоинты платёжных провайдеров.

Запуск: uvicorn admin_api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import (
    AuthError,
    DomainError,
    GiveawayImmutableError,
    GiveawayLockedError,
    InsufficientTicketsError,
    NotFoundError,
    PermissionDeniedError,
    UserBlockedError,
    ValidationError,
)
from app.core.logging import configure_logging, get_logger

from admin_api.routers import (
    audit_log,
    auth,
    broadcasts,
    dashboard,
    giveaways,
    manual_registrations,
    panel_users,
    participants,
    reports,
    sales,
    settings as settings_router,
    tickets,
    webhooks_tbank,
    webhooks_vtb,
)

settings = get_settings()
configure_logging(settings.app_env)
logger = get_logger(__name__)

app = FastAPI(
    title="Raffle Platform Admin API",
    description="API веб-панели администратора платформы розыгрышей цифровых постеров",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DOMAIN_ERROR_STATUS = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    GiveawayLockedError: status.HTTP_409_CONFLICT,
    GiveawayImmutableError: status.HTTP_409_CONFLICT,
    InsufficientTicketsError: status.HTTP_409_CONFLICT,
    AuthError: status.HTTP_401_UNAUTHORIZED,
    UserBlockedError: status.HTTP_403_FORBIDDEN,
}


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """
    Единый обработчик доменных исключений — на случай, если конкретный роутер
    не перехватил исключение сам (роутеры, как правило, ловят его точечно,
    чтобы вернуть более специфичный статус, см. try/except в admin_api/routers/*).
    """
    status_code = _DOMAIN_ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    logger.warning("domain_error", error=str(exc), path=str(request.url))
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(participants.router)
app.include_router(sales.router)
app.include_router(manual_registrations.router)
app.include_router(tickets.router)
app.include_router(giveaways.router)
app.include_router(settings_router.router)
app.include_router(panel_users.router)
app.include_router(broadcasts.router)
app.include_router(reports.router)
app.include_router(audit_log.router)
app.include_router(webhooks_tbank.router)
app.include_router(webhooks_vtb.router)
