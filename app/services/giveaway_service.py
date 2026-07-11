"""
Сервис розыгрышей.

Правила:
  - После открытия регистрации (is_registration_open=True впервые) параметры
    prefix / ticket_price / max_tickets становятся неизменяемыми.
  - is_locked запрещает выдачу новых номерков, но не мешает работе с уже
    выданными (просмотр, история и т.д.).
  - Поддерживается произвольное число независимых и одновременных
    розыгрышей — единственное ограничение: уникальный prefix.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GiveawayImmutableError, ValidationError
from app.models.enums import AuditActorTypeEnum
from app.models.giveaway import Giveaway
from app.repositories.giveaway_repo import GiveawayRepository
from app.services.audit_service import AuditService


class GiveawayService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GiveawayRepository(session)
        self.audit = AuditService(session)

    async def create(
        self,
        name: str,
        prefix: str,
        ticket_price: float,
        max_tickets: int,
        actor_id: Optional[str] = None,
        actor_label: Optional[str] = None,
    ) -> Giveaway:
        existing = await self.repo.get_by_prefix(prefix)
        if existing:
            raise ValidationError(f"Префикс '{prefix}' уже используется другим розыгрышем")

        giveaway = Giveaway(name=name, prefix=prefix, ticket_price=ticket_price, max_tickets=max_tickets)
        await self.repo.add(giveaway)

        await self.audit.log(
            action="giveaway.created",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="giveaway",
            entity_id=giveaway.id,
            details={"name": name, "prefix": prefix, "ticket_price": ticket_price, "max_tickets": max_tickets},
        )
        return giveaway

    async def update_params(
        self,
        giveaway_id: str,
        name: Optional[str] = None,
        ticket_price: Optional[float] = None,
        max_tickets: Optional[int] = None,
        actor_id: Optional[str] = None,
        actor_label: Optional[str] = None,
    ) -> Giveaway:
        giveaway = await self.repo.get(giveaway_id)
        if giveaway is None:
            raise ValueError(f"Розыгрыш {giveaway_id} не найден")

        if giveaway.is_immutable and (ticket_price is not None or max_tickets is not None):
            raise GiveawayImmutableError(
                "Розыгрыш уже открыт — стоимость номерка и максимальное количество изменять нельзя"
            )

        if name is not None:
            giveaway.name = name
        if ticket_price is not None:
            giveaway.ticket_price = ticket_price
        if max_tickets is not None:
            giveaway.max_tickets = max_tickets

        await self.session.flush()
        await self.audit.log(
            action="giveaway.updated",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="giveaway",
            entity_id=giveaway.id,
            details={"name": name, "ticket_price": ticket_price, "max_tickets": max_tickets},
        )
        return giveaway

    async def open_registration(self, giveaway_id: str, actor_id: Optional[str] = None, actor_label: Optional[str] = None) -> Giveaway:
        giveaway = await self.repo.get(giveaway_id)
        if giveaway is None:
            raise ValueError(f"Розыгрыш {giveaway_id} не найден")

        giveaway.is_registration_open = True
        if giveaway.opened_at is None:
            giveaway.opened_at = datetime.now(timezone.utc)
        await self.session.flush()

        await self.audit.log(
            action="giveaway.registration_opened",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="giveaway",
            entity_id=giveaway.id,
        )
        return giveaway

    async def close_registration(self, giveaway_id: str, actor_id: Optional[str] = None, actor_label: Optional[str] = None) -> Giveaway:
        giveaway = await self.repo.get(giveaway_id)
        if giveaway is None:
            raise ValueError(f"Розыгрыш {giveaway_id} не найден")

        giveaway.is_registration_open = False
        await self.session.flush()

        await self.audit.log(
            action="giveaway.registration_closed",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="giveaway",
            entity_id=giveaway.id,
        )
        return giveaway

    async def set_locked(self, giveaway_id: str, locked: bool, actor_id: Optional[str] = None, actor_label: Optional[str] = None) -> Giveaway:
        giveaway = await self.repo.get(giveaway_id)
        if giveaway is None:
            raise ValueError(f"Розыгрыш {giveaway_id} не найден")

        giveaway.is_locked = locked
        if locked:
            giveaway.locked_at = datetime.now(timezone.utc)
        await self.session.flush()

        await self.audit.log(
            action="giveaway.locked" if locked else "giveaway.unlocked",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="giveaway",
            entity_id=giveaway.id,
        )
        return giveaway

    async def list_open_for_participants(self) -> list[Giveaway]:
        """Розыгрыши, доступные для покупки прямо сейчас — используется ботами."""
        return await self.repo.list_open_unlocked()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Giveaway]:
        return await self.repo.list_all(limit=limit, offset=offset)

    async def get(self, giveaway_id: str) -> Optional[Giveaway]:
        return await self.repo.get(giveaway_id)
