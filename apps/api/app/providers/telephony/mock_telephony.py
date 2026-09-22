import asyncio
import uuid
from typing import Any, Callable, Dict, Optional
from app.core.logging import logger
from app.providers.telephony.interface import TelephonyCallResponse, TelephonyProvider


class MockTelephonyProvider(TelephonyProvider):
    """
    Mock Telephony Provider for zero-credential local development and automated testing.
    Simulates outbound call placement, ringing, connection, and termination.
    """

    def __init__(self):
        self._calls: Dict[str, Dict[str, Any]] = {}
        self._status_callbacks: Dict[str, Callable] = {}

    async def create_call(
        self,
        to_phone: str,
        from_phone: str,
        callback_url: str,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> TelephonyCallResponse:
        call_sid = f"mock_call_{uuid.uuid4().hex[:12]}"
        self._calls[call_sid] = {
            "to": to_phone,
            "from": from_phone,
            "status": "INITIATING",
            "callback_url": callback_url,
            "custom_data": custom_data or {},
        }

        logger.info(f"[MockTelephony] Outbound call created {call_sid} to {to_phone}")

        return TelephonyCallResponse(
            provider_call_id=call_sid,
            status="INITIATING",
            to_phone=to_phone,
            from_phone=from_phone,
            raw_response={"mock": True, "call_sid": call_sid},
        )

    async def end_call(self, provider_call_id: str) -> bool:
        call = self._calls.get(provider_call_id)
        if call:
            call["status"] = "COMPLETED"
            logger.info(f"[MockTelephony] Call {provider_call_id} ended.")
            return True
        return False

    async def get_call_status(self, provider_call_id: str) -> str:
        call = self._calls.get(provider_call_id)
        if call:
            return call.get("status", "COMPLETED")
        return "COMPLETED"

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Normalizes mock webhook payloads."""
        call_sid = payload.get("CallSid") or payload.get("provider_call_id", "")
        status = payload.get("Status", "in-progress").lower()
        return {
            "provider_call_id": call_sid,
            "normalized_status": status,
            "raw": payload,
        }

    def verify_webhook_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        # Mock provider accepts all signatures in development
        return True
