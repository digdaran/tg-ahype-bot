"""
Сервис выдачи номерков.

Номерки всегда выдаются случайно и уникально в пределах розыгрыша (по
номеру, а не по порядку выдачи), полное обозначение — "<префикс>-<номер>".

Блокировка розыгрыша (is_locked) запрещает выдачу НОВЫХ номерков, но не
затрагивает уже выданные — они остаются видимыми и рабочими.

Примечание по масштабированию: текущая реализация вычисляет набор свободных
номеров как разность множеств (1..max_tickets) и уже выданных. Для очень
больших розыгрышей (сотни тысяч номерков) рекомендуется заменить на таблицу
предварительно перемешанного пула номеров — интерфейс метода issue_tickets
при этом не изменится.
"""
from __future__ import annotations

import random
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GiveawayLockedError, InsufficientTicketsError
from app.models.enums import AuditActorTypeEnum, TicketSourceEnum
from app.models.giveaway import Giveaway
from app.models.manual_registration import ManualRegistration
from app.models.participant import Participant
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.repositories.giveaway_repo import GiveawayRepository
from app.repositories.ticket_repo import TicketRepository
from app.services.audit_service import AuditService


class TicketService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.giveaways = GiveawayRepository(session)
        self.tickets = TicketRepository(session)
        self.audit = AuditService(session)

    async def _pick_random_numbers(self, giveaway: Giveaway, quantity: int) -> list[int]:
        result = await self.session.execute(select(Ticket.number).where(Ticket.giveaway_id == giveaway.id))
        used = set(result.scalars().all())
        available = [n for n in range(1, giveaway.max_tickets + 1) if n not in used]
        if len(available) < quantity:
            raise InsufficientTicketsError(
                f"Недостаточно свободных номерков в розыгрыше '{giveaway.name}': "
                f"запрошено {quantity}, доступно {len(available)}"
            )
        return random.sample(available, quantity)

    async def issue_tickets(
        self,
        giveaway_id: str,
        participant: Participant,
        quantity: int,
        source: TicketSourceEnum,
        payment: Optional[Payment] = None,
        manual_registration: Optional[ManualRegistration] = None,
        actor_type: AuditActorTypeEnum = AuditActorTypeEnum.SYSTEM,
        actor_id: Optional[str] = None,
        actor_label: Optional[str] = None,
    ) -> list[Ticket]:
        giveaway = await self.giveaways.get_locked_for_update(giveaway_id)
        if giveaway is None:
            raise ValueError(f"Розыгрыш {giveaway_id} не найден")

        if giveaway.is_locked:
            raise GiveawayLockedError(f"Розыгрыш '{giveaway.name}' заблокирован — выдача новых номерков запрещена")

        numbers = await self._pick_random_numbers(giveaway, quantity)

        issued: list[Ticket] = []
        for number in numbers:
            ticket = Ticket(
                giveaway_id=giveaway.id,
                number=number,
                full_code=f"{giveaway.prefix}-{number:06d}",
                participant_id=participant.id,
                source=source,
                payment_id=payment.id if payment else None,
                manual_registration_id=manual_registration.id if manual_registration else None,
            )
            self.session.add(ticket)
            issued.append(ticket)

        giveaway.tickets_issued += quantity
        await self.session.flush()

        await self.audit.log(
            action="tickets.issued",
            actor_type=actor_type,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="giveaway",
            entity_id=giveaway.id,
            details={
                "participant_id": participant.id,
                "quantity": quantity,
                "source": source.value,
                "codes": [t.full_code for t in issued],
            },
        )
        return issued

    async def list_for_participant(self, participant_id: str) -> list[Ticket]:
        return await self.tickets.list_by_participant(participant_id)
