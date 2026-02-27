---
description: Full integration test + final review + PR — ship the MVP
agent: build
---

# Ship: Integration Test + Final Review + PR

Final command in the build pipeline. Runs full integration tests, T5 final review, and creates a PR. Only run when all specs in BUILD_ORDER.md are complete.

## Usage

```
/ship [pr-title]
```

`$ARGUMENTS` — Optional: custom PR title. Default derived from mvp.md.

---

## Pipeline Position

```
/mvp → /prd → /decompose → /build next (repeat) → /ship
```

This is the final step.

---

## Step 1: Verify All Specs Complete

Read `specs/BUILD_ORDER.md`. Check every spec is marked `[x]`.

**If any `[ ]` remain:**
```
Cannot ship — {N} specs incomplete:
- [ ] {spec-name} (Layer {L})
- [ ] {spec-name} (Layer {L})

Run /build next to continue building.
```
Stop.

---

## Step 2: Full Validation Pyramid

Run the complete 5-level validation:

### Level 1: Syntax & Style
```bash
ruff check backend/src tests
ruff format --check backend/src tests
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain
```

### Level 3: Unit Tests
```bash
PYTHONPATH=backend/src pytest tests/ -v --tb=short
```

### Level 4: Integration Tests
```bash
PYTHONPATH=backend/src pytest tests/ -v --tb=short -m integration
```

### Level 5: MVP Acceptance

Read `mvp.md` "MVP Done When" criteria. For each criterion:
- Check if it can be verified automatically
- Run the check or note it needs manual verification
- Mark as MET / NOT MET / MANUAL CHECK NEEDED

Report results:

| Level | Status | Details |
|-------|--------|---------|
| L1 Syntax | PASS/FAIL | {details} |
| L2 Types | PASS/FAIL | {details} |
| L3 Unit Tests | PASS/FAIL | X passed, Y failed |
| L4 Integration | PASS/FAIL | X passed, Y failed |
| L5 MVP Criteria | X/Y MET | {details} |

**If any L1-L4 FAIL:** Stop. Report failures. Suggest `/build` to fix.

---

## Step 3: T5 Final Review (Optional)

If all L1-L4 pass, offer T5 review:

```
All validation levels pass. Run T5 final review (anthropic/claude-sonnet-4-6)?
This is the expensive tier — only use for important releases. [y/n]
```

If yes, dispatch a review prompt to T5 with:
- Full git diff since project start
- BUILD_ORDER.md summary
- Test results

If no, skip to Step 4.

---

## Step 4: Summary Report

```
SHIP REPORT
===========

MVP:       {product name} from mvp.md
Specs:     {total} complete across {layers} layers
Tests:     {count} passing
Lint/Types: CLEAN
MVP Criteria: {met}/{total} met

Changes:   {files changed} files, +{insertions}/-{deletions}
Commits:   {count} commits on branch
```

---

## Step 5: Create PR

Run `/pr` with the appropriate title:

```
/pr {$ARGUMENTS or derived title}
```

---

## Step 6: Archive Build Artifacts

After PR creation:
1. Rename `specs/BUILD_ORDER.md` → `specs/BUILD_ORDER.done.md`
2. Move completed plans from `requests/` to `requests/archived/`
3. Keep `specs/build-state.json` for reference

---

## Notes

- `/ship` is deliberately heavyweight — it's the quality gate before merging
- T5 review is optional and expensive — skip for internal/dev releases
- MVP criteria from mvp.md are the ultimate acceptance test
- If MVP criteria have items marked MANUAL CHECK NEEDED, surface them for human verification
