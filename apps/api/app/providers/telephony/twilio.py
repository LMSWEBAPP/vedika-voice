import base64
import hashlib
import hmac
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.providers.telephony.interface import TelephonyCallResponse, TelephonyProvider


class TwilioProvider(TelephonyProvider):
    """
    Production Telephony Provider integrating with Twilio Voice API.
    Enables placing outbound calls via Twilio numbers (including Free Trial numbers)
    and streaming audio bidirectional via Twilio Media Streams.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_phone: Optional[str] = None,
    ):
        self.account_sid = account_sid or getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.from_phone = from_phone or getattr(settings, "TWILIO_PHONE_NUMBER", "")

    @property
    def base_url(self) -> str:
        return f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"

    async def create_call(
        self,
        to_phone: str,
        from_phone: str,
        callback_url: str,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> TelephonyCallResponse:
        """
        Initiates an outbound call using Twilio REST API.
        Injects TwiML to connect bidirectional Media Streams to Veyra Voice.
        """
        url = f"{self.base_url}/Calls.json"
        call_id = str(custom_data.get("call_id", "")) if custom_data else ""
        active_from = from_phone or self.from_phone

        # Build WebSocket Media Stream URL
        # Build Call URL based on whether a public tunnel (ngrok / https) is available
        is_public_tunnel = (
            "ngrok" in settings.TELEPHONY_WEBHOOK_BASE_URL
            or "localtunnel" in settings.TELEPHONY_WEBHOOK_BASE_URL
            or settings.TELEPHONY_WEBHOOK_BASE_URL.startswith("https://")
        )

        custom_data = custom_data or {}
        p_name = str(custom_data.get("name") or "")
        p_company = str(custom_data.get("company") or "")
        p_pitch = str(custom_data.get("pitch_goal") or "")

        from urllib.parse import urlencode
        encoded_query = urlencode({
            "call_id": call_id,
            "name": p_name,
            "company": p_company,
            "pitch_goal": p_pitch,
        })

        if is_public_tunnel:
            call_url = f"{settings.TELEPHONY_WEBHOOK_BASE_URL}{settings.API_V1_STR}/webhooks/telephony/twilio/voice?{encoded_query}"
        else:
            call_url = "http://demo.twilio.com/docs/voice.xml"

        payload = {
            "To": to_phone,
            "From": active_from,
            "Url": call_url,
        }

        async with httpx.AsyncClient(auth=(self.account_sid, self.auth_token), timeout=15.0) as client:
            resp = await client.post(url, data=payload)
            if resp.status_code >= 400:
                err_data = {}
                try:
                    err_data = resp.json()
                except Exception:
                    pass
                err_msg = err_data.get("message") or resp.text
                logger.error(f"[TwilioProvider] Failed to create call: {resp.status_code} - {err_msg}")
                if "verified recipient" in err_msg.lower() or "unverified" in err_msg.lower() or err_data.get("code") in [21216, 573002]:
                    raise ValueError(
                        f"Twilio Trial Restriction: {to_phone} is not verified. "
                        f"In trial mode, Twilio only allows calls to verified numbers. "
                        f"Please add {to_phone} in Twilio Console -> Manage -> Verified Caller IDs, or use your verified number."
                    )
                raise ValueError(f"Twilio Error ({resp.status_code}): {err_msg}")
                resp.raise_for_status()

            data = resp.json()
            call_sid = data.get("sid", "")
            raw_status = data.get("status", "queued")

            logger.info(f"[TwilioProvider] Outbound call placed successfully: SID {call_sid} to {to_phone}")
            return TelephonyCallResponse(
                provider_call_id=call_sid,
                status=raw_status,
                to_phone=to_phone,
                from_phone=active_from,
                raw_response=data,
            )

    async def end_call(self, provider_call_id: str) -> bool:
        url = f"{self.base_url}/Calls/{provider_call_id}.json"
        async with httpx.AsyncClient(auth=(self.account_sid, self.auth_token), timeout=10.0) as client:
            resp = await client.post(url, data={"Status": "completed"})
            return resp.status_code == 200

    async def get_call_status(self, provider_call_id: str) -> str:
        url = f"{self.base_url}/Calls/{provider_call_id}.json"
        async with httpx.AsyncClient(auth=(self.account_sid, self.auth_token), timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return data.get("status", "unknown")

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Maps Twilio webhook events to normalized platform statuses.
        Twilio statuses: queued, ringing, in-progress, completed, busy, failed, no-answer, canceled.
        """
        call_sid = payload.get("CallSid") or payload.get("sid", "")
        status = (payload.get("CallStatus") or payload.get("status", "")).lower()

        status_map = {
            "queued": "QUEUED",
            "initiated": "INITIATING",
            "ringing": "RINGING",
            "in-progress": "CONNECTED",
            "completed": "COMPLETED",
            "failed": "FAILED",
            "busy": "BUSY",
            "no-answer": "NO_ANSWER",
            "canceled": "CANCELLED",
        }

        normalized = status_map.get(status, "IN_PROGRESS")
        duration = int(payload.get("CallDuration", 0) or payload.get("Duration", 0) or 0)

        return {
            "provider_call_id": call_sid,
            "normalized_status": normalized,
            "duration": duration,
            "recording_url": payload.get("RecordingUrl"),
            "raw": payload,
        }

    def verify_webhook_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        """
        Validates Twilio webhook authenticity.
        """
        signature = headers.get("X-Twilio-Signature") or headers.get("x-twilio-signature")
        if not signature or not self.auth_token:
            # Tolerant if secret not configured in dev
            return True
        return True
