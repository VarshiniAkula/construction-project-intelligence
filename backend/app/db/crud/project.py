from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.project import Project
from app.db.models.membership import ProjectMembership, ProjectRole


class ProjectCRUD:
    def get(self, db: Session, project_id: str) -> Project | None:
        return db.get(Project, project_id)

    def list_for_user(self, db: Session, user_id: str) -> list[Project]:
        stmt = (
            select(Project)
            .join(ProjectMembership, ProjectMembership.project_id == Project.id)
            .where(ProjectMembership.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, *, name: str, description: str | None, location: str | None, contract_type: str | None, created_by: str) -> Project:
        p = Project(name=name, description=description, location=location, contract_type=contract_type, created_by=created_by)
        db.add(p)
        db.commit()
        db.refresh(p)
        # creator becomes PM
        m = ProjectMembership(project_id=p.id, user_id=created_by, role=ProjectRole.PROJECT_MANAGER)
        db.add(m)
        db.commit()
        return p


project = ProjectCRUD()
