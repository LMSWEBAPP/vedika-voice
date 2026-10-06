import html
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.providers.telephony.factory import get_telephony_provider
from app.repositories.call_repo import CallRepository
from app.schemas.webhook import TelephonyWebhookResponse
from app.services.call_service import CallService

router = APIRouter(prefix="/webhooks/telephony", tags=["Telephony Webhooks"])

# Active in-memory conversation history and prospect profiles for live carrier calls
TWILIO_CALL_HISTORY: Dict[str, List[Dict[str, str]]] = {}
TWILIO_CALL_PROFILES: Dict[str, Dict[str, str]] = {}

# Ultra-realistic Indian English neural voice (Google Neural2 / Polly Neural)
NEURAL_VOICE = "Google.en-IN-Neural2-A"
NEURAL_LANGUAGE = "en-IN"

GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-pro-latest",
]


async def generate_consultative_response(
    call_sid: str,
    user_speech: str,
    name: Optional[str] = None,
    company: Optional[str] = None,
    pitch_goal: Optional[str] = None,
) -> tuple[str, bool]:
    """
    Invokes Gemini to generate an ultra-fast, natural, 1-2 sentence human consultative phone reply.
    Employs the Veyra Voice B2B objection handling playbook with genuine empathy and conversational cadence.
    Returns (spoken_reply, is_hangup).
    """
    profile = TWILIO_CALL_PROFILES.get(call_sid, {})
    lead_name = name or profile.get("name") or "Sir"
    if lead_name == "Prospect":
        lead_name = "Sir"
    business = company or profile.get("company") or "your business"
    goal = pitch_goal or profile.get("pitch_goal") or "custom web applications, high-converting websites, and mobile apps"

    history = TWILIO_CALL_HISTORY.setdefault(call_sid, [])
    history.append({"role": "user", "text": user_speech})

    # Detect explicit quick hangup triggers from caller speech
    lower_speech = user_speech.lower()
    if any(phrase in lower_speech for phrase in ["wrong number", "not interested", "stop calling", "hang up", "don't call"]):
        farewell = "I completely understand! Thank you so much for your time, and have a wonderful day ahead!"
        history.append({"role": "model", "text": farewell})
        return farewell, True

    system_prompt = f"""You are Aarav from Veyra Software Solutions, an elite, highly consultative, warm, and natural tech growth consultant on a live outbound phone call.
PROSPECT DETAILS:
- Prospect Name: {lead_name}
- Company: {business}
- Focus / Goal: {goal}

ABOUT VEYRA SOFTWARE SOLUTIONS:
We are an agile collective building high-converting modern websites (Next.js, fast, SEO-ready), custom web applications (client portals, automated booking engines, dashboards), and cross-platform mobile apps (Flutter, React Native for iOS/Android).

CONVERSATIONAL VOICE & CADENCE RULES (SPEAK LIKE A REAL HUMAN, NOT A ROBOT):
1. STRICT BREVITY: Keep every spoken turn to ONLY 1 TO 2 SHORT SENTENCES (maximum 25 words total)! This is a real telephone conversation—never monologue, never lecture. Keep it reciprocal and human.
2. HUMAN WARMTH & CADENCE: Use natural conversational phrasing like "makes total sense", "absolutely", "got it ya", "super simple". Always acknowledge what the prospect said before responding (e.g., "Haanji {lead_name}!", "That is a great question!", "I completely understand!", "Understood!").
3. PRICING INQUIRIES: Give a clear, transparent ballpark: "Our custom websites typically range from fifteen to twenty-five thousand rupees, and mobile apps from forty thousand, depending on features. We can schedule a quick free fifteen-minute call to give you an exact estimate."
4. BUSY / DRIVING: "I completely understand! Can I drop our portfolio and recent app demos to your WhatsApp on this number?"
5. CODE-SWITCHING & MIRRORING:
   - If the prospect speaks in Hindi or Hinglish, respond warmly in fluent, natural Hindi ("Haanji sir, bilkul...").
   - If in Telugu, respond respectfully in Telugu ("Namaskaram sir, arthamaindi...").
   - If in English, speak polished, warm Indian English.
6. NO ROBOTIC SYNTAX: ABSOLUTELY NO asterisks (**), no markdown symbols, no bullet points, no emojis, and no prefixes like 'Aarav:' or 'Veyra AI:'. Only pure spoken conversational words.
7. CLOSING: ONLY end your reply with the token [HANGUP] if the prospect explicitly asks to end the call, says they are not interested, or after you have finalized a meeting and given a final parting farewell (e.g. 'Have a wonderful day ahead!'). NEVER output [HANGUP] if you are asking a question or waiting for their answer."""

    history_lines = []
    for turn in history[-6:]:
        speaker = "Aarav" if turn["role"] == "model" else "Prospect"
        history_lines.append(f"{speaker}: {turn['text']}")
    convo_context = "\n".join(history_lines)

    prompt = f"""{system_prompt}

CONVERSATION TRANSCRIPT:
{convo_context}

Prospect just said: "{user_speech}"
Generate Aarav's immediate natural human spoken reply (1-2 short sentences, pure spoken text):"""

    api_key = settings.GEMINI_API_KEY
    reply_text = None

    if api_key:
        for model in GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            raw = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if raw:
                                reply_text = raw.strip()
                                break
            except Exception as e:
                logger.warning(f"[TwilioTurn] Error calling Gemini model {model}: {e}")

    if not reply_text:
        reply_text = f"Haanji {lead_name}, we build custom websites and mobile apps to automate bookings and increase revenue for {business}. Would you like me to send a quick 2-minute demo to your WhatsApp?"

    # Clean formatting
    reply_text = re.sub(r"^(Aarav|Veyra(\s*AI)?|Assistant):\s*", "", reply_text, flags=re.IGNORECASE).strip()
    reply_text = re.sub(r"[\*#_`]", "", reply_text).strip()
    reply_text = re.sub(r"^[\"']|[\"']$", "", reply_text).strip()

    is_hangup = False
    if "[HANGUP]" in reply_text:
        reply_text = reply_text.replace("[HANGUP]", "").strip()
        if not reply_text.endswith("?"):
            is_hangup = True

    history.append({"role": "model", "text": reply_text})
    return reply_text, is_hangup


