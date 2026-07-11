"""
Webhook ВТБ. Обрабатывается отдельным роутером от Т-Банка (у каждого банка
собственный формат payload и своя схема подписи) — это и есть точка
расширения при подключении новых банков без изменения бизнес-логики.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from app.core.rate_limit import webhook_rate_limiter
from app.database import AsyncSessionLocal
from app.payments.vtb import VTBProvider
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/vtb", dependencies=[Depends(webhook_rate_limiter)])
async def vtb_webhook(request: Request) -> PlainTextResponse:
    payload = await request.json()
    provider = VTBProvider()
    verification = await provider.verify_and_parse_webhook(payload, dict(request.headers))

    async with AsyncSessionLocal() as session:
        service = PaymentService(session)
        await service.finalize_from_webhook(verification, provider_name="vtb")
        await session.commit()

    return PlainTextResponse("OK")
