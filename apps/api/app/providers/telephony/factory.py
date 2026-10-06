from app.core.config import settings
from app.core.logging import logger
from app.providers.telephony.interface import TelephonyProvider
from app.providers.telephony.mock_telephony import MockTelephonyProvider
from app.providers.telephony.exotel import ExotelProvider
from app.providers.telephony.twilio import TwilioProvider

_telephony_provider_instance: TelephonyProvider = None


def get_telephony_provider() -> TelephonyProvider:
    """
    Factory function returning the configured TelephonyProvider singleton.
    Supports 'exotel', 'twilio', and defaults to MockTelephonyProvider.
    """
    global _telephony_provider_instance
    if _telephony_provider_instance is None:
        provider_name = (settings.TELEPHONY_PROVIDER or "mock").lower().strip()
        if provider_name == "exotel" and settings.EXOTEL_ACCOUNT_SID and settings.EXOTEL_API_KEY:
            logger.info("[TelephonyFactory] Initializing ExotelProvider")
            _telephony_provider_instance = ExotelProvider()
        elif provider_name == "twilio" and getattr(settings, "TWILIO_ACCOUNT_SID", None) and getattr(settings, "TWILIO_AUTH_TOKEN", None):
            logger.info("[TelephonyFactory] Initializing TwilioProvider (Twilio Carrier Mode)")
            _telephony_provider_instance = TwilioProvider()
        else:
            if provider_name in ["exotel", "twilio"]:
                logger.warning(
                    f"[TelephonyFactory] '{provider_name}' requested but credentials missing. Falling back to MockTelephonyProvider."
                )
            logger.info("[TelephonyFactory] Initializing MockTelephonyProvider (Simulation Mode)")
            _telephony_provider_instance = MockTelephonyProvider()
    return _telephony_provider_instance
