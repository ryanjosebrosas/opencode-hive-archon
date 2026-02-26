# Code Review: knowledge-schema (Extra loop iteration 1)

## Critical

- None.

## Major

1. `backend/migrations/001_knowledge_schema.sql`
   - Uses `gen_random_uuid()` without enabling `pgcrypto`.
   - Fix: add `create extension if not exists pgcrypto;` before table creation.

2. `backend/src/second_brain/services/memory.py`
   - Supabase path does not enforce 1024-dim embedding contract before RPC.
   - Fix: guard on `len(embedding) == 1024`, otherwise fallback with explicit metadata reason.

## Minor

1. `backend/migrations/001_knowledge_schema.sql`
   - `updated_at` defaults are not auto-maintained on update.

## Verdict

Critical: 0, Major: 2, Minor: 1
