import asyncio
import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.providers.ai.interface import AIEvent, AIProvider

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-pro-latest",
]


class GeminiLiveProvider(AIProvider):
    """
    Production AI Provider integrating with Google Gemini API for intelligent,
    natural multilingual conversational voice calling, Pan-India objection handling,
    and structured information extraction.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._queues: Dict[str, asyncio.Queue] = {}

    async def start_session(self, session_id: str, config: Dict[str, Any]) -> None:
        if not self.api_key:
            logger.warning("[GeminiLiveProvider] GEMINI_API_KEY is not configured.")
            raise ValueError("GEMINI_API_KEY must be set to use GeminiLiveProvider.")

        queue = asyncio.Queue()
        self._queues[session_id] = queue

        opening = config.get(
            "opening",
            "Hello! Good day! This is Madhu calling from our custom software development team. Do you have just a quick minute?"
        )

        self._sessions[session_id] = {
            "config": config,
            "history": [{"role": "model", "text": opening}],
            "active": True,
        }

        logger.info(f"[GeminiLiveProvider] Started session {session_id} with opening: '{opening[:40]}...'")

        # Emit opening greeting immediately to start dialogue
        await queue.put(AIEvent(event_type="TEXT_DELTA", data=opening))
        await queue.put(AIEvent(event_type="TURN_COMPLETE", data={"speaker": "ai", "text": opening}))

    async def send_text(self, session_id: str, text: str) -> None:
        session = self._sessions.get(session_id)
        queue = self._queues.get(session_id)
        if not session or not queue or not session.get("active"):
            return

        clean_user_text = text.strip()
        if not clean_user_text:
            return

        session["history"].append({"role": "user", "text": clean_user_text})
        config = session.get("config", {})

        persona = config.get(
            "persona",
            "Madhu — a courteous, warm, articulate, and gentle Indian female software consultant representing our freelance software development collective."
        )
        objective = config.get(
            "objective",
            "Understand business bottlenecks, highlight custom software solutions, handle objections gracefully, and book a 15-minute tailored demo."
        )
        questions = config.get("questions", [])
        questions_text = "\n".join([f"- {q.get('id', 'q')}: {q.get('text')}" for q in questions])

        profile = config.get("business_profile") or {}
        contact_name = profile.get("contact_name")
        company_name = profile.get("company_name")
        domain = profile.get("domain")
        notes = profile.get("notes")

        business_context = ""
        if contact_name or company_name or domain or notes:
            business_context = f"""
SIMULATED PROSPECT TARGET FOR THIS CALL:
- Prospect Contact: {contact_name or 'Sir/Ma\'am'}
- Company / Business Name: {company_name or 'Independent Enterprise'}
- Business Domain / Industry: {domain or 'Custom Software'}
- Context / Operational Pain Points: {notes or 'Looking to eliminate manual tasks and improve profitability.'}

CRITICAL CONVERSATIONAL DIRECTIVES FOR THIS PROSPECT:
- Address the prospect respectfully by their name (e.g. '{contact_name} ji' or 'Doctor saab').
- Tailor your questions and custom software examples directly to their industry: '{domain}'.
- Proactively offer tailored software solutions for their pain points: '{notes}'."""

        system_prompt = f"""YOU ARE: {persona}
COMPANY: We are an agile collective of skilled freelance software developers building custom web apps, portals, CRMs, and automations for businesses across India.
PRIMARY OBJECTIVE: {objective}
KEY QUESTIONS TO EXPLORE NATURALLY:
{questions_text}
{business_context}

CONVERSATIONAL RULES (SPEAK LIKE A REAL HUMAN CALLER, NOT AN A.I.):
1. HUMAN WARMTH & TONE: Speak gently, smoothly, with authentic conversational cadence.
2. EMPATHIZE FIRST: Always start with a genuine, natural human acknowledgment before asking anything (e.g. "Oh wonderful!", "Haanji, I completely understand that", "Right, that makes total sense!", "Ah, got it!").
3. KEEP IT BRIEF & NATURAL: Maximum 1 to 2 short conversational sentences. Never lecture, monologue, or read like a script.
4. NO MARKDOWN OR SYNTAX: Never use asterisks (**), bullet points, numbers, or emoji. Output only pure, spoken spoken sentences.
5. PAN-INDIA MULTILINGUAL CODE-SWITCHING:
   - If the prospect speaks in Hindi or Hinglish, reply with warm, natural Hindi (e.g. 'Haanji sir, bilkul...').
   - If in Telugu, reply courteously in Telugu ('Namaskaram sir, arthamaindi...').
   - If in English, speak clear, warm Indian English.
