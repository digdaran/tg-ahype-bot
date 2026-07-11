"""
Webhook Т-Банка. Отдельный роутер на банк — это основной способ подтверждения
оплаты. Подпись проверяется внутри TBankProvider.verify_and_parse_webhook.
Всегда отвечаем "OK" банку, даже если платёж не найден/уже финализирован —
чтобы банк не повторял доставку бесконечно (детали — в журнале аудита).
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from admin_api.deps import get_db
from app.database import AsyncSessionLocal
from app.payments.tbank import TBankProvider
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/tbank")
async def tbank_webhook(request: Request) -> PlainTextResponse:
    payload = await request.json()
    provider = TBankProvider()
    verification = await provider.verify_and_parse_webhook(payload, dict(request.headers))

    async with AsyncSessionLocal() as session:
        service = PaymentService(session)
        await service.finalize_from_webhook(verification, provider_name="tbank")
        await session.commit()

    return PlainTextResponse("OK")
