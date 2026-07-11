"""
Тесты аутентификации и матрицы прав ролей (Super Admin / Administrator /
Operator) — admin_api/deps.py:require_permission опирается на
app/core/permissions.py:has_permission, а вход — на AuthService.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, UserBlockedError
from app.core.permissions import PanelRole, has_permission
from app.core.security import hash_password
from app.models.enums import PanelRoleEnum
from app.models.panel_user import PanelUser
from app.services.auth_service import AuthService


async def _make_panel_user(
    session: AsyncSession, login: str = "operator1", role: PanelRoleEnum = PanelRoleEnum.OPERATOR,
    password: str = "correct-horse", is_blocked: bool = False,
) -> PanelUser:
    user = PanelUser(login=login, password_hash=hash_password(password), role=role, is_blocked=is_blocked)
    session.add(user)
    await session.flush()
    return user


async def test_authenticate_success_issues_tokens_and_updates_last_login(session: AsyncSession):
    user = await _make_panel_user(session, password="s3cret!")
    service = AuthService(session)

    access_token, refresh_token, authenticated_user = await service.authenticate("operator1", "s3cret!")

    assert access_token and refresh_token
    assert authenticated_user.id == user.id
    assert authenticated_user.last_login_at is not None


async def test_authenticate_wrong_password_raises(session: AsyncSession):
    await _make_panel_user(session, password="s3cret!")
    service = AuthService(session)

    with pytest.raises(AuthError):
        await service.authenticate("operator1", "wrong-password")


async def test_authenticate_unknown_login_raises_auth_error_not_blocked(session: AsyncSession):
    service = AuthService(session)
    with pytest.raises(AuthError):
        await service.authenticate("no-such-user", "whatever")


async def test_authenticate_blocked_user_raises(session: AsyncSession):
    await _make_panel_user(session, password="s3cret!", is_blocked=True)
    service = AuthService(session)

    with pytest.raises(UserBlockedError):
        await service.authenticate("operator1", "s3cret!")


@pytest.mark.parametrize(
    "role,permission,expected",
    [
        (PanelRole.OPERATOR, "manual_registration.create", True),
        (PanelRole.OPERATOR, "panel_users.manage", False),
        (PanelRole.OPERATOR, "settings.edit", False),
        (PanelRole.ADMINISTRATOR, "settings.edit", True),
        (PanelRole.ADMINISTRATOR, "panel_users.manage", False),
        (PanelRole.SUPER_ADMIN, "panel_users.manage", True),
        (PanelRole.SUPER_ADMIN, "settings.edit", True),
        (PanelRole.SUPER_ADMIN, "giveaways.lock", True),
        (PanelRole.OPERATOR, "giveaways.lock", False),
    ],
)
def test_permission_matrix(role: PanelRole, permission: str, expected: bool):
    assert has_permission(role, permission) is expected


def test_unknown_permission_denied_by_default():
    assert has_permission(PanelRole.SUPER_ADMIN, "no.such.permission") is False
