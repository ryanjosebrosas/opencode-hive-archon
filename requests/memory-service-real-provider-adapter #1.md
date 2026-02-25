# Feature: Memory Service Real Provider Adapter (Mem0-first)

## Feature Description

Implement a real-provider path in `MemoryService` so retrieval can use Mem0 when configured, while preserving deterministic fallback behavior and existing contract output shape.

## User Story

As an operator, I want recall retrieval to use a real memory backend when credentials are available, so results reflect actual stored memory instead of only mock/fallback behavior.

## Problem Statement

The current memory service always uses mock/fallback logic. This is great for deterministic tests, but it limits runtime value and hides provider integration issues until later.

## Solution Statement

- Decision 1: Add a Mem0 adapter path behind configuration flags, because we need real retrieval without hard-locking runtime behavior.
- Decision 2: Keep fallback deterministic and default-safe, because reliability and branch predictability are core requirements.
- Decision 3: Avoid mandatory new dependencies in this slice, because the adapter can gracefully degrade when Mem0 SDK is unavailable.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `services/memory.py`, `deps.py`, retrieval integration tests
- **Dependencies**: Optional Mem0 SDK availability at runtime

### Slice Guardrails (Required)

- **Single Outcome**: `MemoryService.search_memories` supports real Mem0 retrieval with safe fallback.
- **Expected Files Touched**: `backend/src/second_brain/services/memory.py`, `backend/src/second_brain/deps.py`, `tests/test_memory_service.py`, `tests/test_recall_flow_integration.py`.
- **Scope Boundary**: No router policy redesign, no MCP interface changes, no new provider implementations beyond Mem0 path.
- **Split Trigger**: If provider auth/client wiring requires broader architecture changes, stop and open a follow-up plan.

---

## CONTEXT REFERENCES

### Relevant Codebase Files

- `backend/src/second_brain/services/memory.py:17` - current service behavior, mock/fallback lifecycle.
- `backend/src/second_brain/deps.py:28` - service factory wiring and default config entry point.
- `backend/src/second_brain/agents/recall.py:79` - recall orchestrator call path into memory service.
- `backend/src/second_brain/contracts/context_packet.py:6` - `ContextCandidate` contract (must remain stable).
- `tests/test_memory_service.py:6` - current mock lifecycle test conventions.
- `tests/test_recall_flow_integration.py:10` - integration assertions on branch + metadata behavior.

### New Files to Create

- None in this slice (update existing files only).

### Related Memories (from memory.md)

- Memory: Incremental-by-default slices with full validation gates - Relevance: this plan keeps one outcome and still runs full quality checks.
- Memory: Avoid mixed-scope loops - Relevance: this slice is project runtime only (no workflow system edits).

### Relevant Documentation

- [Mem0 Advanced Retrieval](https://docs.mem0.ai/platform/features/advanced-retrieval)
  - Specific section: Reranking / Performance / Fallback tips
  - Why: informs which flags and fallback patterns are safe to expose.
- [Mem0 Cookbook Search Example](https://docs.mem0.ai/cookbooks/companions/voice-companion-openai)
  - Specific section: `search(query, user_id, limit, threshold)` shape
  - Why: aligns adapter call shape to existing Mem0 patterns.

### Patterns to Follow

**Deterministic service fallback** (from `backend/src/second_brain/services/memory.py:89`):
```python
def _search_fallback(self, query: str, top_k: int, threshold: float) -> list[MemorySearchResult]:
    query_lower = query.lower()
    if "empty" in query_lower or "no candidate" in query_lower:
        return []
```
- Why this pattern: keeps branch tests stable when provider is unavailable.
- Common gotchas: do not remove fallback path when adding provider adapter.

**Provider-consistent resolution in recall** (from `backend/src/second_brain/agents/recall.py:150`):
```python
def _resolve_memory_service_for_provider(self, provider: str) -> MemoryService:
    if self.memory_service.provider == provider:
        return self.memory_service
    return create_memory_service(provider=provider, config=self.config)
```
- Why this pattern: adapter must respect selected provider from router.
- Common gotchas: avoid hidden global provider switching.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Add configuration and adapter hooks without breaking existing fallback and mock test semantics.

**Tasks:**
- Extend memory service config contract (`enabled`, `user_id`, `api_key_source` hints).
- Add guarded Mem0 client loader (optional import, no hard failure).
- Keep existing mock mode precedence unchanged.

### Phase 2: Core Implementation

Implement real provider search path and normalize provider responses to `ContextCandidate`.

**Tasks:**
- Add `_search_mem0` method for real retrieval attempt.
- Normalize Mem0 result payload fields to `MemorySearchResult`.
- If provider call fails or unavailable, use deterministic fallback and annotate metadata.

### Phase 3: Integration

Wire config defaults in deps and preserve recall behavior.

**Tasks:**
- Add default config keys for Mem0 adapter mode.
- Ensure `create_memory_service` passes config cleanly.
- Keep recall + routing metadata compatibility.

### Phase 4: Testing & Validation

Expand unit/integration tests for adapter path, fallback path, and metadata shape.

**Tasks:**
- Add tests for SDK missing, provider failure, and successful normalized response.
- Ensure existing deterministic branch tests still pass.

---

## STEP-BY-STEP TASKS

### UPDATE `backend/src/second_brain/services/memory.py`

- **IMPLEMENT**: Add optional Mem0 adapter path in `search_memories`:
  1) mock mode -> 2) real provider attempt (if enabled/provider=mem0/client available) -> 3) deterministic fallback.
