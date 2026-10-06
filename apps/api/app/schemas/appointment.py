from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.campaign import CampaignResponse
from app.schemas.lead import LeadResponse

AppointmentStatus = Literal["REMINDER_SCHEDULED", "CONFIRMED", "COMPLETED", "CANCELLED"]
ContactChannel = Literal["WhatsApp", "Phone", "Google Meet"]


class AppointmentBase(BaseModel):
    scheduled_at: datetime
    status: AppointmentStatus = "REMINDER_SCHEDULED"
    contact_channel: ContactChannel = "WhatsApp"
    requirement_notes: Optional[str] = None
    reminder_sent: bool = False


class AppointmentCreate(AppointmentBase):
    lead_id: str
    campaign_id: str
    call_id: Optional[str] = None


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    contact_channel: Optional[ContactChannel] = None
    requirement_notes: Optional[str] = None
    reminder_sent: Optional[bool] = None


class AppointmentResponse(AppointmentBase):
    id: str
    lead_id: str
    campaign_id: str
    call_id: Optional[str] = None
    created_at: datetime
    lead: Optional[LeadResponse] = None
    campaign: Optional[CampaignResponse] = None

    model_config = ConfigDict(from_attributes=True)
