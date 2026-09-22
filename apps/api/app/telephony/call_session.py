import asyncio
from typing import Any, Callable, Dict, Optional
from app.core.logging import logger
from app.providers.ai.interface import AIProvider
from app.telephony.audio_pipeline import AudioPipeline


class ActiveCallBridge:
    """
    Manages the real-time bridge between a telephony WebSocket and an AIProvider session.
    """

    def __init__(
        self,
        call_id: str,
        ai_provider: AIProvider,
        config: Dict[str, Any],
        on_transcript_turn: Optional[Callable[[str, str], Any]] = None,
        on_call_completed: Optional[Callable[[], Any]] = None,
    ):
        self.call_id = call_id
        self.ai_provider = ai_provider
        self.config = config
        self.audio_pipeline = AudioPipeline()
        self.on_transcript_turn = on_transcript_turn
        self.on_call_completed = on_call_completed
        self.is_active = False
        self._receive_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self.is_active = True
        await self.ai_provider.start_session(self.call_id, self.config)
        logger.info(f"[ActiveCallBridge] Started bridge for call {self.call_id}")

    async def handle_incoming_phone_audio(self, raw_audio: bytes) -> None:
        if not self.is_active:
            return
        pcm_16k = self.audio_pipeline.receive_from_phone(raw_audio)
        await self.ai_provider.send_audio(self.call_id, pcm_16k)

    async def handle_user_text(self, text: str) -> None:
        if not self.is_active:
            return
        if self.on_transcript_turn:
            await self.on_transcript_turn("user", text)
        await self.ai_provider.send_text(self.call_id, text)

    async def close(self) -> None:
        self.is_active = False
        if self._receive_task:
            self._receive_task.cancel()
        await self.ai_provider.end_session(self.call_id)
        if self.on_call_completed:
            await self.on_call_completed()
        logger.info(f"[ActiveCallBridge] Closed bridge for call {self.call_id}")
