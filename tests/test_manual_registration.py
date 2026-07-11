"""
Тесты ручной (офлайн) регистрации (app/services/manual_registration_service.py):
создание -> подтверждение с выдачей номерков -> повторное подтверждение
запрещено; отмена возможна только до подтверждения.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.enums import ManualRegistrationStatusEnum
from app.models.giveaway import Giveaway
from app.services.manual_registration_service import ManualRegistrationService


async def _make_open_giveaway(session: AsyncSession, **overrides) -> Giveaway:
    defaults = dict(
        name="Офлайн розыгрыш", prefix="OFF", ticket_price=50, max_tickets=20, is_registration_open=True,
    )
    defaults.update(overrides)
    giveaway = Giveaway(**defaults)
    session.add(giveaway)
    await session.flush()
    return giveaway


async def test_manual_registration_confirm_issues_tickets(session: AsyncSession):
    giveaway = await _make_open_giveaway(session)
    service = ManualRegistrationService(session)

    registration = await service.create(
        phone="+79995551122", giveaway_id=giveaway.id, quantity=3,
        operator_id="op-1", operator_label="operator1",
    )
    assert registration.status == ManualRegistrationStatusEnum.PENDING

    confirmed = await service.confirm_and_issue_tickets(registration.id, operator_id="op-1", operator_label="operator1")
    assert confirmed.status == ManualRegistrationStatusEnum.CONFIRMED
    assert confirmed.confirmed_at is not None

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 3


async def test_manual_registration_double_confirm_raises(session: AsyncSession):
    giveaway = await _make_open_giveaway(session)
    service = ManualRegistrationService(session)

    registration = await service.create(
        phone="+79995551133", giveaway_id=giveaway.id, quantity=1,
        operator_id="op-1", operator_label="operator1",
    )
    await service.confirm_and_issue_tickets(registration.id, operator_id="op-1", operator_label="operator1")

    with pytest.raises(ValidationError):
        await service.confirm_and_issue_tickets(registration.id, operator_id="op-1", operator_label="operator1")

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 1, "повторное подтверждение не должно выдавать номерки ещё раз"


async def test_manual_registration_cancel_before_confirm(session: AsyncSession):
    giveaway = await _make_open_giveaway(session)
    service = ManualRegistrationService(session)

    registration = await service.create(
        phone="+79995551144", giveaway_id=giveaway.id, quantity=2,
        operator_id="op-1", operator_label="operator1",
    )
    cancelled = await service.cancel(registration.id, operator_id="op-1", operator_label="operator1")
    assert cancelled.status == ManualRegistrationStatusEnum.CANCELLED

    await session.refresh(giveaway)
    assert giveaway.tickets_issued == 0


async def test_manual_registration_cancel_after_confirm_raises(session: AsyncSession):
    giveaway = await _make_open_giveaway(session)
    service = ManualRegistrationService(session)

    registration = await service.create(
        phone="+79995551155", giveaway_id=giveaway.id, quantity=1,
        operator_id="op-1", operator_label="operator1",
    )
    await service.confirm_and_issue_tickets(registration.id, operator_id="op-1", operator_label="operator1")

    with pytest.raises(ValidationError):
        await service.cancel(registration.id, operator_id="op-1", operator_label="operator1")
