from __future__ import annotations

from pydantic import BaseModel
from datetime import date
from typing import List


class ScheduleSummary(BaseModel):
    total_activities: int
    earliest_start: date | None
    latest_finish: date | None
    slipped_activities: int


class ScheduleActivityOut(BaseModel):
    id: str
    activity_id: str
    name: str
    start: date | None
    finish: date | None
    baseline_start: date | None
    baseline_finish: date | None
    percent_complete: float | None
    predecessors: str | None

    class Config:
        from_attributes = True
