"""Единые перечисления, используемые в моделях и сервисах."""
import enum


class PanelRoleEnum(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMINISTRATOR = "administrator"
    OPERATOR = "operator"


class PaymentProviderEnum(str, enum.Enum):
    TBANK = "tbank"
    VTB = "vtb"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class TicketSourceEnum(str, enum.Enum):
    ONLINE = "online"
    MANUAL = "manual"


class ManualRegistrationStatusEnum(str, enum.Enum):
    PENDING = "pending"      # регистрация создана, номерки ещё не выданы, можно отменить
    CONFIRMED = "confirmed"  # номерки выданы оператором, регистрация зафиксирована
    CANCELLED = "cancelled"  # отменена до подтверждения


class BroadcastChannelEnum(str, enum.Enum):
    TELEGRAM = "telegram"
    VK = "vk"
    BOTH = "both"


class BroadcastStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class AuditActorTypeEnum(str, enum.Enum):
    PANEL_USER = "panel_user"
    SYSTEM = "system"
    BOT = "bot"
