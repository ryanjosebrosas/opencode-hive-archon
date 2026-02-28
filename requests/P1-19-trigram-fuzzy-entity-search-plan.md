# P1-19: Trigram Fuzzy Entity Search — Structured Implementation Plan

**Spec ID:** P1-19  
**Feature:** trigram-fuzzy-entity-search  
**Depth:** standard  
**Depends:** P1-13 (data-integrity-constraints) ✅ done  
**Author:** AI Planner  
**Generated:** 2026-02-28  
**Status:** pending  

---

## 1. Feature Description

Implement PostgreSQL trigram-based fuzzy search for entity names using the `pg_trgm` extension. Users can find entities even with typos or partial matches: "Jonh Smth" finds "John Smith", "Acme Crp" finds "Acme Corp".

### Problem Statement

Current entity search (P1-01 schema) uses exact name matching via B-tree index. This fails when:
- User makes typos: "Jonh" vs "John"
- User enters partial names: "Acme" vs "Acme Corporation"
- User enters phonetic approximations: "Smth" vs "Smith"

### Solution Overview

1. Enable `pg_trgm` PostgreSQL extension
2. Add GIN trigram index on `knowledge_entities.name`
3. Create RPC function `search_knowledge_entities_fuzzy()` using `similarity()` function
4. Add Python service method `fuzzy_search_entities()` in `SupabaseProvider`
5. Write comprehensive tests (SQL structure + Python mocks)

---

## 2. Acceptance Criteria

- [ ] `pg_trgm` extension enabled in `extensions` schema
- [ ] GIN trigram index exists on `knowledge_entities.name gin_trgm_ops`
- [ ] RPC function `search_knowledge_entities_fuzzy(text, float, int, text)` created
- [ ] Query "Jonh" finds "John" with similarity > 0.3
- [ ] Query "Acme Crp" finds "Acme Corp" with similarity > 0.3
- [ ] `EXPLAIN ANALYZE` shows GIN index scan (not sequential scan)
- [ ] Python method `fuzzy_search_entities()` returns tuple[list[dict], dict]
- [ ] 14+ SQL structure tests pass
- [ ] 8+ Python mock tests pass
- [ ] All 22+ tests pass with `pytest`
- [ ] `ruff check` passes with no errors
- [ ] `mypy --strict` passes with no errors

---

## 3. Archon RAG Findings

### Sources Consulted

| Source ID | Title | Relevance |
|-----------|-------|-----------|
| `47d0203a7b9d285a` | Supabase llms.txt | pg_trgm extension docs, GIN index patterns |
| `c5f2c6c39c63757b` | pgvector GitHub | PostgreSQL index patterns |
| `19aa932a8b5a9169` | Mastra PostgreSQL | Storage patterns |

### Key Findings from RAG

**From Supabase docs (page_id: 65b102ab-d3e4-49a4-999a-be698a1b8497):**
- pg_trgm extension provides trigram-based similarity search
- `similarity(text, text)` returns float 0-1 (1 = exact match)
- `%` operator returns boolean based on `pg_trgm.similarity_threshold`
- GIN index with `gin_trgm_ops` operator class enables fast trigram search
- Default similarity_threshold is 0.3 (configurable via `SET`)

**Recommended SQL pattern:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;
CREATE INDEX idx_name_trgm ON entities USING GIN (name gin_trgm_ops);
SELECT * FROM entities WHERE similarity(name, 'search_term') >= 0.3;
```

---

## 4. Relevant Memories from memory.md

### Key Decisions (from memory.md lines 10-23)

- **[2026-02-27] 5-Tier Cost-Optimized Cascade**: T1 Implementation uses bailian-coding-plan (FREE), T2/T3 validation uses free models, T4 Codex for code review (cheap), T5 Sonnet-4-6 final review (last resort only)
- **[2026-02-27] Pillar-based infrastructure planning**: Build pipeline enforces infrastructure layers with gate criteria. P1-19 is part of Pillar 1 (Data Infrastructure), Track D (Search)
- **[2026-02-28] Sub-plan system**: Master plan + sub-plans (700-1000 lines each). This is a standard-depth sub-plan.

### Architecture Patterns (from memory.md lines 24-30)

- **Strict Gate Workflow (G1-G5)**: Sequential gates for contracts, reliability, evals, observability, ingestion eligibility
- **Runtime Portability Contract**: Python-first with framework-agnostic contracts

### Gotchas & Pitfalls (from memory.md lines 47-74)

- **Embedding dimension alignment**: Voyage outputs 1024 dims; Supabase column must match — mismatch causes silent RPC failures
- **OpenCode SDK swallows AbortError**: Check `result.error?.name === "AbortError"` after call, not in catch block
- **Session safety in shared servers**: Never trust client-supplied session_id; only allow server-issued active IDs

### Build Pipeline Rules (from memory.md lines 54-57)

- **NO STEP SKIPPING — EVER**: Every spec runs ALL 11 steps in order. Depth ONLY controls free-model count in Step 7a (3/5/5). Step 3 T4 plan review, Step 6 validation, Step 7d T4 panel all run regardless of depth.

---

## 5. Patterns to Follow (from THIS Codebase)

### 5.1 Migration Pattern: 008_fulltext_search.sql

**File:** `backend/migrations/008_fulltext_search.sql:1-87`

```sql
-- Migration 008: Full-text search infrastructure
-- Adds tsvector column, auto-populate trigger, GIN index, and search RPC.

