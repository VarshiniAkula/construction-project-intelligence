from __future__ import annotations

import uuid
from datetime import datetime, timezone, date

from sqlalchemy import String, DateTime, ForeignKey, Date, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScheduleActivity(Base):
    __tablename__ = "schedule_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    activity_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    start: Mapped[date | None] = mapped_column(Date, nullable=True)
    finish: Mapped[date | None] = mapped_column(Date, nullable=True)

    baseline_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    baseline_finish: Mapped[date | None] = mapped_column(Date, nullable=True)

    percent_complete: Mapped[float | None] = mapped_column(Float, nullable=True)
    predecessors: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
