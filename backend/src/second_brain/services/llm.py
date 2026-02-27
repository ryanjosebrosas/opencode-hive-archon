"""LLM synthesis service via Ollama REST API."""

import os
from typing import Any

from second_brain.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3-coder-next"


class OllamaLLMService:
    """LLM synthesis via Ollama (local or cloud) REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url: str = base_url or os.getenv("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL
        self.model: str = model or os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
        self._client: Any | None = None

    def _load_client(self) -> Any | None:
        """Load httpx client lazily."""
        if self._client is not None:
            return self._client
        try:
            import httpx

            self._client = httpx.Client(base_url=self.base_url, timeout=120.0)
            return self._client
        except ImportError:
            logger.debug("httpx not installed")
        except Exception as e:
            logger.warning("httpx client init failed: %s", type(e).__name__)
        return None

    def synthesize(
        self,
        query: str,
        context_candidates: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Generate a synthesis response from retrieved context.

        Args:
            query: The user's original question
            context_candidates: Retrieved context chunks with content and metadata
            system_prompt: Optional custom system prompt

        Returns:
            Tuple of (response_text, metadata)
        """
        metadata: dict[str, Any] = {
            "llm_provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
        }

        client = self._load_client()
        if client is None:
            return self._fallback_response(query, context_candidates), {
                **metadata,
                "fallback": True,
                "reason": "client_unavailable",
            }

        context_block = self._build_context_block(context_candidates)

        default_system = (
            "You are a personal knowledge assistant. Answer the user's question "
            "using ONLY the provided context from their notes. Be specific, cite "
            "which note the information comes from when possible. If the context "
            "doesn't contain enough information to answer, say so honestly."
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt or default_system,
            },
            {
                "role": "user",
                "content": f"Context from your notes:\n\n{context_block}\n\nQuestion: {query}",
            },
        ]

        try:
            response = client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("message", {}).get("content", "")
            if not answer:
                return self._fallback_response(query, context_candidates), {
                    **metadata,
                    "fallback": True,
                    "reason": "empty_response",
                }
            metadata["total_duration"] = data.get("total_duration")
            metadata["eval_count"] = data.get("eval_count")
            return answer, metadata
        except Exception as e:
            logger.warning(
                "Ollama synthesis failed: %s — %s",
                type(e).__name__,
                str(e)[:200],
            )
            return self._fallback_response(query, context_candidates), {
                **metadata,
                "fallback": True,
                "reason": type(e).__name__,
            }

    def _build_context_block(self, candidates: list[dict[str, Any]]) -> str:
        """Format context candidates into a readable block for the LLM."""
        if not candidates:
            return "(No relevant context found in your notes.)"
        parts = []
        for i, c in enumerate(candidates, 1):
            source = c.get("source", "unknown")
            content = c.get("content", "")
            confidence = c.get("confidence", 0.0)
            doc_id = c.get("metadata", {}).get("document_id", "")
            header = f"[{i}] (source: {source}, confidence: {confidence:.2f}"
            if doc_id:
                header += f", doc: {doc_id}"
            header += ")"
            parts.append(f"{header}\n{content}")
        return "\n\n---\n\n".join(parts)

    def _fallback_response(
        self,
        query: str,
        candidates: list[dict[str, Any]],
    ) -> str:
        """Generate a non-LLM fallback when Ollama is unavailable."""
        if not candidates:
            return "I couldn't find relevant context for your query and the LLM is unavailable."
        context_parts = []
        for i, c in enumerate(candidates[:3], 1):
            content = c.get("content", "")
            if len(content) > 300:
                content = content[:300] + "..."
            context_parts.append(f"[{i}] {content}")
        return "(LLM unavailable — showing raw retrieved context)\n\n" + "\n\n".join(context_parts)

    def health_check(self) -> bool:
        """Check if Ollama is reachable."""
        client = self._load_client()
        if client is None:
            return False
        try:
            resp = client.get("/api/tags")
            return int(getattr(resp, "status_code", 0)) == 200
        except Exception:
            return False
