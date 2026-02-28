# P1-18: Hybrid Search RPC — Structured Implementation Plan

## Spec Summary

**ID**: P1-18  
**Name**: hybrid-search-rpc  
**Depth**: heavy  
**Depends**: P1-17 (full-text-search)  
**Branch**: `feat/P1-18-hybrid-search-rpc` (off `feat/P1-17-full-text-search`)

## Acceptance Criteria

1. Hybrid search returns better results than vector-only or keyword-only for test queries.
2. RRF (Reciprocal Rank Fusion) weights are configurable (vector_weight, text_weight).
3. Single RPC call (`hybrid_search_knowledge_chunks`) — NOT two separate calls merged in Python.
4. Active-only chunks returned (same filter as FTS and vector search).
5. Results include: `id`, `content`, `knowledge_type`, `document_id`, `chunk_index`, `source_origin`, `metadata`, `rrf_score`, `vector_rank`, `text_rank`.
6. `SupabaseProvider.hybrid_search()` method added — mirrors `search()` but calls the new RPC.
7. Tests validate migration SQL structure and Python method behavior via mocks.

---

## Related Memories

- P1-17 added `content_tsv` tsvector + GIN index + `search_knowledge_chunks_fulltext` RPC.
- `match_knowledge_chunks` RPC (migration 001) does vector search via `embedding <=> query_embedding` cosine distance.
- `knowledge_chunks` table has: `id`, `content`, `embedding` (vector(1024)), `knowledge_type`, `document_id`, `chunk_index`, `source_origin`, `metadata`, `status`, `content_hash`, `version`, `content_tsv`.
- `status = 'active'` filter required on all search RPCs.
- All RPCs: `SECURITY DEFINER`, `REVOKE ALL FROM public`, `GRANT EXECUTE TO service_role`.
- `supabase.py` `_normalize_results()` handles mapping RPC row → `MemorySearchResult`. Will need a parallel `_normalize_hybrid_results()` for the new columns (`rrf_score` instead of `similarity`).
- Test pattern for P1-17: pure SQL content assertions (no live DB). Same pattern applies here.
- `requests/` is in `.gitignore` — use `git add -f` to force-add plan commit.
- mypy has 1 pre-existing error (mem0 stubs, ignore).
- 11 pre-existing failures in `test_migration_policy.py` (FileNotFoundError) — skip in pytest count.

---

## Relevant Documentation

### RRF Formula
```
rrf_score(d) = Σ_r  1 / (k + rank_r(d))
```
- `k` = 60 (standard constant, dampens high-rank outliers)
- For two signals: `rrf_score = 1/(k + vector_rank) + 1/(k + text_rank)`
- When a result appears in only one list, the missing rank is treated as infinity → contribution = 0.
- Weights: multiply each term: `(vector_weight / (k + vector_rank)) + (text_weight / (k + text_rank))`

### PostgreSQL Implementation Strategy
Use a CTE structure:
1. `vector_results` CTE: `match_knowledge_chunks` logic inlined (no function call within CTE — direct query).
2. `text_results` CTE: `search_knowledge_chunks_fulltext` logic inlined.
3. `combined` CTE: FULL OUTER JOIN on chunk id.
4. Final SELECT: compute RRF score, ORDER BY DESC, LIMIT.

Why inline instead of calling the existing RPCs?
- Calling RPC within RPC is not supported in Supabase PostgREST.
- Inlining the vector and FTS queries into CTEs is the standard approach.

### Vector Search Logic (from migration 001)
```sql
SELECT id, content, 1 - (embedding <=> query_embedding) AS similarity, ...
FROM knowledge_chunks
WHERE 1 - (embedding <=> query_embedding) >= match_threshold
  AND status = 'active'
ORDER BY embedding <=> query_embedding
LIMIT pool_size
```

### Full-Text Search Logic (from migration 008)
```sql
SELECT id, content, ts_rank_cd(content_tsv, tsquery_val) AS rank, ...
FROM knowledge_chunks
WHERE content_tsv @@ tsquery_val
  AND status = 'active'
ORDER BY rank DESC
LIMIT pool_size
```

