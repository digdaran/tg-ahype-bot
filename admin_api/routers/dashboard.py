"""Dashboard: сводные показатели для главной страницы панели."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin_api.deps import get_db, require_permission
from app.models.panel_user import PanelUser
from app.repositories.participant_repo import ParticipantRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.ticket_repo import TicketRepository
from app.repositories.giveaway_repo import GiveawayRepository
from app.models.enums import PaymentStatusEnum

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    session: AsyncSession = Depends(get_db),
    _: PanelUser = Depends(require_permission("dashboard.view")),
) -> dict:
    participants_repo = ParticipantRepository(session)
    payments_repo = PaymentRepository(session)
    tickets_repo = TicketRepository(session)
    giveaways_repo = GiveawayRepository(session)

    total_participants = await participants_repo.count_all()
    total_revenue = await payments_repo.sum_succeeded_amount()
    successful_payments = await payments_repo.count_succeeded()
    average_check = (total_revenue / successful_payments) if successful_payments else 0.0

    giveaways = await giveaways_repo.list_all(limit=1000)
    tickets_issued = sum(g.tickets_issued for g in giveaways)
    tickets_remaining = sum(g.tickets_remaining for g in giveaways)

    recent_payments, _ = await payments_repo.list_filtered(status=PaymentStatusEnum.SUCCEEDED, limit=10)
    recent_participants, _ = await participants_repo.search(limit=10)

    return {
        "total_participants": total_participants,
        "tickets_issued": tickets_issued,
        "tickets_remaining": tickets_remaining,
        "total_revenue": total_revenue,
        "average_check": average_check,
        "recent_payments": [
            {
                "order_id": p.order_id,
                "amount": float(p.amount),
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in recent_payments
        ],
        "recent_registrations": [
            {
                "phone": p.phone,
                "full_name": p.full_name,
                "created_at": p.created_at.isoformat(),
            }
            for p in recent_participants
        ],
    }
