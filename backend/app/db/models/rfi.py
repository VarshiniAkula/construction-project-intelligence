from __future__ import annotations

import uuid
from datetime import datetime, timezone, date

from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, Integer, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RFI(Base):
    __tablename__ = "rfis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    rfi_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Open", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # NLP fields (starter)
    phase_classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issue_classification: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # extracted "common entities" (optional columns)
    trade_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    csi_division: Mapped[str | None] = mapped_column(String(50), nullable=True)
    drawing_reference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gridline_reference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    spec_section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    responsible_party: Mapped[str | None] = mapped_column(String(120), nullable=True)

    cost_impact: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    schedule_impact_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
