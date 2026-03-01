from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_project_member
from app.db import crud
from app.db.models.schedule import ScheduleActivity
from app import schemas

router = APIRouter()


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        # expecting YYYY-MM-DD
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


@router.post("/{project_id}/schedule/import_csv")
async def import_schedule_csv(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user), membership=Depends(require_project_member)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty CSV")
    text = data.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    rows: list[ScheduleActivity] = []
    for row in reader:
        activity_id = (row.get("activity_id") or row.get("Activity ID") or row.get("id") or "").strip()
        name = (row.get("name") or row.get("Name") or row.get("activity_name") or "").strip()
        if not activity_id or not name:
            continue
        sa = ScheduleActivity(
            project_id=project_id,
            activity_id=activity_id,
            name=name,
            start=_parse_date(row.get("start") or row.get("Start")),
            finish=_parse_date(row.get("finish") or row.get("Finish")),
            baseline_start=_parse_date(row.get("baseline_start") or row.get("Baseline Start")),
            baseline_finish=_parse_date(row.get("baseline_finish") or row.get("Baseline Finish")),
            percent_complete=float(row.get("percent_complete") or row.get("% Complete") or 0) if (row.get("percent_complete") or row.get("% Complete")) else None,
            predecessors=(row.get("predecessors") or row.get("Predecessors") or None),
        )
        rows.append(sa)

    crud.schedule.clear_project(db, project_id=project_id)
    if rows:
        crud.schedule.bulk_create(db, rows=rows)

    crud.audit.log(db, user_id=user.id, project_id=project_id, action="schedule.import_csv", details={"count": len(rows)})
    return {"ok": True, "imported": len(rows)}


@router.get("/{project_id}/schedule/summary", response_model=schemas.ScheduleSummary)
def schedule_summary(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    rows = crud.schedule.list_for_project(db, project_id=project_id)
    if not rows:
        return schemas.ScheduleSummary(total_activities=0, earliest_start=None, latest_finish=None, slipped_activities=0)

    starts = [r.start for r in rows if r.start]
    finishes = [r.finish for r in rows if r.finish]
    earliest = min(starts) if starts else None
    latest = max(finishes) if finishes else None

    slipped = 0
    for r in rows:
        if r.finish and r.baseline_finish and r.finish > r.baseline_finish:
            slipped += 1

    return schemas.ScheduleSummary(total_activities=len(rows), earliest_start=earliest, latest_finish=latest, slipped_activities=slipped)
