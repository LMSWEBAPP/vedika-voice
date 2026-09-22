from typing import Optional
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class AgentSession(Base, TimestampMixin):
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    call_id: Mapped[str] = mapped_column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)  # 'gemini' | 'mock'
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    call: Mapped["Call"] = relationship("Call", back_populates="agent_sessions")
