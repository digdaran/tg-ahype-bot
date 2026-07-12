"""
Тесты BroadcastService (app/services/broadcast_service.py) в связке с
выключателем Telegram-интеграции (TELEGRAM_ENABLED, см. app/config.py).

Канал рассылки сейчас только Telegram — VK-интеграция полностью удалена из
проекта (вернёмся к ней отдельно позже).
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.broadcast_service as broadcast_service_module
from app.core.exceptions import ValidationError
from app.models.enums import BroadcastChannelEnum
from app.models.participant import Participant
from app.services.broadcast_service import BroadcastService


async def _make_participant(session: AsyncSession, **overrides) -> Participant:
    defaults = dict(phone="+79990001122")
    defaults.update(overrides)
    participant = Participant(**defaults)
    session.add(participant)
    await session.flush()
    return participant


@pytest.fixture(autouse=True)
def _reset_channel_flag(monkeypatch: pytest.MonkeyPatch):
    # Гарантируем чистое состояние (Telegram включён) на входе в каждый тест.
    monkeypatch.setattr(broadcast_service_module.settings, "telegram_enabled", True)
    yield


async def test_create_draft_rejects_when_telegram_disabled(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(broadcast_service_module.settings, "telegram_enabled", False)
    service = BroadcastService(session)

    with pytest.raises(ValidationError):
        await service.create_draft(
            title="Тест", message_text="Привет", audience_filter={"audience": "all"},
            channel=BroadcastChannelEnum.TELEGRAM, created_by_id="admin-1", created_by_label="admin",
        )


async def test_send_dispatches_to_telegram_participants(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple] = []

    async def fake_send_message(chat_id, text, reply_markup=None):
        calls.append((chat_id, text))
        return True

    monkeypatch.setattr(broadcast_service_module.telegram_api, "send_message", fake_send_message)

    await _make_participant(session, phone="+79990001133", telegram_user_id=111)
    await _make_participant(session, phone="+79990001144", telegram_user_id=222)
    await _make_participant(session, phone="+79990001155")  # без telegram_user_id - не должен получить сообщение

    service = BroadcastService(session)
    broadcast = await service.create_draft(
        title="Тест", message_text="Всем привет", audience_filter={"audience": "all"},
        channel=BroadcastChannelEnum.TELEGRAM, created_by_id="admin-1", created_by_label="admin",
    )
    sent_broadcast = await service.send(broadcast.id, actor_id="admin-1", actor_label="admin")

    assert len(calls) == 2
    assert {c[0] for c in calls} == {111, 222}

    stats = json.loads(sent_broadcast.stats)
    assert stats == {"total": 3, "sent": 2, "failed": 1}


async def test_send_skips_if_telegram_disabled_after_creation(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    """
    Рассылку создали, пока Telegram был включён, а перед отправкой его
    выключили (TELEGRAM_ENABLED=false) — send() не должен дёргать API,
    несмотря на то что у участников есть telegram_user_id.
    """
    calls: list = []

    async def fake_send_message(chat_id, text, reply_markup=None):
        calls.append(chat_id)
        return True

    monkeypatch.setattr(broadcast_service_module.telegram_api, "send_message", fake_send_message)

    await _make_participant(session, phone="+79990001166", telegram_user_id=333)

    service = BroadcastService(session)
    broadcast = await service.create_draft(
        title="Тест", message_text="Привет", audience_filter={"audience": "all"},
        channel=BroadcastChannelEnum.TELEGRAM, created_by_id="admin-1", created_by_label="admin",
    )

    monkeypatch.setattr(broadcast_service_module.settings, "telegram_enabled", False)
    sent_broadcast = await service.send(broadcast.id, actor_id="admin-1", actor_label="admin")

    assert calls == []
    stats = json.loads(sent_broadcast.stats)
    assert stats["sent"] == 0
    assert stats["failed"] == 1
