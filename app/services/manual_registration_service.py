"""
Сервис ручных (офлайн) регистраций.

Поток: создание регистрации (PENDING) -> выдача номерков оператором
(CONFIRMED, номерки создаются) -> либо отмена ДО подтверждения (CANCELLED).
Бот ничего не отправляет участнику — постер физический.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import GiveawayLockedError, ValidationError
from app.models.enums import (
    AuditActorTypeEnum,
    ManualRegistrationStatusEnum,
    TicketSourceEnum,
)
from app.models.manual_registration import ManualRegistration
from app.models.participant import Participant
from app.repositories.giveaway_repo import GiveawayRepository
from app.repositories.manual_registration_repo import ManualRegistrationRepository
from app.services.audit_service import AuditService
from app.services.registration_service import RegistrationService
from app.services.ticket_service import TicketService


class ManualRegistrationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ManualRegistrationRepository(session)
        self.giveaways = GiveawayRepository(session)
        self.registration = RegistrationService(session)
        self.tickets = TicketService(session)
        self.audit = AuditService(session)

    async def create(
        self,
        phone: str,
        giveaway_id: str,
        quantity: int,
        operator_id: str,
        operator_label: str,
        comment: Optional[str] = None,
    ) -> ManualRegistration:
        if quantity < 1:
            raise ValidationError("Количество номерков должно быть положительным")

        giveaway = await self.giveaways.get(giveaway_id)
        if giveaway is None:
            raise ValueError(f"Розыгрыш {giveaway_id} не найден")
        if giveaway.is_locked or not giveaway.is_registration_open:
            raise GiveawayLockedError(f"Розыгрыш '{giveaway.name}' недоступен для регистрации")

        participant, _ = await self.registration.get_or_create_by_phone(phone)

        registration = ManualRegistration(
            participant_id=participant.id,
            giveaway_id=giveaway_id,
            quantity=quantity,
            comment=comment,
            operator_id=operator_id,
            status=ManualRegistrationStatusEnum.PENDING,
        )
        await self.repo.add(registration)

        await self.audit.log(
            action="manual_registration.created",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=operator_id,
            actor_label=operator_label,
            entity_type="manual_registration",
            entity_id=registration.id,
            details={"phone": phone, "quantity": quantity, "giveaway_id": giveaway_id, "comment": comment},
        )
        return registration

    async def confirm_and_issue_tickets(
        self, registration_id: str, operator_id: str, operator_label: str
    ) -> ManualRegistration:
        registration = await self.repo.get(registration_id)
        if registration is None:
            raise ValueError(f"Регистрация {registration_id} не найдена")
        if registration.status != ManualRegistrationStatusEnum.PENDING:
            raise ValidationError("Номерки можно выдать только для регистрации в статусе 'ожидает'")

        participant = await self.session.get(Participant, registration.participant_id)

        issued = await self.tickets.issue_tickets(
            giveaway_id=registration.giveaway_id,
            participant=participant,
            quantity=registration.quantity,
            source=TicketSourceEnum.MANUAL,
            manual_registration=registration,
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=operator_id,
            actor_label=operator_label,
        )

        registration.status = ManualRegistrationStatusEnum.CONFIRMED
        registration.confirmed_at = datetime.now(timezone.utc)
        await self.session.flush()

        await self.audit.log(
            action="manual_registration.confirmed",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=operator_id,
            actor_label=operator_label,
            entity_type="manual_registration",
            entity_id=registration.id,
            details={"codes": [t.full_code for t in issued]},
        )
        return registration

    async def cancel(self, registration_id: str, operator_id: str, operator_label: str) -> ManualRegistration:
        registration = await self.repo.get(registration_id)
        if registration is None:
            raise ValueError(f"Регистрация {registration_id} не найдена")
        if registration.status != ManualRegistrationStatusEnum.PENDING:
            raise ValidationError("Отменить можно только регистрацию, ожидающую подтверждения (до выдачи номерков)")

        registration.status = ManualRegistrationStatusEnum.CANCELLED
        registration.cancelled_by_id = operator_id
        registration.cancelled_at = datetime.now(timezone.utc)
        await self.session.flush()

        await self.audit.log(
            action="manual_registration.cancelled",
            actor_type=AuditActorTypeEnum.PANEL_USER,
            actor_id=operator_id,
            actor_label=operator_label,
            entity_type="manual_registration",
            entity_id=registration.id,
        )
        return registration

    async def list_filtered(
        self,
        status: Optional[ManualRegistrationStatusEnum] = None,
        operator_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ManualRegistration], int]:
        return await self.repo.list_filtered(status=status, operator_id=operator_id, limit=limit, offset=offset)
