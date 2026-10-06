from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.models.user import User
from app.providers.telephony.factory import get_telephony_provider
from app.schemas.call import CallDetailResponse, CallInitiateRequest, CallResponse
from app.services.call_service import CallService

router = APIRouter(prefix="/calls", tags=["Calls"])


class DirectCallRequest(BaseModel):
    phone: str
    name: Optional[str] = "Prospect"
    company: Optional[str] = "Business"
    pitch_goal: Optional[str] = ""
    notes: Optional[str] = ""


@router.post("/direct-call")
async def place_direct_call(data: DirectCallRequest):
    """
    Directly initiates an outbound carrier phone call to the lead's phone number
    using the configured telephony provider (Twilio or Exotel).
    """
    clean_phone = data.phone.strip().replace(" ", "").replace("-", "")
    if not clean_phone.startswith("+"):
        if len(clean_phone) == 10:
            clean_phone = f"+91{clean_phone}"
        else:
            clean_phone = f"+{clean_phone}"

    provider = get_telephony_provider()
    caller_phone = (
        settings.TWILIO_PHONE_NUMBER
        if settings.TELEPHONY_PROVIDER == "twilio" and settings.TWILIO_PHONE_NUMBER
        else settings.EXOTEL_CALLER_ID
    )

    callback_url = f"{settings.TELEPHONY_WEBHOOK_BASE_URL}{settings.API_V1_STR}/webhooks/telephony/call-status"
    try:
        response = await provider.create_call(
            to_phone=clean_phone,
            from_phone=caller_phone,
            callback_url=callback_url,
            custom_data={
                "name": data.name,
                "company": data.company,
                "pitch_goal": data.pitch_goal,
                "notes": data.notes,
            },
        )
        return {
            "success": True,
            "provider_call_id": response.provider_call_id,
            "status": response.status,
            "to_phone": response.to_phone,
            "from_phone": response.from_phone,
            "provider": settings.TELEPHONY_PROVIDER,
            "message": f"Calling {response.to_phone} from {response.from_phone} via {settings.TELEPHONY_PROVIDER.upper()}! Answer your phone.",
        }
    except Exception as exc:
        logger.error(f"[DirectCall] Failed to place call to {clean_phone}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


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
