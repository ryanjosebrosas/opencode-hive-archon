# Code Review: knowledge-schema (Extra loop iteration 2)

## Critical

- None.

## Major

1. `backend/src/second_brain/contracts/knowledge.py`
   - Timestamp fields are typed as `str`, bypassing datetime validation.
   - Fix: change to `datetime` fields (`created_at`, `updated_at`, `ingested_at`, `valid_from`, `valid_to`).

## Minor

1. `backend/migrations/001_knowledge_schema.sql`
   - `updated_at` not auto-maintained by trigger.

## Verdict

Critical: 0, Major: 1, Minor: 1
