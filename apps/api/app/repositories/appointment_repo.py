from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.appointment import Appointment
from app.models.campaign import Campaign
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Appointment, session)

    async def get_with_details(self, appointment_id: str) -> Optional[Appointment]:
        result = await self.session.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.lead),
                selectinload(Appointment.campaign),
                selectinload(Appointment.call),
            )
            .filter(Appointment.id == appointment_id)
        )
        return result.scalars().first()

    async def list_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Appointment], int]:
        query = (
            select(Appointment)
            .join(Campaign, Appointment.campaign_id == Campaign.id)
            .options(
                selectinload(Appointment.lead),
                selectinload(Appointment.campaign),
            )
            .filter(Campaign.user_id == user_id)
        )

        if status:
            query = query.filter(Appointment.status == status)

        count_q = select(func.count()).select_from(query.subquery())
        total_res = await self.session.execute(count_q)
        total = total_res.scalar() or 0

        items_res = await self.session.execute(
            query.order_by(Appointment.scheduled_at.asc()).offset(skip).limit(limit)
        )
        return list(items_res.scalars().all()), total

    async def get_upcoming_reminders(self, user_id: str) -> List[Appointment]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Appointment)
            .join(Campaign, Appointment.campaign_id == Campaign.id)
            .options(selectinload(Appointment.lead))
            .filter(
                Campaign.user_id == user_id,
                Appointment.status == "REMINDER_SCHEDULED",
                Appointment.scheduled_at >= now,
            )
            .order_by(Appointment.scheduled_at.asc())
            .limit(10)
        )
        return list(result.scalars().all())
