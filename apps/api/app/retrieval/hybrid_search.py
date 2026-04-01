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
    stopwords = {"the", "are", "what", "how", "does", "did", "for", "and", "this", "that", "with", "from", "have", "has", "been", "will", "can", "any", "all", "our", "about", "which", "when", "where", "who", "why", "is", "it", "in", "on", "at", "to", "of", "a", "an", "do", "was", "were", "not", "but", "or", "so", "if", "its", "my", "no", "yes", "just", "also", "than", "then", "into", "out", "up", "down", "new", "old", "most", "some", "each", "every", "other"}
    words = [re.sub(r'[^\w]', '', w).lower() for w in query.split()]
    words = [w for w in words if len(w) > 2 and w not in stopwords]
    if not words:
        # If all words were filtered, use the original query words > 2 chars
        words = [re.sub(r'[^\w]', '', w).lower() for w in query.split() if len(w) > 2]
    if not words:
        return []

    # Direct query: get chunks for this project's documents
    # Search all non-error documents (ready, chunking, processing, uploaded)
    docs_result = await sb.table("documents").select("id, file_name, doc_type").eq("project_id", project_id).in_("visibility_scope", allowed_scopes).neq("status", "error").execute()
    doc_map = {d["id"]: d for d in (docs_result.data or [])}
    doc_ids = list(doc_map.keys())

    if not doc_ids:
        return []

    # Search with multiple keywords for better recall — try each keyword
    all_rows = {}
    search_terms = sorted(words, key=len, reverse=True)[:3]  # top 3 longest keywords
    for term in search_terms:
        try:
            result = await (
                sb.table("document_chunks")
                .select("id, document_id, chunk_text, page_number, visibility_scope, trade_scope, doc_type")
                .in_("document_id", doc_ids)
                .in_("visibility_scope", allowed_scopes)
                .ilike("chunk_text", f"%{term}%")
                .limit(limit)
                .execute()
            )
            for row in (result.data or []):
                all_rows[row["id"]] = row
        except Exception as e:
            logger.warning(f"Keyword search for '{term}' failed: {e}")

    # Fallback: if no chunks found, search document_pages directly
    # (handles documents stuck in chunking status that have pages but no chunks)
    if not all_rows:
        for term in search_terms:
            try:
                result = await (
                    sb.table("document_pages")
                    .select("id, document_id, raw_text, page_number")
                    .in_("document_id", doc_ids)
                    .ilike("raw_text", f"%{term}%")
                    .limit(limit)
                    .execute()
                )
                for row in (result.data or []):
                    doc = doc_map.get(row["document_id"], {})
                    all_rows[row["id"]] = {
                        "id": row["id"],
                        "document_id": row["document_id"],
                        "chunk_text": row["raw_text"],
                        "page_number": row.get("page_number", 0),
                        "visibility_scope": "team",
                        "trade_scope": None,
                        "doc_type": doc.get("doc_type", "general"),
                    }
            except Exception as e:
                logger.warning(f"Page search for '{term}' failed: {e}")

    candidates = []
    for row in all_rows.values():
        doc = doc_map.get(row["document_id"], {})
        # Relevance: count how many query words appear
        text_lower = row["chunk_text"].lower()
        match_count = sum(1 for w in words if w in text_lower)
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