- **PATTERN**: `backend/src/second_brain/services/memory.py:49` mock precedence and `:89` fallback determinism.
- **IMPORTS**: `import os`, `from typing import Callable` (if needed), optional runtime import guard helpers.
- **GOTCHA**: Never throw provider exceptions to caller in this slice; return fallback + metadata.
- **VALIDATE**: `python -m pytest -q tests/test_memory_service.py -k "mock or fallback or provider"`

### UPDATE `backend/src/second_brain/services/memory.py`

- **IMPLEMENT**: Add `_search_mem0` + `_normalize_mem0_results` helpers with strict defensive parsing (`id`, `memory/content`, `score/confidence`, metadata passthrough).
- **PATTERN**: contract mapping in `backend/src/second_brain/contracts/context_packet.py:6`.
- **IMPORTS**: existing `MemorySearchResult` and `ContextCandidate` only.
- **GOTCHA**: Clamp confidence to `[0.0, 1.0]` before constructing contract models.
- **VALIDATE**: `python -m pytest -q tests/test_memory_service.py -k "normalize or confidence"`

### UPDATE `backend/src/second_brain/deps.py`

- **IMPLEMENT**: Extend `get_default_config` with Mem0 adapter flags (e.g., `mem0_provider_enabled`, `mem0_user_id`, `mem0_use_real_provider`).
- **PATTERN**: default config style at `backend/src/second_brain/deps.py:44`.
- **IMPORTS**: no new external imports required.
- **GOTCHA**: Keep existing defaults backward-compatible for tests.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py -k provider`

### UPDATE `tests/test_memory_service.py`

- **IMPLEMENT**: Add tests for:
  - provider path disabled -> fallback metadata explains reason,
  - provider module unavailable -> fallback path used,
  - provider exception -> fallback path used,
  - normalized provider payload -> valid `ContextCandidate` list.
- **PATTERN**: class-based test style already used in file.
- **IMPORTS**: `pytest`, `monkeypatch`/stubs as needed.
- **GOTCHA**: do not require external network/API in tests.
- **VALIDATE**: `python -m pytest -q tests/test_memory_service.py`

### UPDATE `tests/test_recall_flow_integration.py`

- **IMPLEMENT**: Add one integration assertion that recall response remains contract-valid when memory provider falls back from failed real-provider attempt.
- **PATTERN**: metadata assertions in `tests/test_recall_flow_integration.py:133`.
- **IMPORTS**: existing imports only unless strictly needed.
- **GOTCHA**: keep test deterministic and independent of actual Mem0 credentials.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py -k "fallback or provider"`

---

## TESTING STRATEGY

### Unit Tests

- Memory service adapter gating, normalization, failure fallback, metadata reasons.

### Integration Tests

- Recall orchestrator behavior with provider path enabled/disabled and fallback continuity.

### Edge Cases

- Empty query with provider enabled.
- Mem0 payload missing score/confidence.
- Provider returns more than `top_k`.
- Provider throws timeout/error.

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
ruff check backend/src tests
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain
```

### Level 3: Unit Tests
```bash
pytest tests/test_memory_service.py -q
```

### Level 4: Integration Tests
```bash
pytest tests/test_recall_flow_integration.py -q
```

### Level 5: Manual Validation

1. Run recall with mem0 provider enabled and no SDK/credentials -> confirm graceful fallback metadata.
2. Run recall with deterministic query (`"empty set query"`) -> branch remains `EMPTY_SET`.
3. Run recall with high-confidence query -> branch behavior unchanged from current policy.

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `MemoryService` supports guarded real Mem0 retrieval path.
- [ ] Fallback behavior remains deterministic when provider unavailable/fails.
- [ ] Contract output shape unchanged (`ContextCandidate` and recall envelope remain stable).
- [ ] New adapter tests pass without external network dependency.
- [ ] No router/fallback policy regressions introduced.

### Runtime (verify after testing/deployment)

- [ ] With valid provider setup, retrieval returns real provider-backed candidates.
- [ ] Without provider setup, system degrades gracefully and remains actionable.
- [ ] Manual branch validation signals remain stable.

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Lint and type checks passed
- [ ] Unit and integration tests passed
- [ ] Manual validation steps executed
- [ ] Execution report generated (`.done.md`)

---

## NOTES

### Key Design Decisions

- Keep provider integration opt-in and failure-tolerant.
- Preserve deterministic behavior as the reliability baseline.

### Risks

- Mem0 SDK response shape may vary by version.
- Credentials and user scoping requirements may need a follow-up configuration slice.

### Confidence Score

- **8.4/10**
- Strong because current service boundary is small and tests are already in place.
