"""AI provider adapters — supports OpenAI-compatible and Anthropic APIs."""
import httpx
import logging

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat_completion(self, messages: list[dict], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "messages": messages,
                **kwargs,
            }
            try:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                raise

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "input": texts,
            }
            try:
                resp = await client.post(
                    f"{self.base_url}/embeddings",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return [item["embedding"] for item in data["data"]]
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                raise

    async def rerank(self, query: str, documents: list[str]) -> list[dict]:
        """Call reranker endpoint. Returns list of {index, score}."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model,
                "query": query,
                "documents": documents,
            }
            try:
                # Try standard rerank endpoint
                resp = await client.post(
                    f"{self.base_url}/rerank",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", data.get("data", []))
            except httpx.HTTPStatusError:
                # Fallback: use chat completion for scoring
                logger.warning("Rerank endpoint not available, using fallback scoring")
                return [{"index": i, "relevance_score": 1.0 / (i + 1)} for i in range(len(documents))]


class AnthropicProvider:
    """Provider for Anthropic's Messages API (Claude models)."""

    def __init__(self, api_key: str, model: str, timeout: float = 120.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com"

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    async def chat_completion(self, messages: list[dict], **kwargs) -> str:
        """Send a chat completion using Anthropic Messages API.

        Accepts OpenAI-style messages (with 'system' role) and converts them
        to Anthropic format (system as top-level param).
        """
        # Extract system message
        system_text = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            else:
                user_messages.append(self._convert_message(msg))

        # Map OpenAI kwargs to Anthropic params
        max_tokens = kwargs.pop("max_tokens", 4096)
        temperature = kwargs.pop("temperature", 0.1)

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": user_messages,
            "temperature": temperature,
        }
        if system_text.strip():
            payload["system"] = system_text.strip()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/v1/messages",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                # Anthropic returns content as a list of blocks
                return "".join(
                    block["text"] for block in data["content"] if block["type"] == "text"
                )
            except Exception as e:
                logger.error(f"Anthropic chat completion error: {e}")
                raise

    def _convert_message(self, msg: dict) -> dict:
        """Convert an OpenAI-style message to Anthropic format.

        Handles text-only and multimodal (vision) messages.
        """
        content = msg.get("content", "")

        # Simple text message
        if isinstance(content, str):
            return {"role": msg["role"], "content": content}

        # Multimodal message (list of content blocks)
        anthropic_content = []
        for block in content:
            if block["type"] == "text":
                anthropic_content.append({"type": "text", "text": block["text"]})
            elif block["type"] == "image_url":
                # Convert OpenAI image_url format to Anthropic source format
                url = block["image_url"]["url"]
                if url.startswith("data:"):
                    # Parse data URI: data:image/png;base64,<data>
                    header, b64_data = url.split(",", 1)
                    media_type = header.split(":")[1].split(";")[0]
                    anthropic_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    })
                else:
                    # URL-based image
                    anthropic_content.append({
                        "type": "image",
                        "source": {
                            "type": "url",
                            "url": url,
                        },
                    })

        return {"role": msg["role"], "content": anthropic_content}

    async def rerank(self, query: str, documents: list[str]) -> list[dict]:
        """Anthropic has no rerank API — use fallback scoring."""
        logger.info("Anthropic does not support reranking, using fallback scoring")
        return [{"index": i, "relevance_score": 1.0 / (i + 1)} for i in range(len(documents))]
