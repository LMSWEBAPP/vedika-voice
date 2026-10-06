from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.call import Call
    from app.models.campaign import Campaign
    from app.models.user import User


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    do_not_call: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="leads")
    campaign_associations: Mapped[List["CampaignLead"]] = relationship(
        "CampaignLead",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    calls: Mapped[List["Call"]] = relationship(
        "Call",
        back_populates="lead",
        cascade="all, delete-orphan"
    )


class CampaignLead(Base, TimestampMixin):
    __tablename__ = "campaign_leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True, nullable=False)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="NEW", index=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_called_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="campaign_leads")
    lead: Mapped["Lead"] = relationship("Lead", back_populates="campaign_associations")
    calls: Mapped[List["Call"]] = relationship("Call", back_populates="campaign_lead")
