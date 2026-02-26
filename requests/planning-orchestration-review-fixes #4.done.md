# Feature: planning-orchestration review fixes #4

## Input Artifact

- `requests/code-reviews/planning-orchestration-review #6.md`

## Bounded Fix Slice

Single outcome: resolve active Critical/Major review blockers around retrieval error semantics and API key handling safety.

In scope:
- Remove process-global env mutation in Mem0 client initialization.
- Distinguish retrieval execution failures from true empty-result branch semantics.
- Add/adjust tests for both behaviors.
- Add quick ignore entries for transient artifacts to reduce review noise.

Out of scope:
- Conversation store copy semantics redesign
- Broad architecture changes

## Tasks

1. Update `backend/src/second_brain/services/memory.py` to avoid runtime `os.environ` writes.
2. Update `backend/src/second_brain/orchestration/planner.py` retrieval failure branch code behavior.
3. Update tests in `tests/test_memory_service.py` and `tests/test_planner.py` accordingly.
4. Update `.gitignore` for Python cache/runtime noise.
5. Validate:
   - `ruff check backend/src tests`
   - `ruff format --check backend/src tests`
   - `mypy backend/src/second_brain`
   - `PYTHONPATH=backend/src pytest tests/ -v --tb=short`

## Acceptance Criteria

- No Critical/Major issues remain in follow-up review.
- Validation commands pass.
