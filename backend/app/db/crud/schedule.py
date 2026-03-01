from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.db.models.schedule import ScheduleActivity


class ScheduleCRUD:
    def clear_project(self, db: Session, *, project_id: str) -> None:
        db.execute(delete(ScheduleActivity).where(ScheduleActivity.project_id == project_id))
        db.commit()

    def bulk_create(self, db: Session, *, rows: list[ScheduleActivity]) -> None:
        db.add_all(rows)
        db.commit()

    def list_for_project(self, db: Session, *, project_id: str) -> list[ScheduleActivity]:
        stmt = select(ScheduleActivity).where(ScheduleActivity.project_id == project_id).order_by(ScheduleActivity.start.asc())
        return list(db.execute(stmt).scalars().all())


schedule = ScheduleCRUD()
