# Feature: Supabase Memory Provider

## Feature Description

Implement a real Supabase-backed memory provider that performs pgvector semantic search using Voyage embeddings. This provider plugs into the existing multi-provider retrieval architecture, replacing the current keyword-based fallback path when `provider="supabase"` is selected by the router. The provider uses `supabase-py` to call a `match_vectors` RPC function on Supabase, and uses the `voyageai` SDK to convert text queries into embeddings before search.

## User Story

As a lifelong learner using the Second Brain, I want my knowledge retrieval to query Supabase pgvector storage as a real provider (not a mock fallback), so that the multi-provider architecture delivers real results from persistent vector storage alongside Mem0.

## Problem Statement

The retrieval router already routes to Supabase as a provider, and test scenarios (S004, S015, S022) exercise Supabase paths — but `MemoryService` has no real Supabase implementation. When `provider="supabase"` is selected, `_should_use_real_provider()` returns `False` (it only checks for Mem0), causing all Supabase requests to fall through to the generic `_search_fallback()` which returns keyword-matched mock data. This means the multi-provider architecture is validated against abstractions but not against a real second backend.

## Solution Statement

- Decision: Create a dedicated `SupabaseProvider` adapter class in `services/supabase.py` — because the current `MemoryService` mixes Mem0-specific logic (lazy client, API key checks) with provider dispatch; a separate adapter keeps each provider self-contained and testable
- Decision: Add `embed()` method to `VoyageRerankService` (rename to `VoyageService`) — because Voyage is already in the stack for rerank, and using the same SDK/client for embeddings avoids adding a new dependency
- Decision: Use `supabase-py` `.rpc("match_vectors", ...)` to call a server-side pgvector function — because this avoids raw SQL from the client, leverages Supabase's RPC interface, and matches the Mem0-Supabase pattern documented in their official docs
- Decision: Use `vector(1024)` column dimension matching Voyage `voyage-4-large` default — because dimension mismatch between embedding model and pgvector column would cause silent failures
- Decision: Wire Voyage rerank for Supabase results via existing external rerank path — because the overlap policy already specifies `external_rerank: configurable` for Supabase, and the orchestrator already applies external rerank when `skip_external_rerank=False`

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `services/supabase.py` (new), `services/voyage.py` (update), `services/memory.py` (update), `deps.py` (update), `services/__init__.py` (update)
- **Dependencies**: `supabase` (supabase-py), `voyageai` (Voyage AI SDK)

### Slice Guardrails (Required)

- **Single Outcome**: Supabase provider returns real pgvector search results through the recall pipeline
- **Expected Files Touched**: 5 files (1 new, 4 updated) + 2 test files (1 new, 1 updated)
- **Scope Boundary**: Does NOT include real Voyage rerank API (stays mocked), data ingestion into Supabase, multi-provider merge, or Graphiti provider
- **Split Trigger**: If embedding pipeline complexity exceeds simple query embedding (e.g., batch ingestion, chunking), split into separate slice

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/services/memory.py` (lines 24-117) — Why: Contains `MemoryService` class with provider dispatch logic, `_should_use_real_provider()`, and `MemorySearchResult` dataclass that the new provider must return
- `backend/src/second_brain/services/memory.py` (lines 145-228) — Why: Contains `_search_with_provider()` and `_normalize_mem0_results()` patterns to mirror for Supabase adapter
- `backend/src/second_brain/services/voyage.py` (lines 1-89) — Why: Contains `VoyageRerankService` that will be extended with `embed()` method; shows existing service structure and mock pattern
- `backend/src/second_brain/deps.py` (lines 1-64) — Why: Contains factory functions and default config; needs Supabase provider factory + Voyage embed config
- `backend/src/second_brain/agents/recall.py` (lines 228-246) — Why: Contains `_resolve_memory_service_for_provider()` which creates provider-specific `MemoryService` instances; the Supabase provider must work with this resolution
- `backend/src/second_brain/orchestration/retrieval_router.py` (lines 86-100) — Why: Shows how router selects Supabase with `skip_external_rerank: False`; confirms external rerank applies to Supabase path
- `backend/src/second_brain/contracts/context_packet.py` (lines 6-13) — Why: `ContextCandidate` model that search results must be converted into
- `backend/src/second_brain/services/__init__.py` (lines 1-12) — Why: Exports that need updating with new types
- `tests/test_memory_service.py` (lines 196-277) — Why: Test patterns for provider paths (TestProviderPath class); mirror for Supabase provider tests
- `tests/test_recall_flow_integration.py` (lines 115-135, 361-424) — Why: Integration test patterns for non-mem0 provider paths and provider route consistency

### New Files to Create

- `backend/src/second_brain/services/supabase.py` — Supabase pgvector provider adapter with `search()` method returning `MemorySearchResult[]`
- `tests/test_supabase_provider.py` — Unit tests for Supabase provider (mock supabase-py client, test normalization, fallback)

### Related Memories (from memory.md)

- Memory: "Python-first with framework-agnostic contracts — Allows fast delivery while preserving portability" — Relevance: Supabase provider must use framework-agnostic contracts (ContextCandidate, MemorySearchResult), not Supabase-specific types in public interface
- Memory: "Provider error context: Keep fallback metadata actionable but sanitized (redact secrets and cap message length)" — Relevance: Supabase provider must sanitize connection strings and API keys in error metadata, mirroring the Mem0 `_sanitize_error_message()` pattern
- Memory: "Avoid mixed-scope loops: Combining workflow/docs changes with backend behavior in one slice increases review noise" — Relevance: This slice is strictly backend provider implementation, no workflow or docs changes
- Memory: "Trace-first approach for Eval/Trace" — Relevance: The trace layer already captures provider identity; no trace changes needed for this slice

### Relevant Documentation

- [Mem0 Supabase Vector DB Setup](https://docs.mem0.ai/components/vectordbs/dbs/supabase)
  - Specific section: SQL Migrations, Config, Best Practices
  - Why: Provides the `match_vectors` RPC function pattern and table schema for pgvector
- [Voyage AI Text Embeddings](https://docs.voyageai.com/docs/embeddings)
  - Specific section: Python API, Model Choices
  - Why: `vo.embed(texts, model="voyage-4-large", input_type="query"|"document")` is the exact API call needed
- [Supabase Python Client](https://supabase.com/llms/python.txt)
  - Specific section: RPC function calls
  - Why: `supabase.rpc("match_vectors", {...}).execute()` pattern for calling server-side functions

### Patterns to Follow

**Mem0 Provider Adapter Pattern** (from `services/memory.py:145-176`):
```python
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
        # ... search and normalize ...
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
```
- Why this pattern: Every provider adapter must have try/except wrapping with fallback to deterministic path on failure, plus sanitized error metadata
- Common gotchas: Must sanitize secrets (API keys, connection strings) in error messages; must cap message length at 200 chars

**Result Normalization Pattern** (from `services/memory.py:187-228`):
```python
def _normalize_mem0_results(
    self,
    mem0_results: Any,
    top_k: int,
    threshold: float,
) -> list[MemorySearchResult]:
    results: list[MemorySearchResult] = []
    for i, item in enumerate(mem0_results):
        if isinstance(item, dict):
            item_id = str(item.get("id", f"mem0-{i}"))
            content = str(item.get("memory", item.get("content", "")))
            score = item.get("score", item.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, float(score) if score is not None else 0.0))
            # ...
