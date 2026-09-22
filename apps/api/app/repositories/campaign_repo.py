from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.campaign import Campaign
from app.models.lead import CampaignLead
from app.models.script import CampaignScript
from app.repositories.base import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self, session: AsyncSession):
        super().__init__(Campaign, session)

    async def get_with_script(self, campaign_id: str) -> Optional[Campaign]:
        result = await self.session.execute(
            select(Campaign)
            .options(selectinload(Campaign.script))
            .filter(Campaign.id == campaign_id)
        )
        return result.scalars().first()

    async def list_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Campaign]:
        result = await self.session.execute(
            select(Campaign)
            .options(selectinload(Campaign.script))
            .filter(Campaign.user_id == user_id)
            .order_by(Campaign.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def upsert_script(self, campaign_id: str, script_data: dict) -> CampaignScript:
        result = await self.session.execute(
            select(CampaignScript).filter(CampaignScript.campaign_id == campaign_id)
        )
        script = result.scalars().first()
        if script:
            for k, v in script_data.items():
                if hasattr(script, k) and v is not None:
                    setattr(script, k, v)
        else:
            script = CampaignScript(campaign_id=campaign_id, **script_data)
            self.session.add(script)
        await self.session.flush()
        return script

    async def get_campaign_lead_count(self, campaign_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(CampaignLead)
            .filter(CampaignLead.campaign_id == campaign_id)
        )
        return result.scalar() or 0
