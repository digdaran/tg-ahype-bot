"""
Тесты gating-логики NotificationService (app/services/notification_service.py):
уведомление после онлайн-оплаты не должно уходить в выключенный канал, даже
если у участника есть привязанный telegram_user_id.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.notification_service as notification_service_module
from app.models.giveaway import Giveaway
from app.models.participant import Participant
from app.models.ticket import Ticket
from app.models.enums import TicketSourceEnum
from app.services.notification_service import NotificationService


async def _make_giveaway(session: AsyncSession) -> Giveaway:
    giveaway = Giveaway(name="Тест", prefix="NTF", ticket_price=10, max_tickets=10)
    session.add(giveaway)
    await session.flush()
    return giveaway


async def _make_ticket(session: AsyncSession, giveaway: Giveaway, participant: Participant, number: int = 1) -> Ticket:
    ticket = Ticket(
        giveaway_id=giveaway.id, number=number, full_code=f"{giveaway.prefix}-{number:06d}",
        participant_id=participant.id, source=TicketSourceEnum.ONLINE,
    )
    session.add(ticket)
    await session.flush()
    return ticket


async def test_notification_skips_disabled_telegram(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    calls: list = []

    async def fake_send_message(chat_id, text, reply_markup=None):
        calls.append(chat_id)
        return True

    monkeypatch.setattr(notification_service_module.telegram_api, "send_message", fake_send_message)
    monkeypatch.setattr(notification_service_module.settings, "telegram_enabled", False)

    giveaway = await _make_giveaway(session)
    participant = Participant(phone="+79990002211", telegram_user_id=555)
    session.add(participant)
    await session.flush()
    ticket = await _make_ticket(session, giveaway, participant)

    await NotificationService().notify_online_purchase(participant, giveaway, [ticket])

    assert calls == [], "Telegram выключен — уведомление не должно отправляться, несмотря на привязанный telegram_user_id"


async def test_notification_sends_when_telegram_enabled(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    calls: list = []

    async def fake_send_message(chat_id, text, reply_markup=None):
        calls.append(chat_id)
        return True

    monkeypatch.setattr(notification_service_module.telegram_api, "send_message", fake_send_message)
    monkeypatch.setattr(notification_service_module.settings, "telegram_enabled", True)

    giveaway = await _make_giveaway(session)
    participant = Participant(phone="+79990002222", telegram_user_id=666)
    session.add(participant)
    await session.flush()
    ticket = await _make_ticket(session, giveaway, participant)

    await NotificationService().notify_online_purchase(participant, giveaway, [ticket])

    assert calls == [666]
