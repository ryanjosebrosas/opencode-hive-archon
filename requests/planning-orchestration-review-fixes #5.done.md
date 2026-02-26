# Feature: planning-orchestration review fixes #5

## Input Artifact

- `requests/code-reviews/planning-orchestration-review #8.md`

## Bounded Fix Slice

Single outcome: harden planner/session behavior by removing mutable state leaks, narrowing error handling, and preventing arbitrary session-id fixation.

## In Scope

- Return defensive copies from `ConversationStore.get_or_create()`.
- Narrow planner exception handling to expected runtime/validation failures.
- Enforce server-issued session IDs in MCP chat path.
- Tighten/extend tests covering these behaviors.
- Run full validation gates.

## Out of Scope

- Full auth/tenant system
- Persistence layer redesign

## Tasks

1. Update `backend/src/second_brain/services/conversation.py` copy semantics for `get_or_create()`.
2. Update `backend/src/second_brain/orchestration/planner.py` to catch expected exception classes only.
3. Update `backend/src/second_brain/mcp_server.py` to reject non-issued session IDs.
4. Update tests in `tests/test_conversation_store.py`, `tests/test_planner.py`, and `tests/test_chat_integration.py`.
5. Run:
   - `ruff check backend/src tests`
   - `ruff format --check backend/src tests`
   - `mypy backend/src/second_brain`
   - `PYTHONPATH=backend/src pytest tests/ -v --tb=short`

## Acceptance Criteria

- No Critical/Major findings remain in follow-up review.
- Validation commands pass.
