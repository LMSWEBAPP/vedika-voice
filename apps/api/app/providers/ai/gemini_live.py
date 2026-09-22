import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import websockets
from app.core.config import settings
from app.core.logging import logger
from app.providers.ai.interface import AIEvent, AIProvider


class GeminiLiveProvider(AIProvider):
    """
    Production AI Provider integrating with Google Gemini Live API.
    Uses WebSocket bidirectional audio/text streaming.
    """

    GEMINI_LIVE_WS_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._sockets: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._listen_tasks: Dict[str, asyncio.Task] = {}

    async def start_session(self, session_id: str, config: Dict[str, Any]) -> None:
        if not self.api_key:
            logger.warning("[GeminiLiveProvider] GEMINI_API_KEY is not configured.")
            raise ValueError("GEMINI_API_KEY must be set to use GeminiLiveProvider.")

        url = f"{self.GEMINI_LIVE_WS_URL}?key={self.api_key}"
        logger.info(f"[GeminiLiveProvider] Connecting to Gemini Live for session {session_id}")

        ws = await websockets.connect(url)
        self._sockets[session_id] = ws
        queue = asyncio.Queue()
        self._queues[session_id] = queue

        # Build system instruction from config
        persona = config.get("persona", "You are a professional voice calling agent.")
        objective = config.get("objective", "")
        opening = config.get("opening", "")
        questions_summary = json.dumps(config.get("questions", []), indent=2)

        system_prompt = (
            f"{persona}\n"
            f"Campaign Objective: {objective}\n"
            f"Required Questions to gather: {questions_summary}\n"
            f"Greeting: Start by saying '{opening}'\n"
            "Guidelines: Speak concisely, naturally, and conversationally over the phone. "
            "Do not output markdown or large lists. Ask one question at a time."
        )

        # Initial handshake setup message
        setup_msg = {
            "setup": {
                "model": f"models/{settings.GEMINI_MODEL}",
                "generation_config": {
                    "response_modalities": ["AUDIO", "TEXT"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": config.get("voice_name", settings.GEMINI_VOICE_NAME)
                            }
                        }
                    }
                },
                "system_instruction": {
                    "parts": [{"text": system_prompt}]
                }
            }
        }
        await ws.send(json.dumps(setup_msg))

        # Start receiving background listener task
        task = asyncio.create_task(self._listen_loop(session_id, ws, queue))
        self._listen_tasks[session_id] = task

    async def _listen_loop(
        self, session_id: str, ws: websockets.WebSocketClientProtocol, queue: asyncio.Queue
    ) -> None:
        try:
            async for raw_message in ws:
                data = json.loads(raw_message)

                server_content = data.get("serverContent")
                if server_content:
                    model_turn = server_content.get("modelTurn")
                    if model_turn:
                        for part in model_turn.get("parts", []):
                            # Text delta
                            if "text" in part:
                                await queue.put(AIEvent(event_type="TEXT_DELTA", data=part["text"]))
                            # Audio delta (base64 encoded PCM)
                            if "inlineData" in part:
                                import base64
                                audio_bytes = base64.b64decode(part["inlineData"].get("data", ""))
                                await queue.put(AIEvent(event_type="AUDIO_DELTA", audio=audio_bytes))

                    if server_content.get("turnComplete"):
                        await queue.put(AIEvent(event_type="TURN_COMPLETE"))

                    if server_content.get("interrupted"):
                        await queue.put(AIEvent(event_type="INTERRUPTED"))

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error(f"[GeminiLiveProvider] Error in listen loop for {session_id}: {exc}")
            await queue.put(AIEvent(event_type="ERROR", data=str(exc)))

    async def send_audio(self, session_id: str, audio_bytes: bytes) -> None:
        ws = self._sockets.get(session_id)
        if not ws:
            return

        import base64
        msg = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "mime_type": "audio/pcm;rate=16000",
                        "data": base64.b64encode(audio_bytes).decode("utf-8")
                    }
                ]
            }
        }
        await ws.send(json.dumps(msg))

    async def send_text(self, session_id: str, text: str) -> None:
        ws = self._sockets.get(session_id)
        if not ws:
            return

        msg = {
            "client_content": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [{"text": text}]
                    }
                ],
                "turn_complete": True
            }
        }
        await ws.send(json.dumps(msg))

    async def receive_events(self, session_id: str) -> AsyncGenerator[AIEvent, None]:
        queue = self._queues.get(session_id)
        if not queue:
            return

        while True:
            try:
                event = await queue.get()
                yield event
                queue.task_done()
                if event.event_type == "END_SESSION":
                    break
            except asyncio.CancelledError:
                break

    async def end_session(self, session_id: str) -> None:
        task = self._listen_tasks.pop(session_id, None)
        if task:
            task.cancel()
        ws = self._sockets.pop(session_id, None)
        if ws:
            try:
                await ws.close()
            except Exception:
                pass
        queue = self._queues.pop(session_id, None)
        if queue:
            await queue.put(AIEvent(event_type="END_SESSION"))
        logger.info(f"[GeminiLiveProvider] Ended session {session_id}")

    async def extract_structured_data(
        self,
        transcript: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calls Gemini REST endpoint with strict JSON schema to extract questions.
        """
        import httpx

        prompt = (
            "Extract structured answers for the following questions from the conversation transcript.\n"
            "Rules:\n"
            "1. ONLY extract information clearly confirmed by the user.\n"
            "2. DO NOT invent or assume missing data.\n"
            "3. If a question was not answered, set its value to null.\n\n"
            f"Questions: {json.dumps(questions, indent=2)}\n\n"
            f"Transcript: {json.dumps(transcript, indent=2)}\n\n"
            "Return a valid JSON object mapping each question's id to its extracted value."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
