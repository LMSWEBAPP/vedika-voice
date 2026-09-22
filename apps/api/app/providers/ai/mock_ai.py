import asyncio
import re
from typing import Any, AsyncGenerator, Dict, List, Optional
from app.core.logging import logger
from app.providers.ai.interface import AIEvent, AIProvider


class MockAIProvider(AIProvider):
    """
    Development and offline AI provider.
    Simulates real-time interactive voice agent conversations,
    audio streaming, turn-taking, and structured information extraction.
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._event_queues: Dict[str, asyncio.Queue] = {}

    async def start_session(self, session_id: str, config: Dict[str, Any]) -> None:
        queue = asyncio.Queue()
        self._sessions[session_id] = {
            "config": config,
            "history": [],
            "current_question_idx": 0,
            "active": True,
        }
        self._event_queues[session_id] = queue

        opening = config.get("opening", "Hello, thank you for taking my call!")
        logger.info(f"[MockAIProvider] Started session {session_id} with opening: '{opening}'")

        # Emit opening greeting immediately
        await self._emit_ai_turn(session_id, opening)

    async def _emit_ai_turn(self, session_id: str, text: str) -> None:
        queue = self._event_queues.get(session_id)
        session = self._sessions.get(session_id)
        if not queue or not session:
            return

        session["history"].append({"speaker": "ai", "text": text})

        # Emit text delta
        await queue.put(AIEvent(event_type="TEXT_DELTA", data=text))

        # Generate simulated PCM 16-bit 16kHz audio frames (silence/comfort chime)
        # 320 bytes = 10ms of 16kHz 16-bit mono PCM
        simulated_audio_chunk = b"\x00\x04" * 160
        for _ in range(3):
            await queue.put(AIEvent(event_type="AUDIO_DELTA", audio=simulated_audio_chunk))
            await asyncio.sleep(0.05)

        await queue.put(AIEvent(event_type="TURN_COMPLETE", data={"speaker": "ai", "text": text}))

    async def send_audio(self, session_id: str, audio_bytes: bytes) -> None:
        """
        Receives simulated phone/browser audio.
        Simulates user speech transcription after sufficient audio packets.
        """
        session = self._sessions.get(session_id)
        if not session or not session.get("active"):
            return

        # Increment packet count and trigger simulated speech after packet threshold
        packet_count = session.get("packet_count", 0) + 1
        session["packet_count"] = packet_count

        if packet_count == 10:
            # Simulate user answering the current question
            q_idx = session.get("current_question_idx", 0)
            questions = session.get("config", {}).get("questions", [])
            user_response = "Yes, that sounds interesting! We have about 50 people in our team."
            if q_idx < len(questions):
                q = questions[q_idx]
                if q.get("type") == "boolean":
                    user_response = "Yes, absolutely."
                elif q.get("type") == "number":
                    user_response = "Around 25."
                elif q.get("type") == "email":
                    user_response = "rahul@example.com"
            await self.send_text(session_id, user_response)

    async def send_text(self, session_id: str, text: str) -> None:
        session = self._sessions.get(session_id)
        queue = self._event_queues.get(session_id)
        if not session or not queue or not session.get("active"):
            return

        logger.info(f"[MockAIProvider] User input received for {session_id}: '{text}'")
        session["history"].append({"speaker": "user", "text": text})

        # Determine next AI response based on script questions
        questions = session.get("config", {}).get("questions", [])
        q_idx = session.get("current_question_idx", 0)

        if q_idx < len(questions):
            next_q = questions[q_idx]
            session["current_question_idx"] = q_idx + 1
            ai_text = f"Got it, thank you. {next_q.get('text')}"
        else:
            closing = session.get("config", {}).get(
                "closing", "Thank you very much for your time. Have a wonderful day!"
            )
            ai_text = closing

        await self._emit_ai_turn(session_id, ai_text)

    async def receive_events(self, session_id: str) -> AsyncGenerator[AIEvent, None]:
        queue = self._event_queues.get(session_id)
        if not queue:
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event
                queue.task_done()
                if event.event_type == "END_SESSION":
                    break
            except asyncio.TimeoutError:
                break
            except asyncio.CancelledError:
                break

    async def end_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["active"] = False
        queue = self._event_queues.get(session_id)
        if queue:
            await queue.put(AIEvent(event_type="END_SESSION"))
        self._sessions.pop(session_id, None)
        self._event_queues.pop(session_id, None)
        logger.info(f"[MockAIProvider] Ended session {session_id}")

    async def extract_structured_data(
        self,
        transcript: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Deterministic rule-based extractor for mock testing without LLM costs.
        Extracts structured values from user transcript turns.
        """
        extracted = {}
        user_turns = [t.get("text", "") for t in transcript if t.get("speaker") == "user"]
        full_user_text = " ".join(user_turns).lower()

        for q in questions:
            q_id = q.get("id")
            q_type = q.get("type", "text")

            if q_type == "boolean":
                if any(w in full_user_text for w in ["yes", "yeah", "sure", "interested", "absolutely", "definitely"]):
                    extracted[q_id] = True
                elif any(w in full_user_text for w in ["no", "not interested", "nope", "never"]):
                    extracted[q_id] = False
                else:
                    extracted[q_id] = True  # Mock optimistic fallback

            elif q_type == "number":
                numbers = re.findall(r"\b\d+\b", full_user_text)
                extracted[q_id] = int(numbers[0]) if numbers else 50

            elif q_type == "email":
                emails = re.findall(r"[\w\.-]+@[\w\.-]+", full_user_text)
                extracted[q_id] = emails[0] if emails else "contact@example.com"

            elif q_type == "rating":
                numbers = re.findall(r"\b([1-9]|10)\b", full_user_text)
                extracted[q_id] = int(numbers[0]) if numbers else 8

            else:
                extracted[q_id] = user_turns[-1] if user_turns else "Confirmed"

        return extracted
