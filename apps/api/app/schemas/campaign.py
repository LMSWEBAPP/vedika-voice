from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.script import ScriptCreate, ScriptResponse

CampaignStatus = Literal["DRAFT", "SCHEDULED", "ACTIVE", "PAUSED", "COMPLETED", "CANCELLED"]


class CampaignBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    objective: str = Field(..., min_length=5)
    primary_language: str = Field(default="en", max_length=10)
    fallback_language: str = Field(default="en", max_length=10)
    schedule_config: Optional[dict] = None


class CampaignCreate(CampaignBase):
    script: Optional[ScriptCreate] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    primary_language: Optional[str] = None
    fallback_language: Optional[str] = None
    schedule_config: Optional[dict] = None


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


class CampaignStats(BaseModel):
    total_leads: int = 0
    calls_completed: int = 0
    calls_in_progress: int = 0
    interested_count: int = 0
    progress_percentage: float = 0.0


class CampaignResponse(CampaignBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    stats: Optional[CampaignStats] = None

    model_config = ConfigDict(from_attributes=True)


class CampaignDetailResponse(CampaignResponse):
    script: Optional[ScriptResponse] = None
