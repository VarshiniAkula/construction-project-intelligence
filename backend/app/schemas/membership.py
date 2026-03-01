from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime

from app.db.models.membership import ProjectRole


class MembershipOut(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: ProjectRole
    created_at: datetime

    class Config:
        from_attributes = True
