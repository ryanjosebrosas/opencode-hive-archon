# Feature: knowledge-schema review fixes #2

## Scope

Single bounded fix slice for Iteration 2 Major findings:
1) retrieval-safe RLS strategy for `match_knowledge_chunks`
2) preserve Mem0 top-level `categories` during normalization

## Source Review

- `requests/code-reviews/knowledge-schema-review #2.md`

## RAG References

- Supabase RLS/policy guidance: `https://supabase.com/llms/guides.txt`
- Mem0 custom categories shape: `https://docs.mem0.ai/platform/features/custom-categories`

## Fix Tasks

1. `backend/migrations/001_knowledge_schema.sql`
   - Update `match_knowledge_chunks` function to `SECURITY DEFINER` and set explicit `search_path`.
   - Add execute grants for retrieval caller roles.
   - Keep RLS enabled on tables.

2. `backend/src/second_brain/services/memory.py`
   - Preserve validated top-level Mem0 `categories` (list[str]) in normalized metadata.

3. `tests/test_knowledge_schema.py`
   - Add coverage that Mem0 `categories` is preserved.

## Validation Commands

```bash
cd backend && python -m ruff check src/second_brain/services/memory.py ../tests/test_knowledge_schema.py
cd backend && python -m mypy src/second_brain/services/memory.py --ignore-missing-imports
cd backend && python -m pytest ../tests/test_knowledge_schema.py ../tests/test_supabase_provider.py -v
cd backend && python -m pytest ../tests/ -v
```