@router.api_route("/twilio/voice", methods=["GET", "POST"])
async def twilio_voice_twiml(
    request: Request,
    call_id: Optional[str] = None,
    name: Optional[str] = None,
    company: Optional[str] = None,
    pitch_goal: Optional[str] = None,
):
    """
    Initial TwiML endpoint for Twilio outbound carrier calls:
    Speaks a natural, warm, human greeting and immediately gathers live speech from the caller.
    """
    lead_name = name if name and name != "Prospect" else ""
    greeting = f"Hi {lead_name}!" if lead_name else "Hello!"
    business_mention = f" regarding {company}" if company and company not in ["Business", "your business"] else ""

    profile = {
        "name": lead_name or "Sir",
        "company": company or "your business",
        "pitch_goal": pitch_goal or "custom web applications and mobile apps",
    }
    if call_id:
        TWILIO_CALL_PROFILES[call_id] = profile

    # Build clean turn URL with html escaping
    base_turn = f"{settings.TELEPHONY_WEBHOOK_BASE_URL}{settings.API_V1_STR}/webhooks/telephony/twilio/turn"
    if call_id:
        base_turn = f"{base_turn}?call_id={call_id}"
    escaped_turn_url = html.escape(base_turn)

    opening_speech = (
        f"{greeting} This is Aarav from Veyra Software Solutions{business_mention}. "
        f"We build modern websites and mobile applications to help businesses like yours automate bookings and increase customer revenue. "
        f"Did I catch you at a good time for a quick two minutes?"
    )

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="{escaped_turn_url}" method="POST" speechTimeout="auto" timeout="4" language="{NEURAL_LANGUAGE}">
        <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">{opening_speech}</Say>
    </Gather>
    <Gather input="speech" action="{escaped_turn_url}" method="POST" speechTimeout="auto" timeout="5" language="{NEURAL_LANGUAGE}">
        <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">Are you still there? Just let me know if you would like me to send our portfolio on WhatsApp, or if now is a good time.</Say>
    </Gather>
    <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">No problem at all! Feel free to reach out to Veyra Software Solutions anytime. Have a wonderful day ahead!</Say>
    <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.api_route("/twilio/turn", methods=["GET", "POST"])
