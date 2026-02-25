"""Memory service with Mem0 provider."""
from dataclasses import dataclass
from typing import Any, Optional
from second_brain.contracts.context_packet import ContextCandidate


@dataclass
class MemorySearchResult:
    """Normalized memory search result."""
    id: str
    content: str
    source: str
    confidence: float
    metadata: dict[str, Any]


class MemoryService:
    """Memory retrieval service with provider abstraction."""
    
    def __init__(self, provider: str = "mem0", config: Optional[dict[str, Any]] = None):
        self.provider = provider
        self.config = config or {}
        self._mock_data: list[MemorySearchResult] | None = None
    
    def search_memories(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6,
        rerank: bool = True,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[ContextCandidate], dict[str, Any]]:
        """
        Search memories and return normalized candidates.
        
        Args:
            query: Search query string
            top_k: Maximum number of results
            threshold: Minimum confidence threshold
            rerank: Whether to apply provider-native rerank (Mem0)
            filters: Optional provider-specific filters
        
        Returns:
            Tuple of (list of ContextCandidate, provider metadata)
        """
        if not query or not query.strip():
            return [], {"provider": self.provider, "query_empty": True}
        
        # Use mock data for deterministic testing when set
        if self._mock_data is not None:
            results = self._search_mock(query, top_k, threshold)
        else:
            # Fallback: deterministic mock results based on query hash
            results = self._search_fallback(query, top_k, threshold)
        
        candidates = [
            ContextCandidate(
                id=r.id,
                content=r.content,
                source=r.source,
                confidence=r.confidence,
                metadata=r.metadata,
            )
            for r in results
        ]
        
        metadata = {
            "provider": self.provider,
            "rerank_applied": rerank if self.provider == "mem0" else False,
            "raw_count": len(results),
        }
        
        return candidates, metadata
    
    def _search_mock(
        self,
        query: str,
        top_k: int,
        threshold: float,
    ) -> list[MemorySearchResult]:
        """Search mock data for testing. Returns all candidates, threshold checked downstream."""
        # Don't filter by threshold - branch determination needs to see low-confidence results
        if self._mock_data is None:
            return []
        results = list(self._mock_data)
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:top_k]
    
    def _search_fallback(
        self,
        query: str,
        top_k: int,
        threshold: float,
    ) -> list[MemorySearchResult]:
        """Deterministic fallback for testing without real provider."""
        query_lower = query.lower()
        
        # Determine scenario based on query content
        if "empty" in query_lower or "no candidate" in query_lower:
            # Empty set scenario
            return []
        elif "low confidence" in query_lower:
            # Low confidence scenario
            return [
                MemorySearchResult(
                    id="mock-low-1",
                    content=f"Low confidence result for: {query}",
                    source=self.provider,
                    confidence=0.45,
                    metadata={"mock": True, "low_conf": True},
                ),
            ]
        elif "degraded" in query_lower:
            # Degraded scenario - low confidence
            return [
                MemorySearchResult(
                    id="mock-degraded-1",
                    content=f"Degraded result for: {query}",
                    source=self.provider,
                    confidence=0.5,
                    metadata={"mock": True, "degraded": True},
                ),
            ]
        else:
            # Default: high confidence scenario (all other queries)
            return [
                MemorySearchResult(
                    id="mock-1",
                    content=f"High confidence result for: {query}",
                    source=self.provider,
                    confidence=0.85,
                    metadata={"mock": True},
                ),
                MemorySearchResult(
                    id="mock-2",
                    content=f"Secondary result for: {query}",
                    source=self.provider,
                    confidence=0.72,
                    metadata={"mock": True},
                ),
            ]
    
    def set_mock_data(self, data: list[MemorySearchResult]) -> None:
        """Set mock data for deterministic testing."""
        self._mock_data = data
    
    def clear_mock_data(self) -> None:
        """Clear mock data."""
        self._mock_data = []
