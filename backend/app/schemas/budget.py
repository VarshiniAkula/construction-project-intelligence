from __future__ import annotations

from pydantic import BaseModel
from typing import List


class BudgetSummary(BaseModel):
    items: int
    baseline_total: float
    actual_total: float
    variance: float


class BudgetItemOut(BaseModel):
    id: str
    cost_code: str
    description: str | None
    baseline_cost: float | None
    actual_cost: float | None
    committed_cost: float | None

    class Config:
        from_attributes = True
