"""Vision model client for document page understanding — supports Anthropic and OpenAI-compatible."""
import base64
from app.ai.provider import OpenAICompatibleProvider, AnthropicProvider
from app.config import settings

_provider = None


def get_vlm_provider():
    global _provider
    if _provider is None:
        if settings.LLM_PROVIDER == "anthropic":
            _provider = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model=settings.ANTHROPIC_VISION_MODEL,
                timeout=180.0,
            )
        else:
            _provider = OpenAICompatibleProvider(
                base_url=settings.VLM_BASE_URL,
                api_key=settings.VLM_API_KEY,
                model=settings.VLM_MODEL,
                timeout=180.0,
            )
    return _provider


VLM_SYSTEM_PROMPT = """You are a construction document analysis assistant. Analyze the provided page image and extract:
1. Page type (drawing, specification, schedule, table, form, text, photo)
2. Title or heading
3. Key content summary (2-3 sentences)
4. Any detected metadata: sheet number, revision, date, trade/discipline
5. Important entities: companies, people, locations, materials, specifications referenced
6. If it's a table, extract key rows/columns as structured data

Return your analysis as JSON with keys: page_type, title, summary, metadata, entities, table_data (if applicable)."""


async def analyze_page(image_bytes: bytes, raw_text: str = "") -> dict:
    provider = get_vlm_provider()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Both providers accept OpenAI-style messages; AnthropicProvider
    # converts image_url format to Anthropic's source format internally.
    messages = [
        {"role": "system", "content": VLM_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                },
                {
                    "type": "text",
                    "text": f"Analyze this construction document page. OCR text (if available): {raw_text[:2000]}" if raw_text else "Analyze this construction document page.",
                },
            ],
        },
    ]

    try:
        response = await provider.chat_completion(messages, temperature=0.1, max_tokens=2000)
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"summary": response, "page_type": "text", "title": "", "metadata": {}, "entities": []}
    except Exception as e:
        return {"summary": f"VLM analysis unavailable: {str(e)}", "page_type": "unknown", "title": "", "metadata": {}, "entities": []}
