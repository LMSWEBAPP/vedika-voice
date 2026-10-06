from app.core.config import settings
from app.core.logging import logger
from app.providers.ai.interface import AIProvider
from app.providers.ai.mock_ai import MockAIProvider
from app.providers.ai.gemini_live import GeminiLiveProvider

_ai_provider_instance: AIProvider = None


def get_ai_provider() -> AIProvider:
    """
    Factory function returning the configured AIProvider singleton.
    Uses GeminiLiveProvider whenever GEMINI_API_KEY is set or AI_PROVIDER is gemini,
    otherwise falls back to MockAIProvider for zero-key simulation.
    """
    global _ai_provider_instance
    provider_name = (settings.AI_PROVIDER or "mock").lower().strip()
    has_gemini_key = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    if has_gemini_key and (provider_name in ["gemini", "gemini_live"] or provider_name != "mock"):
        if not isinstance(_ai_provider_instance, GeminiLiveProvider):
            logger.info("[AIProviderFactory] Initializing GeminiLiveProvider with configured API key")
            _ai_provider_instance = GeminiLiveProvider()
        return _ai_provider_instance
    else:
        if not isinstance(_ai_provider_instance, MockAIProvider):
            logger.info("[AIProviderFactory] Initializing MockAIProvider (Zero-Key Simulation Mode)")
            _ai_provider_instance = MockAIProvider()
        return _ai_provider_instance
