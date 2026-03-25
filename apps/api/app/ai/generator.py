"""Answer generation client — supports Anthropic (Claude), Groq, and OpenAI-compatible models."""
import logging
from app.ai.provider import OpenAICompatibleProvider, AnthropicProvider
from app.config import settings

logger = logging.getLogger(__name__)

_provider = None


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
                timeout=120.0,
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


def _build_fallback_answer(context_chunks: list[dict]) -> dict:
    """Return a formatted response using raw document excerpts (no LLM)."""
    if not context_chunks:
        return {
            "answer": "No relevant documents were found for your query.",
            "model": "none",
        }

    parts = ["Based on the project documents, here are the most relevant excerpts:\n"]
    for chunk in context_chunks:
        file_name = chunk.get("file_name", "Unknown Document")
        page = chunk.get("page_number", "?")
        text = (chunk.get("text", "") or "").strip()
        # Truncate very long chunks for readability
        snippet = text[:500] + ("..." if len(text) > 500 else "")
        parts.append(f"**From {file_name}, Page {page}:**\n> {snippet}\n")

    parts.append("Note: AI summarization is not available. Showing raw document excerpts.")
    return {
        "answer": "\n".join(parts),
        "model": "none",
    }


async def generate_answer(
    query: str,
    context_chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> dict:
    # If no API key is configured, skip the provider call entirely
    if not _has_api_key():
        logger.info("No API key configured for provider '%s'; returning raw excerpts.", settings.LLM_PROVIDER)
        return _build_fallback_answer(context_chunks)

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
        logger.warning("LLM call failed (%s); falling back to raw excerpts.", e)
        return _build_fallback_answer(context_chunks)
