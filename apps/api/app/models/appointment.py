from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.call import Call
    from app.models.campaign import Campaign
    from app.models.lead import Lead


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), index=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True, nullable=False)
    call_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("calls.id"), index=True, nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="REMINDER_SCHEDULED",
        index=True,
        nullable=False
    )  # REMINDER_SCHEDULED, CONFIRMED, COMPLETED, CANCELLED
    contact_channel: Mapped[str] = mapped_column(String(50), default="WhatsApp", nullable=False)  # WhatsApp, Phone, Google Meet
    requirement_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead")
    campaign: Mapped["Campaign"] = relationship("Campaign")
    call: Mapped[Optional["Call"]] = relationship("Call")
