from typing import Any, Dict, List
from fastapi import APIRouter
from app.schemas.script import ScriptCreate

router = APIRouter(prefix="/agents", tags=["Agents"])

AVAILABLE_VOICES = [
    {"name": "Aoede", "gender": "Female", "style": "Warm, engaging, natural", "provider": "gemini"},
    {"name": "Puck", "gender": "Male", "style": "Energetic, upbeat, clear", "provider": "gemini"},
    {"name": "Charon", "gender": "Male", "style": "Calm, authoritative, steady", "provider": "gemini"},
    {"name": "Fenrir", "gender": "Male", "style": "Deep, resonating, polished", "provider": "gemini"},
    {"name": "Kore", "gender": "Female", "style": "Gentle, polite, professional", "provider": "gemini"},
]

QUESTION_TYPES = [
    {"type": "text", "label": "Free Text", "description": "General open-ended responses"},
    {"type": "boolean", "label": "Yes / No", "description": "Boolean affirmation or rejection"},
    {"type": "number", "label": "Number", "description": "Numerical quantity or headcount"},
    {"type": "single_choice", "label": "Single Choice", "description": "Choose one of predefined options"},
    {"type": "multiple_choice", "label": "Multiple Choice", "description": "Choose multiple options"},
    {"type": "date", "label": "Date", "description": "Calendar date for scheduling"},
    {"type": "time", "label": "Time", "description": "Time of day for callbacks"},
    {"type": "phone", "label": "Phone Number", "description": "Contact telephone number"},
    {"type": "email", "label": "Email Address", "description": "Validated email address"},
    {"type": "rating", "label": "Rating (1-10)", "description": "Numerical scale from 1 to 10"},
]


@router.get("/voices")
async def list_available_voices():
    return AVAILABLE_VOICES


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
