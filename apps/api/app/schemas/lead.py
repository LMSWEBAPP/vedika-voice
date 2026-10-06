from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

LeadStatus = Literal[
    "NEW",
    "QUEUED",
    "CALLING",
    "CONTACTED",
    "INTERESTED",
    "NOT_INTERESTED",
    "CALLBACK",
    "NO_ANSWER",
    "INVALID",
    "DO_NOT_CALL"
]


class LeadBase(BaseModel):
    phone: str = Field(..., min_length=7, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    company: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    custom_data: Optional[Dict[str, Any]] = None
    do_not_call: bool = False


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    do_not_call: Optional[bool] = None


class LeadResponse(LeadBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignLeadResponse(BaseModel):
    id: str
    campaign_id: str
    lead_id: str
    status: str
    attempts: int
    last_called_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    lead: LeadResponse

    model_config = ConfigDict(from_attributes=True)


class LeadImportResult(BaseModel):
    total_processed: int
    imported: int
    skipped_duplicates: int
    rejected_dnc: int
    invalid_format: int
    errors: List[str] = []


class BatchAssignLeadsRequest(BaseModel):
    campaign_id: str
    lead_ids: Optional[List[str]] = None
    assign_all_unassigned: bool = False
