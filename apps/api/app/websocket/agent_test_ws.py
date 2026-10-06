import asyncio
import base64
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.providers.ai.factory import get_ai_provider
from app.services.tts_service import tts_service
from app.repositories.campaign_repo import CampaignRepository

from typing import Optional

router = APIRouter()


@router.websocket("/ws/agent/test/{campaign_id}")
async def agent_browser_test_ws(
    websocket: WebSocket,
    campaign_id: str,
    contact_name: Optional[str] = None,
    company_name: Optional[str] = None,
    domain: Optional[str] = None,
    notes: Optional[str] = None,
):
    """
    WebSocket endpoint for testing the AI Voice Agent directly in the browser.
    Enables users to speak via browser microphone or type text, receiving real-time AI voice and text.
    Accepts simulated business profile parameters for dynamic live scenario testing.
    """
    await websocket.accept()
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"[AgentTestWS] Connected browser test session {session_id} for campaign {campaign_id} "
        f"(Business: {company_name or 'Default'}, Domain: {domain or 'Default'})"
    )

    # Fetch script configuration
    async with AsyncSessionLocal() as db_session:
        campaign_repo = CampaignRepository(db_session)
        campaign = await campaign_repo.get_with_script(campaign_id)
        if campaign and campaign.script:
            config = {
                "persona": campaign.script.persona,
                "objective": campaign.script.objective,
                "opening": campaign.script.opening,
                "questions": campaign.script.questions,
                "closing": campaign.script.closing,
                "voice_name": campaign.script.voice_name,
                "language": campaign.primary_language,
            }
        else:
            config = {
                "persona": "Madhu — a courteous, warm, articulate, and gentle Indian female software consultant representing our freelance software development collective.",
                "objective": "Understand business bottlenecks, highlight custom software solutions, handle objections gracefully, and book a 15-minute tailored demo.",
                "opening": "Hello! Good day! This is Madhu calling from our custom software development team. Do you have just a quick minute?",
                "questions": [
                    {"id": "q1_domain", "text": "What domain or industry does your business primarily operate in?", "type": "text"},
                    {"id": "q2_bottleneck", "text": "What is the biggest manual task or software challenge your team faces today?", "type": "text"},
                    {"id": "q3_interest", "text": "Would you be open to a 15-minute demo showing how custom software or automation can save you hours every week?", "type": "boolean"},
                ],
                "closing": "Thank you so much for your time! We look forward to connecting and showing you how custom software can make your operations more profitable. Have a wonderful day!",
                "voice_name": "Kore",
                "language": "en",
            }

    # Inject business profile parameters if provided
    config["business_profile"] = {
        "contact_name": contact_name,
        "company_name": company_name,
        "domain": domain,
        "notes": notes,
    }

    if contact_name or company_name:
        lead_salutation = f"{contact_name} ji" if contact_name else "Sir/Ma'am"
        company_str = f" at {company_name}" if company_name else ""
        config["opening"] = (
            f"Hello {lead_salutation}, good day! This is Madhu calling from our custom software development team{company_str}. Do you have just a quick minute?"
        )

    ai_provider = get_ai_provider()
    await ai_provider.start_session(session_id, config)

    # Background task to push AI events back to browser WebSocket
    async def push_ai_events():
        try:
            async for event in ai_provider.receive_events(session_id):
                if event.event_type == "TEXT_DELTA":
                    await websocket.send_text(
                        json.dumps({"type": "ai_text", "text": event.data})
                    )
                elif event.event_type == "AUDIO_DELTA" and event.audio:
                    b64_audio = base64.b64encode(event.audio).decode("utf-8")
                    await websocket.send_text(
                        json.dumps({"type": "ai_audio", "data": b64_audio, "mime": "audio/mp3"})
                    )
                elif event.event_type == "TURN_COMPLETE":
                    turn_data = event.data or {}
                    speaker = turn_data.get("speaker", "ai")
                    ai_text = turn_data.get("text", "")
                    
                    audio_b64 = ""
                    if speaker == "ai" and ai_text:
                        voice_name = config.get("voice_name") or "Madhu"
                        try:
                            audio_b64 = await tts_service.synthesize_to_base64(
                                text=ai_text,
                                voice_name=voice_name,
                            )
                        except Exception as tts_err:
                            logger.warning(f"[AgentTestWS] TTS synthesis error: {tts_err}")

                    if audio_b64:
                        await websocket.send_text(
                            json.dumps({
                                "type": "ai_audio",
                                "data": audio_b64,
                                "mime": "audio/mp3",
                                "text": ai_text
                            })
                        )

                    await websocket.send_text(
                        json.dumps({
                            "type": "turn_complete",
                            "data": {
                                "speaker": speaker,
                                "text": ai_text,
                                "audio": audio_b64
                            }
                        })
                    )
                elif event.event_type == "END_SESSION":
                    await websocket.send_text(json.dumps({"type": "session_ended"}))
                    break
        except Exception as exc:
            logger.error(f"[AgentTestWS] Error pushing events: {exc}")

    push_task = asyncio.create_task(push_ai_events())

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "text":
                user_text = msg.get("text", "")
                await websocket.send_text(json.dumps({"type": "user_text", "text": user_text}))
                await ai_provider.send_text(session_id, user_text)

            elif msg_type == "audio":
                audio_b64 = msg.get("data", "")
                if audio_b64:
                    raw_audio = base64.b64decode(audio_b64)
                    await ai_provider.send_audio(session_id, raw_audio)

            elif msg_type == "end":
                break

    except WebSocketDisconnect:
        logger.info(f"[AgentTestWS] Browser test socket disconnected for {session_id}")
    finally:
        push_task.cancel()
        await ai_provider.end_session(session_id)