### RRF SQL Pattern
```sql
WITH vector_results AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> query_embedding) AS vrank
  FROM knowledge_chunks
  WHERE 1 - (embedding <=> query_embedding) >= match_threshold
    AND status = 'active'
  LIMIT pool_size
),
text_results AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(content_tsv, tsquery_val) DESC) AS trank
  FROM knowledge_chunks
  WHERE content_tsv @@ tsquery_val
    AND status = 'active'
  LIMIT pool_size
),
combined AS (
  SELECT COALESCE(v.id, t.id) AS id,
         v.vrank,
         t.trank
  FROM vector_results v
  FULL OUTER JOIN text_results t ON v.id = t.id
),
scored AS (
  SELECT id,
         (COALESCE(vector_weight / (60.0 + vrank), 0.0)
        + COALESCE(text_weight   / (60.0 + trank), 0.0)) AS rrf_score,
         vrank AS vector_rank,
         trank AS text_rank
  FROM combined
)
SELECT kc.id, kc.content, kc.knowledge_type, kc.document_id,
       kc.chunk_index, kc.source_origin, kc.metadata,
       s.rrf_score, s.vector_rank, s.text_rank
FROM scored s
JOIN knowledge_chunks kc ON kc.id = s.id
ORDER BY s.rrf_score DESC
LIMIT match_count;
```

---

## Patterns to Follow

### Existing `search()` method in `services/supabase.py`
```python
def search(self, query_embedding, top_k, threshold, filter_type) -> tuple[list[MemorySearchResult], dict]:
    metadata = {"provider": "supabase"}
    try:
        client = self._load_client()
        if client is None:
            return [], {**metadata, "fallback_reason": "client_unavailable"}
        response = client.rpc("match_knowledge_chunks", {...}).execute()
        results = self._normalize_results(response.data or [], top_k)
        return results, {**metadata, "real_provider": True, "raw_count": len(response.data or [])}
    except Exception as e:
        logger.warning("Supabase search failed: %s", type(e).__name__)
        return [], {**metadata, "fallback_reason": "provider_error", ...}
```

New `hybrid_search()` mirrors this pattern exactly — same try/except, same fallback, same metadata keys.

### `_normalize_results()` pattern → new `_normalize_hybrid_results()`
Same field extraction logic. The only difference:
- `rrf_score` instead of `similarity` → stored as `confidence` in `MemorySearchResult`
- Extra metadata keys: `vector_rank`, `text_rank`

### Test pattern (P1-17 style — pure SQL content assertions)
```python
def test_migration_file_exists():
    migration_file = pathlib.Path("migrations/009_hybrid_search.sql")
    assert migration_file.exists()

def test_rfc_function_name():
    sql = pathlib.Path("migrations/009_hybrid_search.sql").read_text()
    assert "hybrid_search_knowledge_chunks" in sql
```

For Python method tests: use MagicMock to mock Supabase client RPC.

---

## Solution Statement

### Migration: `migrations/009_hybrid_search.sql`

Create a single PostgreSQL function `hybrid_search_knowledge_chunks` that:
1. Takes: `query_embedding vector(1024)`, `query_text text`, `match_count int DEFAULT 10`, `match_threshold float DEFAULT 0.0`, `vector_weight float DEFAULT 1.0`, `text_weight float DEFAULT 1.0`, `filter_type text DEFAULT NULL`, `search_mode text DEFAULT 'websearch'`, `pool_size int DEFAULT 50`
2. Uses CTEs: `vector_results`, `text_results`, `combined`, `scored`
3. Returns: `id uuid`, `content text`, `knowledge_type text`, `document_id uuid`, `chunk_index integer`, `source_origin text`, `metadata jsonb`, `rrf_score float`, `vector_rank bigint`, `text_rank bigint`
4. Handles NULL vector_rank / text_rank (COALESCE to 0 contribution)
5. `SECURITY DEFINER`, `REVOKE ALL FROM public`, `GRANT EXECUTE TO service_role`

### Python: `services/supabase.py` additions

Add to `SupabaseProvider`:

