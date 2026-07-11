"""
Единый интерфейс платёжного провайдера.

Любая новая платёжная система подключается добавлением одного класса,
реализующего BasePaymentProvider, и одной строки в app/payments/factory.py —
основная бизнес-логика (сервисный слой, боты, вебхуки) не меняется.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from app.models.enums import PaymentStatusEnum


@dataclass
class PaymentInitResult:
    """Результат создания платежа у провайдера."""
    provider_payment_id: str
    payment_url: str          # ссылка на платёжную страницу / СБП
    raw: dict[str, Any]


@dataclass
class WebhookVerificationResult:
    """Результат разбора и проверки подписи webhook-уведомления банка."""
    is_valid: bool
    order_id: Optional[str]
    provider_payment_id: Optional[str]
    status: PaymentStatusEnum
    raw: dict[str, Any]
    error: Optional[str] = None


@dataclass
class ReserveCheckResult:
    """Результат резервной (ручной) проверки статуса оплаты."""
    status: PaymentStatusEnum
    raw: dict[str, Any]


class BasePaymentProvider(ABC):
    """
    Единый интерфейс для всех платёжных провайдеров (эквайрингов).

    Webhook каждого банка обрабатывается отдельным HTTP-роутером
    (app/admin_api/routers/webhooks_*.py), но оба используют один и тот же
    метод verify_and_parse_webhook для разбора и проверки подписи —
    это и есть единая точка расширения при добавлении нового банка.
    """

    name: str

    @abstractmethod
    async def create_payment(
        self,
        order_id: str,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
    ) -> PaymentInitResult:
        """Создать платёж у провайдера и получить ссылку на оплату (СБП/платёжная страница)."""
        raise NotImplementedError

    @abstractmethod
    async def verify_and_parse_webhook(self, payload: dict[str, Any], headers: dict[str, str]) -> WebhookVerificationResult:
        """Проверить подпись webhook-уведомления и привести его к единому формату."""
        raise NotImplementedError

    @abstractmethod
    async def check_status(self, provider_payment_id: str) -> ReserveCheckResult:
        """Резервная (ручная) проверка статуса платежа — используется, только если webhook не пришёл."""
        raise NotImplementedError
