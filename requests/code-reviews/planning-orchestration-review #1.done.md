# Code Review - planning-orchestration #1

Generated: 2026-02-26T10:20:34

## Severity Counts

| Severity | Count |
|---|---:|
| Critical | 1 |
| Major | 2 |
| Minor | 2 |

## Findings

### Critical

- `backend/src/second_brain/deps.py:77` - Return type annotation references undefined `Planner` symbol (fails Ruff F821 and Mypy name-defined).

### Major

- `backend/src/second_brain/orchestration/planner.py:68` and `backend/src/second_brain/mcp_server.py:174` - `mode` typed as `str` plus `# type: ignore[arg-type]`, allowing invalid values to pass through to model validation.
- `tests/test_chat_integration.py:11` and related tests - Uses global singleton state via `chat_tool`, reducing test isolation.

### Minor

- `backend/src/second_brain/orchestration/planner.py:19` - helper appears unused.
- Untracked runtime artifacts present (`__pycache__/`, `nul`).

## Recommended Fix Slice

1. Resolve `Planner` typing issue in `deps.py`.
2. Remove type-ignore path by constraining/validating `mode` in planner and MCP server.
3. Improve chat integration test isolation by using `MCPServer()` instance for continuity tests.
4. Keep generated artifacts out of commit scope.
