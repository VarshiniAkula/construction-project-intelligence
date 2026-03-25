"""Hybrid search combining dense retrieval (pgvector) with keyword fallback and reranking."""
import logging
from supabase._async.client import AsyncClient

from app.ai.embeddings import embed_query
from app.ai.reranker import rerank_documents
from app.retrieval.qdrant_store import search_chunks_pgvector

logger = logging.getLogger(__name__)


async def _keyword_fallback(
    sb: AsyncClient,
    project_id: str,
    query: str,
    allowed_scopes: list[str],
    trade_scope: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Fallback text search when embedding is unavailable (e.g. Vercel serverless)."""
    import re
    # Extract meaningful keywords, strip punctuation, skip stopwords
    stopwords = {"the", "are", "what", "how", "does", "did", "for", "and", "this", "that", "with", "from", "have", "has", "been", "will", "can", "any", "all", "our", "about", "which", "when", "where", "who", "why"}
    words = [re.sub(r'[^\w]', '', w).lower() for w in query.split()]
    words = [w for w in words if len(w) > 2 and w not in stopwords]
    if not words:
        return []

    # Use the longest meaningful keyword for broad search
    search_term = max(words, key=len)

    q = (
        sb.table("document_chunks")
        .select("id, document_id, chunk_text, page_number, visibility_scope, trade_scope, doc_type")
        .eq("document_id.project_id", project_id)  # won't work via PostgREST join
    )

    # Direct query: get chunks for this project's documents
    docs_result = await sb.table("documents").select("id, file_name, doc_type").eq("project_id", project_id).in_("visibility_scope", allowed_scopes).execute()
    doc_map = {d["id"]: d for d in (docs_result.data or [])}
    doc_ids = list(doc_map.keys())

    if not doc_ids:
        return []

    result = await (
        sb.table("document_chunks")
        .select("id, document_id, chunk_text, page_number, visibility_scope, trade_scope, doc_type")
        .in_("document_id", doc_ids)
        .in_("visibility_scope", allowed_scopes)
        .ilike("chunk_text", f"%{search_term}%")
        .limit(limit)
        .execute()
    )

    candidates = []
    for row in (result.data or []):
        doc = doc_map.get(row["document_id"], {})
        # Simple relevance: count how many query words appear
        text_lower = row["chunk_text"].lower()
        match_count = sum(1 for w in words if w.lower() in text_lower)
        score = match_count / max(len(words), 1)

        candidates.append({
            "id": row["id"],
            "document_id": row["document_id"],
            "chunk_text": row["chunk_text"],
            "text": row["chunk_text"],
            "page_number": row.get("page_number", 0),
            "file_name": doc.get("file_name", "Unknown"),
            "doc_type": row.get("doc_type", "general"),
            "visibility_scope": row["visibility_scope"],
            "trade_scope": row.get("trade_scope"),
            "score": score,
        })

    # Sort by relevance
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:limit]


async def hybrid_retrieve(
    sb: AsyncClient,
    project_id: str,
    query: str,
    allowed_scopes: list[str],
    trade_scope: str | None = None,
    initial_limit: int = 20,
    final_top_k: int = 5,
) -> list[dict]:
    # Step 1: Try embedding the query (skip on Vercel serverless — no persistent model cache)
    import os
    query_embedding = None
    if not os.environ.get("VERCEL"):
        try:
            query_embedding = await embed_query(query)
        except Exception as e:
            logger.warning(f"Embedding failed, will use keyword fallback: {e}")
    else:
        logger.info("Vercel serverless detected, using keyword fallback")

    # Step 2: Dense retrieval or keyword fallback
    candidates = []
    if query_embedding:
        candidates = await search_chunks_pgvector(
            sb=sb,
            project_id=project_id,
            query_embedding=query_embedding,
            allowed_scopes=allowed_scopes,
            trade_scope=trade_scope,
            limit=initial_limit,
        )

    if not candidates:
        logger.info("Using keyword fallback for retrieval")
        candidates = await _keyword_fallback(
            sb=sb,
            project_id=project_id,
            query=query,
            allowed_scopes=allowed_scopes,
            trade_scope=trade_scope,
            limit=initial_limit,
        )

    if not candidates:
        return []

    # Step 3: Rerank candidates (if reranker available)
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
        logger.warning(f"Reranking failed, using raw scores: {e}")
        return candidates[:final_top_k]
