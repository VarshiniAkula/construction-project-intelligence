"""Vector store operations using pgvector (Supabase PostgreSQL)."""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)


async def search_chunks_pgvector(
    db: AsyncSession,
    project_id: str,
    query_embedding: list[float],
    allowed_scopes: list[str],
    trade_scope: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search document chunks using pgvector cosine similarity with RBAC filters."""
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Build the query with RBAC filtering
    sql = """
        SELECT
            dc.id,
            dc.document_id,
            dc.chunk_text,
            dc.page_number,
            dc.visibility_scope,
            dc.trade_scope,
            dc.metadata_json,
            d.file_name,
            d.doc_type,
            1 - (dc.embedding <=> :embedding::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.project_id = :project_id
          AND dc.embedding IS NOT NULL
          AND dc.visibility_scope = ANY(:scopes)
    """
    params = {
        "embedding": embedding_str,
        "project_id": project_id,
        "scopes": allowed_scopes,
    }

    if trade_scope:
        sql += " AND (dc.visibility_scope != 'trade_scoped' OR dc.trade_scope = :trade OR dc.trade_scope IS NULL)"
        params["trade"] = trade_scope

    sql += " ORDER BY dc.embedding <=> :embedding2::vector LIMIT :limit"
    params["embedding2"] = embedding_str
    params["limit"] = limit

    try:
        result = await db.execute(text(sql), params)
        rows = result.mappings().all()
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
            for row in rows
        ]
    except Exception as e:
        logger.error(f"pgvector search error: {e}")
        return []


async def upsert_chunk_embedding(
    db: AsyncSession,
    chunk_id: str,
    embedding: list[float],
) -> None:
    """Update a chunk's embedding in the database."""
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
    await db.execute(
        text("UPDATE document_chunks SET embedding = :emb::vector WHERE id = :id"),
        {"emb": embedding_str, "id": chunk_id},
    )


async def delete_document_chunks(db: AsyncSession, document_id: str) -> None:
    """Delete all chunks for a document."""
    await db.execute(
        text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
        {"doc_id": document_id},
    )
