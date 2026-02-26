# Feature: knowledge-schema review fixes #3

## Scope

Single bounded fix slice: remove cross-user exposure risk by restricting RPC execute grants.

## Source Review

- `requests/code-reviews/knowledge-schema-review #3.md`

## Fix Tasks

1. `backend/migrations/001_knowledge_schema.sql`
   - Keep `SECURITY DEFINER` for retrieval compatibility with RLS.
   - Restrict `match_knowledge_chunks` execution from `authenticated` to `service_role` only.

## Validation

```bash
cd backend && python -m pytest ../tests/ -q
```
