from typing import Any, Dict, Optional
from pydantic import BaseModel


class ExotelCallStatusPayload(BaseModel):
    CallSid: Optional[str] = None
    Status: Optional[str] = None
    CallFrom: Optional[str] = None
    CallTo: Optional[str] = None
    Direction: Optional[str] = None
    CreatedTime: Optional[str] = None
    StartTime: Optional[str] = None
    EndTime: Optional[str] = None
    Duration: Optional[int] = 0
    RecordingUrl: Optional[str] = None
    CustomField: Optional[str] = None


class TelephonyWebhookResponse(BaseModel):
    success: bool
    status: str
    message: Optional[str] = None
    event_handled: Optional[str] = None
