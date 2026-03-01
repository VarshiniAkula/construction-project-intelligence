from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog


class AuditCRUD:
    def log(self, db: Session, *, user_id: str, action: str, project_id: str | None = None, details: dict | None = None, ip_address: str | None = None):
        a = AuditLog(user_id=user_id, project_id=project_id, action=action, details=details, ip_address=ip_address)
        db.add(a)
        db.commit()
        return a


audit = AuditCRUD()
