"""Answer generation client — supports Anthropic (Claude), Groq, OpenAI-compatible models,
and a smart extractive fallback when no API key is configured."""
import logging
import re
import math
from collections import Counter
from app.ai.provider import OpenAICompatibleProvider, AnthropicProvider
from app.config import settings

logger = logging.getLogger(__name__)

_provider = None

# ── Stopwords for extractive Q&A ──
_STOPWORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between out off over under again "
    "further then once here there when where why how all both each few more most "
    "other some such no nor not only own same so than too very and but if or "
    "because until while about what which who whom this that these those i me my "
    "we our you your he him his she her it its they them their".split()
)


def _has_api_key() -> bool:
    """Check whether an API key is configured for the active LLM provider."""
    if settings.LLM_PROVIDER == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    elif settings.LLM_PROVIDER == "groq":
        return bool(settings.GROQ_API_KEY)
    else:
        return bool(settings.LLM_API_KEY and settings.LLM_API_KEY != "not-needed")


def get_generator_provider():
    global _provider
    if _provider is None:
        if settings.LLM_PROVIDER == "anthropic":
            _provider = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL,
                timeout=120.0,
            )
        elif settings.LLM_PROVIDER == "groq":
            _provider = OpenAICompatibleProvider(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                timeout=30.0,
            )
        else:
            _provider = OpenAICompatibleProvider(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                timeout=120.0,
            )
    return _provider


SYSTEM_PROMPT = """You are a construction document assistant for the Construction RAG platform. Your role is to help construction professionals find and understand information from their project documents.

STRICT RULES:
1. Use ONLY the provided project documents to answer questions. Never use outside knowledge.
2. If the answer is not supported by the provided evidence, explicitly say "I don't have enough information in the accessible documents to answer this question."
3. CITE every factual claim using the format [Source N] where N corresponds to the numbered context blocks below.
4. If multiple document revisions exist, prefer the latest approved revision and state which revision you used.
5. If documents conflict with each other, summarize the conflict and cite both sources.
6. Never fabricate or guess information not present in the provided context.
7. Be precise, professional, and concise. Use construction industry terminology.

When answering:
- Start with a direct answer
- Support with specific citations
- Note any caveats or limitations
- If asked about documents you cannot access, say "There is not enough accessible documentation to answer this question."
"""


def format_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        doc_name = chunk.get("file_name", "Unknown Document")
        page = chunk.get("page_number", "?")
        text = chunk.get("text", "")
        parts.append(f"[Source {i}] Document: {doc_name}, Page {page}\n{text}\n")
    return "\n---\n".join(parts)


# ── Smart Extractive Q&A (no LLM needed) ──

def _tokenize(text: str) -> list[str]:
    """Lowercase tokenize, strip non-alphanumeric."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS and len(w) > 1]


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping meaningful ones."""
    raw = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [s.strip() for s in raw if len(s.strip()) > 20]


