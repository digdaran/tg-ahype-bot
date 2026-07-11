"""
Провайдер эквайринга ВТБ.

ВАЖНО: в отличие от Т-Банка, у ВТБ нет единой публичной спецификации API —
конкретные названия полей и эндпоинтов фиксируются в договоре эквайринга и
предоставляются банком при подключении мерчанта. Ниже реализован типовой
контракт (создание заказа / HMAC-подпись / webhook / резервная проверка),
который используется большинством эквайринговых API ВТБ. Если фактический
контракт отличается — правки вносятся ТОЛЬКО в этот файл, остальная
архитектура (интерфейс BasePaymentProvider, фабрика, сервисный слой,
вебхук-роутер) не меняется.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from app.config import get_settings
from app.models.enums import PaymentStatusEnum
from app.payments.base import (
    BasePaymentProvider,
    PaymentInitResult,
    ReserveCheckResult,
    WebhookVerificationResult,
)

settings = get_settings()

_SUCCESS_STATUSES = {"CONFIRMED", "PAID", "SUCCESS"}
_FAIL_STATUSES = {"REJECTED", "CANCELED", "EXPIRED", "FAILED"}


def _sign(payload: dict[str, Any], secret_key: str) -> str:
    canonical = "&".join(f"{k}={payload[k]}" for k in sorted(payload.keys()) if k != "signature")
    return hmac.new(secret_key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()


class VTBProvider(BasePaymentProvider):
    name = "vtb"

    def __init__(self) -> None:
        self.merchant_id = settings.vtb_merchant_id
        self.secret_key = settings.vtb_secret_key
        self.api_url = settings.vtb_api_url.rstrip("/")

    async def create_payment(
        self,
        order_id: str,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
    ) -> PaymentInitResult:
        payload = {
            "merchant_id": self.merchant_id,
            "order_id": order_id,
            "amount": f"{amount:.2f}",
            "currency": currency,
            "description": description[:250],
            "return_url": return_url,
            "notification_url": f"{settings.app_base_url}/api/webhooks/vtb",
        }
        payload["signature"] = _sign(payload, self.secret_key)

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.api_url}/orders", json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("order_id") and not data.get("payment_url"):
            raise RuntimeError(f"VTB create order error: {data}")

        return PaymentInitResult(
            provider_payment_id=str(data.get("payment_id") or data.get("order_id")),
            payment_url=data["payment_url"],
            raw=data,
        )

    async def verify_and_parse_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> WebhookVerificationResult:
        incoming_signature = payload.get("signature", "")
        expected_signature = _sign(payload, self.secret_key)

        if not hmac.compare_digest(incoming_signature, expected_signature):
            return WebhookVerificationResult(
                is_valid=False,
                order_id=payload.get("order_id"),
                provider_payment_id=payload.get("payment_id"),
                status=PaymentStatusEnum.PENDING,
                raw=payload,
                error="invalid_signature",
            )

        bank_status = str(payload.get("status", "")).upper()
        if bank_status in _SUCCESS_STATUSES:
            status = PaymentStatusEnum.SUCCEEDED
        elif bank_status in _FAIL_STATUSES:
            status = PaymentStatusEnum.FAILED
        else:
            status = PaymentStatusEnum.PENDING

        return WebhookVerificationResult(
            is_valid=True,
            order_id=payload.get("order_id"),
            provider_payment_id=payload.get("payment_id"),
            status=status,
            raw=payload,
        )

    async def check_status(self, provider_payment_id: str) -> ReserveCheckResult:
        params = {"merchant_id": self.merchant_id, "payment_id": provider_payment_id}
        params["signature"] = _sign(params, self.secret_key)

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self.api_url}/orders/{provider_payment_id}", params=params)
            response.raise_for_status()
            data = response.json()

        bank_status = str(data.get("status", "")).upper()
        if bank_status in _SUCCESS_STATUSES:
            status = PaymentStatusEnum.SUCCEEDED
        elif bank_status in _FAIL_STATUSES:
            status = PaymentStatusEnum.FAILED
        else:
            status = PaymentStatusEnum.PENDING

        return ReserveCheckResult(status=status, raw=data)
