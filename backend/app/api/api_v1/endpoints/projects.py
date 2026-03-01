from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_project_member, require_project_role
from app.db import crud
from app.db.models.membership import ProjectRole
from app import schemas

router = APIRouter()


@router.get("/", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.project.list_for_user(db, user_id=user.id)


@router.post("/", response_model=schemas.ProjectOut)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db), user=Depends(get_current_user), request: Request = None):
    p = crud.project.create(
        db,
        name=payload.name,
        description=payload.description,
        location=payload.location,
        contract_type=payload.contract_type,
        created_by=user.id,
    )
    crud.audit.log(db, user_id=user.id, project_id=p.id, action="project.create", details={"name": p.name}, ip_address=getattr(request.client, "host", None) if request else None)
    return p


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    p = crud.project.get(db, project_id=project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("/{project_id}/members", response_model=list[schemas.MembershipOut])
def list_members(project_id: str, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    return crud.membership.list_members(db, project_id=project_id)


@router.post("/{project_id}/members", response_model=schemas.MembershipOut)
def add_member(
    project_id: str,
    payload: schemas.ProjectMemberAdd,
    db: Session = Depends(get_db),
    membership=Depends(require_project_role([ProjectRole.PROJECT_MANAGER])),
):
    user = crud.membership.find_user_by_email(db, email=payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Ask them to register first.")
    m = crud.membership.add_member(db, project_id=project_id, user_id=user.id, role=payload.role)
    return m
