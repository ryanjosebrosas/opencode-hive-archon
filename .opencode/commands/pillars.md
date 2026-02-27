---
description: Analyze PRD and identify infrastructure pillars with dependency order and gate criteria
agent: build
---

# Pillars: Infrastructure Layer Analysis

Analyze the PRD and identify the fundamental infrastructure layers (pillars) that must be built in order. Each pillar is a coherent phase of work with clear gate criteria that must pass before the next pillar begins. Produces `specs/PILLARS.md`.

## Usage

```
/pillars [focus area or pillar to re-analyze]
```

`$ARGUMENTS` — Optional: focus on a specific area, or name a pillar to re-analyze mid-project.

---

## Pipeline Position

```
/mvp → /prd → /pillars → /decompose → /build next (repeat) → /ship
```

This is Step 3. Requires `PRD.md` to exist (produced by `/prd`). Output feeds `/decompose`, which breaks each pillar into individual specs.

---

## Step 1: Read Inputs

1. Look for a PRD file (`PRD.md`, `docs/PRD.md`, or any file matching `*-prd.md`). This is the primary input.
2. If no PRD found, stop and report: "No PRD found. Run `/prd` first." Do not proceed.
3. Also read `mvp.md` if present — it provides high-level vision and priority signals.
4. Scan the codebase for existing infrastructure:
   - Check `specs/BUILD_ORDER.md` if it exists (already-built specs indicate existing layers)
   - Check `specs/PILLARS.md` if it exists (preserve completed pillar status on re-run)
   - Scan top-level directories and key files (e.g., `src/`, `db/`, `tests/`) to understand what already exists

Extract from the PRD:
- Core capabilities and feature groups
- Technical architecture decisions
- Integration points and dependencies
- Implementation phases (if defined)

---

## Step 2: Propose Pillar Structure

Analyze the PRD and propose infrastructure pillars. Each pillar should be:

- **Cohesive** — a single infrastructure concern (data, services, API, etc.)
- **Sequential** — later pillars genuinely depend on earlier ones
- **Scoped** — 1–2 weeks of focused work, roughly 3–8 specs
- **Gated** — has concrete pass/fail criteria before the next pillar starts

