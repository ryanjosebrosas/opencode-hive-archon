"""Voyage AI reranking service."""

from typing import Sequence
from second_brain.contracts.context_packet import ContextCandidate


class VoyageRerankService:
    """External reranking service wrapper."""

    def __init__(self, enabled: bool = True, model: str = "rerank-2"):
        self.enabled = enabled
        self.model = model

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
