"""
Тесты выдачи номерков (app/services/ticket_service.py):
- номера уникальны в пределах розыгрыша и не превышают max_tickets;
- выдача сверх лимита свободных номерков запрещена (InsufficientTicketsError);
- выдача в заблокированном розыгрыше запрещена (GiveawayLockedError);
- tickets_issued корректно накапливается при нескольких выдачах подряд.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GiveawayLockedError, InsufficientTicketsError
from app.models.enums import TicketSourceEnum
from app.models.giveaway import Giveaway
from app.models.participant import Participant
from app.services.ticket_service import TicketService


async def _make_giveaway(session: AsyncSession, **overrides) -> Giveaway:
    defaults = dict(name="Тестовый розыгрыш", prefix="TST", ticket_price=100, max_tickets=10)
    defaults.update(overrides)
    giveaway = Giveaway(**defaults)
    session.add(giveaway)
    await session.flush()
    return giveaway


async def _make_participant(session: AsyncSession, phone: str = "+79990000001") -> Participant:
    participant = Participant(phone=phone)
    session.add(participant)
    await session.flush()
    return participant


async def test_issue_tickets_unique_and_within_bounds(session: AsyncSession):
    giveaway = await _make_giveaway(session)
    participant = await _make_participant(session)
    service = TicketService(session)

    issued = await service.issue_tickets(
        giveaway_id=giveaway.id,
        participant=participant,
        quantity=5,
        source=TicketSourceEnum.ONLINE,
    )

    assert len(issued) == 5
    numbers = [t.number for t in issued]
    assert len(set(numbers)) == 5, "номера номерков должны быть уникальны"
    assert all(1 <= n <= giveaway.max_tickets for n in numbers)
    assert all(t.full_code == f"TST-{t.number:06d}" for t in issued)

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 5
    assert giveaway.tickets_remaining == 5


async def test_issue_tickets_accumulates_and_stays_unique_across_calls(session: AsyncSession):
    giveaway = await _make_giveaway(session, max_tickets=10)
    participant = await _make_participant(session)
    service = TicketService(session)

    first_batch = await service.issue_tickets(
        giveaway_id=giveaway.id, participant=participant, quantity=6, source=TicketSourceEnum.ONLINE,
    )
    second_batch = await service.issue_tickets(
        giveaway_id=giveaway.id, participant=participant, quantity=4, source=TicketSourceEnum.MANUAL,
    )

    all_numbers = [t.number for t in first_batch + second_batch]
    assert len(all_numbers) == 10
    assert len(set(all_numbers)) == 10, "номера не должны повторяться между разными вызовами"

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 10
    assert giveaway.tickets_remaining == 0


async def test_issue_tickets_insufficient_raises(session: AsyncSession):
    giveaway = await _make_giveaway(session, max_tickets=3)
    participant = await _make_participant(session)
    service = TicketService(session)

    with pytest.raises(InsufficientTicketsError):
        await service.issue_tickets(
            giveaway_id=giveaway.id, participant=participant, quantity=4, source=TicketSourceEnum.ONLINE,
        )

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 0, "при ошибке номерки не должны выдаваться частично"


async def test_issue_tickets_locked_giveaway_raises(session: AsyncSession):
    giveaway = await _make_giveaway(session, is_locked=True)
    participant = await _make_participant(session)
    service = TicketService(session)

    with pytest.raises(GiveawayLockedError):
        await service.issue_tickets(
            giveaway_id=giveaway.id, participant=participant, quantity=1, source=TicketSourceEnum.ONLINE,
        )
