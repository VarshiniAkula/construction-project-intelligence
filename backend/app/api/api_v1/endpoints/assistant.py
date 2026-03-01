from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_project_member
from app.core.config import settings
from app.services.vectorstore import vectorstore
from app.services.llm import openai_available, generate_with_openai, generate_fallback
from app import schemas

router = APIRouter()


@router.post("/{project_id}/assistant/chat", response_model=schemas.ChatResponse)
def chat(project_id: str, payload: schemas.ChatRequest, db: Session = Depends(get_db), membership=Depends(require_project_member)):
    top_k = payload.top_k or settings.ASSISTANT_TOP_K
    retrieved = vectorstore.search(project_id, payload.message, k=top_k)

    context_blocks = []
    sources: list[schemas.SourceSnippet] = []
    for i, r in enumerate(retrieved, start=1):
        context_blocks.append(f"[{i}] {r.filename} (v{r.version})\n{r.text}")
        snippet = r.text.strip().replace("\n", " ")
        if len(snippet) > 260:
            snippet = snippet[:260].rstrip() + "..."
        sources.append(schemas.SourceSnippet(document_id=r.document_id, filename=r.filename, version=r.version, snippet=snippet))

    if openai_available():
        try:
            answer = generate_with_openai(payload.message, context_blocks)
            mode = "openai"
        except Exception:
            answer = generate_fallback(payload.message, context_blocks)
            mode = "fallback"
    else:
        answer = generate_fallback(payload.message, context_blocks)
        mode = "fallback"

    return schemas.ChatResponse(answer=answer, sources=sources, mode=mode)
