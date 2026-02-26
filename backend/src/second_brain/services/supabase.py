"""Supabase pgvector memory provider."""

import logging
import os
from typing import Any, Optional

from second_brain.services.memory import MemorySearchResult


logger = logging.getLogger(__name__)

_VALID_KNOWLEDGE_TYPES = {
    "note",
    "document",
    "decision",
    "conversation",
    "task",
    "signal",
    "playbook",
    "case_study",
    "transcript",
}

_VALID_SOURCE_ORIGINS = {
    "notion",
    "obsidian",
    "email",
    "manual",
    "youtube",
    "web",
    "other",
}


class SupabaseProvider:
    """Supabase pgvector search provider."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self._client: Any | None = None  # Intentional Any: optional external dependency
        self._supabase_url = self.config.get("supabase_url") or os.getenv("SUPABASE_URL")
        self._supabase_key = self.config.get("supabase_key") or os.getenv("SUPABASE_KEY")

    def _load_client(self) -> Any | None:
        """Load Supabase client lazily."""
        if self._client is not None:
            return self._client
        try:
            from supabase import create_client

            if not self._supabase_url or not self._supabase_key:
                logger.debug("Supabase credentials not configured")
                return None
            self._client = create_client(self._supabase_url, self._supabase_key)
            return self._client
        except ImportError:
            logger.debug("supabase SDK not installed")
        except Exception as e:
            logger.warning("Supabase client init failed: %s", type(e).__name__)
        return None

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float = 0.6,
        filter_type: str | None = None,
    ) -> tuple[list[MemorySearchResult], dict[str, Any]]:
        """Search using Supabase pgvector. Returns (results, metadata)."""
        metadata: dict[str, Any] = {"provider": "supabase"}
        try:
            client = self._load_client()
            if client is None:
                return [], {**metadata, "fallback_reason": "client_unavailable"}
            response = client.rpc(
                "match_knowledge_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                    "match_threshold": threshold,
                    "filter_type": filter_type,
                },
            ).execute()
            results = self._normalize_results(response.data or [], top_k)
            return results, {
                **metadata,
                "real_provider": True,
                "raw_count": len(response.data or []),
            }
        except Exception as e:
            logger.warning("Supabase search failed: %s", type(e).__name__)
            return [], {
                **metadata,
                "fallback_reason": "provider_error",
                "error_type": type(e).__name__,
                "error_message": self._sanitize_error_message(e),
            }

    def _normalize_results(
        self,
        rpc_results: list[dict[str, Any]],
        top_k: int,
    ) -> list[MemorySearchResult]:
        """Normalize match_knowledge_chunks RPC results to MemorySearchResult."""
        results: list[MemorySearchResult] = []

        if not rpc_results:
            return results

        for i, row in enumerate(rpc_results):
            similarity = row.get("similarity", 0.0)
            try:
                confidence = max(0.0, min(1.0, float(similarity)))
            except (TypeError, ValueError):
                confidence = 0.0

            # Read from real columns — not nested metadata blob
            content = str(row.get("content", ""))
            raw_knowledge_type = str(row.get("knowledge_type", "document"))
            knowledge_type = (
                raw_knowledge_type if raw_knowledge_type in _VALID_KNOWLEDGE_TYPES else "document"
            )
            document_id = row.get("document_id")
            chunk_index_raw = row.get("chunk_index", 0)
            try:
                chunk_index = int(chunk_index_raw)
            except (TypeError, ValueError):
                chunk_index = 0
            raw_source_origin = str(row.get("source_origin", "manual"))
            source_origin = (
                raw_source_origin if raw_source_origin in _VALID_SOURCE_ORIGINS else "manual"
            )

            # Preserve any extra jsonb metadata from the row
            extra_metadata = row.get("metadata", {})
            if not isinstance(extra_metadata, dict):
                extra_metadata = {}

            results.append(
                MemorySearchResult(
                    id=str(row.get("id", f"supa-{i}")),
                    content=content,
                    source="supabase",
                    confidence=confidence,
                    metadata={
                        **extra_metadata,
                        "real_provider": True,
                        "knowledge_type": knowledge_type,
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "source_origin": source_origin,
                    },
                )
            )

            if len(results) >= top_k:
                break

        return results

    def _sanitize_error_message(self, error: Exception) -> str:
        """Return bounded and redacted error text safe for metadata."""
        message = str(error)
        for value in [self._supabase_url, self._supabase_key]:
            if value:
                message = message.replace(value, "[REDACTED]")
        return message[:200]
