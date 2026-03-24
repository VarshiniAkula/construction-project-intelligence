"""Hybrid search combining dense retrieval (pgvector) with reranking."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_query
from app.ai.reranker import rerank_documents
from app.retrieval.qdrant_store import search_chunks_pgvector

logger = logging.getLogger(__name__)


async def hybrid_retrieve(
    db: AsyncSession,
    project_id: str,
    query: str,
    allowed_scopes: list[str],
    trade_scope: str | None = None,
    initial_limit: int = 20,
    final_top_k: int = 5,
) -> list[dict]:
    """
    1. Dense search with embeddings via pgvector
    2. Rerank with cross-encoder
    """
    # Step 1: Embed query
    try:
        query_embedding = await embed_query(query)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

    # Step 2: Dense retrieval from pgvector
    candidates = await search_chunks_pgvector(
        db=db,
        project_id=project_id,
        query_embedding=query_embedding,
        allowed_scopes=allowed_scopes,
        trade_scope=trade_scope,
        limit=initial_limit,
    )

    if not candidates:
        return []

    # Step 3: Rerank candidates
    try:
        candidate_texts = [c.get("text", c.get("chunk_text", "")) for c in candidates]
        rerank_results = await rerank_documents(query, candidate_texts, top_k=final_top_k)

        reranked = []
        for r in rerank_results:
            idx = r.get("index", 0)
            if idx < len(candidates):
                candidate = candidates[idx]
                candidate["rerank_score"] = r.get("relevance_score", r.get("score", 0))
                reranked.append(candidate)
        return reranked

    except Exception as e:
        logger.warning(f"Reranking failed, using dense scores: {e}")
        return candidates[:final_top_k]
