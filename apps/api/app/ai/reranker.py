"""Reranker client — supports local fastembed reranker or fallback scoring."""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

_local_model = None


def _get_local_model():
    """Lazy-load fastembed reranker (ONNX, lightweight)."""
    global _local_model
    if _local_model is None:
        try:
            from fastembed import TextCrossEncoder
            model_name = settings.RERANKER_MODEL
            logger.info(f"Loading local reranker model: {model_name}")
            _local_model = TextCrossEncoder(model_name=model_name)
            logger.info(f"Loaded reranker: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load local reranker: {e}. Using fallback scoring.")
            _local_model = "fallback"
    return _local_model


async def rerank_documents(query: str, documents: list[str], top_k: int = 5) -> list[dict]:
    if settings.RERANKER_PROVIDER == "local":
        model = _get_local_model()
        if model == "fallback":
            # Simple keyword-overlap scoring as fallback
            results = _keyword_rerank(query, documents)
        else:
            pairs = [(query, doc) for doc in documents]
            scores = list(model.rerank(query, documents))
            results = [{"index": i, "relevance_score": float(s)} for i, s in enumerate(scores)]
        sorted_results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
        return sorted_results[:top_k]
    else:
        from app.ai.provider import OpenAICompatibleProvider
        provider = OpenAICompatibleProvider(
            base_url=settings.RERANKER_BASE_URL,
            api_key=settings.RERANKER_API_KEY,
            model=settings.RERANKER_MODEL,
        )
        results = await provider.rerank(query, documents)
        sorted_results = sorted(results, key=lambda x: x.get("relevance_score", x.get("score", 0)), reverse=True)
        return sorted_results[:top_k]


def _keyword_rerank(query: str, documents: list[str]) -> list[dict]:
    """Simple keyword-overlap reranker when no ML model is available."""
    query_terms = set(query.lower().split())
    results = []
    for i, doc in enumerate(documents):
        doc_terms = set(doc.lower().split())
        overlap = len(query_terms & doc_terms)
        score = overlap / max(len(query_terms), 1)
        results.append({"index": i, "relevance_score": score})
    return results
