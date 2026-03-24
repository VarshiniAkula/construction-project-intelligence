from pydantic import BaseModel
from datetime import datetime


class ChatSessionCreate(BaseModel):
    title: str = "New Chat"


class ChatSessionResponse(BaseModel):
    id: str
    project_id: str
    title: str
    created_at: datetime
    last_message: str | None = None

    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    content: str


class CitationItem(BaseModel):
    document_id: str
    file_name: str
    page_number: int | None = None
    snippet: str = ""
    relevance_score: float = 0.0


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: list[CitationItem] = []
    model_metadata: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatAnswerResponse(BaseModel):
    answer: str
    citations: list[CitationItem] = []
    confidence: float = 0.0
    conflicts: list[str] = []
    used_document_ids: list[str] = []
    message: ChatMessageResponse | None = None
