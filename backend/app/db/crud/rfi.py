from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.rfi import RFI


class RFICRUD:
    def get(self, db: Session, rfi_id: str) -> RFI | None:
        return db.get(RFI, rfi_id)

    def list_for_project(self, db: Session, *, project_id: str) -> list[RFI]:
        stmt = select(RFI).where(RFI.project_id == project_id).order_by(RFI.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, *, project_id: str, rfi_number: str | None, title: str, question: str, status: str = "Open"):
        r = RFI(project_id=project_id, rfi_number=rfi_number, title=title, question=question, status=status)
        db.add(r)
        db.commit()
        db.refresh(r)
        return r

    def update_analysis(
        self,
        db: Session,
        *,
        rfi_id: str,
        phase: str | None,
        issue: str | None,
        entities: dict | None,
        fields: dict | None = None,
    ) -> None:
        r = self.get(db, rfi_id)
        if not r:
            return
        r.phase_classification = phase
        r.issue_classification = issue
        r.entities = entities
        if fields:
            for k, v in fields.items():
                if hasattr(r, k):
                    setattr(r, k, v)
        db.add(r)
        db.commit()


rfi = RFICRUD()
