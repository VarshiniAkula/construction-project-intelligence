from pydantic import BaseModel
from datetime import datetime


class MemberAdd(BaseModel):
    email: str
    role: str
    assigned_trade: str | None = None


class MemberUpdate(BaseModel):
    role: str | None = None
    assigned_trade: str | None = None


class MemberResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    role: str
    assigned_trade: str | None = None
    user_email: str = ""
    user_full_name: str = ""
    user_company: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
