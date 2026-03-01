from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime, date


class RFICreate(BaseModel):
    rfi_number: str | None = None
    title: str
    question: str
    status: str = "Open"


class RFIOut(BaseModel):
    id: str
    project_id: str
    rfi_number: str | None
    title: str
    question: str
    status: str
    created_at: datetime
    due_date: date | None
    answered_at: datetime | None

    phase_classification: str | None
    issue_classification: str | None
    entities: dict | None

    trade_name: str | None
    csi_division: str | None
    drawing_reference: str | None
    gridline_reference: str | None
    room_number: str | None
    spec_section: str | None
    responsible_party: str | None
    cost_impact: float | None
    schedule_impact_days: int | None

    class Config:
        from_attributes = True
