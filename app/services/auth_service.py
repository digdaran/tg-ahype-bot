"""Сервис аутентификации и управления пользователями веб-панели."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, UserBlockedError, ValidationError
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.enums import AuditActorTypeEnum, PanelRoleEnum
from app.models.panel_user import PanelUser
from app.repositories.panel_user_repo import PanelUserRepository
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PanelUserRepository(session)
        self.audit = AuditService(session)

    async def authenticate(self, login: str, password: str, ip_address: Optional[str] = None) -> tuple[str, str, PanelUser]:
        user = await self.repo.get_by_login(login)
        if user is None or not verify_password(password, user.password_hash):
            await self.audit.log(
                action="auth.login_failed",
                actor_type=AuditActorTypeEnum.PANEL_USER,
                actor_label=login,
                ip_address=ip_address,
            )
            raise AuthError("Неверный логин или пароль")

        if user.is_blocked:
            await self.audit.log(
                action="auth.login_blocked_user",
                actor_type=AuditActorTypeEnum.PANEL_USER,
                actor_id=user.id,
                actor_label=user.login,
                ip_address=ip_address,
            )
            raise UserBlockedError("Пользователь заблокирован")

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()

        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.id)

        await self.audit.log(
            action="auth.login_success",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=user.id,
            actor_label=user.login,
            ip_address=ip_address,
        )
        return access_token, refresh_token, user

    async def logout(self, user: PanelUser, ip_address: Optional[str] = None) -> None:
        await self.audit.log(
            action="auth.logout",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=user.id,
            actor_label=user.login,
            ip_address=ip_address,
        )

    async def create_user(
        self, login: str, password: str, role: PanelRoleEnum, full_name: Optional[str],
        actor_id: str, actor_label: str,
    ) -> PanelUser:
        existing = await self.repo.get_by_login(login)
        if existing:
            raise ValidationError(f"Логин '{login}' уже занят")

        user = PanelUser(login=login, password_hash=hash_password(password), role=role, full_name=full_name)
        await self.repo.add(user)

        await self.audit.log(
            action="panel_user.created",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="panel_user",
            entity_id=user.id,
            details={"login": login, "role": role.value},
        )
        return user

    async def set_blocked(self, user_id: str, blocked: bool, actor_id: str, actor_label: str) -> PanelUser:
        user = await self.repo.get(user_id)
        if user is None:
            raise ValueError(f"Пользователь {user_id} не найден")
        user.is_blocked = blocked
        await self.session.flush()

        await self.audit.log(
            action="panel_user.blocked" if blocked else "panel_user.unblocked",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="panel_user",
            entity_id=user.id,
        )
        return user

    async def change_password(self, user_id: str, new_password: str, actor_id: str, actor_label: str) -> PanelUser:
        user = await self.repo.get(user_id)
        if user is None:
            raise ValueError(f"Пользователь {user_id} не найден")
        user.password_hash = hash_password(new_password)
        await self.session.flush()

        await self.audit.log(
            action="panel_user.password_changed",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="panel_user",
            entity_id=user.id,
        )
        return user

    async def list_all(self) -> list[PanelUser]:
        return await self.repo.list_all()
