from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.membership import ProjectMembership
from app.models.document import Document
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.is_superadmin:
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
        projects = result.scalars().all()
    else:
        result = await db.execute(
            select(Project)
            .join(ProjectMembership, ProjectMembership.project_id == Project.id)
            .where(ProjectMembership.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
        projects = result.scalars().all()

    responses = []
    for p in projects:
        member_count = await db.scalar(
            select(func.count()).select_from(ProjectMembership).where(ProjectMembership.project_id == p.id)
        )
        doc_count = await db.scalar(
            select(func.count()).select_from(Document).where(Document.project_id == p.id)
        )
        my_membership = await db.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == p.id,
                ProjectMembership.user_id == user.id,
            )
        )
        m = my_membership.scalar_one_or_none()
        responses.append(ProjectResponse(
            id=p.id, name=p.name, code=p.code,
            location=p.location, description=p.description,
            created_at=p.created_at,
            member_count=member_count or 0,
            document_count=doc_count or 0,
            my_role=m.role if m else ("admin" if user.is_superadmin else None),
        ))
    return responses


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Project).where(Project.code == body.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project code already exists")

    project = Project(name=body.name, code=body.code, location=body.location, description=body.description)
    db.add(project)
    await db.flush()

    membership = ProjectMembership(
        user_id=user.id, project_id=project.id, role="admin"
    )
    db.add(membership)

    await log_action(db, "project.create", user_id=user.id, project_id=project.id, entity_type="project", entity_id=project.id)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id, name=project.name, code=project.code,
        location=project.location, description=project.description,
        created_at=project.created_at, member_count=1, document_count=0,
        my_role="admin",
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not user.is_superadmin:
        mem = await db.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == user.id,
            )
        )
        if not mem.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member")

    member_count = await db.scalar(
        select(func.count()).select_from(ProjectMembership).where(ProjectMembership.project_id == project_id)
    )
    doc_count = await db.scalar(
        select(func.count()).select_from(Document).where(Document.project_id == project_id)
    )
    mem_result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user.id,
        )
    )
    m = mem_result.scalar_one_or_none()
    return ProjectResponse(
        id=project.id, name=project.name, code=project.code,
        location=project.location, description=project.description,
        created_at=project.created_at,
        member_count=member_count or 0, document_count=doc_count or 0,
        my_role=m.role if m else ("admin" if user.is_superadmin else None),
    )
