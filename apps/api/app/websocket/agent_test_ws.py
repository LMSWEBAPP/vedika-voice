import asyncio
import base64
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.providers.ai.factory import get_ai_provider
from app.repositories.campaign_repo import CampaignRepository

router = APIRouter()


@router.websocket("/ws/agent/test/{campaign_id}")
async def agent_browser_test_ws(websocket: WebSocket, campaign_id: str):
    """
    WebSocket endpoint for testing the AI Voice Agent directly in the browser.
    Enables users to speak via browser microphone or type text, receiving real-time AI voice and text.
    """
    await websocket.accept()
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    logger.info(f"[AgentTestWS] Connected browser test session {session_id} for campaign {campaign_id}")

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
                "persona": "Friendly and professional voice assistant.",
                "objective": "Lead qualification",
                "opening": "Hello! Thank you for testing Veyra Voice.",
                "questions": [
                    {"id": "q1", "text": "Are you interested in exploring our AI calling platform?", "type": "boolean"},
                    {"id": "q2", "text": "How many team members do you currently have?", "type": "number"}
                ],
                "closing": "Thank you for trying out our test session!",
                "voice_name": "Aoede",
                "language": "en",
            }

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
                        json.dumps({"type": "ai_audio", "data": b64_audio})
                    )
                elif event.event_type == "TURN_COMPLETE":
                    await websocket.send_text(
                        json.dumps({"type": "turn_complete", "data": event.data})
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
