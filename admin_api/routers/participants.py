"""Раздел «Участники»: поиск, фильтрация, история, редактирование."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_current_user, get_db, require_permission
from app.core.exceptions import ValidationError
from app.models.panel_user import PanelUser
from app.repositories.manual_registration_repo import ManualRegistrationRepository
from app.repositories.participant_repo import ParticipantRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.ticket_repo import TicketRepository
from app.schemas.manual_registration import ManualRegistrationOut
from app.schemas.participant import ParticipantListResponse, ParticipantOut, ParticipantUpdateRequest
from app.schemas.payment import PaymentOut
from app.schemas.ticket import TicketOut

router = APIRouter(prefix="/api/participants", tags=["participants"])


@router.get("", response_model=ParticipantListResponse)
async def list_participants(
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("participants.view")),
) -> ParticipantListResponse:
    repo = ParticipantRepository(session)
    items, total = await repo.search(query=q, limit=limit, offset=offset)
    return ParticipantListResponse(items=[ParticipantOut.model_validate(i) for i in items], total=total)


@router.get("/{participant_id}", response_model=ParticipantOut)
async def get_participant(
    participant_id: str,
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("participants.view")),
) -> ParticipantOut:
    repo = ParticipantRepository(session)
    participant = await repo.get(participant_id)
    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден")
    return ParticipantOut.model_validate(participant)


@router.patch("/{participant_id}", response_model=ParticipantOut)
async def update_participant(
    participant_id: str,
    payload: ParticipantUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: PanelUser = Depends(require_permission("participants.edit")),
) -> ParticipantOut:
    from app.models.enums import AuditActorTypeEnum
    from app.services.audit_service import AuditService

    repo = ParticipantRepository(session)
    participant = await repo.get(participant_id)
    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден")

    if payload.full_name is not None:
        participant.full_name = payload.full_name
    if payload.comment is not None:
        participant.comment = payload.comment
    if payload.is_blocked is not None:
        participant.is_blocked = payload.is_blocked

    await session.flush()
    await AuditService(session).log(
        action="participant.updated",
        actor_type=AuditActorTypeEnum.PANEL_USER,
        actor_id=current_user.id,
        actor_label=current_user.login,
        entity_type="participant",
        entity_id=participant.id,
        details=payload.model_dump(exclude_none=True),
    )
    await session.commit()
    return ParticipantOut.model_validate(participant)


@router.get("/{participant_id}/tickets", response_model=list[TicketOut])
async def get_participant_tickets(
    participant_id: str,
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("tickets.view")),
) -> list[TicketOut]:
    repo = TicketRepository(session)
    tickets = await repo.list_by_participant(participant_id)
    return [TicketOut.model_validate(t) for t in tickets]


@router.get("/{participant_id}/payments", response_model=list[PaymentOut])
async def get_participant_payments(
    participant_id: str,
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("sales.view")),
) -> list[PaymentOut]:
    repo = PaymentRepository(session)
    payments = await repo.list_by_participant(participant_id)
    return [PaymentOut.model_validate(p) for p in payments]


@router.get("/{participant_id}/manual-registrations", response_model=list[ManualRegistrationOut])
async def get_participant_manual_registrations(
    participant_id: str,
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("manual_registration.view")),
) -> list[ManualRegistrationOut]:
    repo = ManualRegistrationRepository(session)
    regs = await repo.list_by_participant(participant_id)
    return [ManualRegistrationOut.model_validate(r) for r in regs]
