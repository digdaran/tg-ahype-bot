"""
Единая точка импорта всех ORM-моделей.

scripts/init_db.py импортирует именно этот модуль, чтобы вся metadata
Base была заполнена перед create_all() (см. app/database.py).
"""
from app.models.participant import Participant
from app.models.giveaway import Giveaway
from app.models.ticket import Ticket
from app.models.payment import Payment
from app.models.manual_registration import ManualRegistration
from app.models.panel_user import PanelUser
from app.models.audit_log import AuditLog
from app.models.broadcast import Broadcast
from app.models.settings import PlatformSettings

__all__ = [
    "Participant",
    "Giveaway",
    "Ticket",
    "Payment",
    "ManualRegistration",
    "PanelUser",
    "AuditLog",
    "Broadcast",
    "PlatformSettings",
]
