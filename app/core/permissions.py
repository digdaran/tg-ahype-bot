"""
Роли и права доступа панели администратора.

Роли: Super Admin, Administrator, Operator.
Права — простые строковые константы, проверяются в зависимостях роутеров
(app/admin_api зависит от app/core, не наоборот).
"""
from enum import Enum


class PanelRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMINISTRATOR = "administrator"
    OPERATOR = "operator"


# Матрица прав: какие роли могут выполнять какое действие.
PERMISSIONS: dict[str, set[PanelRole]] = {
    # Участники
    "participants.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    "participants.edit": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Продажи
    "sales.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    "sales.export": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Ручные регистрации
    "manual_registration.create": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    "manual_registration.cancel": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    "manual_registration.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    # Номерки
    "tickets.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    # Розыгрыши
    "giveaways.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
    "giveaways.create": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    "giveaways.edit": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    "giveaways.lock": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Настройки
    "settings.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    "settings.edit": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Пользователи панели
    "panel_users.view": {PanelRole.SUPER_ADMIN},
    "panel_users.manage": {PanelRole.SUPER_ADMIN},
    # Рассылки
    "broadcasts.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    "broadcasts.send": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Отчёты
    "reports.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Журнал аудита
    "audit_log.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR},
    # Dashboard
    "dashboard.view": {PanelRole.SUPER_ADMIN, PanelRole.ADMINISTRATOR, PanelRole.OPERATOR},
}


def has_permission(role: PanelRole, permission: str) -> bool:
    allowed = PERMISSIONS.get(permission)
    if allowed is None:
        return False
    return role in allowed
