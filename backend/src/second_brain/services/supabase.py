"""Supabase pgvector memory provider."""

import os
from typing import Any, Optional, get_args

from second_brain.contracts.knowledge import SourceOriginValue, KnowledgeTypeValue
from second_brain.logging_config import get_logger
from second_brain.services.memory import MemorySearchResult

logger = get_logger(__name__)

_VALID_KNOWLEDGE_TYPES = set(get_args(KnowledgeTypeValue))
_VALID_SOURCE_ORIGINS = set(get_args(SourceOriginValue))

# Parameter validation constants
_MAX_TOP_K = 100
_MIN_TOP_K = 1
_MAX_WEIGHT = 100.0
_MIN_WEIGHT = 0.0
_MAX_THRESHOLD = 1.0
_MIN_THRESHOLD = 0.0
_MAX_RESULTS_LIMIT = 1000


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
        # Validate parameters
        if not isinstance(query_embedding, list):
            raise TypeError("query_embedding must be a list")
        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")
        if not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number")
        
        # Clamp top_k to valid range
        top_k = max(_MIN_TOP_K, min(_MAX_TOP_K, top_k))
        
        # Validate and clamp threshold
        if threshold < _MIN_THRESHOLD or threshold > _MAX_THRESHOLD:
            logger.warning(
                "threshold %s out of range [%s, %s], clamping",
                threshold, _MIN_THRESHOLD, _MAX_THRESHOLD,
            )
        threshold = max(_MIN_THRESHOLD, min(_MAX_THRESHOLD, float(threshold)))
        
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

        # Apply top_k limit early before processing
        top_k = max(_MIN_TOP_K, min(_MAX_TOP_K, top_k))

        # Limit input size to prevent memory issues
        if len(rpc_results) > _MAX_RESULTS_LIMIT:
            logger.warning(
                "Truncating %d results to maximum limit %d",
                len(rpc_results), _MAX_RESULTS_LIMIT,
            )
            # Limit to top_k first, then limit by _MAX_RESULTS_LIMIT if needed
            rpc_results = rpc_results[:_MAX_RESULTS_LIMIT]

        for i, row in enumerate(rpc_results):
            # Validate that row is actually a dictionary before accessing it
            if not isinstance(row, dict):
                logger.warning("Skipping non-dict row at index %d", i)
                continue

            similarity = row.get("similarity", 0.0)
            try:
                confidence = max(0.0, min(1.0, float(similarity)))
            except (TypeError, ValueError):
                logger.warning("Invalid similarity value %s, using 0.0", similarity)
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
                # Ensure chunk_index is non-negative with bounds checking
                chunk_index = max(0, chunk_index)
            except (TypeError, ValueError):
                logger.warning("Invalid chunk_index value %s, using 0", chunk_index_raw)
                chunk_index = 0
                
            raw_source_origin = str(row.get("source_origin", "manual"))
            source_origin = (
                raw_source_origin if raw_source_origin in _VALID_SOURCE_ORIGINS else "manual"
            )

            # Preserve any extra jsonb metadata from the row
            extra_metadata = row.get("metadata", {})
            if not isinstance(extra_metadata, dict):
                logger.warning("Non-dict metadata found at index %d, using empty dict", i)
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
        
        # Redact sensitive configuration data
        for value in [self._supabase_url, self._supabase_key]:
            if value:
                message = message.replace(value, "[REDACTED]")
        
        # Redact common sensitive patterns with improved regex
        import re
        # Redact API keys that follow common formats
        message = re.sub(r"[sS][kK]_[a-zA-Z0-9]{32,}", "[REDACTED_KEY]", message)
        message = re.sub(r"sbp_[a-zA-Z0-9]{48}", "[REDACTED_KEY]", message)
        message = re.sub(r"[a-zA-Z0-9]{32}\.[a-zA-Z0-9]{16}", "[REDACTED_TOKEN]", message)
        
        # Redact URLs to private resources
        message = re.sub(
            r"https://[a-z0-9-]{10,}\.supabase\.co",
            "[REDACTED_URL]",
            message,
        )
        
        # Redact potential database connection strings
        message = re.sub(r"postgresql[s]?://[^\"\s\']*[\s\']?", "[REDACTED_CONNECTION]", message)
        
        # Remove potential internal paths or stack traces
        message = re.sub(r"File \"[^\"]+\"", "File [REDACTED]", message)
        message = re.sub(r"\s+line\s+\d+,?\s*", " line [REDACTED] ", message)
        
        # Limit to 150 characters total to prevent large error messages
        limited_message = message[:150]
        
        # Return only the first line to avoid multi-line stack traces
        first_line = limited_message.split("\n")[0]
        return first_line

    def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.0,
        vector_weight: float = 1.0,
        text_weight: float = 1.0,
        filter_type: str | None = None,
        search_mode: str = "websearch",
    ) -> tuple[list[MemorySearchResult], dict[str, Any]]:
        """Hybrid search combining vector similarity + full-text (RRF).

        Uses the hybrid_search_knowledge_chunks RPC which performs Reciprocal Rank
        Fusion server-side. Returns (results, metadata).
        """
        # Validate required parameters
        if not isinstance(query_embedding, list):
            raise TypeError("query_embedding must be a list")
        if not isinstance(query_text, str):
            raise TypeError("query_text must be a string")
        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")
        if not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number")
        if not isinstance(vector_weight, (int, float)):
            raise TypeError("vector_weight must be a number")
        if not isinstance(text_weight, (int, float)):
            raise TypeError("text_weight must be a number")
        
        # Check if query_text is empty before proceeding with expensive operations
        stripped_query_text = query_text.strip()
        if not stripped_query_text:
            # Early exit for empty query_text
            return [], {"provider": "supabase", "mode": "hybrid", "fallback_reason": "empty_query"}
        
        # Clamp top_k to valid range
        top_k = max(_MIN_TOP_K, min(_MAX_TOP_K, top_k))
        
        # Validate and clamp threshold
        if threshold < _MIN_THRESHOLD or threshold > _MAX_THRESHOLD:
            logger.warning(
                "threshold %s out of range [%s, %s], clamping",
                threshold, _MIN_THRESHOLD, _MAX_THRESHOLD,
            )
        threshold = max(_MIN_THRESHOLD, min(_MAX_THRESHOLD, float(threshold)))
        
        # Validate and clamp weights
        if vector_weight < _MIN_WEIGHT or vector_weight > _MAX_WEIGHT:
            logger.warning(
                "vector_weight %s out of range [%s, %s], clamping",
                vector_weight, _MIN_WEIGHT, _MAX_WEIGHT,
            )
        vector_weight = max(_MIN_WEIGHT, min(_MAX_WEIGHT, float(vector_weight)))
        
        if text_weight < _MIN_WEIGHT or text_weight > _MAX_WEIGHT:
            logger.warning(
                "text_weight %s out of range [%s, %s], clamping",
                text_weight, _MIN_WEIGHT, _MAX_WEIGHT,
            )
        text_weight = max(_MIN_WEIGHT, min(_MAX_WEIGHT, float(text_weight)))
        
        metadata: dict[str, Any] = {"provider": "supabase", "mode": "hybrid"}
        try:
            client = self._load_client()
            if client is None:
                return [], {**metadata, "fallback_reason": "client_unavailable"}
            response = client.rpc(
                "hybrid_search_knowledge_chunks",
                {
                    "query_embedding": query_embedding,
                    "query_text": query_text,
                    "match_count": top_k,
                    "match_threshold": threshold,
                    "vector_weight": vector_weight,
                    "text_weight": text_weight,
                    "filter_type": filter_type,
                    "search_mode": search_mode,
                },
            ).execute()
            results = self._normalize_hybrid_results(response.data or [], top_k)
            return results, {
                **metadata,
                "real_provider": True,
                "raw_count": len(response.data or []),
            }
        except Exception as e:
            logger.warning("Supabase hybrid search failed: %s", type(e).__name__)
            return [], {
                **metadata,
                "fallback_reason": "provider_error",
                "error_type": type(e).__name__,
                "error_message": self._sanitize_error_message(e),
            }

    def _normalize_hybrid_results(
        self,
        rpc_results: list[dict[str, Any]],
        top_k: int,
    ) -> list[MemorySearchResult]:
        """Normalize hybrid_search_knowledge_chunks RPC results to MemorySearchResult."""
        results: list[MemorySearchResult] = []

        if not rpc_results:
            return results

        # Apply top_k limit early before processing
        top_k = max(_MIN_TOP_K, min(_MAX_TOP_K, top_k))

        # Limit input size to prevent memory issues
        if len(rpc_results) > _MAX_RESULTS_LIMIT:
            logger.warning(
                "Truncating %d results to maximum limit %d",
                len(rpc_results), _MAX_RESULTS_LIMIT,
            )
            # Limit to top_k first, then limit by _MAX_RESULTS_LIMIT if needed
            rpc_results = rpc_results[:_MAX_RESULTS_LIMIT]

        for i, row in enumerate(rpc_results):
            # Validate that row is actually a dictionary before accessing it
            if not isinstance(row, dict):
                logger.warning("Skipping non-dict row at index %d", i)
                continue

            rrf_score = row.get("rrf_score", 0.0)
            try:
                confidence = max(0.0, min(1.0, float(rrf_score)))
            except (TypeError, ValueError):
                logger.warning("Invalid rrf_score value %s, using 0.0", rrf_score)
                confidence = 0.0

            content = str(row.get("content", ""))
            raw_knowledge_type = str(row.get("knowledge_type", "document"))
            knowledge_type = (
                raw_knowledge_type if raw_knowledge_type in _VALID_KNOWLEDGE_TYPES else "document"
            )
            document_id = row.get("document_id")
            
            chunk_index_raw = row.get("chunk_index", 0)
            try:
                chunk_index = int(chunk_index_raw)
                # Ensure chunk_index is non-negative with bounds checking
                chunk_index = max(0, chunk_index)
            except (TypeError, ValueError):
                logger.warning("Invalid chunk_index value %s, using 0", chunk_index_raw)
                chunk_index = 0
                
            raw_source_origin = str(row.get("source_origin", "manual"))
            source_origin = (
                raw_source_origin if raw_source_origin in _VALID_SOURCE_ORIGINS else "manual"
            )

            extra_metadata = row.get("metadata", {})
            if not isinstance(extra_metadata, dict):
                logger.warning("Non-dict metadata found at index %d, using empty dict", i)
                extra_metadata = {}

            vector_rank = row.get("vector_rank")
            text_rank = row.get("text_rank")

            results.append(
                MemorySearchResult(
                    id=str(row.get("id", f"supa-hybrid-{i}")),
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
                        "vector_rank": vector_rank,
                        "text_rank": text_rank,
                        "rrf_score": rrf_score,
                    },
                )
            )

            if len(results) >= top_k:
                break

        return results

    def fuzzy_search_entities(
        self,
        search_term: str,
        top_k: int = 10,
        threshold: float = 0.3,
        filter_type: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Fuzzy entity search using pg_trgm trigram similarity.

        Returns (results, metadata). Results are raw dicts with id, name,
        entity_type, description, similarity.
        """
        # Validate required parameters
        if not isinstance(search_term, str):
            raise TypeError("search_term must be a string")
        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")
        if not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number")
        
        # Check if search_term is empty before proceeding
        stripped = search_term.strip()
        if not stripped:
            return [], {"provider": "supabase", "mode": "fuzzy_entity", "fallback_reason": "empty_query"}
        
        # Clamp top_k to valid range
        top_k = max(_MIN_TOP_K, min(_MAX_TOP_K, top_k))
        
        # Validate and clamp threshold
        if threshold < _MIN_THRESHOLD or threshold > _MAX_THRESHOLD:
            logger.warning(
                "threshold %s out of range [%s, %s], clamping",
                threshold, _MIN_THRESHOLD, _MAX_THRESHOLD,
            )
        clamped_threshold = max(_MIN_THRESHOLD, min(_MAX_THRESHOLD, float(threshold)))
        
        metadata: dict[str, Any] = {"provider": "supabase", "mode": "fuzzy_entity"}
        try:
            client = self._load_client()
            if client is None:
                return [], {**metadata, "fallback_reason": "client_unavailable"}
            response = client.rpc(
                "search_knowledge_entities_fuzzy",
                {
                    "search_term": stripped,
                    "similarity_threshold": clamped_threshold,
                    "match_count": top_k,
                    "filter_type": filter_type,
                },
            ).execute()
            results: list[dict[str, Any]] = response.data or []
            return results, {
                **metadata,
                "real_provider": True,
                "raw_count": len(results),
            }
        except Exception as e:
            logger.warning("Supabase fuzzy entity search failed: %s", type(e).__name__)
            return [], {
                **metadata,
                "fallback_reason": "provider_error",
                "error_type": type(e).__name__,
                "error_message": self._sanitize_error_message(e),
            }
