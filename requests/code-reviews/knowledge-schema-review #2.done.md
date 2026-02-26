# Code Review: knowledge-schema (Iteration 2)

## Critical

- None.

## Major

1. `backend/migrations/001_knowledge_schema.sql:76`
   - RLS enabled without policy/definer strategy for retrieval path.
   - Impact: `match_knowledge_chunks` may return no rows for non-service roles.
   - Fix: add explicit policy or make RPC `SECURITY DEFINER` with scoped grants.

2. `backend/src/second_brain/services/memory.py:305`
   - Mem0 top-level `categories` is not preserved in normalized metadata.
   - Impact: custom category labels are dropped.
   - Fix: forward validated `categories` list into `MemorySearchResult.metadata`.

## Minor

1. `backend/src/second_brain/services/supabase.py:12`
   - Local constants duplicate contract literals.

2. `backend/src/second_brain/services/supabase.py:103`
   - `_normalize_results` accepts `threshold` but does not use it.

## Verdict

Critical: 0, Major: 2, Minor: 2
