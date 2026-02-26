# Code Review: knowledge-schema (Iteration 3)

## Critical

- None.

## Major

1. `backend/migrations/001_knowledge_schema.sql`
   - `match_knowledge_chunks` was `SECURITY DEFINER` with execute granted to `authenticated`.
   - Impact: potential cross-user row exposure without tenant/user scoping.
   - Fix: limit execute grant to backend service role only (or add strict tenant predicate).

## Minor

1. `backend/src/second_brain/services/memory.py`
   - `filters` parameter not yet propagated to provider calls.

2. `backend/src/second_brain/contracts/knowledge.py`
   - Timestamp fields are strings rather than `datetime`.

## Verdict

Critical: 0, Major: 1, Minor: 2