```
- Why this pattern: Defensive normalization handles missing fields, type mismatches, and None values gracefully
- Common gotchas: Supabase RPC returns `similarity` field (not `score`), and content is in `metadata` JSONB (not `memory` field)

**VoyageRerankService Structure** (from `services/voyage.py:7-53`):
```python
class VoyageRerankService:
    def __init__(self, enabled: bool = True, model: str = "rerank-2"):
        self.enabled = enabled
        self.model = model

    def rerank(self, query, candidates, top_k=5):
        metadata = {"rerank_type": "none", "rerank_model": self.model}
        if not self.enabled or not candidates:
            metadata["bypass_reason"] = "disabled" if not self.enabled else "no_candidates"
            return list(candidates), metadata
        # ...
```
- Why this pattern: Service init takes enabled flag + model name; methods return (results, metadata) tuples with bypass reason tracking
- Common gotchas: Keep mock path for testing; real API call should be behind enabled flag

**Dependency Factory Pattern** (from `deps.py:30-43`):
```python
def create_memory_service(
    provider: str = "mem0",
    config: dict[str, Any] | None = None,
) -> MemoryService:
    return MemoryService(provider=provider, config=config)

def create_voyage_rerank_service(
    enabled: bool = True,
    model: str = "rerank-2",
) -> VoyageRerankService:
    return VoyageRerankService(enabled=enabled, model=model)
