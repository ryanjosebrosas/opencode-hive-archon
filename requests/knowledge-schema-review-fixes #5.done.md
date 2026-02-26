# Feature: knowledge-schema review fixes #5

## Scope

Single bounded fix slice: enforce datetime-typed timestamp fields in knowledge contracts to restore strong validation.

## Source Review

- `requests/code-reviews/knowledge-schema-review #6.md`

## Fix Tasks

1. `backend/src/second_brain/contracts/knowledge.py`
   - Convert timestamp fields from `str` to `datetime`.
   - Keep UTC default factories and existing field names unchanged.

2. `tests/test_knowledge_schema.py`
   - Ensure existing tests remain valid under datetime-typed fields.

## Validation

```bash
cd backend && python -m ruff check src/second_brain/contracts/knowledge.py ../tests/test_knowledge_schema.py
cd backend && python -m mypy src/second_brain/contracts/knowledge.py --ignore-missing-imports
cd backend && python -m pytest ../tests/test_knowledge_schema.py ../tests/test_supabase_provider.py -q
cd backend && python -m pytest ../tests/ -q
```
