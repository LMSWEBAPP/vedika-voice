from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.lead import LeadResponse

CallStatus = Literal[
    "QUEUED",
    "INITIATING",
    "RINGING",
    "CONNECTED",
    "AI_GREETING",
    "IN_PROGRESS",
    "PAUSED",
    "COMPLETED",
    "FAILED",
    "NO_ANSWER",
    "BUSY",
    "CANCELLED"
]


class CallInitiateRequest(BaseModel):
    campaign_id: str
    lead_id: str


class CallTranscriptResponse(BaseModel):
    id: str
    speaker: str  # 'ai', 'user', 'system'
    text: str
    timestamp: datetime
    language: str
    confidence: Optional[float] = 1.0
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CallAnswerResponse(BaseModel):
    id: str
    question_id: str
    question_text: str
    raw_answer: str
    extracted_value: Optional[Any] = None
    is_valid: bool
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class CallEventResponse(BaseModel):
    id: str
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallResponse(BaseModel):
    id: str
    campaign_id: str
    lead_id: str
    provider: str
    provider_call_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: int
    language: str
    termination_reason: Optional[str] = None
    recording_url: Optional[str] = None
    created_at: datetime
    lead: Optional[LeadResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CallDetailResponse(CallResponse):
    transcripts: List[CallTranscriptResponse] = []
    answers: List[CallAnswerResponse] = []
    events: List[CallEventResponse] = []
