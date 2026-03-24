from pydantic import BaseModel
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: str
    project_id: str | None = None
    user_id: str | None = None
    user_email: str = ""
    user_name: str = ""
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    details_json: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True
