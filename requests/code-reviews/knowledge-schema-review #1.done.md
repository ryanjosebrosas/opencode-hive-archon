# Code Review: knowledge-schema (Iteration 1)

## Critical

1. `backend/src/second_brain/services/memory.py:153`
   - Un-typed third-party import `from mem0 import Memory` lacks mypy suppression under strict mode.
   - Impact: type safety gate fails (`import-untyped`).
   - Fix: add `# type: ignore[import-untyped]` on import; keep call-site suppression if needed.

## Major

1. `backend/src/second_brain/contracts/knowledge.py:77,87,90,109,110,130,134,148,149,150`
   - UUID-backed schema fields are modeled as plain `str`/`list[str]`.
   - Impact: invalid IDs can bypass contract validation and fail later at DB boundaries.
   - Fix: use `uuid.UUID`/`list[uuid.UUID]` for ID fields.

2. `backend/src/second_brain/services/supabase.py:118-124`
   - Merge order allows row `metadata` to override canonical columns (`knowledge_type`, `source_origin`, etc.).
   - Impact: normalized metadata can become non-deterministic.
   - Fix: merge extra metadata first, then set canonical keys last.

## Minor

1. `tests/test_knowledge_schema.py:30-33,48-50,116-122`
   - Invalid literal tests only assert `ValidationError`, not specific `literal_error` type.
   - Impact: weaker regression signal.
   - Fix: assert `exc.errors()[0]["type"] == "literal_error"`.

## RAG Notes

- Supabase vector extension and HNSW usage align with `https://supabase.com/llms/guides.txt`.
- Mem0 metadata extension path aligns with `https://docs.mem0.ai/platform/features/custom-categories`.
- Literal validation semantics align with `https://docs.pydantic.dev/latest/errors/validation_errors/index.md`.

## Verdict

Critical: 1, Major: 2, Minor: 1
