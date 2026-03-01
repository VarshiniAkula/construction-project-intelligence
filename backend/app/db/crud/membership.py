from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.membership import ProjectMembership, ProjectRole
from app.db.models.user import User


class MembershipCRUD:
    def get_membership(self, db: Session, *, project_id: str, user_id: str) -> ProjectMembership | None:
        stmt = select(ProjectMembership).where(ProjectMembership.project_id == project_id, ProjectMembership.user_id == user_id)
        return db.execute(stmt).scalars().first()

    def list_members(self, db: Session, *, project_id: str) -> list[ProjectMembership]:
        stmt = select(ProjectMembership).where(ProjectMembership.project_id == project_id)
        return list(db.execute(stmt).scalars().all())

    def add_member(self, db: Session, *, project_id: str, user_id: str, role: ProjectRole) -> ProjectMembership:
        existing = self.get_membership(db, project_id=project_id, user_id=user_id)
        if existing:
            existing.role = role
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        m = ProjectMembership(project_id=project_id, user_id=user_id, role=role)
        db.add(m)
        db.commit()
        db.refresh(m)
        return m

    def remove_member(self, db: Session, *, project_id: str, user_id: str) -> None:
        m = self.get_membership(db, project_id=project_id, user_id=user_id)
        if not m:
            return
        db.delete(m)
        db.commit()

    def find_user_by_email(self, db: Session, *, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        return db.execute(stmt).scalars().first()


membership = MembershipCRUD()
