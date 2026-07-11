"""
Создаёт первичного пользователя Super Admin, если пользователей в панели ещё нет.
Логин/пароль берутся из INITIAL_SUPERADMIN_LOGIN / INITIAL_SUPERADMIN_PASSWORD (.env).

Запуск: python -m scripts.create_superadmin
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.enums import PanelRoleEnum
from app.repositories.panel_user_repo import PanelUserRepository
from app.services.auth_service import AuthService

settings = get_settings()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        repo = PanelUserRepository(session)
        existing = await repo.get_by_login(settings.initial_superadmin_login)
        if existing:
            print(f"Пользователь '{settings.initial_superadmin_login}' уже существует — пропуск.")
            return

        service = AuthService(session)
        user = await service.create_user(
            login=settings.initial_superadmin_login,
            password=settings.initial_superadmin_password,
            role=PanelRoleEnum.SUPER_ADMIN,
            full_name="Super Admin",
            actor_id="system",
            actor_label="bootstrap",
        )
        await session.commit()
        print(f"Создан Super Admin: {user.login}")


if __name__ == "__main__":
    asyncio.run(main())