```python
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
    """Hybrid search combining vector similarity + full-text (RRF). Returns (results, metadata)."""
    ...

def _normalize_hybrid_results(
    self,
    rpc_results: list[dict[str, Any]],
    top_k: int,
) -> list[MemorySearchResult]:
    """Normalize hybrid_search_knowledge_chunks RPC results to MemorySearchResult."""
    ...
```

### Tests: `tests/test_hybrid_search.py`

**SQL structure tests** (migration file assertions — same pattern as P1-17):
1. `test_migration_file_exists` — file exists
2. `test_rpc_function_name` — "hybrid_search_knowledge_chunks" in SQL
3. `test_rrf_formula_present` — "60.0 +" in SQL (k constant)
4. `test_vector_cte_present` — "vector_results" CTE in SQL
5. `test_text_cte_present` — "text_results" CTE in SQL
6. `test_combined_cte_present` — "FULL OUTER JOIN" or "combined" in SQL
7. `test_rrf_score_column_returned` — "rrf_score" in SQL
8. `test_vector_rank_column_returned` — "vector_rank" in SQL
9. `test_text_rank_column_returned` — "text_rank" in SQL
10. `test_active_status_filter` — "status = 'active'" in SQL
11. `test_security_definer_set` — "SECURITY DEFINER" in SQL
12. `test_grant_to_service_role` — "GRANT EXECUTE" and "service_role" in SQL
13. `test_configurable_weights` — "vector_weight" and "text_weight" as parameters in SQL
14. `test_pool_size_parameter` — "pool_size" in SQL
15. `test_match_threshold_parameter` — "match_threshold" in SQL

**Python method tests** (mock client):
16. `test_hybrid_search_returns_tuple` — returns (list, dict)
17. `test_hybrid_search_no_client_returns_empty` — client=None → empty list, "client_unavailable"
18. `test_hybrid_search_calls_correct_rpc` — asserts rpc called with "hybrid_search_knowledge_chunks"
19. `test_hybrid_search_passes_weights` — asserts vector_weight/text_weight passed to RPC
20. `test_hybrid_search_normalizes_rrf_score_to_confidence` — rrf_score maps to MemorySearchResult.confidence
21. `test_hybrid_search_includes_rank_metadata` — vector_rank and text_rank in result.metadata
22. `test_hybrid_search_exception_returns_fallback` — exception → empty list + "provider_error"
23. `test_hybrid_search_respects_top_k` — returns at most top_k results

---

## Implementation Plan — Step by Step

### Step 1: Create migration `migrations/009_hybrid_search.sql`

File content (exact, verbatim):

