from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional


class AIEvent:
    def __init__(self, event_type: str, data: Any = None, audio: Optional[bytes] = None):
        self.event_type = event_type  # 'TEXT_DELTA', 'AUDIO_DELTA', 'TURN_COMPLETE', 'INTERRUPTED', 'ERROR'
        self.data = data
        self.audio = audio


class AIProvider(ABC):
    """
    Abstract AI Provider interface.
    Decouples business logic and telephony from specific LLM / Speech providers.
    """

    @abstractmethod
    async def start_session(self, session_id: str, config: Dict[str, Any]) -> None:
        """Initialize a persistent real-time streaming AI voice session."""
        pass

    @abstractmethod
    async def send_audio(self, session_id: str, audio_bytes: bytes) -> None:
        """Stream raw user audio into the AI session."""
        pass

    @abstractmethod
    async def send_text(self, session_id: str, text: str) -> None:
        """Inject text or context updates into the AI session."""
        pass

    @abstractmethod
    async def receive_events(self, session_id: str) -> AsyncGenerator[AIEvent, None]:
        """Stream AI events (audio response chunks, text deltas, interruptions)."""
        pass

    @abstractmethod
    async def end_session(self, session_id: str) -> None:
        """Gracefully terminate the AI session and free allocated resources."""
        pass

    @abstractmethod
    async def extract_structured_data(
        self,
        transcript: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract structured answers from conversation turns without hallucination."""
        pass
