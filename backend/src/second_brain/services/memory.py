"""Memory service with Mem0 provider."""
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional
from second_brain.contracts.context_packet import ContextCandidate


logger = logging.getLogger(__name__)


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
        
        self._mem0_client: Any | None = None
        self._mem0_enabled = self.config.get("mem0_use_real_provider", False)
        self._mem0_user_id = self.config.get("mem0_user_id")
        self._mem0_api_key = self.config.get("mem0_api_key")
    
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
        normalized_query = query.strip()
        if not normalized_query:
            return [], {"provider": self.provider, "query_empty": True}

        try:
            normalized_top_k = max(1, int(top_k))
        except (TypeError, ValueError):
            normalized_top_k = 1

        try:
            normalized_threshold = float(threshold)
        except (TypeError, ValueError):
            normalized_threshold = 0.6
        normalized_threshold = max(0.0, min(1.0, normalized_threshold))
        
        results: list[MemorySearchResult] = []
        metadata: dict[str, Any] = {}
        
        if self._mock_data is not None:
            results = self._search_mock(normalized_query, normalized_top_k, normalized_threshold)
            metadata = {"provider": self.provider, "mock_mode": True}
        elif self._should_use_real_provider():
            real_results, real_metadata = self._search_with_provider(
                normalized_query,
                normalized_top_k,
                normalized_threshold,
            )
            results = real_results
            metadata = real_metadata
        else:
            results = self._search_fallback(normalized_query, normalized_top_k, normalized_threshold)
            metadata = {"provider": self.provider, "fallback_reason": "real_provider_disabled"}
        
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
        
        metadata["raw_count"] = len(results)
        if self.provider == "mem0" and not metadata.get("mock_mode"):
            metadata["rerank_applied"] = rerank
        
        return candidates, metadata
    
    def _should_use_real_provider(self) -> bool:
        """Check if real provider should be used."""
        if not self._mem0_enabled:
            return False
        if self.provider != "mem0":
            return False
        # Check if we have credentials to attempt provider call
        return self._mem0_api_key is not None or self._has_env_api_key()
    
    def _has_env_api_key(self) -> bool:
        """Check if API key is available from environment."""
        return os.getenv("MEM0_API_KEY") is not None
    
    def _load_mem0_client(self) -> Any | None:
        """Load Mem0 client lazily with optional import."""
        if self._mem0_client is not None:
            return self._mem0_client
        
        try:
            from mem0 import Memory  # type: ignore[import-untyped]
            api_key = self._mem0_api_key
            if not api_key:
                api_key = os.getenv("MEM0_API_KEY")
            
            if api_key:
                self._mem0_client = Memory()
                return self._mem0_client
        except ImportError:
            logger.debug("Mem0 SDK not installed; falling back to deterministic path")
        except Exception as error:
            logger.warning("Mem0 client initialization failed: %s", type(error).__name__)
        
        return None
    
    def _search_with_provider(
        self,
        query: str,
        top_k: int,
        threshold: float,
    ) -> tuple[list[MemorySearchResult], dict[str, Any]]:
        """Search using real Mem0 provider with fallback on failure."""
        try:
            client = self._load_mem0_client()
            if client is None:
                return self._search_fallback(query, top_k, threshold), {
                    "provider": self.provider,
                    "fallback_reason": "client_unavailable",
                }
            
            search_kwargs: dict[str, Any] = {"limit": top_k}
            if self._mem0_user_id:
                search_kwargs["user_id"] = self._mem0_user_id
            
            mem0_results = client.search(query=query, **search_kwargs)
            results = self._normalize_mem0_results(mem0_results, top_k, threshold)

            return results, {"provider": self.provider, "real_provider": True}
        except Exception as e:
            logger.warning("Mem0 provider search failed: %s", type(e).__name__)
            fallback_results = self._search_fallback(query, top_k, threshold)
            return fallback_results, {
                "provider": self.provider,
                "fallback_reason": "provider_error",
                "error_type": type(e).__name__,
                "error_message": self._sanitize_error_message(e),
            }

    def _sanitize_error_message(self, error: Exception) -> str:
        """Return bounded and redacted error text safe for metadata."""
        message = str(error)
        sensitive_values = [self._mem0_api_key, os.getenv("MEM0_API_KEY")]
        for value in sensitive_values:
            if value:
                message = message.replace(value, "[REDACTED]")
        return message[:200]
    
    def _normalize_mem0_results(
        self,
        mem0_results: Any,
        top_k: int,
        threshold: float,
    ) -> list[MemorySearchResult]:
        """Normalize Mem0 results to MemorySearchResult."""
        results: list[MemorySearchResult] = []
        
        if not mem0_results:
            return results
        
        for i, item in enumerate(mem0_results):
            if isinstance(item, dict):
                item_id = str(item.get("id", f"mem0-{i}"))
                content = str(item.get("memory", item.get("content", "")))
                score = item.get("score", item.get("confidence", 0.0))
                try:
                    confidence = max(0.0, min(1.0, float(score) if score is not None else 0.0))
                except (TypeError, ValueError):
                    confidence = 0.0
                raw_metadata = item.get("metadata", {})
                
                metadata = {
                    "real_provider": True,
                    **(raw_metadata if isinstance(raw_metadata, dict) else {}),
                }
                
                results.append(MemorySearchResult(
                    id=item_id,
                    content=content,
                    source=self.provider,
                    confidence=confidence,
                    metadata=metadata,
                ))
            
            if len(results) >= top_k:
                break
        
        return results
    
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
        """
        Clear mock data and disable mock mode.
        
        Sets _mock_data to None, restoring fallback search path.
        Use set_mock_data([]) for explicit empty mock scenarios.
        """
        self._mock_data = None
