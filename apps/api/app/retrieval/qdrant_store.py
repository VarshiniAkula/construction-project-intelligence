"""Vector store operations using Supabase RPC + pgvector."""
import logging
from supabase._async.client import AsyncClient

logger = logging.getLogger(__name__)


async def search_chunks_pgvector(
    sb: AsyncClient,
    project_id: str,
    query_embedding: list[float],
    allowed_scopes: list[str],
    trade_scope: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search document chunks using Supabase RPC function for pgvector cosine similarity."""
    try:
        result = await sb.rpc("search_chunks", {
            "p_project_id": project_id,
            "p_embedding": query_embedding,
            "p_allowed_scopes": allowed_scopes,
            "p_trade_scope": trade_scope,
            "p_limit": limit,
        }).execute()

        return [
            {
                "id": str(row["id"]),
                "document_id": str(row["document_id"]),
                "chunk_text": row["chunk_text"],
                "text": row["chunk_text"],
                "page_number": row["page_number"],
                "file_name": row["file_name"],
                "doc_type": row["doc_type"],
                "visibility_scope": row["visibility_scope"],
                "trade_scope": row["trade_scope"],
                "score": float(row["similarity"]) if row["similarity"] else 0.0,
            }
            for row in (result.data or [])
        ]
    except Exception as e:
        logger.error(f"pgvector search error: {e}")
        return []