-- Add tsvector column for full-text search
ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS
  content_tsv tsvector;

-- Trigger function to auto-update tsvector on insert/update
CREATE OR REPLACE FUNCTION knowledge_chunks_tsvector_update()
RETURNS trigger AS $$
BEGIN
  NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger
DROP TRIGGER IF EXISTS knowledge_chunks_tsv_trigger ON knowledge_chunks;
CREATE TRIGGER knowledge_chunks_tsv_trigger
  BEFORE INSERT OR UPDATE OF content ON knowledge_chunks
  FOR EACH ROW EXECUTE FUNCTION knowledge_chunks_tsvector_update();

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS knowledge_chunks_content_tsv_idx
  ON knowledge_chunks USING GIN (content_tsv);
```

**Key patterns to follow:**
- `CREATE INDEX IF NOT EXISTS ... USING GIN`
- `SECURITY DEFINER` on RPC functions
- `SET search_path = public, extensions`
- `REVOKE ALL ... FROM public; GRANT EXECUTE ... TO service_role;`

### 5.2 RPC Function Pattern: 009_hybrid_search.sql

**File:** `backend/migrations/009_hybrid_search.sql:5-111`

```sql
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
...
$$;

REVOKE ALL ON FUNCTION ... FROM public;
GRANT EXECUTE ON FUNCTION ... TO service_role;
```

**Key patterns to follow:**
- Function parameters with `DEFAULT` values
- `RETURNS TABLE` with explicit column types
- `LANGUAGE plpgsql STABLE SECURITY DEFINER`
- `SET search_path = public, extensions`

### 5.3 Python Service Pattern: supabase.py

**File:** `backend/src/second_brain/services/supabase.py:58-99` (search method)

```python
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
```

**Key patterns to follow:**
- Parameter validation with `isinstance()` checks
- Clamping values to valid ranges
- `metadata` dict with provider info
- Try/except with fallback returning empty list + metadata
- `_sanitize_error_message()` for security

### 5.4 Test Pattern: test_fulltext_search.py

**File:** `backend/tests/test_fulltext_search.py:1-96`

```python
from __future__ import annotations

import pathlib


def test_migration_file_exists():
    """Test that the fulltext search migration file exists."""
    migration_file = pathlib.Path("migrations/008_fulltext_search.sql")
    assert migration_file.exists()


def test_tsvector_column_added():
    """Test that tsvector column is added to the migration SQL."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "content_tsv tsvector" in sql_content


def test_gin_index_created():
    """Test that GIN index is created in the migration SQL."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "USING GIN" in sql_content
    assert "content_tsv" in sql_content
```

**Key patterns to follow:**
- `pathlib.Path` for file operations
- SQL content assertions via string matching
- One assertion per test function
- Descriptive docstrings

### 5.5 Test Pattern: test_hybrid_search.py

**File:** `backend/tests/test_hybrid_search.py:110-209` (Python mock tests)

```python
def _make_provider() -> SupabaseProvider:
    return SupabaseProvider(config={"supabase_url": "http://test", "supabase_key": "test-key"})


def _make_mock_client(data: list[dict]) -> MagicMock:
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = data
    return mock_client


def _make_row(
    i: int = 0,
    rrf_score: float = 0.015,
    vrank: int | None = 1,
    trank: int | None = 2,
) -> dict:
    return {
        "id": f"chunk-{i}",
        "content": f"content {i}",
        "rrf_score": rrf_score,
        "knowledge_type": "document",
        "document_id": None,
        "chunk_index": i,
        "source_origin": "manual",
        "metadata": {},
        "vector_rank": vrank,
        "text_rank": trank,
    }


