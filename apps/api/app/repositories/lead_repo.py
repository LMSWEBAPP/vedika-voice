from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.lead import CampaignLead, Lead
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    def __init__(self, session: AsyncSession):
        super().__init__(Lead, session)

    async def get_by_phone(self, phone: str, user_id: str) -> Optional[Lead]:
        clean_phone = phone.strip()
        result = await self.session.execute(
            select(Lead).filter(Lead.phone == clean_phone, Lead.user_id == user_id)
        )
        return result.scalars().first()

    async def list_by_user(
        self,
        user_id: str,
        search: Optional[str] = None,
        do_not_call: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Lead], int]:
        query = select(Lead).filter(Lead.user_id == user_id)

        if do_not_call is not None:
            query = query.filter(Lead.do_not_call == do_not_call)

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Lead.full_name.ilike(s),
                    Lead.phone.ilike(s),
                    Lead.company.ilike(s),
                    Lead.email.ilike(s),
                )
            )

        # Count total
        count_q = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_q)
        total = total_result.scalar() or 0

        # Paginated items
        items_result = await self.session.execute(
            query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def assign_to_campaign(self, campaign_id: str, lead_id: str) -> CampaignLead:
        # Check if already assigned
        result = await self.session.execute(
            select(CampaignLead).filter(
                CampaignLead.campaign_id == campaign_id,
                CampaignLead.lead_id == lead_id,
            )
        )
        existing = result.scalars().first()
        if existing:
            return existing

        c_lead = CampaignLead(campaign_id=campaign_id, lead_id=lead_id, status="NEW")
        self.session.add(c_lead)
        await self.session.flush()
        return c_lead

    async def get_campaign_leads(
        self,
        campaign_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[CampaignLead], int]:
        query = (
            select(CampaignLead)
            .options(selectinload(CampaignLead.lead))
            .filter(CampaignLead.campaign_id == campaign_id)
        )

        if status:
            query = query.filter(CampaignLead.status == status)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0

        items_res = await self.session.execute(
            query.order_by(CampaignLead.created_at.asc()).offset(skip).limit(limit)
        )
        return list(items_res.scalars().all()), total

    async def get_next_queued_campaign_lead(self, campaign_id: str) -> Optional[CampaignLead]:
        result = await self.session.execute(
            select(CampaignLead)
            .options(selectinload(CampaignLead.lead))
            .filter(
                CampaignLead.campaign_id == campaign_id,
                CampaignLead.status.in_(["NEW", "QUEUED"]),
            )
            .order_by(CampaignLead.created_at.asc())
            .limit(1)
        )
        return result.scalars().first()

    async def update_campaign_lead_status(
        self, campaign_id: str, lead_id: str, status: str, increment_attempt: bool = False
    ) -> Optional[CampaignLead]:
        result = await self.session.execute(
            select(CampaignLead).filter(
                CampaignLead.campaign_id == campaign_id,
                CampaignLead.lead_id == lead_id,
            )
        )
        c_lead = result.scalars().first()
        if c_lead:
            c_lead.status = status
            if increment_attempt:
                c_lead.attempts += 1
                c_lead.last_called_at = datetime.now(timezone.utc)
            await self.session.flush()
        return c_lead
