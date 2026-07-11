"""
Сервис рассылок.

Панель администратора не запускает бот-процессы напрямую — сообщения
отправляются прямыми HTTP-вызовами Telegram Bot API / VK API. Это позволяет
не тянуть aiogram/vkbottle (с их несовместимыми версиями aiohttp) в backend,
и работает даже если контейнеры ботов временно не запущены.

Поддерживаемые аудитории: все / только оплатившие / только неоплатившие /
только офлайн / только онлайн / диапазон дат регистрации / диапазон
количества номерков.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.integrations import telegram_api, vk_api
from app.models.broadcast import Broadcast
from app.models.enums import (
    AuditActorTypeEnum,
    BroadcastChannelEnum,
    BroadcastStatusEnum,
)
from app.models.participant import Participant
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.repositories.broadcast_repo import BroadcastRepository
from app.services.audit_service import AuditService

settings = get_settings()


class BroadcastService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BroadcastRepository(session)
        self.audit = AuditService(session)

    async def _resolve_audience(self, audience_filter: dict[str, Any]) -> list[Participant]:
        audience = audience_filter.get("audience", "all")

        stmt = select(Participant)

        if audience == "paid":
            stmt = stmt.where(Participant.id.in_(select(Payment.participant_id).distinct()))
        elif audience == "unpaid":
            stmt = stmt.where(~Participant.id.in_(select(Payment.participant_id).distinct()))
        elif audience == "online":
            stmt = stmt.where(
                Participant.id.in_(select(Ticket.participant_id).where(Ticket.source == "online").distinct())
            )
        elif audience == "offline":
            stmt = stmt.where(
                Participant.id.in_(select(Ticket.participant_id).where(Ticket.source == "manual").distinct())
            )

        date_from = audience_filter.get("date_from")
        date_to = audience_filter.get("date_to")
        if date_from:
            stmt = stmt.where(Participant.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            stmt = stmt.where(Participant.created_at <= datetime.fromisoformat(date_to))

        result = await self.session.execute(stmt)
        participants = list(result.scalars().unique().all())

        min_tickets = audience_filter.get("min_tickets")
        max_tickets = audience_filter.get("max_tickets")
        if min_tickets is not None or max_tickets is not None:
            filtered = []
            for p in participants:
                count_result = await self.session.execute(
                    select(Ticket).where(Ticket.participant_id == p.id)
                )
                count = len(count_result.scalars().all())
                if min_tickets is not None and count < min_tickets:
                    continue
                if max_tickets is not None and count > max_tickets:
                    continue
                filtered.append(p)
            participants = filtered

        return participants

    async def create_draft(
        self,
        title: str,
        message_text: str,
        audience_filter: dict[str, Any],
        channel: BroadcastChannelEnum,
        created_by_id: str,
        created_by_label: str,
    ) -> Broadcast:
        broadcast = Broadcast(
            title=title,
            message_text=message_text,
            audience_filter=json.dumps(audience_filter, ensure_ascii=False),
            channel=channel,
            status=BroadcastStatusEnum.DRAFT,
            created_by_id=created_by_id,
        )
        await self.repo.add(broadcast)
        await self.audit.log(
            action="broadcast.created",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=created_by_id,
            actor_label=created_by_label,
            entity_type="broadcast",
            entity_id=broadcast.id,
            details={"title": title, "channel": channel.value, "audience_filter": audience_filter},
        )
        return broadcast

    async def send(self, broadcast_id: str, actor_id: str, actor_label: str) -> Broadcast:
        broadcast = await self.repo.get(broadcast_id)
        if broadcast is None:
            raise ValueError(f"Рассылка {broadcast_id} не найдена")

        broadcast.status = BroadcastStatusEnum.SENDING
        await self.session.flush()

        audience_filter = json.loads(broadcast.audience_filter)
        recipients = await self._resolve_audience(audience_filter)

        sent, failed = 0, 0
        semaphore = asyncio.Semaphore(10)

        async def _dispatch(participant: Participant, idx: int) -> None:
            nonlocal sent, failed
            async with semaphore:
                ok = False
                if broadcast.channel in (BroadcastChannelEnum.TELEGRAM, BroadcastChannelEnum.BOTH) and participant.telegram_user_id:
                    ok = await telegram_api.send_message(participant.telegram_user_id, broadcast.message_text) or ok
                if broadcast.channel in (BroadcastChannelEnum.VK, BroadcastChannelEnum.BOTH) and participant.vk_user_id:
                    ok = await vk_api.send_message(participant.vk_user_id, broadcast.message_text, random_id=idx) or ok
                if ok:
                    sent += 1
                else:
                    failed += 1

        await asyncio.gather(*(_dispatch(p, i) for i, p in enumerate(recipients)))

        broadcast.status = BroadcastStatusEnum.SENT
        broadcast.sent_at = datetime.now(timezone.utc)
        broadcast.stats = json.dumps({"total": len(recipients), "sent": sent, "failed": failed})
        await self.session.flush()

        await self.audit.log(
            action="broadcast.sent",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=actor_id,
            actor_label=actor_label,
            entity_type="broadcast",
            entity_id=broadcast.id,
            details={"total": len(recipients), "sent": sent, "failed": failed},
        )
        return broadcast

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Broadcast]:
        return await self.repo.list_all(limit=limit, offset=offset)
