"""Qdrant client for the worker."""
import os
from qdrant_client import QdrantClient, models

_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _client
    if _client is None:
        mode = os.environ.get("QDRANT_MODE", "memory")
        if mode == "memory":
            _client = QdrantClient(location=":memory:")
        else:
            _client = QdrantClient(
                host=os.environ.get("QDRANT_HOST", "localhost"),
                port=int(os.environ.get("QDRANT_PORT", "6333")),
            )
    return _client


def ensure_collection(project_id: str) -> str:
    collection_name = f"project_{project_id.replace('-', '_')}"
    client = get_qdrant()

    collections = client.get_collections().collections
    if collection_name not in [c.name for c in collections]:
        dim = int(os.environ.get("EMBEDDING_DIM", "384"))
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(size=dim, distance=models.Distance.COSINE),
            },
        )
        for field in ["visibility_scope", "trade_scope", "doc_type", "document_id"]:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
    return collection_name


def upsert_points(collection_name: str, points: list[models.PointStruct]) -> None:
    client = get_qdrant()
    for i in range(0, len(points), 100):
        client.upsert(collection_name=collection_name, points=points[i : i + 100])
