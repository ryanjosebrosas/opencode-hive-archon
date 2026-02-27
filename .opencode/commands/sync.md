---
description: Validate build state and re-sync context between sessions
agent: build
---

# Sync: State Validation Checkpoint

Re-validate build state against actual code. Run this when returning after a break, before heavy specs, or when something feels off.

## Usage

```
/sync
```

---

## Pipeline Position

Use between `/build` iterations within the main pipeline:
```
/mvp → /prd → /pillars → /decompose → /build next → /sync → /build next → ... → /ship
```

Shorthand:
```
/build next → /sync → /build next → ...
```

**When to run /sync:**
- Returning after a session break
- Before the first heavy-depth spec
- After re-running `/decompose`
- When a `/build` fails unexpectedly
- Every 3rd spec as a routine checkpoint

---

## Step 1: Read Build State

Read these files:
- `specs/BUILD_ORDER.md` — spec list with completion status
- `specs/build-state.json` — cross-session context (if exists)
- `memory.md` — project memory

Report current state:

```
SYNC CHECK
==========
Specs: {done}/{total} complete ({pct}%)
Layer: {current}/{max}
Last completed: {spec-name} ({date from git log})
Next pending: {spec-name} ({depth})
```

---

## Step 2: Validate Completed Specs

For each spec marked `[x]` in BUILD_ORDER.md, verify the code actually exists:

1. Check that the `touches` files from the spec exist
2. Run a quick syntax check on those files: `ruff check {files}`
3. If any completed spec has missing/broken files, flag it:

```
WARNING: Spec {name} marked complete but {file} is missing/broken.
Consider re-building: /build {spec-number}
```

---

## Step 3: Validate Dependencies

For the next pending spec, verify all its dependencies are genuinely complete:

1. Check each `depends_on` spec is `[x]`
2. Check the dependency's files exist and pass basic checks
3. Report any issues

---

## Step 4: Run Full Test Suite

```bash
ruff check backend/src tests
mypy backend/src/second_brain
PYTHONPATH=backend/src pytest tests/ -q
```

Report results. If anything fails, surface it — don't let broken state propagate.

---

## Step 4b: Pillar Health (when specs/PILLARS.md exists)

When PILLARS.md is available, add a pillar-level health section to the sync output:

```
=== Pillar Health ===
P1 Data Infrastructure: 7/7 specs [x] | Gate: PASS
P2 API Skeleton:        3/5 specs [~] | Gate: PENDING
P3 AI Agent Layer:      0/6 specs [ ] | Blocked by P2
```

**Cross-pillar validation**: For completed pillars, re-run their gate criteria to check for regression. If a previously passing gate now fails, report it prominently.

**Consistency check**: Verify that PILLARS.md status markers match BUILD_ORDER.md completion markers and build-state.json. Flag mismatches.

**Backward compatible**: If no PILLARS.md exists, skip this section entirely.

---

## Step 5: Validate build-state.json

If `specs/build-state.json` exists, cross-check it against reality:

1. Does `completed` list match `[x]` specs in BUILD_ORDER.md?
2. Are `patternsEstablished` still valid? (quick grep for pattern usage)
3. Is `currentLayer` accurate?

Fix any drift and update the file.

---

## Step 6: Context Summary

Output a summary suitable for continuing work:

```
SYNC COMPLETE
=============
All {done} completed specs verified.
Tests: {count} passing
State: CLEAN / {N} issues found

Next: /build next → {spec-name} ({depth}, Layer {L})
Estimated: {remaining} specs left, ~{time} to MVP

Patterns in use:
- {pattern 1}
- {pattern 2}

Recent decisions:
- {decision 1}
- {decision 2}
```

---

## Notes

- `/sync` is read-only — it reports issues but doesn't fix them
- If issues are found, suggest the appropriate fix command
- Keep `/sync` fast — should complete in under 30 seconds
- The context summary is designed to prime a fresh session with everything needed to continue
