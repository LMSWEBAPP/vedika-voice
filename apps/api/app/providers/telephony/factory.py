from app.core.config import settings
from app.core.logging import logger
from app.providers.telephony.interface import TelephonyProvider
from app.providers.telephony.mock_telephony import MockTelephonyProvider
from app.providers.telephony.exotel import ExotelProvider

_telephony_provider_instance: TelephonyProvider = None


def get_telephony_provider() -> TelephonyProvider:
    """
    Factory function returning the configured TelephonyProvider singleton.
    Defaults to MockTelephonyProvider when TELEPHONY_PROVIDER != 'exotel' or credentials missing.
    """
    global _telephony_provider_instance
    if _telephony_provider_instance is None:
        provider_name = (settings.TELEPHONY_PROVIDER or "mock").lower().strip()
        if provider_name == "exotel" and settings.EXOTEL_ACCOUNT_SID and settings.EXOTEL_API_KEY:
            logger.info("[TelephonyFactory] Initializing ExotelProvider")
            _telephony_provider_instance = ExotelProvider()
        else:
            if provider_name == "exotel":
                logger.warning(
                    "[TelephonyFactory] 'exotel' requested but credentials missing. Falling back to MockTelephonyProvider."
                )
            logger.info("[TelephonyFactory] Initializing MockTelephonyProvider (Simulation Mode)")
            _telephony_provider_instance = MockTelephonyProvider()
    return _telephony_provider_instance
