import hashlib
import hmac
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.providers.telephony.interface import TelephonyCallResponse, TelephonyProvider


class ExotelProvider(TelephonyProvider):
    """
    Production Telephony Provider integrating with Exotel telephony API.
    Handles outbound call initiation, webhooks, and status mapping.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        api_key: Optional[str] = None,
        api_token: Optional[str] = None,
        subdomain: Optional[str] = None,
        caller_id: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.account_sid = account_sid or settings.EXOTEL_ACCOUNT_SID
        self.api_key = api_key or settings.EXOTEL_API_KEY
        self.api_token = api_token or settings.EXOTEL_API_TOKEN
        self.subdomain = subdomain or settings.EXOTEL_SUB_DOMAIN
        self.caller_id = caller_id or settings.EXOTEL_CALLER_ID
        self.webhook_secret = webhook_secret or settings.EXOTEL_WEBHOOK_SECRET

    @property
    def base_url(self) -> str:
        return f"https://{self.subdomain}/v1/Accounts/{self.account_sid}"

    async def create_call(
        self,
        to_phone: str,
        from_phone: str,
        callback_url: str,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> TelephonyCallResponse:
        url = f"{self.base_url}/Calls/connect.json"
        payload = {
            "From": from_phone or self.caller_id,
            "To": to_phone,
            "CallerId": self.caller_id,
            "StatusCallback": callback_url,
            "StatusCallbackEvents[0]": "terminal",
            "CustomField": str(custom_data.get("call_id", "")) if custom_data else "",
        }

        async with httpx.AsyncClient(auth=(self.api_key, self.api_token), timeout=10.0) as client:
            resp = await client.post(url, data=payload)
            resp.raise_for_status()
            data = resp.json()

            call_info = data.get("Call", {})
            call_sid = call_info.get("Sid", "")
            raw_status = call_info.get("Status", "queued")

            logger.info(f"[ExotelProvider] Call created successfully: SID {call_sid}")
            return TelephonyCallResponse(
                provider_call_id=call_sid,
                status=raw_status,
                to_phone=to_phone,
                from_phone=from_phone,
                raw_response=data,
            )

    async def end_call(self, provider_call_id: str) -> bool:
        url = f"{self.base_url}/Calls/{provider_call_id}.json"
        async with httpx.AsyncClient(auth=(self.api_key, self.api_token), timeout=10.0) as client:
            resp = await client.post(url, data={"Status": "completed"})
            return resp.status_code == 200

    async def get_call_status(self, provider_call_id: str) -> str:
        url = f"{self.base_url}/Calls/{provider_call_id}.json"
        async with httpx.AsyncClient(auth=(self.api_key, self.api_token), timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return data.get("Call", {}).get("Status", "unknown")

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Maps Exotel status payload to normalized platform statuses."""
        call_sid = payload.get("CallSid") or payload.get("Sid", "")
        status = (payload.get("Status") or "").lower()

        # Map Exotel status to platform status
        status_map = {
            "queued": "QUEUED",
            "ringing": "RINGING",
            "in-progress": "CONNECTED",
            "completed": "COMPLETED",
            "failed": "FAILED",
            "busy": "BUSY",
            "no-answer": "NO_ANSWER",
            "canceled": "CANCELLED",
        }

        normalized = status_map.get(status, "IN_PROGRESS")
        return {
            "provider_call_id": call_sid,
            "normalized_status": normalized,
            "duration": int(payload.get("Duration", 0) or 0),
            "recording_url": payload.get("RecordingUrl"),
            "raw": payload,
        }

    def verify_webhook_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        if not self.webhook_secret:
            return True  # If no secret configured, pass in non-enforcing mode

        signature = headers.get("X-Exotel-Signature") or headers.get("x-exotel-signature")
        if not signature:
            return False

        computed = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
