import asyncio
import base64
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.database import AsyncSessionLocal
from app.core.logging import logger
from app.providers.ai.factory import get_ai_provider
from app.repositories.call_repo import CallRepository
from app.telephony.call_session import ActiveCallBridge

router = APIRouter()


@router.websocket("/ws/telephony/media/{call_id}")
async def telephony_media_ws(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for bidirectional telephony audio streaming.
    Receives carrier audio (μ-law), transcodes via AudioPipeline, and streams AI speech back.
    """
    await websocket.accept()
    logger.info(f"[TelephonyWS] WebSocket connected for call {call_id}")

    ai_provider = get_ai_provider()
    bridge = ActiveCallBridge(
        call_id=call_id,
        ai_provider=ai_provider,
        config={"opening": "Hello! Thank you for answering."},
    )

    await bridge.start()

    # Task to stream AI events back to telephony socket
    async def stream_ai_to_telephony():
        try:
            async for event in ai_provider.receive_events(call_id):
                if event.event_type == "AUDIO_DELTA" and event.audio:
                    phone_audio = bridge.audio_pipeline.encode_for_phone(event.audio)
                    b64_payload = base64.b64encode(phone_audio).decode("utf-8")
                    msg = {
                        "event": "media",
                        "media": {"payload": b64_payload}
                    }
                    await websocket.send_text(json.dumps(msg))
                elif event.event_type == "END_SESSION":
                    await websocket.send_text(json.dumps({"event": "stop"}))
                    break
        except Exception as exc:
            logger.error(f"[TelephonyWS] Error streaming AI to telephony for {call_id}: {exc}")

    outbound_task = asyncio.create_task(stream_ai_to_telephony())

    try:
        while True:
            raw_msg = await websocket.receive_text()
            data = json.loads(raw_msg)
            event_type = data.get("event")

            if event_type == "media":
                payload_b64 = data.get("media", {}).get("payload", "")
                if payload_b64:
                    raw_audio = base64.b64decode(payload_b64)
                    await bridge.handle_incoming_phone_audio(raw_audio)

            elif event_type == "stop":
                logger.info(f"[TelephonyWS] Received stop event for call {call_id}")
                break

    except WebSocketDisconnect:
        logger.info(f"[TelephonyWS] WebSocket disconnected for call {call_id}")
    finally:
        outbound_task.cancel()
        await bridge.close()
