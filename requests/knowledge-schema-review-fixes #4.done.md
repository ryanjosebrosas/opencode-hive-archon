# Feature: knowledge-schema review fixes #4

## Scope

Single bounded fix slice for extra loop major findings:
1) ensure UUID generator extension dependency is explicit in migration
2) enforce Supabase embedding dimension contract (1024) before RPC

## Source Review

- `requests/code-reviews/knowledge-schema-review #5.md`

## Fix Tasks

1. `backend/migrations/001_knowledge_schema.sql`
   - Add `create extension if not exists pgcrypto;` before first `gen_random_uuid()` usage.

2. `backend/src/second_brain/services/memory.py`
   - Add runtime guard in `_search_with_supabase()`:
     - if embedding is not length 1024, return deterministic fallback
     - include metadata (`fallback_reason=embedding_dimension_mismatch`, expected/actual dimensions)

3. `tests/test_supabase_provider.py`
   - Add unit test covering dimension mismatch guard and fallback behavior.

## Validation

```bash
cd backend && python -m ruff check src/second_brain/services/memory.py ../tests/test_supabase_provider.py
cd backend && python -m mypy src/second_brain/services/memory.py --ignore-missing-imports
cd backend && python -m pytest ../tests/test_supabase_provider.py ../tests/test_knowledge_schema.py -q
cd backend && python -m pytest ../tests/ -q
```
