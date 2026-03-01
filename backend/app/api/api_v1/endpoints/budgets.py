from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_project_member
from app.db import crud
from app.db.models.budget import BudgetItem
from app import schemas

router = APIRouter()


def _to_float(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


@router.post("/{project_id}/budget/import_csv")
async def import_budget_csv(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user), membership=Depends(require_project_member)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty CSV")
    text = data.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    rows: list[BudgetItem] = []
    for row in reader:
        cost_code = (row.get("cost_code") or row.get("Cost Code") or row.get("code") or "").strip()
        if not cost_code:
            continue
        bi = BudgetItem(
            project_id=project_id,
            cost_code=cost_code,
            description=(row.get("description") or row.get("Description") or None),
            baseline_cost=_to_float(row.get("baseline_cost") or row.get("Baseline Cost")),
            actual_cost=_to_float(row.get("actual_cost") or row.get("Actual Cost")),
            committed_cost=_to_float(row.get("committed_cost") or row.get("Committed Cost")),
        )
        rows.append(bi)

    crud.budget.clear_project(db, project_id=project_id)
    if rows:
        crud.budget.bulk_create(db, rows=rows)

    crud.audit.log(db, user_id=user.id, project_id=project_id, action="budget.import_csv", details={"count": len(rows)})
    return {"ok": True, "imported": len(rows)}


@router.get("/{project_id}/budget/summary", response_model=schemas.BudgetSummary)
def budget_summary(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    rows = crud.budget.list_for_project(db, project_id=project_id)
    baseline_total = 0.0
    actual_total = 0.0
    for r in rows:
        try:
            baseline_total += float(r.baseline_cost or 0.0)
        except Exception:
            pass
        try:
            actual_total += float(r.actual_cost or 0.0)
        except Exception:
            pass
    variance = actual_total - baseline_total
    return schemas.BudgetSummary(items=len(rows), baseline_total=baseline_total, actual_total=actual_total, variance=variance)
