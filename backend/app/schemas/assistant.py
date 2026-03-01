from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    top_k: int | None = None


class SourceSnippet(BaseModel):
    document_id: str
    filename: str
    version: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceSnippet] = []
    mode: str
