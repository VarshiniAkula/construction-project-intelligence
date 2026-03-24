"""Answer generation client — supports Anthropic (Claude) and OpenAI-compatible models."""
import json
from app.ai.provider import OpenAICompatibleProvider, AnthropicProvider
from app.config import settings

_provider = None


def get_generator_provider():
    global _provider
    if _provider is None:
        if settings.LLM_PROVIDER == "anthropic":
            _provider = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_MODEL,
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


async def generate_answer(
    query: str,
    context_chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> dict:
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
        model_name = settings.ANTHROPIC_MODEL if settings.LLM_PROVIDER == "anthropic" else settings.LLM_MODEL
        return {
            "answer": answer,
            "model": model_name,
        }
    except Exception as e:
        return {
            "answer": "I'm unable to generate an answer at this time. The language model service returned an error. Please try again later.",
            "model": "error",
            "error": str(e),
        }
