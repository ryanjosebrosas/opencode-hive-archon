# Feature: planning-orchestration review fixes #1

## Input Artifact

- `requests/code-reviews/planning-orchestration-review #1.md`

## Bounded Fix Slice

Single outcome: make the current planning-orchestration changes pass lint/type/format gates without broad refactors.

In scope:
- Fix undefined `Planner` type reference in `backend/src/second_brain/deps.py`
- Remove invalid `mode` type-ignore path by adding explicit mode typing/validation in chat entrypoints
- Fix chat integration test isolation around shared singleton behavior where practical in this slice
- Run full validation (ruff, format-check, mypy, pytest)

Out of scope:
- Persistent conversation storage redesign
- Architectural changes outside planning-orchestration files

## Step-by-Step Tasks

1. Update `backend/src/second_brain/deps.py` typing so `Planner` is a valid type for static checks.
2. Update `backend/src/second_brain/orchestration/planner.py` and `backend/src/second_brain/mcp_server.py` to use a constrained mode type instead of `# type: ignore`.
3. Update `tests/test_chat_integration.py` to avoid depending on global singleton side effects where not needed.
4. Format changed files and run:
   - `ruff check backend/src tests`
   - `ruff format --check backend/src tests`
   - `mypy backend/src/second_brain`
   - `PYTHONPATH=backend/src pytest tests/ -v --tb=short`

## Acceptance Criteria

- Ruff check passes with zero errors.
- Ruff format check passes.
- Mypy passes for `backend/src/second_brain`.
- Full tests pass.
- No new unrelated files are modified for this slice.
