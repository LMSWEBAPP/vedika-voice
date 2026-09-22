from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class TelephonyCallResponse:
    def __init__(
        self,
        provider_call_id: str,
        status: str,
        to_phone: str,
        from_phone: str,
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.provider_call_id = provider_call_id
        self.status = status
        self.to_phone = to_phone
        self.from_phone = from_phone
        self.raw_response = raw_response or {}


class TelephonyProvider(ABC):
    """
    Abstract Telephony Provider interface.
    Decouples business logic and campaign management from specific carriers (Exotel, Twilio, etc.).
    """

    @abstractmethod
    async def create_call(
        self,
        to_phone: str,
        from_phone: str,
        callback_url: str,
        custom_data: Optional[Dict[str, Any]] = None,
    ) -> TelephonyCallResponse:
        """Initiate an outbound call."""
        pass

    @abstractmethod
    async def end_call(self, provider_call_id: str) -> bool:
        """Terminate an active call."""
        pass

    @abstractmethod
    async def get_call_status(self, provider_call_id: str) -> str:
        """Fetch current status from the carrier."""
        pass

    @abstractmethod
    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Normalize carrier webhook events into standard platform events."""
        pass

    @abstractmethod
    def verify_webhook_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        """Validate HMAC signature of incoming webhooks to prevent spoofing."""
        pass