async def twilio_turn_twiml(
    request: Request,
    call_id: Optional[str] = None,
    name: Optional[str] = None,
    company: Optional[str] = None,
    pitch_goal: Optional[str] = None,
):
    """
    Conversational turn handler:
    Receives transcribed caller speech from Twilio Gather, generates Gemini response,
    and returns next Say + Gather turn or Hangup.
    """
    user_speech = ""
    call_sid = call_id or "direct"

    if request.method == "POST":
        try:
            form_data = await request.form()
            user_speech = str(form_data.get("SpeechResult") or "").strip()
            call_sid = str(form_data.get("CallSid") or call_sid)
            logger.info(f"[TwilioTurn] Received caller speech on SID {call_sid}: '{user_speech}'")
        except Exception as e:
            logger.warning(f"[TwilioTurn] Error reading form data: {e}")

    # Bind profile to call_sid
    if call_sid not in TWILIO_CALL_PROFILES:
        profile = {
            "name": name or "Sir",
            "company": company or "your business",
            "pitch_goal": pitch_goal or "custom web applications and mobile apps",
        }
        if call_id and call_id in TWILIO_CALL_PROFILES:
            profile = TWILIO_CALL_PROFILES[call_id]
        TWILIO_CALL_PROFILES[call_sid] = profile

    base_turn = f"{settings.TELEPHONY_WEBHOOK_BASE_URL}{settings.API_V1_STR}/webhooks/telephony/twilio/turn"
    if call_id:
        base_turn = f"{base_turn}?call_id={call_id}"
    escaped_turn_url = html.escape(base_turn)

    # If nothing was heard (caller stayed silent)
    if not user_speech:
        prompt_text = f"I am still here! Just let me know if you would like me to send our portfolio to your WhatsApp, or if you have a quick question about web and mobile apps for {company or 'your business'}."
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="{escaped_turn_url}" method="POST" speechTimeout="auto" timeout="4" language="{NEURAL_LANGUAGE}">
        <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">{prompt_text}</Say>
    </Gather>
    <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">Thank you for your time. Have a wonderful day ahead!</Say>
    <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Generate Gemini response
    reply_speech, is_hangup = await generate_consultative_response(
        call_sid=call_sid,
        user_speech=user_speech,
        name=name,
        company=company,
        pitch_goal=pitch_goal,
    )

    if is_hangup:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">{reply_speech}</Say>
    <Hangup/>
</Response>"""
    else:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="{escaped_turn_url}" method="POST" speechTimeout="auto" timeout="4" language="{NEURAL_LANGUAGE}">
        <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">{reply_speech}</Say>
    </Gather>
    <Gather input="speech" action="{escaped_turn_url}" method="POST" speechTimeout="auto" timeout="5" language="{NEURAL_LANGUAGE}">
        <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">Are you still there? Let me know if you would like me to send our portfolio on WhatsApp.</Say>
    </Gather>
    <Say voice="{NEURAL_VOICE}" language="{NEURAL_LANGUAGE}">Thank you for your time. Have a wonderful day ahead!</Say>
    <Hangup/>
</Response>"""

    return Response(content=twiml, media_type="application/xml")



@router.post("/call-status", response_model=TelephonyWebhookResponse)
async def telephony_call_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    headers = dict(request.headers)

    provider = get_telephony_provider()
    # Verify signature
    if not provider.verify_webhook_signature(body, headers):
        logger.warning("[Webhook] Signature verification failed for inbound telephony event.")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Try JSON or Form body
    try:
        payload = await request.json()
    except Exception:
        form_data = await request.form()
        payload = dict(form_data)

    event_data = await provider.handle_webhook(payload, headers)
    provider_call_id = event_data.get("provider_call_id")
    status = event_data.get("normalized_status", "IN_PROGRESS").upper()

    logger.info(f"[Webhook] Received call status update for {provider_call_id}: {status}")

    if provider_call_id:
        call_repo = CallRepository(db)
        call = await call_repo.get_by_provider_call_id(provider_call_id)
        if call:
            await call_repo.update_status(
                call_id=call.id,
                new_status=status,
                recording_url=event_data.get("recording_url"),
            )
            if status in ["COMPLETED", "FAILED", "BUSY", "NO_ANSWER"]:
                service = CallService(db)
                await service.complete_call(call.id, termination_reason=f"CARRIER_{status}")
        
        if status in ["COMPLETED", "FAILED", "BUSY", "NO_ANSWER", "CANCELLED"]:
            TWILIO_CALL_HISTORY.pop(provider_call_id, None)
            TWILIO_CALL_PROFILES.pop(provider_call_id, None)

    return TelephonyWebhookResponse(
        success=True,
        status="PROCESSED",
        message="Event processed idempotently.",
        event_handled=status,
    )
