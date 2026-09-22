import asyncio
from typing import Optional
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.models.campaign import Campaign
from app.repositories.campaign_repo import CampaignRepository
from app.repositories.lead_repo import LeadRepository
from app.services.call_service import CallService


class CampaignWorker:
    """
    Background worker orchestrating calls for active campaigns.
    Processes queued leads without blocking HTTP threads.
    """

    def __init__(self, campaign_id: str):
        self.campaign_id = campaign_id
        self._is_running = False

    async def start(self) -> None:
        self._is_running = True
        logger.info(f"[CampaignWorker] Starting batch runner for campaign {self.campaign_id}")

        while self._is_running:
            async with AsyncSessionLocal() as session:
                camp_repo = CampaignRepository(session)
                campaign = await camp_repo.get(self.campaign_id)
                if not campaign or campaign.status != "ACTIVE":
                    logger.info(f"[CampaignWorker] Campaign {self.campaign_id} is no longer ACTIVE. Stopping worker.")
                    break

                lead_repo = LeadRepository(session)
                next_cl = await lead_repo.get_next_queued_campaign_lead(self.campaign_id)
                if not next_cl:
                    logger.info(f"[CampaignWorker] No more queued leads for campaign {self.campaign_id}. Completed.")
                    await camp_repo.update_status(self.campaign_id, "COMPLETED")
                    break

                lead_id = next_cl.lead_id

                # Call the lead
                call_service = CallService(session)
                try:
                    await call_service.initiate_call(self.campaign_id, lead_id)
                except Exception as exc:
                    logger.error(f"[CampaignWorker] Error calling lead {lead_id}: {exc}")

            # Throttle between call initiations to respect rate limits
            await asyncio.sleep(4.0)

        self._is_running = False

    def stop(self) -> None:
        self._is_running = False
