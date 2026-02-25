# Feature: Fix Memory Provider Adapter Major Findings

## Goal

Resolve the 3 deferred major findings from code review so the memory adapter slice reaches clean status.

## Source

- `requests/code-loops/memory-service-real-provider-adapter-loop-report #1.md`
- `requests/code-reviews/memory-service-real-provider-adapter-review #1.md`

## Required Fixes (P1)

1. Add explicit logging for provider exceptions currently swallowed in `memory.py`.
2. Preserve provider error context in fallback metadata (safe, non-sensitive fields only).
3. Add input validation for `search_memories` parameters (`top_k`, `threshold`, query handling).

## Scope Guardrails

- Keep this slice focused on `MemoryService` and related tests only.
- Do not modify router policy, MCP API shape, or workflow command files.

## Validation (Full)

```bash
ruff check backend/src tests
mypy backend/src/second_brain
pytest tests/test_memory_service.py -q
pytest tests/test_recall_flow_integration.py -q
```

## Done When

- [x] All 3 major findings are fixed
- [x] No regression in memory or recall integration tests
- [x] Full validation passes
- [x] Follow-up report saved under `requests/code-loops/`