```sql
-- Migration 009: Hybrid search via Reciprocal Rank Fusion (RRF)
-- Combines vector similarity (embedding <=> query) + full-text (tsvector @@ tsquery)
-- into a single RPC call. Uses RRF formula: score = Σ weight/(k + rank).

CREATE OR REPLACE FUNCTION hybrid_search_knowledge_chunks(
  query_embedding   extensions.vector(1024),
  query_text        text,
  match_count       int     DEFAULT 10,
  match_threshold   float   DEFAULT 0.0,
  vector_weight     float   DEFAULT 1.0,
  text_weight       float   DEFAULT 1.0,
  filter_type       text    DEFAULT NULL,
  search_mode       text    DEFAULT 'websearch',
  pool_size         int     DEFAULT 50
)
RETURNS TABLE (
  id             uuid,
  content        text,
  knowledge_type text,
  document_id    uuid,
  chunk_index    integer,
  source_origin  text,
  metadata       jsonb,
  rrf_score      float,
  vector_rank    bigint,
  text_rank      bigint
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  tsquery_val tsquery;
BEGIN
  -- Build tsquery from search_mode parameter
  IF search_mode = 'phrase' THEN
    tsquery_val := phraseto_tsquery('english', query_text);
  ELSIF search_mode = 'simple' THEN
    tsquery_val := plainto_tsquery('english', query_text);
  ELSE
    tsquery_val := websearch_to_tsquery('english', query_text);
  END IF;

  RETURN QUERY
  WITH vector_results AS (
    SELECT
      kc.id,
      ROW_NUMBER() OVER (ORDER BY kc.embedding <=> query_embedding) AS vrank
    FROM knowledge_chunks kc
    WHERE
      1 - (kc.embedding <=> query_embedding) >= match_threshold
      AND kc.status = 'active'
      AND (filter_type IS NULL OR kc.knowledge_type = filter_type)
    LIMIT pool_size
  ),
  text_results AS (
    SELECT
      kc.id,
      ROW_NUMBER() OVER (
        ORDER BY ts_rank_cd(kc.content_tsv, tsquery_val) DESC
      ) AS trank
    FROM knowledge_chunks kc
    WHERE
      kc.content_tsv @@ tsquery_val
      AND kc.status = 'active'
      AND (filter_type IS NULL OR kc.knowledge_type = filter_type)
    LIMIT pool_size
  ),
  combined AS (
    SELECT
      COALESCE(v.id, t.id) AS chunk_id,
      v.vrank,
      t.trank
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.id = t.id
  ),
  scored AS (
    SELECT
      chunk_id,
      (
        COALESCE(vector_weight / (60.0 + vrank), 0.0)
      + COALESCE(text_weight   / (60.0 + trank), 0.0)
      ) AS rrf_score,
      vrank AS vector_rank,
      trank AS text_rank
    FROM combined
  )
  SELECT
    kc.id,
    kc.content,
    kc.knowledge_type,
    kc.document_id,
    kc.chunk_index,
    kc.source_origin,
    kc.metadata,
    s.rrf_score::float,
    s.vector_rank,
    s.text_rank
  FROM scored s
  JOIN knowledge_chunks kc ON kc.id = s.chunk_id
  ORDER BY s.rrf_score DESC
  LIMIT match_count;
END;
$$;

REVOKE ALL ON FUNCTION hybrid_search_knowledge_chunks(
  extensions.vector(1024), text, int, float, float, float, text, text, int
) FROM public;
GRANT EXECUTE ON FUNCTION hybrid_search_knowledge_chunks(
  extensions.vector(1024), text, int, float, float, float, text, text, int
) TO service_role;
```

### Step 2: Add `hybrid_search()` and `_normalize_hybrid_results()` to `services/supabase.py`

Append after the existing `_sanitize_error_message` method. Do NOT touch existing methods.

```python
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

    for i, row in enumerate(rpc_results):
        rrf_score = row.get("rrf_score", 0.0)
        try:
            confidence = max(0.0, min(1.0, float(rrf_score)))
        except (TypeError, ValueError):
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
        except (TypeError, ValueError):
            chunk_index = 0
        raw_source_origin = str(row.get("source_origin", "manual"))
        source_origin = (
            raw_source_origin if raw_source_origin in _VALID_SOURCE_ORIGINS else "manual"
        )

        extra_metadata = row.get("metadata", {})
        if not isinstance(extra_metadata, dict):
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
```

### Step 3: Create `tests/test_hybrid_search.py`

Full test file with 23 tests (15 SQL structure + 8 Python method tests).

SQL structure tests (import pathlib, read migration file, assert strings).

Python method tests (use `unittest.mock.MagicMock` to mock supabase client).

