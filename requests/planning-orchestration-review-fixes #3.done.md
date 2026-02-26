# Feature: planning-orchestration review fixes #3

## Input Artifact

- `requests/code-reviews/planning-orchestration-review #4.md`

## Bounded Fix Slice

Single outcome: remove user-facing raw exception text from planner fallback metadata while preserving actionable behavior.

## Tasks

1. Update `backend/src/second_brain/orchestration/planner.py` error fallback metadata to avoid exposing raw exception message.
2. Keep minimal structured metadata suitable for diagnostics without sensitive detail.
3. Re-run lint/type/tests.

## Acceptance Criteria

- No Critical/Major findings remain in re-review.
- Validation commands pass.
