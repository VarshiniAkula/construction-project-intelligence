from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime

from app.db.models.membership import ProjectRole


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    contract_type: str | None = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str | None
    location: str | None
    contract_type: str | None
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    email: str
    role: ProjectRole
