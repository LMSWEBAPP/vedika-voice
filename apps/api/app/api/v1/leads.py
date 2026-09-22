from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.lead import (
    BatchAssignLeadsRequest,
    CampaignLeadResponse,
    LeadCreate,
    LeadImportResult,
    LeadResponse,
    LeadUpdate,
)
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    search: Optional[str] = Query(None),
    do_not_call: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    leads, _ = await service.list_leads(
        user_id=current_user.id,
        search=search,
        do_not_call=do_not_call,
        skip=skip,
        limit=limit,
    )
    return leads


@router.post("", response_model=LeadResponse)
async def create_lead(
    data: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    return await service.create_lead(user_id=current_user.id, data=data)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    return await service.get_lead(lead_id)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    return await service.update_lead(lead_id, data)


@router.post("/{lead_id}/dnc", response_model=LeadResponse)
async def toggle_dnc(
    lead_id: str,
    do_not_call: bool = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    return await service.set_do_not_call(lead_id, do_not_call)


@router.post("/upload-csv", response_model=LeadImportResult)
async def upload_csv(
    file: UploadFile = File(...),
    campaign_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    csv_text = content.decode("utf-8", errors="ignore")
    service = LeadService(db)
    return await service.import_csv(
        user_id=current_user.id,
        csv_content=csv_text,
        campaign_id=campaign_id,
    )


@router.post("/assign")
async def batch_assign_leads(
    data: BatchAssignLeadsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    assigned_count = await service.assign_to_campaign(
        campaign_id=data.campaign_id,
        lead_ids=data.lead_ids or [],
    )
    return {"success": True, "assigned_count": assigned_count}


@router.get("/campaign/{campaign_id}", response_model=List[CampaignLeadResponse])
async def get_campaign_leads(
    campaign_id: str,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LeadService(db)
    c_leads, _ = await service.get_campaign_leads(
        campaign_id=campaign_id, status=status, skip=skip, limit=limit
    )
    return c_leads
