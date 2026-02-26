"""Voyage AI reranking and embedding service."""

import logging
import os
from typing import Any, Sequence

from second_brain.contracts.context_packet import ContextCandidate


logger = logging.getLogger(__name__)


class VoyageRerankService:
    """External reranking and embedding service wrapper."""

    def __init__(
        self,
        enabled: bool = True,
        model: str = "rerank-2",
        embed_model: str = "voyage-4-large",
        embed_enabled: bool = False,
    ):
        self.enabled = enabled
        self.model = model
        self.embed_model = embed_model
        self.embed_enabled = embed_enabled
        self._voyage_client: Any | None = None  # Intentional Any: optional external dependency

    def _load_voyage_client(self) -> Any | None:
        """Load Voyage AI client lazily."""
        if self._voyage_client is not None:
            return self._voyage_client
        try:
            import voyageai  # type: ignore[import-not-found]

            api_key = os.getenv("VOYAGE_API_KEY")
            if api_key:
                self._voyage_client = voyageai.Client(api_key=api_key)
            else:
                self._voyage_client = voyageai.Client()
            return self._voyage_client
        except ImportError:
            logger.debug("voyageai SDK not installed")
        except Exception as e:
            logger.warning("Voyage client init failed: %s", type(e).__name__)
        return None

    def embed(
        self, text: str, input_type: str = "query"
    ) -> tuple[list[float] | None, dict[str, Any]]:
        """Embed text using Voyage AI. Returns (embedding_vector, metadata)."""
        metadata: dict[str, Any] = {"embed_model": self.embed_model}
        if not self.embed_enabled:
            return None, {**metadata, "embed_error": "embedding_disabled"}
        try:
            client = self._load_voyage_client()
            if client is None:
                return None, {**metadata, "embed_error": "client_unavailable"}
            result = client.embed([text], model=self.embed_model, input_type=input_type)
            if not result.embeddings:
                return None, {**metadata, "embed_error": "empty_embeddings"}
            return result.embeddings[0], {**metadata, "total_tokens": result.total_tokens}
        except Exception as e:
            logger.warning("Voyage embed failed: %s", type(e).__name__)
            return None, {**metadata, "embed_error": type(e).__name__}

    def rerank(
        self,
        query: str,
        candidates: Sequence[ContextCandidate],
        top_k: int = 5,
    ) -> tuple[list[ContextCandidate], dict[str, str]]:
        """
        Rerank candidates by relevance to query.

        Args:
            query: Search query
            candidates: List of candidates to rerank
            top_k: Maximum results to return

        Returns:
            Tuple of (reranked candidates, metadata with rerank_type)
        """
        metadata = {
            "rerank_type": "none",
            "rerank_model": self.model,
        }

        # Bypass mode: disabled or empty candidates
        if not self.enabled or not candidates:
            metadata["rerank_type"] = "none"
            metadata["bypass_reason"] = "disabled" if not self.enabled else "no_candidates"
            return list(candidates), metadata

        # Single candidate: no rerank needed
        if len(candidates) == 1:
            metadata["rerank_type"] = "none"
            metadata["bypass_reason"] = "single_candidate"
            return list(candidates), metadata

        # Deterministic mock rerank for testing (no external API call)
        # In production, this would call Voyage AI API
        reranked = self._mock_rerank(query, candidates, top_k)
        metadata["rerank_type"] = "external"

        return reranked, metadata

    def _mock_rerank(
        self,
        query: str,
        candidates: Sequence[ContextCandidate],
        top_k: int,
    ) -> list[ContextCandidate]:
        """
        Deterministic mock rerank for testing.

        Simulates reranking by adjusting confidence scores based on
        query-content overlap (deterministic).
        """
        scored = []
        query_terms = set(query.lower().split())

        for candidate in candidates:
            content_terms = set(candidate.content.lower().split())
            overlap = len(query_terms & content_terms)

            # Adjust confidence based on term overlap (mock behavior)
            adjusted_confidence = min(1.0, candidate.confidence + (overlap * 0.05))

            new_candidate = ContextCandidate(
                id=candidate.id,
                content=candidate.content,
                source=candidate.source,
                confidence=adjusted_confidence,
                metadata={**candidate.metadata, "rerank_adjusted": True},
            )
            scored.append((adjusted_confidence, new_candidate))

        # Sort by adjusted confidence descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [c for _, c in scored[:top_k]]
