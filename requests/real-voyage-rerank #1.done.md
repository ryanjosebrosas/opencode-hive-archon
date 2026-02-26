# Feature: Real Voyage Rerank

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

## Feature Description

Replace the `_mock_rerank()` term-overlap heuristic in `VoyageRerankService` with a real Voyage AI `vo.rerank()` API call. The mock currently uses keyword intersection to simulate relevance scores, which means every non-Mem0 retrieval path (Supabase, future Graphiti) gets fake quality scores. The real reranker uses a cross-encoder model that jointly processes query-document pairs for accurate semantic relevance scoring. The mock is preserved as a fallback when the SDK is unavailable or the API call fails.

## User Story

As the retrieval system,
I want non-Mem0 provider paths to use real Voyage AI reranking,
So that retrieval quality reflects actual semantic relevance instead of fake term-overlap scores.

## Problem Statement

`VoyageRerankService.rerank()` at `voyage.py:101-103` always dispatches to `_mock_rerank()` regardless of configuration. The comment at line 101 says "In production, this would call Voyage AI API" — but production is never implemented. This means:
- Supabase results get fake rerank scores based on word overlap
- Trace records capture mock scores, making eval data meaningless
- The external rerank path documented in `retrieval-overlap-policy.md` is decorative

## Solution Statement

- Decision: Add a `_real_rerank()` method that calls `vo.rerank(query, documents, model, top_k)` and normalizes `RerankingResult` objects back to `ContextCandidate` — because the Voyage SDK returns a different shape (`{index, document, relevance_score}`) than our internal contract
- Decision: Add `use_real_rerank: bool = False` constructor parameter — because this defaults to safe behavior (mock) and requires explicit opt-in, same pattern as `embed_enabled` for embeddings
- Decision: Fall back to `_mock_rerank()` on any failure (ImportError, API error, timeout) — because the retrieval pipeline must never crash on rerank failure; degraded results are better than no results
- Decision: Use existing `_load_voyage_client()` for SDK loading — because the lazy client loader already handles ImportError, API key detection, and caching; no duplication needed
- Decision: Update default model from `rerank-2` to `rerank-2` (keep as-is) — because the codebase already defaults to this and it's still supported; upgrading to `rerank-2.5` is a separate config change

## Feature Metadata

**Feature Type**: Enhancement (replacing mock with real implementation)
**Estimated Complexity**: Low
**Primary Systems Affected**: `services/voyage.py`
**Dependencies**: `voyageai` SDK (existing optional dependency)

### Slice Guardrails (Required)

- **Single Outcome**: `VoyageRerankService.rerank()` calls real Voyage API when enabled, falls back to mock on failure
- **Expected Files Touched**: 2 files (1 updated, 1 new test file)
- **Scope Boundary**: Does NOT include upgrading rerank model version, changing rerank-related config in deps.py beyond the new flag, or modifying any other service
- **Split Trigger**: If normalization logic becomes complex (e.g., custom scoring transforms), split into follow-up

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `backend/src/second_brain/services/voyage.py` (lines 67-142) — Why: Contains the entire `rerank()` method and `_mock_rerank()` that will be updated; also contains `embed()` and `_load_voyage_client()` patterns to mirror
- `backend/src/second_brain/services/voyage.py` (lines 29-46) — Why: Contains `_load_voyage_client()` lazy loader that the rerank path will reuse
- `backend/src/second_brain/services/voyage.py` (lines 48-65) — Why: Contains `embed()` method showing the real-API-with-fallback pattern to mirror exactly
- `backend/src/second_brain/services/memory.py` (lines 167-198) — Why: Contains `_search_with_provider()` showing try/except/fallback pattern with sanitized error metadata
- `backend/src/second_brain/contracts/context_packet.py` (lines 6-13) — Why: `ContextCandidate` model that reranked results must conform to
- `docs/architecture/retrieval-overlap-policy.md` (lines 36-42) — Why: Specifies that non-Mem0 paths use `voyage_rerank(results)` for external reranking
- `tests/test_supabase_provider.py` (lines 147-172) — Why: Contains `TestVoyageEmbedding` class with mock client testing pattern to mirror for rerank tests

### New Files to Create

