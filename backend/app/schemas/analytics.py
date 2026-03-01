from __future__ import annotations

from pydantic import BaseModel
from typing import List


class RfiAgingPoint(BaseModel):
    status: str
    count: int
    avg_age_days: float


class TopIssuePoint(BaseModel):
    issue: str
    count: int


class TradeRiskPoint(BaseModel):
    trade: str
    open_rfis: int
    risk_score: float


class AnalyticsResponse(BaseModel):
    rfi_aging: List[RfiAgingPoint]
    top_issues: List[TopIssuePoint]
    trade_risk: List[TradeRiskPoint]