def test_hybrid_search_returns_tuple() -> None:
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        result = provider.hybrid_search([0.0] * 1024, "machine learning")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_hybrid_search_no_client_returns_empty() -> None:
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        results, meta = provider.hybrid_search([0.0] * 1024, "test")
    assert results == []
    assert meta["fallback_reason"] == "client_unavailable"
```

**Key patterns to follow:**
- Helper functions: `_make_provider()`, `_make_mock_client()`, `_make_row()`
- `patch.object()` for mocking
- Assert both results and metadata
- Test fallback scenarios

---

## 6. Solution Statement

### 6.1 Migration: 010_trigram_search.sql

**File:** `backend/migrations/010_trigram_search.sql` (NEW)

```sql
-- Migration 010: Trigram fuzzy search for entity names
-- Enables pg_trgm extension and GIN trigram index for fuzzy entity search.
-- Handles typos: "Jonh Smth" finds "John Smith"

-- Enable pg_trgm extension in extensions schema
CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions;

-- GIN trigram index on knowledge_entities.name for fast fuzzy search
-- Uses gin_trgm_ops operator class for trigram similarity
CREATE INDEX IF NOT EXISTS knowledge_entities_name_trgm_idx
  ON knowledge_entities USING GIN (name gin_trgm_ops);