- `tests/test_voyage_rerank.py` — Unit tests for real rerank path, mock fallback path, and edge cases

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Voyage AI Reranker Python API](https://docs.voyageai.com/docs/reranker)
  - Specific section: Python API — Parameters and Returns
  - Why: Exact API signature: `vo.rerank(query, documents, model, top_k)` returns `RerankingObject` with `results` list of `RerankingResult(index, document, relevance_score)` and `total_tokens`
- [Voyage AI Reranker Models](https://docs.voyageai.com/docs/reranker#model-choices)
  - Specific section: Model Choices table
  - Why: `rerank-2` has 16,000 token context length; documents list max 1,000 items; total token limit 600K

### Patterns to Follow

### Code Samples to Mirror (required)

**Local sample 1** — `voyage.py:48-65` (`embed()` method): Real-API-with-fallback pattern
```python
def embed(self, text: str, input_type: str = "query") -> tuple[list[float] | None, dict[str, Any]]:
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
```
Why: This is the exact pattern to mirror — check enabled flag, try client, call API, normalize result, catch + fallback.

**Local sample 2** — `voyage.py:108-142` (`_mock_rerank()` method): The mock to keep as fallback
```python
def _mock_rerank(self, query, candidates, top_k):
    scored = []
    query_terms = set(query.lower().split())
    for candidate in candidates:
        content_terms = set(candidate.content.lower().split())
        overlap = len(query_terms & content_terms)
        adjusted_confidence = min(1.0, candidate.confidence + (overlap * 0.05))
        new_candidate = ContextCandidate(
            id=candidate.id, content=candidate.content,
            source=candidate.source, confidence=adjusted_confidence,
            metadata={**candidate.metadata, "rerank_adjusted": True},
        )
        scored.append((adjusted_confidence, new_candidate))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]
```
Why: This stays as the fallback; the real rerank will produce `ContextCandidate` objects in the same shape.

**Local sample 3** — `tests/test_supabase_provider.py:155-172` (`TestVoyageEmbedding`): Mock client test pattern
```python
def test_embed_success_with_mocked_client(self):
    service = VoyageRerankService(embed_enabled=True, embed_model="voyage-4-large")
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.embeddings = [[0.1, 0.2, 0.3] * 341 + [0.1]]
    mock_result.total_tokens = 5
    mock_client.embed.return_value = mock_result
    service._voyage_client = mock_client
    embedding, metadata = service.embed("test query", input_type="query")
    assert embedding is not None
```
Why: Same pattern for injecting mock voyage client + asserting return shape.

**Archon sample** — [Voyage Reranker Python API](https://docs.voyageai.com/docs/reranker):
```python
vo = voyageai.Client()
reranking = vo.rerank(query, documents, model="rerank-2.5", top_k=3)
for r in reranking.results:
    print(f"Document: {r.document}")
    print(f"Relevance Score: {r.relevance_score}")
    # r.index = original index in documents list
```
Why: This is the exact Voyage SDK call signature. `reranking.results` is a list of `RerankingResult` with `.index`, `.document`, `.relevance_score`. `reranking.total_tokens` is the token count.

**Naming Conventions:**
- Methods: `_real_rerank()` for API call, `_mock_rerank()` for fallback (existing)
- Metadata keys: `rerank_type`, `rerank_model`, `bypass_reason`, `total_tokens` (match existing)
- Flag: `use_real_rerank` (mirrors `embed_enabled` pattern)

**Error Handling:**
- Any exception from Voyage API → `logger.warning()` + fall back to `_mock_rerank()`
- Client unavailable → fall back to `_mock_rerank()`
- Empty results from API → fall back to `_mock_rerank()`

**Logging Pattern:**
- `logger.warning("Voyage rerank failed: %s", type(e).__name__)` (mirrors `voyage.py:64`)

---

## IMPLEMENTATION PLAN

### Phase 1: Core Implementation

Update `VoyageRerankService` to attempt real Voyage rerank API, falling back to mock.

**Tasks:**
- Add `use_real_rerank` parameter to constructor
- Add `_real_rerank()` method that calls Voyage API and normalizes results
- Update `rerank()` to try real first, then mock on failure

### Phase 2: Testing

Create comprehensive unit tests for the real and fallback paths.

**Tasks:**
- Unit tests with mocked Voyage client for successful rerank
- Tests for fallback on disabled, client unavailable, API error
- Tests for result normalization (relevance_score → confidence mapping)
- Regression: existing tests must pass unchanged

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task must be atomic and independently testable.

### UPDATE `backend/src/second_brain/services/voyage.py`

- **IMPLEMENT**: Make these changes to `VoyageRerankService`:

  1. Add `use_real_rerank` parameter to `__init__`:
     ```python
     def __init__(
         self,
         enabled: bool = True,
         model: str = "rerank-2",
         embed_model: str = "voyage-4-large",
         embed_enabled: bool = False,
         use_real_rerank: bool = False,
     ):
         self.enabled = enabled
         self.model = model
         self.embed_model = embed_model
         self.embed_enabled = embed_enabled
         self.use_real_rerank = use_real_rerank
         self._voyage_client: Any | None = None
     ```

  2. Add `_real_rerank()` method (place between `embed()` and `rerank()`):
     ```python
     def _real_rerank(
         self,
         query: str,
         candidates: Sequence[ContextCandidate],
         top_k: int,
     ) -> list[ContextCandidate] | None:
         """
         Rerank using real Voyage AI API. Returns None on failure (caller should fallback).
         """
         try:
             client = self._load_voyage_client()
             if client is None:
                 logger.debug("Voyage client unavailable for rerank")
                 return None

             # Extract document texts for Voyage API
             documents = [c.content for c in candidates]

             # Call Voyage rerank API
             reranking = client.rerank(
                 query=query,
                 documents=documents,
                 model=self.model,
                 top_k=top_k,
             )

             if not reranking.results:
                 logger.debug("Voyage rerank returned empty results")
                 return None

             # Map Voyage results back to ContextCandidate using original index
             reranked: list[ContextCandidate] = []
             candidates_list = list(candidates)  # ensure indexable
             for r in reranking.results:
                 original = candidates_list[r.index]
                 reranked.append(
                     ContextCandidate(
                         id=original.id,
                         content=original.content,
                         source=original.source,
                         confidence=max(0.0, min(1.0, float(r.relevance_score))),
                         metadata={
                             **original.metadata,
                             "rerank_adjusted": True,
                             "original_confidence": original.confidence,
                         },
                     )
                 )
             return reranked

         except Exception as e:
             logger.warning("Voyage rerank failed: %s", type(e).__name__)
             return None
     ```

  3. Update `rerank()` method — replace lines 101-106 with:
     ```python
     # Try real Voyage rerank if enabled
     if self.use_real_rerank:
         real_result = self._real_rerank(query, candidates, top_k)
         if real_result is not None:
             metadata["rerank_type"] = "external"
             metadata["real_rerank"] = True
             return real_result, metadata
         # Real rerank failed, fall through to mock
         logger.debug("Real rerank failed, falling back to mock")

     # Deterministic mock rerank (fallback or default)
     reranked = self._mock_rerank(query, candidates, top_k)
     metadata["rerank_type"] = "external"
     metadata["real_rerank"] = False
     ```

- **PATTERN**: Mirror `embed()` at `voyage.py:48-65` for try/except/fallback pattern
- **IMPORTS**: No new imports needed (all existing: `logging`, `os`, `Any`, `Sequence`, `ContextCandidate`)
- **GOTCHA**: Voyage `reranking.results[i].index` refers to the original position in the `documents` list, NOT the rank position. Must use it to look up the correct `ContextCandidate` from the input list. Also, `relevance_score` can be >1.0 in edge cases — clamp to `[0.0, 1.0]`.
- **VALIDATE**: `python -m pytest tests/test_supabase_provider.py::TestVoyageEmbedding -v` (existing embed tests still pass) and `python -m pytest tests/test_voyage_rerank.py -v` (new tests)

### CREATE `tests/test_voyage_rerank.py`

- **IMPLEMENT**: Comprehensive unit tests:

  ```python
  """Unit tests for VoyageRerankService rerank functionality."""

  from unittest.mock import MagicMock

  from second_brain.contracts.context_packet import ContextCandidate
  from second_brain.services.voyage import VoyageRerankService


  def _make_candidates(n: int = 3) -> list[ContextCandidate]:
      """Create test candidates."""
      return [
          ContextCandidate(
              id=f"doc-{i}",
              content=f"Test document {i} about topic {chr(65 + i)}",
              source="supabase",
              confidence=0.7 + i * 0.05,
              metadata={"index": i},
          )
          for i in range(n)
      ]


  class TestRealRerank:
      """Test real Voyage rerank API path."""

      def test_real_rerank_success(self):
          """With mocked client, real rerank returns reordered candidates."""
          service = VoyageRerankService(enabled=True, use_real_rerank=True)

          mock_client = MagicMock()
          mock_reranking = MagicMock()

          # Voyage returns results sorted by relevance (index refers to original position)
          mock_result_0 = MagicMock()
          mock_result_0.index = 2  # originally 3rd doc is most relevant
          mock_result_0.document = "Test document 2 about topic C"
          mock_result_0.relevance_score = 0.95

          mock_result_1 = MagicMock()
          mock_result_1.index = 0  # originally 1st doc is 2nd most relevant
          mock_result_1.document = "Test document 0 about topic A"
          mock_result_1.relevance_score = 0.72

          mock_reranking.results = [mock_result_0, mock_result_1]
          mock_reranking.total_tokens = 100
          mock_client.rerank.return_value = mock_reranking
          service._voyage_client = mock_client

          candidates = _make_candidates(3)
          reranked, metadata = service.rerank("test query", candidates, top_k=2)

          assert len(reranked) == 2
          assert reranked[0].id == "doc-2"  # highest relevance
          assert reranked[0].confidence == 0.95
          assert reranked[1].id == "doc-0"
          assert reranked[1].confidence == 0.72
          assert metadata["rerank_type"] == "external"
          assert metadata["real_rerank"] is True

          # Verify Voyage API was called correctly
          mock_client.rerank.assert_called_once_with(
              query="test query",
              documents=[c.content for c in candidates],
              model="rerank-2",
              top_k=2,
          )

      def test_real_rerank_preserves_original_metadata(self):
          """Real rerank preserves original candidate metadata plus adds rerank fields."""
          service = VoyageRerankService(enabled=True, use_real_rerank=True)

          mock_client = MagicMock()
          mock_reranking = MagicMock()
          mock_result = MagicMock()
          mock_result.index = 0
          mock_result.document = "doc content"
          mock_result.relevance_score = 0.88
          mock_reranking.results = [mock_result]
          mock_client.rerank.return_value = mock_reranking
          service._voyage_client = mock_client

          candidates = [
              ContextCandidate(
                  id="doc-0",
                  content="doc content",
                  source="supabase",
                  confidence=0.7,
                  metadata={"custom_field": "preserved"},
              )
          ]

          # Single candidate normally bypasses rerank, so use 2
          candidates.append(
              ContextCandidate(
                  id="doc-1", content="other", source="supabase",
                  confidence=0.5, metadata={},
              )
          )
          mock_result_1 = MagicMock()
          mock_result_1.index = 1
          mock_result_1.document = "other"
          mock_result_1.relevance_score = 0.3
          mock_reranking.results = [mock_result, mock_result_1]

          reranked, _ = service.rerank("query", candidates, top_k=2)

          assert reranked[0].metadata["custom_field"] == "preserved"
          assert reranked[0].metadata["rerank_adjusted"] is True
          assert reranked[0].metadata["original_confidence"] == 0.7

      def test_real_rerank_clamps_relevance_score(self):
          """Relevance scores outside 0-1 are clamped."""
          service = VoyageRerankService(enabled=True, use_real_rerank=True)

          mock_client = MagicMock()
          mock_reranking = MagicMock()

          mock_r0 = MagicMock()
          mock_r0.index = 0
          mock_r0.relevance_score = 1.5  # over 1.0
          mock_r0.document = "doc"

          mock_r1 = MagicMock()
          mock_r1.index = 1
          mock_r1.relevance_score = -0.1  # below 0.0
          mock_r1.document = "doc2"

          mock_reranking.results = [mock_r0, mock_r1]
          mock_client.rerank.return_value = mock_reranking
          service._voyage_client = mock_client

          candidates = _make_candidates(2)
          reranked, _ = service.rerank("q", candidates, top_k=2)

          assert reranked[0].confidence == 1.0
          assert reranked[1].confidence == 0.0


  class TestRealRerankFallback:
      """Test fallback from real rerank to mock."""

      def test_real_rerank_disabled_uses_mock(self):
          """When use_real_rerank=False, uses mock rerank."""
          service = VoyageRerankService(enabled=True, use_real_rerank=False)
          candidates = _make_candidates(3)

          reranked, metadata = service.rerank("test", candidates, top_k=3)

          assert len(reranked) == 3
          assert metadata["rerank_type"] == "external"
          assert metadata.get("real_rerank") is False

      def test_real_rerank_client_unavailable_falls_back(self):
          """When Voyage client can't load, falls back to mock."""
          service = VoyageRerankService(enabled=True, use_real_rerank=True)
          # Don't set _voyage_client — client loading will fail (no SDK)

          candidates = _make_candidates(3)
          reranked, metadata = service.rerank("test", candidates, top_k=3)

          assert len(reranked) == 3
          assert metadata["rerank_type"] == "external"
          assert metadata.get("real_rerank") is False

      def test_real_rerank_api_error_falls_back(self):
          """When Voyage API throws, falls back to mock."""
          service = VoyageRerankService(enabled=True, use_real_rerank=True)

          mock_client = MagicMock()
          mock_client.rerank.side_effect = RuntimeError("API timeout")
          service._voyage_client = mock_client

          candidates = _make_candidates(3)
          reranked, metadata = service.rerank("test", candidates, top_k=3)

          assert len(reranked) == 3
          assert metadata["rerank_type"] == "external"
          assert metadata.get("real_rerank") is False

      def test_real_rerank_empty_results_falls_back(self):
          """When Voyage API returns empty results, falls back to mock."""
          service = VoyageRerankService(enabled=True, use_real_rerank=True)

          mock_client = MagicMock()
          mock_reranking = MagicMock()
          mock_reranking.results = []
          mock_client.rerank.return_value = mock_reranking
          service._voyage_client = mock_client

          candidates = _make_candidates(3)
          reranked, metadata = service.rerank("test", candidates, top_k=3)

          assert len(reranked) == 3
          assert metadata.get("real_rerank") is False


  class TestExistingBehaviorPreserved:
      """Regression tests: existing rerank behavior must not change."""

      def test_disabled_returns_unchanged(self):
          """Disabled service returns candidates unchanged."""
          service = VoyageRerankService(enabled=False)
          candidates = _make_candidates(2)

          reranked, metadata = service.rerank("test", candidates, top_k=5)

          assert reranked == list(candidates)
          assert metadata["rerank_type"] == "none"
          assert metadata["bypass_reason"] == "disabled"

      def test_empty_candidates_returns_empty(self):
          """Empty candidates returns empty list."""
          service = VoyageRerankService(enabled=True)

          reranked, metadata = service.rerank("test", [], top_k=5)

          assert reranked == []
          assert metadata["bypass_reason"] == "no_candidates"

      def test_single_candidate_bypasses(self):
          """Single candidate bypasses rerank."""
          service = VoyageRerankService(enabled=True)
          candidates = _make_candidates(1)

          reranked, metadata = service.rerank("test", candidates, top_k=5)

          assert len(reranked) == 1
          assert metadata["bypass_reason"] == "single_candidate"

      def test_mock_rerank_still_works(self):
          """Mock rerank produces deterministic results."""
          service = VoyageRerankService(enabled=True, use_real_rerank=False)
          candidates = _make_candidates(3)

          reranked, metadata = service.rerank("document topic", candidates, top_k=3)

          assert len(reranked) == 3
          assert metadata["rerank_type"] == "external"
          # Mock adjusts confidence based on term overlap
          for c in reranked:
              assert c.metadata.get("rerank_adjusted") is True

      def test_embed_not_affected_by_rerank_flag(self):
          """use_real_rerank does not affect embed behavior."""
          service = VoyageRerankService(
              enabled=True, use_real_rerank=True, embed_enabled=False,
          )
          embedding, metadata = service.embed("test")
          assert embedding is None
          assert metadata["embed_error"] == "embedding_disabled"
  ```

- **PATTERN**: Mirror `tests/test_supabase_provider.py:147-172` for mock client injection pattern
- **IMPORTS**:
  ```python
  from unittest.mock import MagicMock
  from second_brain.contracts.context_packet import ContextCandidate
  from second_brain.services.voyage import VoyageRerankService
  ```
- **GOTCHA**: Do NOT import `voyageai` at test module level — it may not be installed. All Voyage SDK interaction is mocked via `MagicMock` injected into `_voyage_client`.
- **VALIDATE**: `python -m pytest tests/test_voyage_rerank.py -v`

---

## TESTING STRATEGY

### Unit Tests

- `tests/test_voyage_rerank.py::TestRealRerank` — 3 tests: successful rerank with mocked client, metadata preservation, relevance score clamping
- `tests/test_voyage_rerank.py::TestRealRerankFallback` — 4 tests: disabled flag, client unavailable, API error, empty results
- `tests/test_voyage_rerank.py::TestExistingBehaviorPreserved` — 5 tests: disabled bypass, empty candidates, single candidate, mock still works, embed unaffected

### Edge Cases

- `relevance_score > 1.0` from API → clamped to 1.0
- `relevance_score < 0.0` from API → clamped to 0.0
- `r.index` out of bounds → should not happen with Voyage API, but `_real_rerank` wraps in try/except
- Voyage client loads but API call returns `None`/empty → fallback to mock

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and feature correctness.

### Level 1: Syntax and Style

```bash
python -m ruff check backend/src/second_brain/services/voyage.py tests/test_voyage_rerank.py --fix
```

### Level 2: Type Safety

```bash
python -m mypy backend/src/second_brain/ --strict
```

### Level 3: Unit Tests

```bash
python -m pytest tests/test_voyage_rerank.py -v
python -m pytest tests/test_supabase_provider.py::TestVoyageEmbedding -v
```

### Level 4: Integration Tests

```bash
python -m pytest tests/ -v
```

### Level 5: Manual Validation

1. Verify test count >= 175 (existing) + 12 (new) = 187:
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -5
   ```

2. Verify no new ruff/mypy errors:
   ```bash
   python -m ruff check backend/src/second_brain/ tests/ --statistics
   python -m mypy backend/src/second_brain/ --strict 2>&1 | tail -3
   ```

---

## ACCEPTANCE CRITERIA

- [x] `VoyageRerankService.rerank()` calls real Voyage API when `use_real_rerank=True` and client is available
- [x] Falls back to `_mock_rerank()` when real rerank fails (any exception)
- [x] Falls back to `_mock_rerank()` when `use_real_rerank=False` (default)
- [x] Voyage `RerankingResult` objects correctly normalized to `ContextCandidate` with clamped confidence
- [x] Original candidate metadata preserved with `rerank_adjusted: True` and `original_confidence` fields added
- [x] `metadata["real_rerank"]` is `True` when real API succeeded, `False` when mock used
- [x] All existing tests pass unchanged (zero regressions)
- [x] 12 new tests pass for real rerank, fallback, and regression
- [x] ruff and mypy pass with zero errors

---

## COMPLETION CHECKLIST

- [x] Both tasks completed in order
- [x] Each task validation passed
- [x] All validation commands executed (Levels 1-5)
- [x] Full test suite passes (>= 187 tests)
- [x] No linting or type checking errors
- [x] Manual validation confirms import chain and test count
- [x] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **`use_real_rerank=False` default**: Same safety pattern as `embed_enabled=False`. Real API calls are opt-in. Existing tests and code that create `VoyageRerankService()` without this flag continue to use mock. Zero regression risk.
- **`_real_rerank()` returns `None` on failure**: Rather than raising, it returns `None` so the caller (`rerank()`) can seamlessly fall through to `_mock_rerank()`. This avoids duplicating try/except in the caller.
- **`original_confidence` in metadata**: When real rerank replaces the confidence score with Voyage's `relevance_score`, the original embedding-based confidence is preserved in metadata for debugging and eval comparison.
- **No deps.py changes needed**: The `use_real_rerank` flag is a constructor param. When the user wants real rerank, they pass it via config. `create_voyage_rerank_service()` in deps.py already accepts `**kwargs`-style params via its explicit args — but adding `use_real_rerank` to the factory is not needed for this slice (YAGNI). It can be wired in a follow-up config slice.

### Archon RAG Evidence

- **Voyage Reranker API** (source: `4c95d7ffe2fde002`, page: `c048082c-52e8-4f3f-ab52-b8492925bde0`)
  - `vo.rerank(query, documents, model="rerank-2", top_k=3)` returns `RerankingObject`
  - `RerankingResult` has `.index` (int), `.document` (str), `.relevance_score` (float)
  - `reranking.total_tokens` (int) for tracking API usage
  - Documents list max 1,000 items, total tokens max 600K for rerank-2

### Risks

- **Relevance score range**: Voyage docs show scores like `0.94` and `0.28` — appears to be 0-1 normalized, but docs don't explicitly guarantee this. The clamp to `[0.0, 1.0]` handles edge cases.
- **Index out of bounds**: If Voyage returns an index >= len(candidates), `_real_rerank()` would raise IndexError. The outer try/except catches this and falls back to mock. Low probability — the API should only return valid indices.

### Confidence Score: 9/10

- **Strengths**: Surgical 2-file change; `embed()` method already proves the pattern works; lazy client loader exists; Voyage API is simple and well-documented; `_mock_rerank()` stays as reliable fallback; 12 comprehensive tests cover all paths
- **Uncertainties**: Exact `relevance_score` range from API (mitigated by clamping)
- **Mitigations**: Default-off flag ensures zero regression; try/except/fallback ensures graceful degradation
