from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class DocumentOut(BaseModel):
    id: str
    project_id: str
    original_filename: str
    content_type: str | None
    version: int
    sha256: str
    uploaded_by: str
    created_at: datetime
    status: str
    extracted_text_chars: int
    error: str | None

    class Config:
        from_attributes = True