def _build_extractive_answer(query: str, context_chunks: list[dict]) -> dict:
    """Build a coherent answer by extracting and scoring the most relevant
    sentences from context chunks against the user's query."""
    if not context_chunks:
        return {
            "answer": "No relevant documents were found for your query.",
            "model": "extractive",
        }

    query_tokens = _tokenize(query)
    if not query_tokens:
        query_tokens = [w.lower() for w in query.split() if len(w) > 1]

    # Build IDF from all sentences across chunks
    all_sentences: list[tuple[str, int, dict]] = []  # (sentence, source_idx, chunk)
    for idx, chunk in enumerate(context_chunks):
        text = chunk.get("text", "") or ""
        for sent in _split_sentences(text):
            all_sentences.append((sent, idx + 1, chunk))

    if not all_sentences:
        # Chunks exist but no extractable sentences; show raw excerpts
        parts = []
        for i, chunk in enumerate(context_chunks, 1):
            text = (chunk.get("text", "") or "").strip()[:400]
            fname = chunk.get("file_name", "Unknown")
            page = chunk.get("page_number", "?")
            parts.append(f"From **{fname}** (Page {page}) [Source {i}]:\n> {text}")
        return {
            "answer": "\n\n".join(parts),
            "model": "extractive",
        }

    # Compute IDF for query tokens across sentences
    doc_freq: Counter = Counter()
    for sent, _, _ in all_sentences:
        sent_tokens = set(_tokenize(sent))
        for qt in query_tokens:
            if qt in sent_tokens:
                doc_freq[qt] += 1

    n_docs = len(all_sentences)
    idf = {qt: math.log((n_docs + 1) / (doc_freq.get(qt, 0) + 1)) + 1.0 for qt in query_tokens}

    # Score each sentence
    scored: list[tuple[float, str, int, dict]] = []
    for sent, src_idx, chunk in all_sentences:
        sent_tokens = _tokenize(sent)
        sent_token_set = set(sent_tokens)
        if not sent_tokens:
            continue

        # TF-IDF-like score
        score = 0.0
        matches = 0
        for qt in query_tokens:
            if qt in sent_token_set:
                tf = sent_tokens.count(qt) / len(sent_tokens)
                score += tf * idf.get(qt, 1.0)
                matches += 1

        # Bonus for matching multiple query terms
        if len(query_tokens) > 1:
            coverage = matches / len(query_tokens)
            score *= (1.0 + coverage)

        # Bonus for chunk rerank score (from retrieval)
        chunk_score = chunk.get("score", 0)
        if chunk_score > 0:
            score *= (1.0 + chunk_score * 0.5)

        # Slight penalty for very short or very long sentences
        if len(sent) < 40:
            score *= 0.7
        elif len(sent) > 500:
            score *= 0.85

        if score > 0:
            scored.append((score, sent, src_idx, chunk))

    if not scored:
        # No query term matches; return top chunk excerpts
        parts = ["Based on the project documents:\n"]
        for i, chunk in enumerate(context_chunks[:3], 1):
            text = (chunk.get("text", "") or "").strip()[:400]
            fname = chunk.get("file_name", "Unknown")
            page = chunk.get("page_number", "?")
            parts.append(f"From **{fname}** (Page {page}) [Source {i}]:\n> {text}")
        return {
            "answer": "\n\n".join(parts),
            "model": "extractive",
        }

    # Select top sentences (deduplicated)
    scored.sort(key=lambda x: x[0], reverse=True)
    selected: list[tuple[str, int, dict]] = []
    seen_text: set[str] = set()
    for _, sent, src_idx, chunk in scored:
        normalized = sent.lower().strip()
        if normalized not in seen_text and len(selected) < 8:
            seen_text.add(normalized)
            selected.append((sent, src_idx, chunk))

    # Group by source for coherent presentation
    source_groups: dict[int, list[str]] = {}
    source_meta: dict[int, dict] = {}
    for sent, src_idx, chunk in selected:
        source_groups.setdefault(src_idx, []).append(sent)
        source_meta[src_idx] = chunk

    # Build answer
    parts = ["Based on the project documents:\n"]
    for src_idx in sorted(source_groups.keys()):
        chunk = source_meta[src_idx]
        fname = chunk.get("file_name", "Unknown")
        page = chunk.get("page_number", "?")
        sentences = source_groups[src_idx]
        combined = " ".join(sentences)
        parts.append(f"**{fname}** (Page {page}) [Source {src_idx}]: {combined}")

    return {
        "answer": "\n\n".join(parts),
        "model": "extractive",
    }


async def generate_answer(
    query: str,
    context_chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> dict:
    # If no API key is configured, use smart extractive Q&A
    if not _has_api_key():
        logger.info("No API key for '%s'; using extractive Q&A.", settings.LLM_PROVIDER)
        return _build_extractive_answer(query, context_chunks)

    provider = get_generator_provider()
    context = format_context(context_chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_history:
        for msg in chat_history[-6:]:  # last 3 turns
            messages.append({"role": msg["role"], "content": msg["content"]})

    user_message = f"""Based on the following project documents, answer this question:

Question: {query}

Project Documents:
{context}

Remember: Cite every claim with [Source N]. If evidence is insufficient, say so."""

    messages.append({"role": "user", "content": user_message})

    try:
        answer = await provider.chat_completion(messages, temperature=0.1, max_tokens=2000)
        if settings.LLM_PROVIDER == "anthropic":
            model_name = settings.ANTHROPIC_MODEL
        elif settings.LLM_PROVIDER == "groq":
            model_name = settings.GROQ_MODEL
        else:
            model_name = settings.LLM_MODEL
        return {
            "answer": answer,
            "model": model_name,
        }
    except Exception as e:
        logger.warning("LLM call failed (%s); falling back to extractive Q&A.", e)
        return _build_extractive_answer(query, context_chunks)
