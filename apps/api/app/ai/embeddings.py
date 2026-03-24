"""Embedding client — supports local fastembed (ONNX) or OpenAI-compatible API."""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

_local_model = None
_api_provider = None


def _get_local_model():
    """Lazy-load fastembed model (~100MB ONNX, no torch needed)."""
    global _local_model
    if _local_model is None:
        from fastembed import TextEmbedding
        model_name = settings.EMBEDDING_MODEL
        logger.info(f"Loading local embedding model: {model_name}")
        _local_model = TextEmbedding(model_name=model_name)
        logger.info(f"Loaded {model_name}")
    return _local_model


def _get_api_provider():
    global _api_provider
    if _api_provider is None:
        from app.ai.provider import OpenAICompatibleProvider
        _api_provider = OpenAICompatibleProvider(
            base_url=settings.EMBEDDING_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
    return _api_provider


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.EMBEDDING_PROVIDER == "local":
        model = _get_local_model()
        embeddings = list(model.embed(texts))
        return [emb.tolist() for emb in embeddings]
    else:
        provider = _get_api_provider()
        return await provider.embeddings(texts)


async def embed_query(query: str) -> list[float]:
    results = await embed_texts([query])
    return results[0]
