from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.logging import logger
from app.providers.telephony.factory import get_telephony_provider
from app.repositories.call_repo import CallRepository
from app.schemas.webhook import TelephonyWebhookResponse
from app.services.call_service import CallService

router = APIRouter(prefix="/webhooks/telephony", tags=["Telephony Webhooks"])


@router.post("/call-status", response_model=TelephonyWebhookResponse)
async def telephony_call_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    headers = dict(request.headers)

    provider = get_telephony_provider()
    # Verify signature
    if not provider.verify_webhook_signature(body, headers):
        logger.warning("[Webhook] Signature verification failed for inbound telephony event.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Try JSON or Form body
    try:
        payload = await request.json()
    except Exception:
        form_data = await request.form()
        payload = dict(form_data)

    event_data = await provider.handle_webhook(payload, headers)
    provider_call_id = event_data.get("provider_call_id")
    status = event_data.get("normalized_status", "IN_PROGRESS").upper()

    logger.info(f"[Webhook] Received call status update for {provider_call_id}: {status}")

    if provider_call_id:
        call_repo = CallRepository(db)
        call = await call_repo.get_by_provider_call_id(provider_call_id)
        if call:
            await call_repo.update_status(
                call_id=call.id,
                new_status=status,
                recording_url=event_data.get("recording_url"),
            )
            if status in ["COMPLETED", "FAILED", "BUSY", "NO_ANSWER"]:
                service = CallService(db)
                await service.complete_call(call.id, termination_reason=f"CARRIER_{status}")

    return TelephonyWebhookResponse(
        success=True,
        status="PROCESSED",
        message="Event processed idempotently.",
        event_handled=status,
    )
