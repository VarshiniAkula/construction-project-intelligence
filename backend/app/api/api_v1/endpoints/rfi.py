from __future__ import annotations

import csv
import io
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_project_member
from app.db import crud
from app.services.rfi_nlp import analyze_rfi
from app import schemas

router = APIRouter()


@router.get("/{project_id}/rfis", response_model=list[schemas.RFIOut])
def list_rfis(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    return crud.rfi.list_for_project(db, project_id=project_id)


@router.post("/{project_id}/rfis", response_model=schemas.RFIOut)
def create_rfi(project_id: str, payload: schemas.RFICreate, db: Session = Depends(get_db), user=Depends(get_current_user), membership=Depends(require_project_member)):
    r = crud.rfi.create(db, project_id=project_id, rfi_number=payload.rfi_number, title=payload.title, question=payload.question, status=payload.status)
    crud.audit.log(db, user_id=user.id, project_id=project_id, action="rfi.create", details={"rfi_id": r.id, "rfi_number": r.rfi_number})
    return r


@router.post("/{project_id}/rfis/import_csv")
async def import_rfis_csv(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user), membership=Depends(require_project_member)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty CSV")
    text = data.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    for row in reader:
        title = (row.get("title") or row.get("Title") or "").strip()
        question = (row.get("question") or row.get("Question") or row.get("description") or row.get("Description") or "").strip()
        if not title or not question:
            continue
        rfi_number = (row.get("rfi_number") or row.get("RFI Number") or row.get("number") or "").strip() or None
        status = (row.get("status") or row.get("Status") or "Open").strip() or "Open"
        crud.rfi.create(db, project_id=project_id, rfi_number=rfi_number, title=title, question=question, status=status)
        created += 1

    crud.audit.log(db, user_id=user.id, project_id=project_id, action="rfi.import_csv", details={"count": created})
    return {"ok": True, "created": created}


@router.post("/{project_id}/rfis/{rfi_id}/analyze")
def analyze_single_rfi(project_id: str, rfi_id: str, db: Session = Depends(get_db), user=Depends(get_current_user), membership=Depends(require_project_member)):
    r = crud.rfi.get(db, rfi_id)
    if not r or r.project_id != project_id:
        raise HTTPException(status_code=404, detail="RFI not found")
    combined = f"{r.title}\n\n{r.question}"
    phase, issue, entities, fields = analyze_rfi(combined)
    crud.rfi.update_analysis(db, rfi_id=r.id, phase=phase, issue=issue, entities=entities, fields=fields)
    crud.audit.log(db, user_id=user.id, project_id=project_id, action="rfi.analyze", details={"rfi_id": rfi_id, "phase": phase, "issue": issue})
    return {"ok": True, "phase": phase, "issue": issue, "entities": entities}
