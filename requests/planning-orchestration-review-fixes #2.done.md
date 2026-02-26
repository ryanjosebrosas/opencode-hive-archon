# Feature: planning-orchestration review fixes #2

## Input Artifact

- `requests/code-reviews/planning-orchestration-review #3.md`

## Bounded Fix Slice

Single outcome: harden planner runtime behavior for graceful failures and bounded response size, then re-validate.

In scope:
- Add exception handling around retrieval execution in `Planner.chat()` with safe fallback response metadata.
- Bound candidate content size in proceed response formatting.
- Remove dead helper flagged in review.
- Validate with lint/types/tests.

Out of scope:
- Wider architecture/storage redesign
- Cleanup of unrelated generated artifacts

## Tasks

1. Update `backend/src/second_brain/orchestration/planner.py` for safe retrieval exception handling.
2. Truncate/sanitize candidate snippets in proceed response.
3. Remove or repurpose unused helper.
4. Run:
   - `ruff check backend/src tests`
   - `ruff format --check backend/src tests`
   - `mypy backend/src/second_brain`
   - `PYTHONPATH=backend/src pytest tests/ -v --tb=short`

## Acceptance Criteria

- No Critical/Major review issues remain for this slice.
- Validation commands pass.