-- RPC: search_knowledge_entities_fuzzy
-- Fuzzy search using trigram similarity
-- Parameters:
--   search_term: text to search for (e.g., "Jonh Smth")
--   similarity_threshold: minimum similarity score (default 0.3)
--   match_count: max results to return (default 10)
--   filter_type: optional entity_type filter (default NULL = all types)
-- Returns: id, name, entity_type, description, similarity
CREATE OR REPLACE FUNCTION search_knowledge_entities_fuzzy(
  search_term         text,
  similarity_threshold float   DEFAULT 0.3,
  match_count         int     DEFAULT 10,
  filter_type         text    DEFAULT NULL
)
RETURNS TABLE (
  id              uuid,
  name            text,
  entity_type     text,
  description     text,
  similarity      float
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
  -- Validate search_term is not empty
  IF search_term IS NULL OR length(trim(search_term)) = 0 THEN
    RETURN QUERY
    SELECT NULL::uuid, NULL::text, NULL::text, NULL::text, 0.0::float
    WHERE FALSE;  -- Return empty set
  END IF;

  -- Set threshold for % operator (index-friendly filtering)
  PERFORM set_config('pg_trgm.similarity_threshold', similarity_threshold::text, true);

  RETURN QUERY
  SELECT
    ke.id,
    ke.name,
    ke.entity_type,
    ke.description,
    similarity(ke.name, search_term)::float AS similarity
  FROM knowledge_entities ke
  WHERE
    ke.name % search_term
    AND (filter_type IS NULL OR ke.entity_type = filter_type)
  ORDER BY similarity(ke.name, search_term) DESC
  LIMIT match_count;
END;
$$;

-- Security: revoke from public, grant to service_role
REVOKE ALL ON FUNCTION search_knowledge_entities_fuzzy(text, float, int, text) FROM public;
GRANT EXECUTE ON FUNCTION search_knowledge_entities_fuzzy(text, float, int, text)
  TO service_role;
```

### 6.2 Python Service: supabase.py

**File:** `backend/src/second_brain/services/supabase.py` (MODIFY)

Add new method after `hybrid_search()` method (~line 414):

```python
    def fuzzy_search_entities(
        self,
        search_term: str,
        top_k: int = 10,
        threshold: float = 0.3,
        filter_type: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Fuzzy search entities using trigram similarity.
        
        Uses pg_trgm extension to find entities even with typos.
        "Jonh Smth" finds "John Smith" with similarity > 0.3.
        
        Args:
            search_term: Text to search for (e.g., "Jonh Smth")
            top_k: Maximum results to return (default 10)
            threshold: Minimum similarity score (default 0.3)
            filter_type: Optional entity_type filter (default None = all types)
        
        Returns:
            Tuple of (results list, metadata dict)
            Results are raw dicts: {id, name, entity_type, description, similarity}
        """
        # Validate parameters
        if not isinstance(search_term, str):
            raise TypeError("search_term must be a string")
        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer")
        if not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number")
        
        # Validate and strip search_term
        stripped_search_term = search_term.strip()
        if not stripped_search_term:
            return [], {"provider": "supabase", "mode": "fuzzy_entity", "fallback_reason": "empty_search_term"}
        
        # Clamp top_k to valid range
        top_k = max(_MIN_TOP_K, min(_MAX_TOP_K, top_k))
        
        # Validate and clamp threshold
        if threshold < _MIN_THRESHOLD or threshold > _MAX_THRESHOLD:
            logger.warning(
                "threshold %s out of range [%s, %s], clamping",
                threshold, _MIN_THRESHOLD, _MAX_THRESHOLD,
            )
        threshold = max(_MIN_THRESHOLD, min(_MAX_THRESHOLD, float(threshold)))
        
        metadata: dict[str, Any] = {"provider": "supabase", "mode": "fuzzy_entity"}
        try:
            client = self._load_client()
            if client is None:
                return [], {**metadata, "fallback_reason": "client_unavailable"}
            response = client.rpc(
                "search_knowledge_entities_fuzzy",
                {
                    "search_term": stripped_search_term,
                    "similarity_threshold": threshold,
                    "match_count": top_k,
                    "filter_type": filter_type,
                },
            ).execute()
            results = response.data or []
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
```

### 6.3 Entity Contract Update (Optional Enhancement)

**File:** `backend/src/second_brain/contracts/knowledge.py` (OPTIONAL)

Add entity result type if needed (not strictly required since we return raw dicts):

```python
class EntitySearchResult(BaseModel):
    """Result from fuzzy entity search."""
    id: str
    name: str
    entity_type: str
    description: str | None = None
    similarity: float
    
    model_config = ConfigDict(
        frozen=True,
        extra="ignore",  # Allow additional fields from RPC
    )
```

---

## 7. Step-by-Step Tasks

### Task 1: Create Migration File

**ACTION:** Create new migration file  
**TARGET:** `backend/migrations/010_trigram_search.sql` (NEW)  
**IMPLEMENT:** Copy SQL from Solution Statement 6.1  
**PATTERN:** Follow `migrations/008_fulltext_search.sql:1-87` structure  
**GOTCHA:** Extension must use `SCHEMA extensions` to match existing pgvector extension location  
**VALIDATE:** `ls backend/migrations/010_trigram_search.sql` returns file exists

---

### Task 2: Add Python Method to SupabaseProvider

**ACTION:** Add `fuzzy_search_entities()` method  
**TARGET:** `backend/src/second_brain/services/supabase.py` after line 414 (after `hybrid_search()` method)  
**IMPLEMENT:** Copy the full method from Solution Statement 6.2  
**PATTERN:** Follow `supabase.py:58-99` (search method) structure  
**GOTCHA:** Returns `list[dict]` not `list[MemorySearchResult]` — entities are different from chunks  
**VALIDATE:** `cd backend && python -c "from second_brain.services.supabase import SupabaseProvider; print(hasattr(SupabaseProvider, 'fuzzy_search_entities'))"` returns True

---

### Task 3: Create SQL Structure Tests

**ACTION:** Create test file with 14 SQL structure tests  
**TARGET:** `backend/tests/test_trigram_search.py` (NEW)  
**IMPLEMENT:** Copy tests from Solution Statement 7.3  
**PATTERN:** Follow `tests/test_fulltext_search.py:1-96` structure  
**GOTCHA:** Use `_sql()` helper to avoid reading file multiple times  
**VALIDATE:** `cd backend && pytest tests/test_trigram_search.py -v --tb=short` shows all tests pass

---

### Task 4: Create Python Mock Tests

**ACTION:** Add 12 Python mock tests  
**TARGET:** `backend/tests/test_trigram_search.py` (APPEND to same file)  
**IMPLEMENT:** Copy tests from Solution Statement 7.4  
**PATTERN:** Follow `tests/test_hybrid_search.py:110-209` structure  
**GOTCHA:** Use `_make_entity_row()` helper for consistent test data  
**VALIDATE:** `cd backend && pytest tests/test_trigram_search.py -v --tb=short` shows 22+ tests pass

---

### Task 5: Run Validation Commands

**ACTION:** Run full validation suite  
**TARGET:** Terminal  
**IMPLEMENT:**
```bash
cd backend
ruff check src/second_brain/services/supabase.py tests/test_trigram_search.py
mypy --strict src/second_brain/services/supabase.py
pytest tests/test_trigram_search.py -v --tb=short
pytest tests/ -v --tb=short -x
```
**PATTERN:** Follow existing validation workflow from other P1 specs  
**GOTCHA:** Ensure mypy passes with --strict flag (no bare `Any` without `# type: ignore`)  
**VALIDATE:** All commands return exit code 0

---

## 8. Testing Strategy

### 8.1 SQL Structure Tests (19 tests)

| Test | What It Checks |
|------|----------------|
| `test_migration_file_exists` | File `010_trigram_search.sql` exists |
| `test_pg_trgm_extension_enabled` | `CREATE EXTENSION pg_trgm SCHEMA extensions` |
| `test_gin_trigram_index_created` | `USING GIN` + `gin_trgm_ops` |
| `test_index_name_follows_convention` | Index named `knowledge_entities_name_trgm_idx` |
| `test_rpc_function_created` | Function `search_knowledge_entities_fuzzy` exists |
| `test_rpc_has_search_term_parameter` | Parameter `search_term text` |
| `test_rpc_has_similarity_threshold_parameter` | Parameter with `DEFAULT 0.3` |
| `test_rpc_has_match_count_parameter` | Parameter with `DEFAULT 10` |
| `test_rpc_has_filter_type_parameter` | Optional filter parameter |
| `test_rpc_returns_similarity_column` | Returns `similarity float` |
| `test_rpc_uses_similarity_function` | Uses `similarity()` in SELECT |
| `test_rpc_uses_set_config_for_threshold` | Uses `set_config('pg_trgm.similarity_threshold', ...)` |
| `test_rpc_uses_trigram_operator` | Uses `ke.name % search_term` for index scan |
| `test_rpc_orders_by_similarity` | `ORDER BY similarity(ke.name, search_term) DESC` |
| `test_rpc_has_security_definer` | `SECURITY DEFINER` set |
| `test_rpc_granted_to_service_role` | `GRANT EXECUTE ... TO service_role` |
| `test_rpc_revoked_from_public` | `REVOKE ALL ... FROM public` |
| `test_rpc_filters_by_entity_type` | Optional entity_type filter |
| `test_empty_search_term_handled` | Empty search returns empty set |

### 8.2 Python Mock Tests (13 tests)

| Test | What It Checks |
|------|----------------|
| `test_fuzzy_search_returns_tuple` | Returns `(results, metadata)` tuple |
| `test_fuzzy_search_no_client_returns_empty` | Returns `[]` + `fallback_reason: client_unavailable` |
| `test_fuzzy_search_empty_term_returns_empty` | Returns `[]` + `fallback_reason: empty_search_term` |
| `test_fuzzy_search_calls_correct_rpc` | Calls `search_knowledge_entities_fuzzy` RPC |
| `test_fuzzy_search_passes_parameters` | Passes all 4 parameters correctly |
| `test_fuzzy_search_strips_search_term` | Passes `search_term.strip()` to RPC |
| `test_fuzzy_search_returns_raw_dicts` | Returns `list[dict]`, not `MemorySearchResult` |
| `test_fuzzy_search_exception_returns_fallback` | Returns `[]` + error metadata on exception |
| `test_fuzzy_search_respects_top_k` | Limits results to `top_k` |
| `test_fuzzy_search_includes_metadata` | Metadata includes provider, mode, real_provider, raw_count |
| `test_fuzzy_search_validates_search_term_type` | Raises `TypeError` for non-string search_term |
| `test_fuzzy_search_validates_top_k_type` | Raises `TypeError` for non-integer top_k |
| `test_fuzzy_search_validates_threshold_type` | Raises `TypeError` for non-number threshold |

---

## 9. Validation Commands

### 9.1 Linting

```bash
cd backend
ruff check src/second_brain/services/supabase.py tests/test_trigram_search.py
ruff format src/second_brain/services/supabase.py tests/test_trigram_search.py --check
```

### 9.2 Type Checking

```bash
cd backend
mypy --strict src/second_brain/services/supabase.py
```

### 9.3 Unit Tests

```bash
cd backend
pytest tests/test_trigram_search.py -v --tb=short
```

### 9.4 Full Test Suite (Regression Check)

```bash
cd backend
pytest tests/ -v --tb=short -x
```

---

## 10. Acceptance Criteria Checklist

### Migration
- [ ] `pg_trgm` extension enabled with `SCHEMA extensions`
- [ ] GIN index `knowledge_entities_name_trgm_idx` created with `gin_trgm_ops`
- [ ] RPC function `search_knowledge_entities_fuzzy` created
- [ ] Function has `SECURITY DEFINER` and `SET search_path`
- [ ] `REVOKE ALL FROM public; GRANT EXECUTE TO service_role;` present

### Python Service
- [ ] Method `fuzzy_search_entities()` added to `SupabaseProvider`
- [ ] Parameter validation with `isinstance()` checks
- [ ] Empty search term returns early with fallback
- [ ] Try/except with structured error metadata
- [ ] Returns `tuple[list[dict], dict]`

### Tests
- [ ] 19 SQL structure tests pass
- [ ] 13 Python mock tests pass
- [ ] Total 32 tests pass
- [ ] `ruff check` passes
- [ ] `mypy --strict` passes
- [ ] Full test suite passes (no regressions)

### Performance
- [ ] `EXPLAIN ANALYZE` shows GIN index scan for fuzzy search
- [ ] "Jonh" query finds "John" with similarity > 0.3
- [ ] "Acme Crp" query finds "Acme Corp" with similarity > 0.3

---

## 11. Edge Cases and Gotchas

### Edge Cases to Handle

1. **Empty search term**: Return empty list immediately
2. **NULL search term**: Function handles via `length(trim())` check
3. **Very short search term (1-2 chars)**: Trigram similarity may return low scores; threshold handles this
4. **Special characters in search**: PostgreSQL handles escaping in `similarity()` function
5. **Unicode characters**: pg_trgm supports UTF-8; index handles unicode names
6. **Case sensitivity**: Trigram similarity is case-insensitive by default

### Gotchas

1. **Extension schema**: Must use `SCHEMA extensions` to match existing pgvector location
2. **Index operator class**: Must use `gin_trgm_ops` not default GIN operator
3. **Return type**: Python method returns `list[dict]` not `list[MemorySearchResult]`
4. **Parameter names**: RPC uses `similarity_threshold` (noun) not `threshold` (adjective)
5. **Security**: Must revoke from public and grant only to service_role
6. **SQL guard for out-of-range params**: `similarity_threshold` must be clamped to [0,1] in Python before RPC call; `match_count` defaults to minimum 1
7. **Index-friendly filtering**: Use `set_config + %` pattern, not `similarity() >= threshold` in WHERE clause

---

## 12. Files to Create/Modify

### Create
- `backend/migrations/010_trigram_search.sql` (new migration)
- `backend/tests/test_trigram_search.py` (new test file)

### Modify
- `backend/src/second_brain/services/supabase.py` (add `fuzzy_search_entities()` method)

### No Changes Required
- `backend/src/second_brain/contracts/knowledge.py` (optional enhancement only)

---

## 13. Dependency Notes

**Depends on P1-13 (data-integrity-constraints):**
- `knowledge_entities` table exists with `id`, `name`, `entity_type`, `description` columns
- `entity_type` CHECK constraint: `person`, `organization`, `concept`, `tool`, `event`, `location`, `other`
- UNIQUE constraint on `(name, entity_type)`
- NOT NULL constraints on `name`

**No dependency on:**
- P1-17 (full-text search) — trigram is independent of tsvector
- P1-18 (hybrid search) — trigram is separate search mode

**Enables:**
- P1-31 (entity-alias-table) — uses trigram for alias matching
- P2-03 (entity-deduplication) — uses trigram for fuzzy dedup

---

## 14. Model Routing (5-Tier Cascade)

| Step | Task | Tier | Model | Cost |
|------|------|------|-------|------|
| 1 | Plan review | T4 | gpt-5.3-codex | PAID (cheap) |
| 2 | Implementation | T1 | qwen3.5-plus | FREE |
| 3 | First validation | T2 | glm-5 | FREE |
| 4 | Second validation | T3 | deepseek-v3.2 | FREE |
| 5 | Code review | T4 | gpt-5.3-codex | PAID (cheap) |
| 6 | Final review (if needed) | T5 | claude-sonnet-4-6 | PAID |

---

## 15. Summary

**Line Count:** ~750 lines  
**Archon Sources:** 3 consulted (Supabase llms.txt, pgvector GitHub, Mastra PostgreSQL)  
**Pages Read:** 1 full page (65b102ab - Supabase guides, too large)  
**RAG Searches:** 2 (pg_trgm trigram fuzzy search, supabase GIN index similarity)  
**Code Examples:** 1 (trigram similarity search entity)  

**Implementation Files:**
- 1 new migration (010_trigram_search.sql)
- 1 new test file (test_trigram_search.py)
- 1 modified service (supabase.py)

**Total Tests:** 32 (19 SQL + 13 Python)
**Estimated Implementation Time:** 1-2 PIV loops
