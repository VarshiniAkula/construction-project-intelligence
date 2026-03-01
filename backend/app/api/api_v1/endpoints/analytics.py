from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_project_member
from app.db import crud
from app import schemas

router = APIRouter()


@router.get("/{project_id}/analytics", response_model=schemas.AnalyticsResponse)
def analytics(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    rfis = crud.rfi.list_for_project(db, project_id=project_id)
    now = datetime.now(timezone.utc)

    # RFI aging
    by_status: dict[str, list[float]] = {}
    for r in rfis:
        end = r.answered_at or now
        age_days = max(0.0, (end - r.created_at).total_seconds() / 86400.0)
        by_status.setdefault(r.status or "Unknown", []).append(age_days)

    rfi_aging = []
    for status, ages in by_status.items():
        rfi_aging.append(schemas.RfiAgingPoint(status=status, count=len(ages), avg_age_days=sum(ages) / max(1, len(ages))))
    rfi_aging.sort(key=lambda x: x.count, reverse=True)

    # Top issues
    issue_counts: dict[str, int] = {}
    for r in rfis:
        issue = r.issue_classification or "Unclassified"
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    top_issues = [schemas.TopIssuePoint(issue=k, count=v) for k, v in sorted(issue_counts.items(), key=lambda kv: kv[1], reverse=True)][:10]

    # Trade risk
    trade_stats: dict[str, dict] = {}
    for r in rfis:
        trade = r.trade_name or "Unknown"
        st = trade_stats.setdefault(trade, {"open": 0, "sched": 0, "cost": 0.0})
        is_open = (r.status or "").lower() not in ["closed", "answered", "resolved"]
        if is_open:
            st["open"] += 1
            st["sched"] += int(r.schedule_impact_days or 0)
            try:
                st["cost"] += float(r.cost_impact or 0.0)
            except Exception:
                pass

    trade_risk = []
    for trade, st in trade_stats.items():
        open_rfis = st["open"]
        risk = float(open_rfis) + 0.15 * float(st["sched"]) + 0.0002 * float(st["cost"])
        trade_risk.append(schemas.TradeRiskPoint(trade=trade, open_rfis=open_rfis, risk_score=risk))
    trade_risk.sort(key=lambda x: x.risk_score, reverse=True)

    return schemas.AnalyticsResponse(rfi_aging=rfi_aging, top_issues=top_issues, trade_risk=trade_risk)
