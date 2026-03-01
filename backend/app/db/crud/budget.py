from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.db.models.budget import BudgetItem


class BudgetCRUD:
    def clear_project(self, db: Session, *, project_id: str) -> None:
        db.execute(delete(BudgetItem).where(BudgetItem.project_id == project_id))
        db.commit()

    def bulk_create(self, db: Session, *, rows: list[BudgetItem]) -> None:
        db.add_all(rows)
        db.commit()

    def list_for_project(self, db: Session, *, project_id: str) -> list[BudgetItem]:
        stmt = select(BudgetItem).where(BudgetItem.project_id == project_id).order_by(BudgetItem.cost_code.asc())
        return list(db.execute(stmt).scalars().all())


budget = BudgetCRUD()
