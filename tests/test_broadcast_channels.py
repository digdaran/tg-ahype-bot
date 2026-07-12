"""
Тесты включения/выключения интеграций на уровне рассылок
(app/services/broadcast_service.py):
- рассылку строго в выключенный канал создать нельзя (ValidationError);
- рассылку в BOTH создать можно всегда, но выключенный канал при отправке
  реально пропускается (не дёргает HTTP API этого канала).
"""
from __future__ import annotations

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
def _reset_channel_flags(monkeypatch: pytest.MonkeyPatch):
    # На случай, если предыдущий тест поменял флаги и забыл откатить —
    # гарантируем чистое состояние (оба канала включены) на входе в тест.
    monkeypatch.setattr(broadcast_service_module.settings, "telegram_enabled", True)
    monkeypatch.setattr(broadcast_service_module.settings, "vk_enabled", True)
    yield


async def test_create_draft_rejects_single_disabled_channel(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(broadcast_service_module.settings, "vk_enabled", False)
    service = BroadcastService(session)

    with pytest.raises(ValidationError):
        await service.create_draft(
            title="Тест", message_text="Привет", audience_filter={"audience": "all"},
            channel=BroadcastChannelEnum.VK, created_by_id="admin-1", created_by_label="admin",
        )


async def test_create_draft_allows_both_even_if_vk_disabled(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(broadcast_service_module.settings, "vk_enabled", False)
    service = BroadcastService(session)

    broadcast = await service.create_draft(
        title="Тест", message_text="Привет", audience_filter={"audience": "all"},
        channel=BroadcastChannelEnum.BOTH, created_by_id="admin-1", created_by_label="admin",
    )
    assert broadcast.channel == BroadcastChannelEnum.BOTH


async def test_send_skips_disabled_channel(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    telegram_calls: list[tuple] = []
    vk_calls: list[tuple] = []

    async def fake_telegram_send(chat_id, text, reply_markup=None):
        telegram_calls.append((chat_id, text))
        return True

    async def fake_vk_send(user_id, text, random_id=None):
        vk_calls.append((user_id, text))
        return True

    monkeypatch.setattr(broadcast_service_module.telegram_api, "send_message", fake_telegram_send)
    monkeypatch.setattr(broadcast_service_module.vk_api, "send_message", fake_vk_send)
    monkeypatch.setattr(broadcast_service_module.settings, "vk_enabled", False)

    await _make_participant(session, phone="+79990001133", telegram_user_id=111, vk_user_id=222)

    service = BroadcastService(session)
    broadcast = await service.create_draft(
        title="Тест", message_text="Привет всем", audience_filter={"audience": "all"},
        channel=BroadcastChannelEnum.BOTH, created_by_id="admin-1", created_by_label="admin",
    )
    sent_broadcast = await service.send(broadcast.id, actor_id="admin-1", actor_label="admin")

    assert len(telegram_calls) == 1, "Telegram включён — сообщение должно уйти"
    assert len(vk_calls) == 0, "VK выключен — send_message для VK вызываться не должен"

    import json

    stats = json.loads(sent_broadcast.stats)
    assert stats["channels_used"] == ["telegram"]


async def test_send_uses_both_channels_when_both_enabled(session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    telegram_calls: list[tuple] = []
    vk_calls: list[tuple] = []

    async def fake_telegram_send(chat_id, text, reply_markup=None):
        telegram_calls.append((chat_id, text))
        return True

    async def fake_vk_send(user_id, text, random_id=None):
        vk_calls.append((user_id, text))
        return True

    monkeypatch.setattr(broadcast_service_module.telegram_api, "send_message", fake_telegram_send)
    monkeypatch.setattr(broadcast_service_module.vk_api, "send_message", fake_vk_send)

    await _make_participant(session, phone="+79990001144", telegram_user_id=333, vk_user_id=444)

    service = BroadcastService(session)
    broadcast = await service.create_draft(
        title="Тест", message_text="Привет всем", audience_filter={"audience": "all"},
        channel=BroadcastChannelEnum.BOTH, created_by_id="admin-1", created_by_label="admin",
    )
    await service.send(broadcast.id, actor_id="admin-1", actor_label="admin")

    assert len(telegram_calls) == 1
    assert len(vk_calls) == 1
