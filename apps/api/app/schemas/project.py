from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    code: str
    location: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    code: str
    location: str | None = None
    description: str | None = None
    created_at: datetime
    member_count: int = 0
    document_count: int = 0
    my_role: str | None = None

    class Config:
        from_attributes = True
