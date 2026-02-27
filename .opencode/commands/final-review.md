---
description: Final review gate — summarize all changes, verify acceptance criteria, get human approval before commit
agent: build
---

# Final Review: Pre-Commit Approval Gate

## Purpose

Final checkpoint between `/code-loop` (or `/code-review`) and `/commit`. Aggregates all review findings, shows what changed, verifies acceptance criteria from the plan, and asks for explicit human approval before committing.

**Workflow position:**
```
/execute → /code-loop → /final-review → /commit
```

This command does NOT fix code. It summarizes, verifies, and asks.

## Usage

```
/final-review [plan-path]
```

- `plan-path` (optional): Path to the plan file (e.g., `requests/retrieval-trace-plan.md`). If provided, acceptance criteria are pulled from the plan. If omitted, criteria check is skipped and only the summary + diff is shown.

---

## Step 1: Gather Context

Run these commands to understand the current state:

```bash
git status
git diff --stat HEAD
git diff HEAD
git log -5 --oneline
```

Also check for review artifacts:

```bash
ls requests/archive/code-reviews/ 2>/dev/null || echo "No code review artifacts"
ls requests/archive/code-loops/ 2>/dev/null || echo "No code loop artifacts"
```

---

## Step 2: Change Summary

Present a concise summary of everything that changed:

### Files Changed

| File | Status | Lines +/- |
|------|--------|-----------|
| {path} | {added/modified/deleted} | +X / -Y |

### Change Overview

For each changed file, write 1-2 sentences describing WHAT changed and WHY:

- `path/to/file.py` — {what changed and why}
- `path/to/test.py` — {what changed and why}

---

## Step 3: Validation Results

Run the full validation pyramid and report results:

### Level 1: Syntax & Style
```bash
ruff check backend/src tests
ruff format --check backend/src tests
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain
```

### Level 3: Tests
```bash
PYTHONPATH=backend/src pytest tests/ -v --tb=short
```

Report the results as a table:

| Check | Status | Details |
|-------|--------|---------|
| Ruff linting | PASS/FAIL | {details if fail} |
| Ruff formatting | PASS/FAIL | {details if fail} |
| Mypy type checking | PASS/FAIL | {details if fail} |
| Tests | PASS/FAIL | X passed, Y failed |

**If any Level 1-3 checks FAIL**: Stop here. Report failures and recommend running `/code-loop` or `/execute` to fix before retrying `/final-review`.

---

## Step 4: Review Findings Summary

If code review artifacts exist in `requests/archive/code-reviews/` or `requests/archive/code-loops/`, summarize:

### Review History

| Review | Critical | Major | Minor | Status |
|--------|----------|-------|-------|--------|
| Review #1 | X | Y | Z | {Fixed/Open} |
| Review #2 | X | Y | Z | {Fixed/Open} |

### Outstanding Issues

List any remaining issues from reviews that were NOT fixed:

- **{severity}**: `file:line` — {description} — Reason not fixed: {reason}

If no outstanding issues: "All review findings have been addressed."

---

## Step 5: Acceptance Criteria Check

**If plan-path was provided**, read the plan file and locate the `## ACCEPTANCE CRITERIA` section.

For each criterion, verify whether it is met:

### Implementation Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | {criterion text} | MET/NOT MET | {how verified} |
| 2 | {criterion text} | MET/NOT MET | {how verified} |

### Runtime Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | {criterion text} | MET/NOT MET/DEFERRED | {how verified or why deferred} |

**If plan-path was NOT provided**: Skip this section and note "No plan provided — acceptance criteria check skipped."

---

## Step 6: Final Verdict

Summarize the readiness assessment:

```
FINAL REVIEW SUMMARY
====================

Changes:     X files changed, +Y/-Z lines
Tests:       A passed, B failed
Lint/Types:  CLEAN / X issues remaining
Reviews:     N iterations, M issues fixed, P outstanding
Criteria:    X/Y met (Z deferred)

VERDICT:     READY TO COMMIT / NOT READY
```

**READY TO COMMIT** when:
- All validation levels pass (lint, types, tests)
- No Critical or Major review findings outstanding
- All Implementation acceptance criteria met (if plan provided)

**NOT READY** when:
- Any validation level fails
- Critical or Major review findings still open
- Implementation acceptance criteria not met

---

## Step 7: Ask for Approval

**If READY TO COMMIT:**

Ask the user:

```
Ready to commit. Suggested message:

  {type}({scope}): {description}

Proceed with /commit? (yes / modify message / abort)
```

Wait for explicit user response. Do NOT auto-commit.

**If NOT READY:**

Report what needs to be fixed and suggest next action:

```
Not ready to commit. Outstanding issues:

1. {issue}
2. {issue}

Recommended: Run /code-loop to address remaining issues, then retry /final-review.
```

---

## Output

This command produces no persistent artifact. Its output is the conversation itself — the summary and approval decision. The subsequent `/commit` command handles the actual commit and report.

---

## Notes

- This command is read-only: it does NOT modify files, stage changes, or create commits.
- If the user says "yes", they should run `/commit` as the next command.
- If the user wants to modify the commit message, note it and they can pass it to `/commit`.
- Keep the summary concise — the user has already been through `/code-loop` and wants a quick final check, not a deep re-review.