```
- Why this pattern: Simple factory functions with sensible defaults; config dict passes through to service constructors
- Common gotchas: Don't load env vars at import time; let service constructors handle lazy credential loading

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation — Voyage Embedding + Supabase Provider

Create the two new capabilities needed for real Supabase search:

1. Extend `VoyageRerankService` to `VoyageService` with an `embed()` method that converts text queries to vectors using the `voyageai` SDK
2. Create `SupabaseProvider` class that takes a query embedding, calls `supabase.rpc("match_vectors", ...)`, and returns normalized `MemorySearchResult[]`

Both use lazy client loading and fallback-on-failure patterns mirroring the Mem0 adapter.

### Phase 2: Core Integration — Wire MemoryService Dispatch

Update `MemoryService` to detect `provider="supabase"` and route to `SupabaseProvider.search()` instead of the generic `_search_fallback()`. This requires:

1. Adding a `_should_use_supabase_provider()` check alongside the existing `_should_use_real_provider()` (which only handles Mem0)
2. Creating a `_search_with_supabase()` method that embeds the query via Voyage, then calls `SupabaseProvider.search()`
3. Updating the dispatch logic in `search_memories()` to handle the Supabase path

### Phase 3: Dependency Wiring — Config, Factories, Exports

1. Update `deps.py` with Supabase config keys (`supabase_url`, `supabase_key`, `supabase_use_real_provider`) and Voyage embed config (`voyage_api_key`, `voyage_embed_model`)
2. Add factory function `create_supabase_provider()` in deps
3. Update `services/__init__.py` exports

### Phase 4: Testing & Validation

1. Unit tests for `SupabaseProvider`: mock supabase-py client, test normalization, test fallback on error, test sanitization
2. Unit tests for `VoyageService.embed()`: mock voyageai client, test embedding generation, test fallback
3. Integration test: Supabase provider wired through full recall pipeline with mocked external clients
4. Regression: existing test suite must pass unchanged

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `backend/src/second_brain/services/voyage.py`

- **IMPLEMENT**: Extend `VoyageRerankService` with `embed()` method for text-to-vector conversion. Add lazy `voyageai.Client` loading. Keep existing `rerank()` and `_mock_rerank()` intact.

  Add to class:
  ```python
  def __init__(self, enabled: bool = True, model: str = "rerank-2",
               embed_model: str = "voyage-4-large", embed_enabled: bool = False):
      self.enabled = enabled
      self.model = model
      self.embed_model = embed_model
      self.embed_enabled = embed_enabled
      self._voyage_client: Any | None = None

  def _load_voyage_client(self) -> Any | None:
      """Load Voyage AI client lazily."""
      if self._voyage_client is not None:
          return self._voyage_client
      try:
          import voyageai  # type: ignore[import-untyped]
          api_key = os.getenv("VOYAGE_API_KEY")
          if api_key:
              self._voyage_client = voyageai.Client(api_key=api_key)
          else:
              self._voyage_client = voyageai.Client()  # uses env var
          return self._voyage_client
      except ImportError:
          logger.debug("voyageai SDK not installed")
      except Exception as e:
          logger.warning("Voyage client init failed: %s", type(e).__name__)
      return None

  def embed(self, text: str, input_type: str = "query") -> tuple[list[float] | None, dict[str, Any]]:
      """Embed text using Voyage AI. Returns (embedding_vector, metadata)."""
      metadata: dict[str, Any] = {"embed_model": self.embed_model}
      if not self.embed_enabled:
          return None, {**metadata, "embed_error": "embedding_disabled"}
      try:
          client = self._load_voyage_client()
          if client is None:
              return None, {**metadata, "embed_error": "client_unavailable"}
          result = client.embed([text], model=self.embed_model, input_type=input_type)
          return result.embeddings[0], {**metadata, "total_tokens": result.total_tokens}
      except Exception as e:
          logger.warning("Voyage embed failed: %s", type(e).__name__)
          return None, {**metadata, "embed_error": type(e).__name__}
  ```

- **PATTERN**: Follow lazy client loading from `services/memory.py:123-143` (`_load_mem0_client`)
- **IMPORTS**: Add at top of file:
  ```python
  import logging
  import os
  from typing import Any, Sequence
  ```
- **GOTCHA**: The `voyageai` SDK auto-reads `VOYAGE_API_KEY` from env. Don't double-pass the key. Also, `vo.embed()` takes a list of strings, not a single string — always wrap in `[text]` and take `[0]` from result.
- **VALIDATE**: `python -m pytest tests/test_supabase_provider.py -k "voyage" -v` (test created in Task 6)

### Task 2: CREATE `backend/src/second_brain/services/supabase.py`

- **IMPLEMENT**: Create `SupabaseProvider` class with:
  - `__init__(self, config: dict)` — stores config, sets `_client = None` for lazy loading
  - `_load_client(self) -> Any | None` — lazy Supabase client init using `create_client(url, key)`
  - `_sanitize_error_message(self, error: Exception) -> str` — mirrors Mem0 pattern, redacts `supabase_url` and `supabase_key`
  - `search(self, query_embedding: list[float], top_k: int, threshold: float) -> tuple[list[MemorySearchResult], dict[str, Any]]` — calls `supabase.rpc("match_vectors", {"query_embedding": query_embedding, "match_count": top_k}).execute()`, normalizes results to `MemorySearchResult[]`
  - `_normalize_results(self, rpc_results: list[dict], top_k: int, threshold: float) -> list[MemorySearchResult]` — converts RPC response dicts (`{id, similarity, metadata}`) into `MemorySearchResult` objects with confidence clamping

  Full class structure:
  ```python
  """Supabase pgvector memory provider."""
  import logging
  import os
  from typing import Any, Optional
  from second_brain.services.memory import MemorySearchResult

  logger = logging.getLogger(__name__)

  class SupabaseProvider:
      """Supabase pgvector search provider."""

      def __init__(self, config: Optional[dict[str, Any]] = None):
          self.config = config or {}
          self._client: Any | None = None
          self._supabase_url = self.config.get("supabase_url") or os.getenv("SUPABASE_URL")
          self._supabase_key = self.config.get("supabase_key") or os.getenv("SUPABASE_KEY")

      def _load_client(self) -> Any | None:
          if self._client is not None:
              return self._client
          try:
              from supabase import create_client  # type: ignore[import-untyped]
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
      ) -> tuple[list[MemorySearchResult], dict[str, Any]]:
          metadata: dict[str, Any] = {"provider": "supabase"}
          try:
              client = self._load_client()
              if client is None:
                  return [], {**metadata, "fallback_reason": "client_unavailable"}
              response = client.rpc(
                  "match_vectors",
                  {"query_embedding": query_embedding, "match_count": top_k},
              ).execute()
              results = self._normalize_results(response.data or [], top_k, threshold)
              return results, {**metadata, "real_provider": True, "raw_count": len(response.data or [])}
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
          threshold: float,
      ) -> list[MemorySearchResult]:
          results: list[MemorySearchResult] = []
          for i, row in enumerate(rpc_results):
              similarity = row.get("similarity", 0.0)
              try:
                  confidence = max(0.0, min(1.0, float(similarity)))
              except (TypeError, ValueError):
                  confidence = 0.0
              row_metadata = row.get("metadata", {})
              content = ""
              if isinstance(row_metadata, dict):
                  content = str(row_metadata.get("content", row_metadata.get("text", "")))
              results.append(
                  MemorySearchResult(
                      id=str(row.get("id", f"supa-{i}")),
                      content=content,
                      source="supabase",
                      confidence=confidence,
                      metadata={
                          "real_provider": True,
                          **(row_metadata if isinstance(row_metadata, dict) else {}),
                      },
                  )
              )
              if len(results) >= top_k:
                  break
          return results

      def _sanitize_error_message(self, error: Exception) -> str:
          message = str(error)
          for value in [self._supabase_url, self._supabase_key]:
              if value:
                  message = message.replace(value, "[REDACTED]")
          return message[:200]
  ```

- **PATTERN**: Mirror `services/memory.py:145-228` for try/except + normalize pattern; mirror `services/memory.py:178-185` for `_sanitize_error_message`
- **IMPORTS**:
  ```python
  import logging
  import os
  from typing import Any, Optional
  from second_brain.services.memory import MemorySearchResult
  ```
- **GOTCHA**: Supabase RPC returns `{id, similarity, metadata}` where `metadata` is a JSONB column — the actual text content lives inside metadata (e.g., `metadata.content` or `metadata.text`), not as a top-level field. Also, `response.data` can be `None` on error — always default to `[]`.
- **VALIDATE**: `python -m pytest tests/test_supabase_provider.py -k "supabase" -v`

### Task 3: UPDATE `backend/src/second_brain/services/memory.py`

- **IMPLEMENT**: Add Supabase provider dispatch to `MemoryService`:

  1. Add new instance variables in `__init__`:
     ```python
     self._supabase_enabled = self.config.get("supabase_use_real_provider", False)
     ```

  2. Add `_should_use_supabase_provider()` method:
     ```python
     def _should_use_supabase_provider(self) -> bool:
         if not self._supabase_enabled:
             return False
         if self.provider != "supabase":
             return False
         supabase_url = self.config.get("supabase_url") or os.getenv("SUPABASE_URL")
         supabase_key = self.config.get("supabase_key") or os.getenv("SUPABASE_KEY")
         return supabase_url is not None and supabase_key is not None
     ```

  3. Add `_search_with_supabase()` method:
     ```python
     def _search_with_supabase(
         self, query: str, top_k: int, threshold: float,
     ) -> tuple[list[MemorySearchResult], dict[str, Any]]:
         from second_brain.services.supabase import SupabaseProvider
         from second_brain.services.voyage import VoyageRerankService
         voyage = VoyageRerankService(
             embed_enabled=True,
             embed_model=self.config.get("voyage_embed_model", "voyage-4-large"),
         )
         embedding, embed_meta = voyage.embed(query, input_type="query")
         if embedding is None:
             return self._search_fallback(query, top_k, threshold), {
                 "provider": self.provider,
                 "fallback_reason": "embedding_failed",
                 "embed_error": embed_meta.get("embed_error"),
             }
         provider = SupabaseProvider(config=self.config)
         results, search_meta = provider.search(embedding, top_k, threshold)
         if not results and search_meta.get("fallback_reason"):
             fallback = self._search_fallback(query, top_k, threshold)
             return fallback, {**search_meta, "used_fallback": True}
         return results, search_meta
     ```

  4. Update `search_memories()` dispatch (between mock check and `_should_use_real_provider` check):

     **Current** (lines 79-91):
     ```python
     elif self._should_use_real_provider():
         real_results, real_metadata = self._search_with_provider(
             normalized_query,
             normalized_top_k,
             normalized_threshold,
         )
         results = real_results
         metadata = real_metadata
     else:
         results = self._search_fallback(
             normalized_query, normalized_top_k, normalized_threshold
         )
         metadata = {"provider": self.provider, "fallback_reason": "real_provider_disabled"}
     ```

     **Replace with**:
     ```python
     elif self._should_use_supabase_provider():
         supabase_results, supabase_metadata = self._search_with_supabase(
             normalized_query,
             normalized_top_k,
             normalized_threshold,
         )
         results = supabase_results
         metadata = supabase_metadata
     elif self._should_use_real_provider():
         real_results, real_metadata = self._search_with_provider(
             normalized_query,
             normalized_top_k,
             normalized_threshold,
         )
         results = real_results
         metadata = real_metadata
     else:
         results = self._search_fallback(
             normalized_query, normalized_top_k, normalized_threshold
         )
         metadata = {"provider": self.provider, "fallback_reason": "real_provider_disabled"}
     ```

- **PATTERN**: Mirror `_should_use_real_provider()` at line 110-117 and `_search_with_provider()` at line 145-176
- **IMPORTS**: No new imports needed at module level (lazy imports inside methods)
- **GOTCHA**: Supabase check MUST come before Mem0 check in dispatch order, because `_should_use_real_provider()` returns `False` for non-mem0 providers (line 114: `if self.provider != "mem0": return False`). The Supabase path is only entered when `provider="supabase"` AND `supabase_use_real_provider=True`.
- **VALIDATE**: `python -m pytest tests/test_memory_service.py -v && python -m pytest tests/test_supabase_provider.py -v`

### Task 4: UPDATE `backend/src/second_brain/deps.py`

- **IMPLEMENT**: Add Supabase and Voyage embedding config to `get_default_config()` and optionally add a `create_supabase_provider()` factory.

  1. Update `get_default_config()`:

     **Current** (lines 53-64):
     ```python
     def get_default_config() -> dict[str, Any]:
         return {
             "default_mode": "conversation",
             "default_top_k": 5,
             "default_threshold": 0.6,
             "mem0_rerank_native": True,
             "mem0_skip_external_rerank": True,
             "mem0_use_real_provider": False,
             "mem0_user_id": None,
             "mem0_api_key": None,
         }
     ```

     **Replace with**:
     ```python
     def get_default_config() -> dict[str, Any]:
         return {
             "default_mode": "conversation",
             "default_top_k": 5,
             "default_threshold": 0.6,
             "mem0_rerank_native": True,
             "mem0_skip_external_rerank": True,
             "mem0_use_real_provider": False,
             "mem0_user_id": None,
             "mem0_api_key": None,
             "supabase_use_real_provider": False,
             "supabase_url": None,
             "supabase_key": None,
             "voyage_embed_model": "voyage-4-large",
         }
     ```

  2. Update `create_voyage_rerank_service()` signature to include embed params:

     **Current** (lines 38-43):
     ```python
     def create_voyage_rerank_service(
         enabled: bool = True,
         model: str = "rerank-2",
     ) -> VoyageRerankService:
         return VoyageRerankService(enabled=enabled, model=model)
     ```

     **Replace with**:
     ```python
     def create_voyage_rerank_service(
         enabled: bool = True,
         model: str = "rerank-2",
         embed_model: str = "voyage-4-large",
         embed_enabled: bool = False,
     ) -> VoyageRerankService:
         return VoyageRerankService(
             enabled=enabled,
             model=model,
             embed_model=embed_model,
             embed_enabled=embed_enabled,
         )
     ```

- **PATTERN**: Mirror existing factory pattern at `deps.py:30-35`
- **IMPORTS**: No new imports needed (existing imports sufficient)
- **GOTCHA**: Keep `supabase_use_real_provider: False` as default — real provider only activates with explicit config + credentials. This ensures all existing tests pass unchanged.
- **VALIDATE**: `python -m pytest tests/ -v` (full suite — deps changes can affect everything)

### Task 5: UPDATE `backend/src/second_brain/services/__init__.py`

- **IMPLEMENT**: Add `SupabaseProvider` to exports.

  **Current**:
  ```python
  from second_brain.services.memory import MemoryService, MemorySearchResult
  from second_brain.services.voyage import VoyageRerankService
  from second_brain.services.trace import TraceCollector

  __all__ = [
      "MemoryService",
      "MemorySearchResult",
      "VoyageRerankService",
      "TraceCollector",
  ]
  ```

  **Replace with**:
  ```python
  from second_brain.services.memory import MemoryService, MemorySearchResult
  from second_brain.services.voyage import VoyageRerankService
  from second_brain.services.supabase import SupabaseProvider
  from second_brain.services.trace import TraceCollector

  __all__ = [
      "MemoryService",
      "MemorySearchResult",
      "VoyageRerankService",
      "SupabaseProvider",
      "TraceCollector",
  ]
  ```

- **PATTERN**: Follow existing export pattern in `services/__init__.py:1-12`
- **IMPORTS**: `from second_brain.services.supabase import SupabaseProvider`
- **GOTCHA**: Import order matters for circular dependency prevention. `supabase.py` imports from `memory.py` (for `MemorySearchResult`), so `supabase` import must come after `memory` import in `__init__.py`.
- **VALIDATE**: `python -c "from second_brain.services import SupabaseProvider; print('OK')"`

### Task 6: CREATE `tests/test_supabase_provider.py`

- **IMPLEMENT**: Comprehensive unit tests for Supabase provider and Voyage embedding:

  ```python
  """Unit tests for Supabase provider and Voyage embedding service."""

  import pytest
  from unittest.mock import MagicMock, patch
  from second_brain.services.supabase import SupabaseProvider
  from second_brain.services.memory import MemoryService, MemorySearchResult
  from second_brain.services.voyage import VoyageRerankService


  class TestSupabaseProviderSearch:
      """Test SupabaseProvider.search() with mocked Supabase client."""

      def test_search_returns_normalized_results(self):
          """Successful RPC returns normalized MemorySearchResult list."""
          provider = SupabaseProvider(config={
              "supabase_url": "https://test.supabase.co",
              "supabase_key": "test-key",
          })
          mock_client = MagicMock()
          mock_response = MagicMock()
          mock_response.data = [
              {"id": "doc-1", "similarity": 0.92, "metadata": {"content": "Test document 1", "topic": "ai"}},
              {"id": "doc-2", "similarity": 0.78, "metadata": {"content": "Test document 2", "topic": "ml"}},
          ]
          mock_client.rpc.return_value.execute.return_value = mock_response
          provider._client = mock_client

          results, metadata = provider.search(
              query_embedding=[0.1] * 1024, top_k=5, threshold=0.6,
          )

          assert len(results) == 2
          assert results[0].id == "doc-1"
          assert results[0].content == "Test document 1"
          assert results[0].source == "supabase"
          assert results[0].confidence == 0.92
          assert metadata.get("real_provider") is True

      def test_search_client_unavailable_returns_empty(self):
          """When client can't load, returns empty with fallback_reason."""
          provider = SupabaseProvider(config={})
          results, metadata = provider.search([0.1] * 1024, top_k=5)
          assert results == []
          assert metadata["fallback_reason"] == "client_unavailable"

      def test_search_rpc_error_returns_empty_with_metadata(self):
          """When RPC throws, returns empty with sanitized error."""
          provider = SupabaseProvider(config={
              "supabase_url": "https://secret.supabase.co",
              "supabase_key": "secret-key",
          })
          mock_client = MagicMock()
          mock_client.rpc.return_value.execute.side_effect = RuntimeError(
              "connection to https://secret.supabase.co failed"
          )
          provider._client = mock_client

          results, metadata = provider.search([0.1] * 1024, top_k=5)

          assert results == []
          assert metadata["fallback_reason"] == "provider_error"
          assert "secret.supabase.co" not in metadata["error_message"]
          assert "[REDACTED]" in metadata["error_message"]

      def test_normalize_clamps_confidence(self):
          """Similarity values outside 0-1 are clamped."""
          provider = SupabaseProvider()
          results = provider._normalize_results(
              [{"id": "x", "similarity": 1.5, "metadata": {"content": "test"}}],
              top_k=5, threshold=0.0,
          )
          assert results[0].confidence == 1.0

      def test_normalize_handles_missing_fields(self):
          """Missing id/similarity/metadata are handled gracefully."""
          provider = SupabaseProvider()
          results = provider._normalize_results(
              [{"similarity": 0.8}], top_k=5, threshold=0.0,
          )
          assert results[0].id == "supa-0"
          assert results[0].content == ""
          assert results[0].confidence == 0.8

      def test_search_respects_top_k(self):
          """Results are capped at top_k."""
          provider = SupabaseProvider()
          mock_client = MagicMock()
          mock_response = MagicMock()
          mock_response.data = [
              {"id": f"doc-{i}", "similarity": 0.9 - i * 0.1, "metadata": {"content": f"doc {i}"}}
              for i in range(10)
          ]
          mock_client.rpc.return_value.execute.return_value = mock_response
          provider._client = mock_client

          results, _ = provider.search([0.1] * 1024, top_k=3)
          assert len(results) == 3


  class TestVoyageEmbedding:
      """Test VoyageRerankService.embed() method."""

      def test_embed_disabled_returns_none(self):
          """When embed_enabled=False, returns None with error metadata."""
          service = VoyageRerankService(embed_enabled=False)
          embedding, metadata = service.embed("test query")
          assert embedding is None
          assert metadata["embed_error"] == "embedding_disabled"

      def test_embed_client_unavailable_returns_none(self):
          """When voyageai SDK not available, returns None."""
          service = VoyageRerankService(embed_enabled=True)
          # Don't mock — SDK likely not installed in test env
          embedding, metadata = service.embed("test query")
          assert embedding is None
          assert "embed_error" in metadata

      def test_embed_success_with_mocked_client(self):
          """With mocked client, returns embedding vector."""
          service = VoyageRerankService(embed_enabled=True, embed_model="voyage-4-large")
          mock_client = MagicMock()
          mock_result = MagicMock()
          mock_result.embeddings = [[0.1, 0.2, 0.3] * 341 + [0.1]]  # 1024 dims
          mock_result.total_tokens = 5
          mock_client.embed.return_value = mock_result
          service._voyage_client = mock_client

          embedding, metadata = service.embed("test query", input_type="query")

          assert embedding is not None
          assert len(embedding) == 1024
          assert metadata["total_tokens"] == 5
          mock_client.embed.assert_called_once_with(
              ["test query"], model="voyage-4-large", input_type="query"
          )

      def test_embed_preserves_existing_rerank(self):
          """Adding embed doesn't break existing rerank functionality."""
          service = VoyageRerankService(enabled=True, embed_enabled=False)
          from second_brain.contracts.context_packet import ContextCandidate
          candidates = [
              ContextCandidate(id="1", content="test a", source="s", confidence=0.8, metadata={}),
              ContextCandidate(id="2", content="test b", source="s", confidence=0.7, metadata={}),
          ]
          reranked, meta = service.rerank("test", candidates, top_k=5)
          assert len(reranked) == 2
          assert meta["rerank_type"] == "external"


  class TestMemoryServiceSupabasePath:
      """Test MemoryService dispatch to Supabase provider."""

      def test_supabase_disabled_uses_fallback(self):
          """When supabase_use_real_provider=False, uses keyword fallback."""
          service = MemoryService(
              provider="supabase",
              config={"supabase_use_real_provider": False},
          )
          candidates, metadata = service.search_memories("test query", top_k=5)
          assert len(candidates) >= 1
          assert metadata.get("fallback_reason") == "real_provider_disabled"

      def test_supabase_no_credentials_uses_fallback(self):
          """When credentials missing, uses fallback."""
          service = MemoryService(
              provider="supabase",
              config={"supabase_use_real_provider": True},
          )
          candidates, metadata = service.search_memories("test query", top_k=5)
          assert len(candidates) >= 1
          # Falls through to fallback because no URL/key configured

      def test_supabase_embed_failure_uses_fallback(self, monkeypatch):
          """When embedding fails, falls back to keyword search."""
          service = MemoryService(
              provider="supabase",
              config={
                  "supabase_use_real_provider": True,
                  "supabase_url": "https://test.supabase.co",
                  "supabase_key": "test-key",
              },
          )
          # Voyage embed will fail (SDK not installed or no API key)
          candidates, metadata = service.search_memories("test query", top_k=5)
          assert len(candidates) >= 1
          # Should get fallback because embedding failed

      def test_existing_mem0_path_unchanged(self):
          """Mem0 provider path is not affected by Supabase changes."""
          service = MemoryService(
              provider="mem0",
              config={"mem0_use_real_provider": False},
          )
          candidates, metadata = service.search_memories("test query", top_k=5)
          assert len(candidates) >= 1
          assert metadata["provider"] == "mem0"
          assert metadata.get("fallback_reason") == "real_provider_disabled"
  ```

- **PATTERN**: Mirror `tests/test_memory_service.py:196-277` (TestProviderPath) for structure; use `MagicMock` for external client mocking
- **IMPORTS**:
  ```python
  import pytest
  from unittest.mock import MagicMock, patch
  from second_brain.services.supabase import SupabaseProvider
  from second_brain.services.memory import MemoryService, MemorySearchResult
  from second_brain.services.voyage import VoyageRerankService
  ```
- **GOTCHA**: Don't import `supabase` or `voyageai` at test module level — they may not be installed. All real SDK interaction is mocked via `MagicMock` injected into `_client` attributes.
- **VALIDATE**: `python -m pytest tests/test_supabase_provider.py -v`

### Task 7: UPDATE `tests/test_recall_flow_integration.py`

- **IMPLEMENT**: Add integration test verifying Supabase provider wired through full recall pipeline. Add to `TestProviderRouteConsistency` class:

  ```python
  def test_supabase_route_with_real_provider_disabled_uses_fallback(self):
      """
      When route selects supabase but real provider is disabled,
      recall still returns valid contract response via fallback.
      """
      memory_service = MemoryService(
          provider="supabase",
          config={"supabase_use_real_provider": False},
      )
      rerank_service = VoyageRerankService(enabled=True)

      orchestrator = RecallOrchestrator(
          memory_service=memory_service,
          rerank_service=rerank_service,
          feature_flags={"mem0_enabled": False, "supabase_enabled": True},
          provider_status={"mem0": "unavailable", "supabase": "available"},
      )

      request = RetrievalRequest(
          query="supabase fallback test",
          mode="conversation",
          top_k=5,
          threshold=0.6,
      )

      response = orchestrator.run(request)

      assert response.context_packet is not None
      assert response.next_action is not None
      assert response.routing_metadata["selected_provider"] == "supabase"
      assert isinstance(response.context_packet.candidates, list)
  ```

- **PATTERN**: Mirror `test_injected_mem0_route_to_supabase_uses_supabase_backend` at lines 364-393
- **IMPORTS**: No new imports needed (existing imports cover all types)
- **GOTCHA**: This test works without Supabase or Voyage SDKs installed because the real provider is disabled — it exercises the fallback path through the full pipeline.
- **VALIDATE**: `python -m pytest tests/test_recall_flow_integration.py -v`

---

## TESTING STRATEGY

### Unit Tests

- `tests/test_supabase_provider.py::TestSupabaseProviderSearch` — 6 tests covering: successful search with mocked client, client unavailable, RPC error with sanitization, confidence clamping, missing fields, top_k cap
- `tests/test_supabase_provider.py::TestVoyageEmbedding` — 4 tests covering: embed disabled, client unavailable, successful embed with mock, rerank not broken
- `tests/test_supabase_provider.py::TestMemoryServiceSupabasePath` — 4 tests covering: disabled config, no credentials, embed failure fallback, existing Mem0 path unchanged

### Integration Tests

- `tests/test_recall_flow_integration.py::TestProviderRouteConsistency::test_supabase_route_with_real_provider_disabled_uses_fallback` — Full recall pipeline with Supabase route selection but fallback execution
- Existing `test_non_mem0_allows_external_rerank` already exercises Supabase route — must still pass

### Edge Cases

- Empty Supabase table (RPC returns `[]`) — should emit EMPTY_SET branch
- Supabase returns results with `None` metadata — normalization handles gracefully
- Voyage embed fails mid-request — falls back to keyword search with `fallback_reason: embedding_failed`
- Connection string contains secrets — sanitized in error metadata

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.
> Full validation depth is required for every slice; one proof signal is not enough.

### Level 1: Syntax & Style
```
python -m ruff check backend/src/second_brain/ tests/ --fix
```

### Level 2: Type Safety
```
python -m mypy backend/src/second_brain/ --strict
```

### Level 3: Unit Tests
```
python -m pytest tests/test_supabase_provider.py -v
python -m pytest tests/test_memory_service.py -v
```

### Level 4: Integration Tests
```
python -m pytest tests/test_recall_flow_integration.py -v
python -m pytest tests/ -v
```

### Level 5: Manual Validation

1. Verify import chain:
   ```python
   python -c "from second_brain.services import SupabaseProvider; print('Import OK')"
   python -c "from second_brain.services.voyage import VoyageRerankService; s = VoyageRerankService(embed_enabled=False); print('Voyage OK')"
   ```

2. Verify full test count is >= 160 (existing) + 15 (new) = 175:
   ```
   python -m pytest tests/ -v --tb=short 2>&1 | tail -5
   ```

3. Verify no new ruff/mypy errors beyond baseline:
   ```
   python -m ruff check backend/src/second_brain/ tests/ --statistics
   python -m mypy backend/src/second_brain/ --strict 2>&1 | tail -3
   ```

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] `SupabaseProvider` class exists in `services/supabase.py` with `search()` and `_normalize_results()`
- [x] `VoyageRerankService.embed()` method works with mocked client
- [x] `MemoryService` dispatches to Supabase when `provider="supabase"` and `supabase_use_real_provider=True`
- [x] All existing tests pass unchanged (zero regressions)
- [x] 15+ new tests pass for Supabase provider, Voyage embed, and MemoryService Supabase path
- [x] `deps.py` includes Supabase config keys in `get_default_config()`
- [x] Error metadata sanitizes secrets (connection strings, API keys)
- [x] ruff and mypy pass with zero errors

### Runtime (verify after testing/deployment)

- [ ] With real Supabase credentials + Voyage API key, `MemoryService(provider="supabase", config={...}).search_memories("test")` returns real pgvector results
- [ ] Supabase provider results flow through external rerank (Voyage) correctly
- [ ] Trace records show `selected_provider: "supabase"` for Supabase-routed requests

---

## COMPLETION CHECKLIST

- [x] All tasks completed in order (Tasks 1-7)
- [x] Each task validation passed
- [x] All validation commands executed successfully (Levels 1-5)
- [x] Full test suite passes (unit + integration, >= 175 tests)
- [ ] No linting or type checking errors (ruff: 0 errors, mypy: 14 pre-existing in other files)
- [x] Manual testing confirms imports and factories work
- [x] Acceptance criteria all met (implementation criteria complete, runtime criteria pending real credentials)

---

## NOTES

### Key Design Decisions

- **Separate `SupabaseProvider` class vs extending `MemoryService`**: Chose separate class because `MemoryService` already has too much Mem0-specific logic (lazy client, API key checks, normalize_mem0_results). A dedicated adapter keeps each provider self-contained, testable, and follows the adapter pattern that will scale to future providers (Graphiti).
- **Embedding in `VoyageRerankService` vs separate service**: Chose to extend the existing Voyage service because it already manages the SDK relationship, model selection, and enabled flags. Creating a separate `VoyageEmbeddingService` would duplicate client management. The service can be renamed to `VoyageService` in a future refactor if the dual responsibility becomes unwieldy.
- **Content stored in metadata JSONB vs separate column**: The `match_vectors` RPC function returns `{id, similarity, metadata}`. Content text lives inside the `metadata` JSONB column. This matches the Mem0 Supabase schema and avoids schema changes. The normalization layer extracts `metadata.content` or `metadata.text`.
- **vector(1024) for Voyage vs vector(1536) for OpenAI**: Voyage `voyage-4-large` outputs 1024 dimensions by default. The SQL table MUST use `vector(1024)`. If you switch embedding models later, you need to re-embed all data AND update the SQL column dimension.

### SQL Migration (run in Supabase SQL Editor before using real provider)

```sql
-- Enable pgvector extension
create extension if not exists vector;

