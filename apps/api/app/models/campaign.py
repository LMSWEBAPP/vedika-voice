from typing import List, Optional
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", index=True, nullable=False)
    primary_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    fallback_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    schedule_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    script: Mapped[Optional["CampaignScript"]] = relationship(
        "CampaignScript",
        back_populates="campaign",
        uselist=False,
        cascade="all, delete-orphan"
    )
    campaign_leads: Mapped[List["CampaignLead"]] = relationship(
        "CampaignLead",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    calls: Mapped[List["Call"]] = relationship(
        "Call",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
