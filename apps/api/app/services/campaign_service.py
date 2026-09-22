from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import NotFoundError, VeyraException
from app.models.call import Call
from app.models.campaign import Campaign
from app.models.lead import CampaignLead
from app.repositories.campaign_repo import CampaignRepository
from app.schemas.campaign import (
    CampaignCreate,
    CampaignDetailResponse,
    CampaignResponse,
    CampaignStats,
    CampaignUpdate,
)
from app.schemas.script import ScriptCreate, ScriptResponse, ScriptUpdate


class CampaignService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.campaign_repo = CampaignRepository(session)

    async def create_campaign(self, user_id: str, data: CampaignCreate) -> CampaignDetailResponse:
        campaign = Campaign(
            user_id=user_id,
            name=data.name,
            description=data.description,
            objective=data.objective,
            status="DRAFT",
            primary_language=data.primary_language,
            fallback_language=data.fallback_language,
            schedule_config=data.schedule_config,
        )
        created = await self.campaign_repo.create(campaign)

        # If script provided in create request, create it
        if data.script:
            script_dict = data.script.model_dump()
            # Ensure questions are serialized as dicts
            if "questions" in script_dict:
                script_dict["questions"] = [
                    q if isinstance(q, dict) else q.model_dump() for q in script_dict["questions"]
                ]
            await self.campaign_repo.upsert_script(created.id, script_dict)

        loaded = await self.campaign_repo.get_with_script(created.id)
        return await self._to_detail_response(loaded)

    async def get_campaign(self, campaign_id: str) -> CampaignDetailResponse:
        campaign = await self.campaign_repo.get_with_script(campaign_id)
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)
        return await self._to_detail_response(campaign)

    async def list_campaigns(self, user_id: str, skip: int = 0, limit: int = 100) -> List[CampaignResponse]:
        campaigns = await self.campaign_repo.list_by_user(user_id, skip=skip, limit=limit)
        results = []
        for c in campaigns:
            stats = await self.get_campaign_stats(c.id)
            resp = CampaignResponse.model_validate(c)
            resp.stats = stats
            results.append(resp)
        return results

    async def update_campaign(self, campaign_id: str, data: CampaignUpdate) -> CampaignDetailResponse:
        campaign = await self.campaign_repo.get_with_script(campaign_id)
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)

        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(campaign, k, v)

        await self.campaign_repo.update(campaign)
        return await self._to_detail_response(campaign)

    async def update_status(self, campaign_id: str, new_status: str) -> CampaignDetailResponse:
        campaign = await self.campaign_repo.get_with_script(campaign_id)
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)

        valid_transitions = {
            "DRAFT": ["ACTIVE", "SCHEDULED", "CANCELLED"],
            "SCHEDULED": ["ACTIVE", "PAUSED", "CANCELLED"],
            "ACTIVE": ["PAUSED", "COMPLETED", "CANCELLED"],
            "PAUSED": ["ACTIVE", "COMPLETED", "CANCELLED"],
            "COMPLETED": ["ACTIVE"],
            "CANCELLED": ["DRAFT"],
        }

        current = campaign.status
        if new_status not in valid_transitions.get(current, []):
            raise VeyraException(
                code="INVALID_STATUS_TRANSITION",
                message=f"Cannot transition campaign status from '{current}' to '{new_status}'.",
            )

        campaign.status = new_status
        await self.campaign_repo.update(campaign)
        return await self._to_detail_response(campaign)

    async def save_script(self, campaign_id: str, data: ScriptUpdate) -> ScriptResponse:
        campaign = await self.campaign_repo.get(campaign_id)
        if not campaign:
            raise NotFoundError("Campaign", campaign_id)

        script_dict = data.model_dump(exclude_unset=True)
        if "questions" in script_dict and script_dict["questions"] is not None:
            script_dict["questions"] = [
                q if isinstance(q, dict) else q.model_dump() for q in script_dict["questions"]
            ]

        script = await self.campaign_repo.upsert_script(campaign_id, script_dict)
        return ScriptResponse.model_validate(script)

    async def get_campaign_stats(self, campaign_id: str) -> CampaignStats:
        total_leads_res = await self.session.execute(
            select(func.count()).select_from(CampaignLead).filter(CampaignLead.campaign_id == campaign_id)
        )
        total_leads = total_leads_res.scalar() or 0

        calls_completed_res = await self.session.execute(
            select(func.count())
            .select_from(Call)
            .filter(Call.campaign_id == campaign_id, Call.status == "COMPLETED")
        )
        calls_completed = calls_completed_res.scalar() or 0

        calls_in_progress_res = await self.session.execute(
            select(func.count())
            .select_from(Call)
            .filter(
                Call.campaign_id == campaign_id,
                Call.status.in_(["INITIATING", "RINGING", "CONNECTED", "IN_PROGRESS"]),
            )
        )
        calls_in_progress = calls_in_progress_res.scalar() or 0

        interested_res = await self.session.execute(
            select(func.count())
            .select_from(CampaignLead)
            .filter(CampaignLead.campaign_id == campaign_id, CampaignLead.status == "INTERESTED")
        )
        interested_count = interested_res.scalar() or 0

        progress = (calls_completed / total_leads * 100.0) if total_leads > 0 else 0.0

        return CampaignStats(
            total_leads=total_leads,
            calls_completed=calls_completed,
            calls_in_progress=calls_in_progress,
            interested_count=interested_count,
            progress_percentage=round(progress, 1),
        )

    async def _to_detail_response(self, campaign: Campaign) -> CampaignDetailResponse:
        stats = await self.get_campaign_stats(campaign.id)
        detail = CampaignDetailResponse.model_validate(campaign)
        detail.stats = stats
        if campaign.script:
            detail.script = ScriptResponse.model_validate(campaign.script)
        return detail
