from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.call import CallDetailResponse, CallInitiateRequest, CallResponse
from app.services.call_service import CallService

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.get("", response_model=List[CallResponse])
async def list_calls(
    campaign_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CallService(db)
    calls, _ = await service.list_calls(
        campaign_id=campaign_id, status=status, skip=skip, limit=limit
    )
    return calls


@router.post("/initiate", response_model=CallResponse)
async def initiate_call(
    data: CallInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CallService(db)
    return await service.initiate_call(campaign_id=data.campaign_id, lead_id=data.lead_id)


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_details(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CallService(db)
    return await service.get_call_details(call_id)


@router.post("/{call_id}/retry", response_model=CallResponse)
async def retry_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CallService(db)
    old_call = await service.get_call_details(call_id)
    return await service.initiate_call(
        campaign_id=old_call.campaign_id,
        lead_id=old_call.lead_id,
    )