**Typical pillar order** (adapt to the PRD — don't force this structure):

| Layer | Example Pillar Name | What It Establishes |
|-------|--------------------|--------------------|
| 0 | Data Infrastructure | Schema, storage, core models |
| 1 | Core Services | Business logic, processing pipelines |
| 2 | Integration Layer | External APIs, auth, cross-cutting concerns |
| 3 | Interface Layer | API endpoints, CLI, UI components |
| 4 | Observability | Logging, metrics, monitoring |

**Pillar count:** Let the PRD dictate. Typically 4–7 for a medium project. Don't add pillars that aren't warranted.

**If `$ARGUMENTS` is provided:** Focus re-analysis on the named pillar or area. All other pillars retain their current status.

---

## Step 3: Present Pillars for Approval

Present the proposed pillars to the user as a structured summary:

```
Infrastructure Pillars: {N} pillars identified

Pillar 1 ({Name}): {brief description} — ~{N} specs
Pillar 2 ({Name}): {brief description} — ~{N} specs
Pillar 3 ({Name}): {brief description} — ~{N} specs
...

Dependency order: 1 → 2 → 3 → ...

Key gate criteria:
  Pillar 1: {main gate test}
  Pillar 2: {main gate test}

Does this pillar structure look right? Any pillars to add, merge, split, or reorder?
```

Wait for explicit approval before writing `specs/PILLARS.md`. Adjust if requested.

---

## Step 4: Council Validation (Optional)

If the project has >5 pillars, complex cross-dependencies, or the pillar order is non-obvious, suggest:

```
This pillar structure has {N} layers with cross-cutting dependencies.
Run /council to get multi-model validation of pillar order and scope? [y/n]
```

If yes, dispatch the proposed pillar structure to `/council` for critique. Incorporate feedback before writing the file.

---

## Step 5: Write PILLARS.md

Create `specs/` directory if needed. Write `specs/PILLARS.md` using this exact format:

```markdown
# Infrastructure Pillars
<!-- Generated: {date} | Source: PRD.md | Status: {N}/{total} complete -->

## Pillar 1: {Name} (e.g., "Data Infrastructure")
- **Status**: [ ] not started
- **Why first**: {what depends on this existing — be specific}
- **Scope**: {what's included — list specific capabilities/modules}
- **Not included**: {explicit scope boundary — what is deferred to a later pillar}
- **Depends on**: None (foundation)
- **Estimated specs**: ~{N} (light: {n}, standard: {n}, heavy: {n})
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] Integration test: {specific test description}
  - [ ] Manual validation: {what to manually check}
  - [ ] ruff + mypy + pytest clean

## Pillar 2: {Name}
- **Status**: [ ] not started
- **Why next**: {what this enables — what becomes possible after this pillar}
- **Scope**: {what's included}
- **Not included**: {boundary}
- **Depends on**: Pillar 1
- **Estimated specs**: ~{N} (light: {n}, standard: {n}, heavy: {n})
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] Integration test: {specific test — must verify this pillar connects to the prior one}
  - [ ] Manual validation: {what to check}
  - [ ] ruff + mypy + pytest clean

## Pillar 3: {Name}
- **Status**: [ ] not started
- **Why next**: {what this enables}
- **Scope**: {what's included}
- **Not included**: {boundary}
- **Depends on**: Pillar 1, Pillar 2
- **Estimated specs**: ~{N} (light: {n}, standard: {n}, heavy: {n})
- **Gate criteria**:
  - [ ] All specs for this pillar marked [x] in BUILD_ORDER.md
  - [ ] Integration test: {specific test}
  - [ ] Manual validation: {what to check}
  - [ ] ruff + mypy + pytest clean

...

## Pillar Order Summary
| # | Pillar | Depends On | Est. Specs | Status |
|---|--------|-----------|------------|--------|
| 1 | {name} | None | ~N | [ ] |
| 2 | {name} | 1 | ~N | [ ] |
| 3 | {name} | 1, 2 | ~N | [ ] |
```

**Status values:**
- `[ ] not started` — no specs built yet
- `[~] in progress` — some specs complete, gate not yet passed
- `[x] complete` — all gate criteria passed

---

## Step 6: Output Confirmation

After writing `specs/PILLARS.md`:

1. Confirm the file path
2. Print the Pillar Order Summary table
3. State the next step: "Run `/decompose` to break each pillar into individual specs."

---

## Re-Run (Mid-Project)

`/pillars` can be re-run at any time. When re-running:

1. Read existing `specs/PILLARS.md`
2. Preserve all pillars marked `[x] complete` — do not modify their content or status
3. Re-analyze in-progress and not-started pillars against the current PRD and codebase state
4. If `$ARGUMENTS` names a specific pillar, focus re-analysis on that pillar only
5. Flag any changes to scope or gate criteria vs. the prior run
6. Ask the user to confirm changes before overwriting

---

## Notes

- **Pillar granularity:** Each pillar = 1–2 weeks of focused work (3–8 specs). Too many pillars = false precision. Too few = no meaningful gates.
- **Gate enforcement:** `/build` should refuse to start specs in Pillar N+1 until Pillar N's gate criteria are all checked. PILLARS.md is the enforcement document.
- **Integration tests in gates:** Each pillar's gate must include a cross-pillar integration test — not just unit tests. This catches interface mismatches early.
- **Scope boundaries matter:** "Not included" is as important as "Scope." Explicitly naming what's deferred prevents scope creep mid-pillar.
- **Don't duplicate with BUILD_ORDER.md:** PILLARS.md is high-level phase grouping. BUILD_ORDER.md (from `/decompose`) is the granular spec list. They reference each other but serve different purposes.
- **PRD phases ≠ Pillars:** The PRD's implementation phases are a starting point, not a template. Pillars are infrastructure layers; PRD phases are often feature-oriented. Reconcile but don't equate.
