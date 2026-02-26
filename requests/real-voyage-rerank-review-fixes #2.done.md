# Fix Plan: Code Review Issues #2

**Feature**: real-voyage-rerank
**Source**: `requests/code-reviews/real-voyage-rerank-review #2.md`
**Scope**: P0 + P1 fixes only (Critical + Major)

---

## Solution Statement

Fix type safety issues and initialization bugs identified in code review. Focus on:
1. Mem0 API key not passed to client (Critical)
2. Mode validation missing in MCP server and recall agent (Major)
3. Thread safety in trace collector and conversation store (Major)
4. Provider metadata discarded in recall agent (Major)

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/src/second_brain/services/memory.py:158` | Pass API key to Mem0 client |
| `backend/src/second_brain/mcp_server.py:59` | Add mode validation |
| `backend/src/second_brain/agents/recall.py:406` | Add mode validation, type annotation |
| `backend/src/second_brain/services/trace.py:30-37` | Add threading.Lock |
| `backend/src/second_brain/services/conversation.py:47-52` | Add threading.Lock |
| `backend/src/second_brain/agents/recall.py:117` | Preserve provider metadata |

---

## Step-by-Step Tasks

### Task 1: Fix Mem0 API key initialization
- **ACTION**: Fix bug
- **TARGET**: `backend/src/second_brain/services/memory.py:158`
- **IMPLEMENT**: Pass `api_key=api_key` to `Memory()` constructor when API key is available
- **PATTERN**: Lines 153-155 look up the API key, line 158 should use it
- **IMPORTS**: None
- **GOTCHA**: SDK may fall back to env var, but explicit is better
- **VALIDATE**: Unit test passes, ruff/mypy clean

### Task 2: Add mode validation in MCP server
- **ACTION**: Add validation
- **TARGET**: `backend/src/second_brain/mcp_server.py:59`
- **IMPLEMENT**: Create `VALID_MODES` constant, validate mode string, raise ValueError for invalid
- **PATTERN**: 
  ```python
  VALID_MODES = ("fast", "accurate", "conversation")
  if mode not in VALID_MODES:
      raise ValueError(f"Invalid mode: {mode}. Must be one of {VALID_MODES}")
  ```
- **IMPORTS**: None
- **GOTCHA**: Remove the `cast()` call
- **VALIDATE**: Test with invalid mode raises ValueError

### Task 3: Add mode validation in recall agent
- **ACTION**: Add validation + type annotation
- **TARGET**: `backend/src/second_brain/agents/recall.py:406`
- **IMPLEMENT**: 
  1. Add type annotation `mode: Literal["fast", "accurate", "conversation"]` to `run_recall`
  2. Add validation at function start
  3. Remove `# type: ignore` comment
- **PATTERN**: Same as Task 2
- **IMPORTS**: `from typing import Literal`
- **GOTCHA**: Function is called from mcp_server, so validate there first
- **VALIDATE**: mypy passes without type: ignore

### Task 4: Add thread safety to trace collector
- **ACTION**: Add thread safety
- **TARGET**: `backend/src/second_brain/services/trace.py`
- **IMPLEMENT**: 
  1. Add `import threading` 
  2. Add `self._lock = threading.Lock()` in `__init__`
  3. Wrap `record`, `get_traces`, `get_by_id`, `get_latest`, `clear` with lock
- **PATTERN**: Use `with self._lock:` context manager
- **IMPORTS**: `import threading`
- **GOTCHA**: Don't hold lock during callback invocation
- **VALIDATE**: ruff/mypy pass, existing tests pass

### Task 5: Add thread safety to conversation store
- **ACTION**: Add thread safety
- **TARGET**: `backend/src/second_brain/services/conversation.py`
- **IMPLEMENT**: 
  1. Add `import threading`
  2. Add `self._lock = threading.Lock()` in `__init__`
  3. Wrap `add_turn`, `get_session`, `delete_session`, `_enforce_session_limit` with lock
- **PATTERN**: Use `with self._lock:` context manager
- **IMPORTS**: `import threading`
- **GOTCHA**: Avoid holding lock during I/O
- **VALIDATE**: ruff/mypy pass, existing tests pass

### Task 6: Preserve provider metadata in recall agent
- **ACTION**: Preserve metadata
- **TARGET**: `backend/src/second_brain/agents/recall.py:117`
- **IMPLEMENT**: 
  1. Change `_provider_metadata` to `provider_metadata`
  2. Merge relevant fields into `routing_metadata`
- **PATTERN**: `routing_metadata.update(provider_metadata)`
- **IMPORTS**: None
- **GOTCHA**: Don't overwrite existing routing_metadata fields
- **VALIDATE**: Manual check that metadata appears in traces

---

## Validation Commands

```bash
cd backend && ruff check src/
cd backend && mypy src/
cd backend && python -m pytest tests/ -v
```

---

## Out of Scope

- Minor issues (defer to follow-up)
- LSP import resolution errors (test environment configuration, not code)