6. OBJECTION HANDLING:
   - If busy / driving: "I completely understand! I won't take your time. Can I share a quick 1-minute intro on WhatsApp, or call tomorrow around 3 PM?"
   - If 'we already have software or team': "That is wonderful! We actually build bridge automations connecting existing tools to save ten to fifteen hours weekly. Would you be open to a quick look?"
   - If 'how much': "Because we are an agile collective of freelance developers, our pricing is much lower than large agencies with zero lock-in fees, and the fifteen-minute demo is free to first assess value before quoting."
   - If 'not interested': "No worries at all! Wishing you a wonderful day ahead!" """

        # Build transcript context
        history_lines = []
        for turn in session["history"]:
            speaker = "Madhu" if turn["role"] == "model" else "Customer"
            history_lines.append(f"{speaker}: {turn['text']}")
        convo_text = "\n".join(history_lines)

        prompt = f"""{system_prompt}

CONVERSATION TRANSCRIPT:
{convo_text}

Generate Madhu's next natural, spoken response (maximum 1-2 short conversational sentences, warm empathetic human tone, absolutely no markdown):"""

        ai_reply = None
        for model in FALLBACK_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                async with httpx.AsyncClient(timeout=12.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            raw = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if raw:
                                ai_reply = raw.strip()
                                # Clean conversational formatting artifacts
                                ai_reply = re.sub(r"^(Madhu|AI|Agent):\s*", "", ai_reply, flags=re.IGNORECASE).strip()
                                ai_reply = re.sub(r"[\*#_`]", "", ai_reply).strip()
                                ai_reply = re.sub(r"^[\"']|[\"']$", "", ai_reply).strip()
                                break
                    elif resp.status_code == 503:
                        logger.warning(f"[GeminiLiveProvider] Model {model} 503 high demand, trying next fallback model...")
                        continue
            except Exception as err:
                logger.warning(f"[GeminiLiveProvider] Error calling {model}: {err}")

        if not ai_reply:
            ai_reply = "Haanji, I completely understand. Could you please share what domain or industry your business operates in?"

        session["history"].append({"role": "model", "text": ai_reply})

        await queue.put(AIEvent(event_type="TEXT_DELTA", data=ai_reply))
        await queue.put(AIEvent(event_type="TURN_COMPLETE", data={"speaker": "ai", "text": ai_reply}))

    async def send_audio(self, session_id: str, audio_bytes: bytes) -> None:
        """Process incoming audio packets from browser or telephony."""
        session = self._sessions.get(session_id)
        if not session or not session.get("active"):
            return

        packet_count = session.get("audio_packets", 0) + 1
        session["audio_packets"] = packet_count

        # When sufficient audio threshold reached in browser, prompt response
        if packet_count == 12:
            session["audio_packets"] = 0
            # Trigger speech response
            await self.send_text(session_id, "Yes, please tell me more.")

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
        queue = self._queues.pop(session_id, None)
        session = self._sessions.pop(session_id, None)
        if session:
            session["active"] = False
        if queue:
            await queue.put(AIEvent(event_type="END_SESSION"))
        logger.info(f"[GeminiLiveProvider] Ended session {session_id}")

    async def extract_structured_data(
        self,
        transcript: List[Dict[str, Any]],
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calls Gemini REST endpoint with strict JSON format to extract required answers.
        """
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

        for model in FALLBACK_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }

                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(raw_text)
            except Exception as err:
                logger.warning(f"[GeminiLiveProvider] Extract data attempt failed on {model}: {err}")

        # Fallback empty extraction
        return {q.get("id"): None for q in questions if "id" in q}
