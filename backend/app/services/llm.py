from __future__ import annotations

from typing import List

from app.core.config import settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


SYSTEM_PROMPT = (
    "You are a construction project intelligence assistant.\n"
    "You specialize in construction management workflows, terminology, trade coordination, RFIs, submittals, change orders,\n"
    "scheduling (CPM concepts), budgets, and contractual processes.\n\n"
    "Rules:\n"
    "- If the answer depends on project documents, cite them using the provided snippets.\n"
    "- Be concrete and action-oriented: suggest next steps, risks, and who should respond (architect/engineer/sub).\n"
    "- If information is missing, say what is missing and what document(s) to check.\n"
    "- Do NOT invent drawing references, spec sections, or code citations.\n"
)


def openai_available() -> bool:
    return bool(settings.OPENAI_API_KEY) and OpenAI is not None


def generate_with_openai(question: str, context_blocks: List[str]) -> str:
    if not openai_available():
        raise RuntimeError("OpenAI is not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    context = "\n\n".join(context_blocks).strip()
    user_prompt = (
        "Question:\n"
        f"{question}\n\n"
        "Relevant project document snippets:\n"
        f"{context}\n\n"
        "Answer in a clear, professional construction-management style."
    )
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def generate_fallback(question: str, context_blocks: List[str]) -> str:
    # A deterministic, local, non-LLM fallback.
    bullets = []
    for i, c in enumerate(context_blocks[:5], start=1):
        snippet = c.strip().replace("\n", " ")
        if len(snippet) > 280:
            snippet = snippet[:280].rstrip() + "..."
        bullets.append(f"{i}. {snippet}")
    context_part = "\n".join(bullets) if bullets else "(No relevant snippets found.)"

    return (
        "I do not have an LLM API key configured, so I am answering using document retrieval only.\n\n"
        "**Your question**\n"
        f"{question}\n\n"
        "**Most relevant document excerpts**\n"
        f"{context_part}\n\n"
        "**Suggested next steps**\n"
        "- If this is an RFI-type question: identify the impacted trade, confirm drawing/spec references, and decide who owns the response (A/E vs GC vs Sub).\n"
        "- Upload any missing specs/drawings that mention this scope so retrieval can find them next time.\n"
    )