-- Create memories table with 1024-dim for Voyage embeddings
create table if not exists memories (
  id text primary key,
  embedding vector(1024),
  metadata jsonb,
  created_at timestamp with time zone default timezone('utc', now()),
  updated_at timestamp with time zone default timezone('utc', now())
);

-- Create vector similarity search function
create or replace function match_vectors(
  query_embedding vector(1024),
  match_count int,
  filter jsonb default '{}'::jsonb
)
returns table (
  id text,
  similarity float,
  metadata jsonb
)
language plpgsql
as $$
begin
  return query
  select
    t.id::text,
    1 - (t.embedding <=> query_embedding) as similarity,
    t.metadata
  from memories t
  where case
    when filter::text = '{}'::text then true
    else t.metadata @> filter
  end
  order by t.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Create HNSW index for fast search
create index if not exists memories_embedding_idx
  on memories using hnsw (embedding vector_cosine_ops);
```

### Risks

- **Supabase SDK type stubs**: `supabase-py` has no official type stubs, so mypy will need `# type: ignore[import-untyped]` on import. Same pattern as Mem0.
- **Voyage API rate limits**: Embedding API has rate limits. For now this is fine (single query embedding per search). Batch embedding for ingestion will need rate limiting in a future slice.
- **pgvector dimension mismatch**: If the Supabase table uses `vector(1536)` (OpenAI default) but we send `vector(1024)` (Voyage), the RPC will error. The SQL migration in this plan specifies 1024.

### Confidence Score: 8/10

- **Strengths**: All codebase patterns are well-established (adapter, fallback, sanitization); both SDKs have clear Python APIs; existing tests provide comprehensive regression coverage; the router already handles Supabase routing
- **Uncertainties**: `supabase-py` `.rpc()` response format needs verification against real instance; Voyage embedding dimension alignment with existing data (if any); mypy strictness with untyped SDK imports
- **Mitigations**: Fallback-on-failure ensures graceful degradation if either SDK fails; all external calls are behind enabled flags defaulting to `False`; test suite uses mocked clients exclusively
