"""
Фабрика платёжных провайдеров.

Используемый эквайринг выбирается ОДНОЙ переменной окружения PAYMENT_PROVIDER
(tbank | vtb) либо (в приоритете) настройкой payment_provider_override в
панели администратора (Настройки). Чтобы добавить новый банк:
  1. Реализовать класс, унаследованный от BasePaymentProvider.
  2. Зарегистрировать его в словаре _PROVIDERS ниже.
Остальной код (сервисы, боты, вебхуки) менять не нужно.
"""
from __future__ import annotations

from app.config import get_settings
from app.models.enums import PaymentProviderEnum
from app.payments.base import BasePaymentProvider
from app.payments.tbank import TBankProvider
from app.payments.vtb import VTBProvider

settings = get_settings()

_PROVIDERS: dict[PaymentProviderEnum, type[BasePaymentProvider]] = {
    PaymentProviderEnum.TBANK: TBankProvider,
    PaymentProviderEnum.VTB: VTBProvider,
}


def get_provider(provider: PaymentProviderEnum | str | None = None) -> BasePaymentProvider:
    """
    Вернуть экземпляр провайдера.

    Если provider не передан явно — используется PAYMENT_PROVIDER из .env.
    (Учёт runtime-override из БД выполняется на уровне сервисного слоя,
    см. app/services/settings_service.py::get_active_payment_provider,
    чтобы фабрика оставалась синхронной и не зависела от сессии БД.)
    """
    key = PaymentProviderEnum(provider) if provider else settings.payment_provider
    provider_cls = _PROVIDERS.get(key)
    if provider_cls is None:
        raise ValueError(f"Неизвестный платёжный провайдер: {key}")
    return provider_cls()


def available_providers() -> list[str]:
    return [p.value for p in _PROVIDERS.keys()]
