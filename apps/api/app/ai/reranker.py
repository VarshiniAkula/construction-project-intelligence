"""Reranker client — supports local fastembed reranker or fallback scoring."""
import logging
import os
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
        # On Vercel, skip fastembed entirely and use keyword fallback
        if os.environ.get("VERCEL"):
            logger.info("Running on Vercel; using keyword rerank fallback.")
            model = "fallback"
        else:
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
    """Keyword-overlap reranker with TF-IDF-like scoring when no ML model is available."""
    import re
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "shall", "for", "and", "nor", "but", "or", "yet", "so", "in", "on", "at", "to", "of", "with", "by", "from", "as", "into", "through", "during", "before", "after", "above", "below", "between", "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "each", "every", "both", "few", "more", "most", "other", "some", "such", "no", "not", "only", "own", "same", "than", "too", "very", "just", "because", "about", "this", "that", "these", "those", "what", "which", "who", "whom", "it", "its"}
    query_words = [re.sub(r'[^\w]', '', w).lower() for w in query.split()]
    query_terms = [w for w in query_words if len(w) > 1 and w not in stopwords]
    if not query_terms:
        query_terms = [w for w in query_words if len(w) > 1]

    results = []
    for i, doc in enumerate(documents):
        doc_lower = doc.lower()
        # Score: weighted keyword matches + position bonus for early matches
        match_count = 0
        position_bonus = 0.0
        for term in query_terms:
            pos = doc_lower.find(term)
            if pos >= 0:
                match_count += 1
                # Bonus for matches near the start of the chunk
                position_bonus += max(0, 1.0 - pos / max(len(doc_lower), 1))
        score = (match_count / max(len(query_terms), 1)) * 0.7 + (position_bonus / max(len(query_terms), 1)) * 0.3
        results.append({"index": i, "relevance_score": score})
    return results
