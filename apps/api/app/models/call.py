from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now


class Call(Base, TimestampMixin):
    __tablename__ = "calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True, nullable=False)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), index=True, nullable=False)
    campaign_lead_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaign_leads.id"), index=True, nullable=True
    )
    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    provider_call_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", index=True, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    termination_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recording_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="calls")
    lead: Mapped["Lead"] = relationship("Lead", back_populates="calls")
    campaign_lead: Mapped[Optional["CampaignLead"]] = relationship("CampaignLead", back_populates="calls")
    events: Mapped[List["CallEvent"]] = relationship("CallEvent", back_populates="call", cascade="all, delete-orphan")
    transcripts: Mapped[List["CallTranscript"]] = relationship(
        "CallTranscript",
        back_populates="call",
        cascade="all, delete-orphan",
        order_by="CallTranscript.timestamp"
    )
    answers: Mapped[List["CallAnswer"]] = relationship(
        "CallAnswer",
        back_populates="call",
        cascade="all, delete-orphan"
    )
    agent_sessions: Mapped[List["AgentSession"]] = relationship(
        "AgentSession",
        back_populates="call",
        cascade="all, delete-orphan"
    )


class CallEvent(Base):
    __tablename__ = "call_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    call_id: Mapped[str] = mapped_column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    call: Mapped["Call"] = relationship("Call", back_populates="events")


class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    call_id: Mapped[str] = mapped_column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    speaker: Mapped[str] = mapped_column(String(20), nullable=False)  # 'ai' | 'user' | 'system'
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=1.0, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    call: Mapped["Call"] = relationship("Call", back_populates="transcripts")


class CallAnswer(Base, TimestampMixin):
    __tablename__ = "call_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    call_id: Mapped[str] = mapped_column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    question_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_answer: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    call: Mapped["Call"] = relationship("Call", back_populates="answers")
