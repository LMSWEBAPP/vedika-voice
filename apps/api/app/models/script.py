from typing import Optional
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class CampaignScript(Base, TimestampMixin):
    __tablename__ = "campaign_scripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id"),
        unique=True,
        index=True,
        nullable=False
    )
    persona: Mapped[str] = mapped_column(
        Text,
        default="Professional, empathetic, concise, and courteous representative.",
        nullable=False
    )
    voice_name: Mapped[str] = mapped_column(String(50), default="Aoede", nullable=False)
    opening: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    questions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    closing: Mapped[str] = mapped_column(Text, nullable=False)
    fallback_response: Mapped[Optional[str]] = mapped_column(
        Text,
        default="I understand. Let me make a note of that for our specialist team.",
        nullable=True
    )
    ai_disclosure: Mapped[Optional[str]] = mapped_column(
        Text,
        default="This is an automated AI assistant calling on behalf of our team.",
        nullable=True
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="script")
