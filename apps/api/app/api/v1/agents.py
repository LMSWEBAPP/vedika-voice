from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.schemas.script import ScriptCreate
from app.services.tts_service import tts_service

router = APIRouter(prefix="/agents", tags=["Agents"])

AVAILABLE_VOICES = [
    {
        "name": "Zephyr",
        "gender": "Female / Natural",
        "style": "Ultra-expressive, warm, natural human tone with familiar Indian cadence (Gemini Live native)",
        "neural_voice": "Zephyr",
        "provider": "gemini-live",
    },
    {
        "name": "Madhu",
        "gender": "Female",
        "style": "Warm, expressive, natural Indian English & Hindi",
        "neural_voice": "en-IN-NeerjaExpressiveNeural",
        "provider": "neural",
    },
    {
        "name": "Aoede",
        "gender": "Female",
        "style": "Articulate, gentle, professional Indian English",
        "neural_voice": "en-IN-NeerjaNeural",
        "provider": "neural",
    },
    {
        "name": "Kore",
        "gender": "Female",
        "style": "Courteous, calm, consultative Indian English",
        "neural_voice": "en-IN-NeerjaNeural",
        "provider": "neural",
    },
    {
        "name": "Rohan",
        "gender": "Male",
        "style": "Confident, clear, professional Indian English",
        "neural_voice": "en-IN-PrabhatNeural",
        "provider": "neural",
    },
    {
        "name": "Puck",
        "gender": "Male",
        "style": "Energetic, dynamic, friendly Indian English",
        "neural_voice": "en-IN-PrabhatNeural",
        "provider": "neural",
    },
    {
        "name": "Swara",
        "gender": "Female",
        "style": "Native, warm, conversational Hindi",
        "neural_voice": "hi-IN-SwaraNeural",
        "provider": "neural",
    },
    {
        "name": "Madhur",
        "gender": "Male",
        "style": "Respectful, gentle, natural Hindi",
        "neural_voice": "hi-IN-MadhurNeural",
        "provider": "neural",
    },
    {
        "name": "Jenny",
        "gender": "Female",
        "style": "Natural, upbeat, conversational US English",
        "neural_voice": "en-US-JennyNeural",
        "provider": "neural",
    },
    {
        "name": "Guy",
        "gender": "Male",
        "style": "Casual, authentic, clear US English",
        "neural_voice": "en-US-GuyNeural",
        "provider": "neural",
    },
]


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize into natural human speech")
    voice_name: Optional[str] = Field(default="Madhu", description="Voice profile identifier")
    rate: Optional[str] = Field(default="+0%", description="Speech rate adjustment (e.g. +0%, -5%)")
    pitch: Optional[str] = Field(default="+0Hz", description="Speech pitch adjustment")


@router.get("/voices")
async def list_available_voices():
    return AVAILABLE_VOICES


@router.post("/synthesize-speech")
async def synthesize_speech(req: SpeechSynthesisRequest):
    """
    Synthesize natural, ultra-realistic human neural speech from text.
    Returns Base64 encoded MP3 audio with zero metallic artifacts.
    """
    try:
        resolved_voice = tts_service.resolve_voice(req.voice_name, req.text)
        audio_b64 = await tts_service.synthesize_to_base64(
            text=req.text,
            voice_name=req.voice_name,
            rate=req.rate or "+0%",
            pitch=req.pitch or "+0Hz",
        )
        if not audio_b64:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Voice synthesis returned empty audio data.",
            )
        return {
            "status": "success",
            "audio_base64": audio_b64,
            "format": "audio/mp3",
            "voice": resolved_voice,
            "text": req.text,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synthesize neural speech: {str(exc)}",
        )



QUESTION_TYPES = [
    {"type": "text", "label": "Freeform Text", "description": "Captures unstructured conversational answers"},
    {"type": "number", "label": "Numeric", "description": "Captures numerical quantities, headcounts, or amounts"},
    {"type": "boolean", "label": "Yes / No (Boolean)", "description": "Captures binary agreement, interest, or qualification"},
    {"type": "single_choice", "label": "Single Choice", "description": "Selects one option from a predefined list of choices"},
    {"type": "multiple_choice", "label": "Multiple Choice", "description": "Selects multiple applicable options from a list"},
    {"type": "date", "label": "Calendar Date", "description": "Extracts scheduled calendar dates"},
    {"type": "time", "label": "Time / Slot", "description": "Extracts preferred time windows or demo slots"},
    {"type": "phone", "label": "Phone Number", "description": "Extracts E.164 phone numbers"},
    {"type": "email", "label": "Email Address", "description": "Extracts validated email addresses"},
    {"type": "rating", "label": "Rating (1-5 or 1-10)", "description": "Captures numerical score or satisfaction rating"},
]


@router.get("/question-types")
async def list_question_types():
    return QUESTION_TYPES


@router.post("/validate-script")
async def validate_script_configuration(script: ScriptCreate):
    errors = []
    q_ids = set()

    for idx, q in enumerate(script.questions):
        if q.id in q_ids:
            errors.append(f"Question ID '{q.id}' at index {idx} is duplicated.")
        q_ids.add(q.id)

        if q.condition:
            dep_id = q.condition.depends_on_question_id
            if dep_id not in q_ids and dep_id != q.id:
                # Dependency should ideally come before this question
                pass

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "total_questions": len(script.questions),
    }
