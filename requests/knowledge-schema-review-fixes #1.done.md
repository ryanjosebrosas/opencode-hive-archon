# Feature: knowledge-schema review fixes #1

## Scope

Single bounded fix slice for Iteration 1 review findings: close all Critical and Major issues, plus the quick Minor test-hardening update.

## Source Review

- `requests/code-reviews/knowledge-schema-review #1.md`

## RAG References

- Supabase pgvector/HNSW guidance: `https://supabase.com/llms/guides.txt`
- Mem0 metadata conventions: `https://docs.mem0.ai/platform/features/custom-categories`
- Pydantic literal validation behavior: `https://docs.pydantic.dev/latest/errors/validation_errors/index.md`

## Fix Tasks

1. `backend/src/second_brain/services/memory.py`
   - Restore strict-mypy-safe import suppression for untyped Mem0 dependency.
   - Keep runtime behavior unchanged.

2. `backend/src/second_brain/contracts/knowledge.py`
   - Strengthen ID fields to `uuid.UUID`/`list[uuid.UUID]` where schema is UUID-backed.
   - Keep all enums/default behavior unchanged.

3. `backend/src/second_brain/services/supabase.py`
   - Make normalization deterministic by preventing `metadata` override of canonical fields.
   - Preserve extra metadata keys without overriding canonical values.

4. `tests/test_knowledge_schema.py`
   - Strengthen invalid Literal tests by asserting `literal_error` type in `ValidationError` payload.

## Validation Commands

```bash
cd backend && python -m ruff check src/second_brain/contracts/knowledge.py src/second_brain/services/supabase.py src/second_brain/services/memory.py ../tests/test_knowledge_schema.py
cd backend && python -m mypy src/second_brain/contracts/knowledge.py src/second_brain/services/supabase.py src/second_brain/services/memory.py --ignore-missing-imports
cd backend && python -m pytest ../tests/test_knowledge_schema.py ../tests/test_supabase_provider.py -v
cd backend && python -m pytest ../tests/ -v
```
