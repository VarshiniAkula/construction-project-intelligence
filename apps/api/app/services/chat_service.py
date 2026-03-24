"""Chat/RAG pipeline orchestration."""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import ProjectMembership
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.rbac.filters import get_allowed_scopes
from app.retrieval.hybrid_search import hybrid_retrieve
from app.ai.generator import generate_answer
from app.schemas.chat import CitationItem, ChatAnswerResponse, ChatMessageResponse
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


async def process_chat_message(
    db: AsyncSession,
    user_id: str,
    project_id: str,
    session_id: str,
    membership: ProjectMembership,
    content: str,
) -> ChatAnswerResponse:
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=content,
    )
    db.add(user_msg)
    await db.flush()

    # Build RBAC scopes for pgvector search
    allowed_scopes = get_allowed_scopes(membership)
    trade_scope = membership.assigned_trade if membership.role == "subcontractor" else None

    # Retrieve and rerank
    retrieved_chunks = await hybrid_retrieve(
        db=db,
        project_id=project_id,
        query=content,
        allowed_scopes=allowed_scopes,
        trade_scope=trade_scope,
        initial_limit=20,
        final_top_k=5,
    )

    if not retrieved_chunks:
        answer_text = "I don't have enough accessible documentation in this project to answer your question. Please try uploading relevant documents or adjusting your question."
        citations = []
        confidence = 0.0
    else:
        # Enrich chunks with document info
        doc_ids = list(set(c.get("document_id", "") for c in retrieved_chunks))
        doc_map = {}
        for doc_id in doc_ids:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc_map[doc_id] = doc

        context_chunks = []
        for chunk in retrieved_chunks:
            doc_id = chunk.get("document_id", "")
            doc = doc_map.get(doc_id)
            context_chunks.append({
                "text": chunk.get("text", chunk.get("chunk_text", "")),
                "file_name": chunk.get("file_name", doc.file_name if doc else "Unknown"),
                "page_number": chunk.get("page_number", 0),
                "document_id": doc_id,
                "score": chunk.get("rerank_score", chunk.get("score", 0)),
            })

        # Get recent chat history
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(6)
        )
        history = [
            {"role": m.role, "content": m.content}
            for m in reversed(history_result.scalars().all())
        ]

        # Generate answer
        gen_result = await generate_answer(content, context_chunks, history)
        answer_text = gen_result["answer"]

        # Build citations
        citations = [
            CitationItem(
                document_id=c["document_id"],
                file_name=c["file_name"],
                page_number=c["page_number"],
                snippet=c["text"][:200],
                relevance_score=c["score"],
            )
            for c in context_chunks
        ]
        confidence = min(1.0, sum(c["score"] for c in context_chunks) / max(len(context_chunks), 1))

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer_text,
        citations_json=[c.model_dump() for c in citations],
        model_metadata_json={"model": "claude", "chunks_used": len(retrieved_chunks)},
    )
    db.add(assistant_msg)

    # Update session title if first message
    session = await db.get(ChatSession, session_id)
    if session and session.title == "New Chat":
        session.title = content[:80]

    await log_action(
        db, "chat.query", user_id=user_id, project_id=project_id,
        entity_type="chat_session", entity_id=session_id,
        details={"query_length": len(content), "chunks_retrieved": len(retrieved_chunks)},
    )
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatAnswerResponse(
        answer=answer_text,
        citations=citations,
        confidence=confidence,
        conflicts=[],
        used_document_ids=list(set(c.document_id for c in citations)),
        message=ChatMessageResponse(
            id=assistant_msg.id,
            session_id=session_id,
            role="assistant",
            content=answer_text,
            citations=citations,
            created_at=assistant_msg.created_at,
        ),
    )
