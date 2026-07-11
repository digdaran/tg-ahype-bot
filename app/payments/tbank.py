"""
Провайдер эквайринга Т-Банк (Tinkoff Acquiring API v2).

Документация: https://www.tbank.ru/kassa/dev/payments/
Основные методы: Init (создание платежа/ссылки СБП), GetState (проверка статуса),
Notification webhook (асинхронное уведомление о статусе).

Подпись (Token) формируется так:
  1. Берутся все параметры запроса верхнего уровня, кроме вложенных
     объектов/массивов (Receipt, DATA, Items) и самого Token.
  2. Добавляется Password = TBANK_SECRET_KEY.
  3. Пары "ключ": "значение" сортируются по ключу, значения конкатенируются
     без разделителей, вычисляется SHA-256, результат — hex-строка.
"""
from __future__ import annotations

import hashlib
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

_SUCCESS_STATUSES = {"CONFIRMED", "AUTHORIZED"}
_FAIL_STATUSES = {"REJECTED", "DEADLINE_EXPIRED", "CANCELED"}


def _build_token(params: dict[str, Any], secret_key: str) -> str:
    flat = {
        k: v
        for k, v in params.items()
        if k != "Token" and not isinstance(v, (dict, list))
    }
    flat["Password"] = secret_key
    concatenated = "".join(str(flat[k]) for k in sorted(flat.keys()))
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()


class TBankProvider(BasePaymentProvider):
    name = "tbank"

    def __init__(self) -> None:
        self.terminal_key = settings.tbank_terminal_key
        self.secret_key = settings.tbank_secret_key
        self.api_url = settings.tbank_api_url.rstrip("/")

    async def create_payment(
        self,
        order_id: str,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
    ) -> PaymentInitResult:
        amount_kopecks = int(round(amount * 100))
        payload = {
            "TerminalKey": self.terminal_key,
            "Amount": amount_kopecks,
            "OrderId": order_id,
            "Description": description[:250],
            "SuccessURL": return_url,
            "FailURL": return_url,
            "NotificationURL": f"{settings.app_base_url}/api/webhooks/tbank",
        }
        payload["Token"] = _build_token(payload, self.secret_key)

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.api_url}/Init", json=payload)
            response.raise_for_status()
            data = response.json()

        if not data.get("Success"):
            raise RuntimeError(f"T-Bank Init error: {data.get('Message')} / {data.get('Details')}")

        return PaymentInitResult(
            provider_payment_id=str(data["PaymentId"]),
            payment_url=data["PaymentURL"],
            raw=data,
        )

    async def verify_and_parse_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> WebhookVerificationResult:
        incoming_token = payload.get("Token", "")
        expected_token = _build_token(payload, self.secret_key)

        if incoming_token != expected_token:
            return WebhookVerificationResult(
                is_valid=False,
                order_id=payload.get("OrderId"),
                provider_payment_id=str(payload.get("PaymentId")) if payload.get("PaymentId") else None,
                status=PaymentStatusEnum.PENDING,
                raw=payload,
                error="invalid_signature",
            )

        bank_status = str(payload.get("Status", ""))
        if bank_status in _SUCCESS_STATUSES:
            status = PaymentStatusEnum.SUCCEEDED
        elif bank_status in _FAIL_STATUSES:
            status = PaymentStatusEnum.FAILED
        else:
            status = PaymentStatusEnum.PENDING

        return WebhookVerificationResult(
            is_valid=True,
            order_id=payload.get("OrderId"),
            provider_payment_id=str(payload.get("PaymentId")) if payload.get("PaymentId") else None,
            status=status,
            raw=payload,
        )

    async def check_status(self, provider_payment_id: str) -> ReserveCheckResult:
        payload = {"TerminalKey": self.terminal_key, "PaymentId": provider_payment_id}
        payload["Token"] = _build_token(payload, self.secret_key)

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.api_url}/GetState", json=payload)
            response.raise_for_status()
            data = response.json()

        bank_status = str(data.get("Status", ""))
        if bank_status in _SUCCESS_STATUSES:
            status = PaymentStatusEnum.SUCCEEDED
        elif bank_status in _FAIL_STATUSES:
            status = PaymentStatusEnum.FAILED
        else:
            status = PaymentStatusEnum.PENDING

        return ReserveCheckResult(status=status, raw=data)
