from app.core.config import settings
from app.core.logging import logger
from app.providers.ai.interface import AIProvider
from app.providers.ai.mock_ai import MockAIProvider
from app.providers.ai.gemini_live import GeminiLiveProvider

_ai_provider_instance: AIProvider = None


def get_ai_provider() -> AIProvider:
    """
    Factory function returning the configured AIProvider singleton.
    Defaults to MockAIProvider when AI_PROVIDER != 'gemini' or GEMINI_API_KEY is empty.
    """
    global _ai_provider_instance
    if _ai_provider_instance is None:
        provider_name = (settings.AI_PROVIDER or "mock").lower().strip()
        if provider_name == "gemini" and settings.GEMINI_API_KEY:
            logger.info("[AIProviderFactory] Initializing GeminiLiveProvider")
            _ai_provider_instance = GeminiLiveProvider()
        else:
            if provider_name == "gemini" and not settings.GEMINI_API_KEY:
                logger.warning(
                    "[AIProviderFactory] 'gemini' requested but GEMINI_API_KEY is unset. Falling back to MockAIProvider."
                )
            logger.info("[AIProviderFactory] Initializing MockAIProvider (Zero-Key Simulation Mode)")
            _ai_provider_instance = MockAIProvider()
    return _ai_provider_instance
