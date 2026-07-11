"""Доменные исключения. Позволяют сервисному слою не зависеть от HTTP/бот-фреймворков."""


class DomainError(Exception):
    """Базовая ошибка бизнес-логики."""


class NotFoundError(DomainError):
    """Запрашиваемая сущность не найдена."""


class ValidationError(DomainError):
    """Некорректные входные данные."""


class PermissionDeniedError(DomainError):
    """Недостаточно прав для действия."""


class GiveawayLockedError(DomainError):
    """Розыгрыш заблокирован — выдача новых номерков запрещена."""


class GiveawayImmutableError(DomainError):
    """Параметры розыгрыша нельзя менять после открытия регистрации."""


class InsufficientTicketsError(DomainError):
    """Недостаточно свободных номерков для выдачи."""


class DuplicatePaymentError(DomainError):
    """Повторная обработка уже финализированного платежа (идемпотентность)."""


class PaymentProviderError(DomainError):
    """Ошибка на стороне платёжного провайдера."""


class AuthError(DomainError):
    """Неверные учётные данные / истёкший токен."""


class UserBlockedError(DomainError):
    """Пользователь панели заблокирован."""
