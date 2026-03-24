from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    file_name: str
    file_type: str
    doc_type: str
    visibility_scope: str
    trade_scope: str | None = None
    revision: str | None = None
    status: str
    issue_date: str | None = None
    page_count: int | None = None
    processing_error: str | None = None
    uploaded_by_name: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    metadata_json: dict | None = None
    storage_key: str = ""
    pages: list["PageResponse"] = []


class PageResponse(BaseModel):
    id: str
    page_number: int
    page_summary: str | None = None
    image_storage_key: str | None = None

    class Config:
        from_attributes = True


class DocumentUploadParams(BaseModel):
    doc_type: str = "general"
    visibility_scope: str = "project_full"
    trade_scope: str | None = None
    revision: str | None = None
    issue_date: str | None = None
