import asyncio
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignDetailResponse,
    CampaignResponse,
    CampaignStatusUpdate,
    CampaignUpdate,
)
from app.schemas.script import ScriptResponse, ScriptUpdate
from app.services.campaign_service import CampaignService
from app.workers.campaign_worker import CampaignWorker

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.list_campaigns(user_id=current_user.id, skip=skip, limit=limit)


@router.post("", response_model=CampaignDetailResponse)
async def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.create_campaign(user_id=current_user.id, data=data)


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.get_campaign(campaign_id)


@router.put("/{campaign_id}", response_model=CampaignDetailResponse)
async def update_campaign(
    campaign_id: str,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.update_campaign(campaign_id, data)


@router.post("/{campaign_id}/status", response_model=CampaignDetailResponse)
async def update_campaign_status(
    campaign_id: str,
    data: CampaignStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.update_status(campaign_id, data.status)


@router.put("/{campaign_id}/script", response_model=ScriptResponse)
async def update_campaign_script(
    campaign_id: str,
    data: ScriptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.save_script(campaign_id, data)


@router.post("/{campaign_id}/start", response_model=CampaignDetailResponse)
async def start_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    res = await service.update_status(campaign_id, "ACTIVE")
    worker = CampaignWorker(campaign_id)
    asyncio.create_task(worker.start())
    return res


@router.post("/{campaign_id}/pause", response_model=CampaignDetailResponse)
async def pause_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.update_status(campaign_id, "PAUSED")


@router.post("/{campaign_id}/stop", response_model=CampaignDetailResponse)
async def stop_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CampaignService(db)
    return await service.update_status(campaign_id, "COMPLETED")