Template for mock tests:
```python
from unittest.mock import MagicMock, patch
from second_brain.services.supabase import SupabaseProvider

def _make_provider():
    return SupabaseProvider(config={"supabase_url": "http://test", "supabase_key": "test-key"})

def _make_mock_client(data):
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = data
    return mock_client

def test_hybrid_search_returns_tuple():
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        result = provider.hybrid_search([0.0] * 1024, "machine learning")
    assert isinstance(result, tuple)
    assert len(result) == 2

def test_hybrid_search_no_client_returns_empty():
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        results, meta = provider.hybrid_search([0.0] * 1024, "test")
    assert results == []
    assert meta["fallback_reason"] == "client_unavailable"

def test_hybrid_search_calls_correct_rpc():
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.hybrid_search([0.0] * 1024, "machine learning")
    mock_client.rpc.assert_called_once()
    call_args = mock_client.rpc.call_args
    assert call_args[0][0] == "hybrid_search_knowledge_chunks"

def test_hybrid_search_passes_weights():
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.hybrid_search([0.0] * 1024, "test", vector_weight=0.7, text_weight=0.3)
    call_params = mock_client.rpc.call_args[0][1]
    assert call_params["vector_weight"] == 0.7
    assert call_params["text_weight"] == 0.3

def test_hybrid_search_normalizes_rrf_score():
    provider = _make_provider()
    mock_data = [{
        "id": "abc123", "content": "ML content", "rrf_score": 0.015,
        "knowledge_type": "document", "document_id": None,
        "chunk_index": 0, "source_origin": "manual",
        "metadata": {}, "vector_rank": 1, "text_rank": 2
    }]
    mock_client = _make_mock_client(mock_data)
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.hybrid_search([0.0] * 1024, "ML")
    assert len(results) == 1
    assert results[0].confidence == 0.015

def test_hybrid_search_includes_rank_metadata():
    provider = _make_provider()
    mock_data = [{
        "id": "abc123", "content": "test", "rrf_score": 0.01,
        "knowledge_type": "document", "document_id": None,
        "chunk_index": 0, "source_origin": "manual",
        "metadata": {}, "vector_rank": 3, "text_rank": 5
    }]
    mock_client = _make_mock_client(mock_data)
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.hybrid_search([0.0] * 1024, "test")
    assert results[0].metadata["vector_rank"] == 3
    assert results[0].metadata["text_rank"] == 5

def test_hybrid_search_exception_returns_fallback():
    provider = _make_provider()
    mock_client = MagicMock()
    mock_client.rpc.side_effect = RuntimeError("connection failed")
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, meta = provider.hybrid_search([0.0] * 1024, "test")
    assert results == []
    assert meta["fallback_reason"] == "provider_error"

def test_hybrid_search_respects_top_k():
    provider = _make_provider()
    mock_data = [
        {"id": f"id-{i}", "content": f"content {i}", "rrf_score": 0.01 * (10 - i),
         "knowledge_type": "document", "document_id": None,
         "chunk_index": i, "source_origin": "manual",
         "metadata": {}, "vector_rank": i + 1, "text_rank": i + 1}
        for i in range(10)
    ]
    mock_client = _make_mock_client(mock_data)
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.hybrid_search([0.0] * 1024, "test", top_k=3)
    assert len(results) == 3
```

---

## Validation Commands

```bash
# Run from backend/ directory
cd backend && mypy --strict src/second_brain/services/supabase.py
cd backend && ruff check src/second_brain/services/supabase.py
cd backend && python -m pytest tests/test_hybrid_search.py -v
```

Expected: 0 mypy errors (for this file), 0 ruff violations, 23/23 tests pass.

---

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `backend/migrations/009_hybrid_search.sql` | CREATE | Full RRF RPC function |
| `backend/src/second_brain/services/supabase.py` | MODIFY | Add `hybrid_search()` + `_normalize_hybrid_results()` |
| `backend/tests/test_hybrid_search.py` | CREATE | 23 tests (15 SQL + 8 Python) |

---

## Notes for Implementer

1. Do NOT call existing RPCs from within the new RPC — inline the SQL directly into CTEs.
2. The `query_embedding` parameter is `extensions.vector(1024)` — must match existing schema.
3. The `COALESCE(vector_weight / (60.0 + vrank), 0.0)` pattern handles NULL vrank gracefully (chunk appeared only in text results).
4. `rrf_score::float` cast needed because PostgreSQL arithmetic on bigint and float may produce numeric.
5. `search_path = public, extensions` required so `vector` type resolves correctly.
6. In test mock for `_make_mock_client`: `mock_client.rpc.return_value.execute.return_value.data = data` — this is the Supabase SDK chain pattern.
7. mypy: `hybrid_search` return type is `tuple[list[MemorySearchResult], dict[str, Any]]` — explicit annotation required for `--strict` compliance.
8. Do NOT add `Co-Authored-By` to commits.
