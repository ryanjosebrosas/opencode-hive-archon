---
description: Fully autonomous spec builder — plan, review, execute, validate, commit, loop
agent: build
---

# Build: Autonomous Spec Pipeline

Fully autonomous builder that picks specs from BUILD_ORDER.md and processes them in a continuous loop: plan → review → execute → validate → code review → fix → commit → next. Zero interaction between specs. Stops only on gate failure, unresolvable error, or user interrupt.

## Usage

```
/build [next | spec-number | spec-name]
```

`$ARGUMENTS` — Which spec to start from:
- `next` (default) — pick the next pending spec in order
- `P1-05` or `flexible-metadata-schema` — start from a specific spec

Once started, the pipeline loops autonomously through specs until a stop condition is hit.

---

## Pipeline Position

```
/mvp → /prd → /pillars → /decompose → /build next (this — runs until pillar done) → /ship
```

This is Step 5 (the main loop). You run it once; it builds until done.

---

## Stop Conditions

The autonomous loop stops ONLY when:

| Condition | Behavior |
|-----------|----------|
| **Gate PASSED** | Auto-continue to next pillar |
| **Gate FAILED** | STOP — report which criteria failed |
| **Unresolvable error** | STOP — after max retries exhausted, report what's blocking |
| **User interrupts** (Ctrl+C) | STOP — save checkpoint, report progress |
| **All specs complete** | STOP — project done, run `/ship` |

Gates that PASS trigger automatic continuation to the next pillar. Gates that FAIL always stop for review.

---

## The Pipeline (Steps 1-11)

### Step 1: Pick Spec

Read `specs/BUILD_ORDER.md`. If it doesn't exist: "No BUILD_ORDER.md found. Run `/decompose` first." and stop.

**If `$ARGUMENTS` is `next` or empty:**
- Find the first `[ ]` spec whose dependencies are ALL marked `[x]`
- If no spec has all deps satisfied, report which deps are blocking and stop

**If `$ARGUMENTS` is a number or name:**
- Find that spec. Check its dependencies are satisfied.
- If deps not satisfied: "Spec {name} depends on {list}. Build those first." and stop.

Print progress dashboard:
```
╔══════════════════════════════════════════════╗
║  BUILD: {spec-name}                          ║
║  Spec {N}/{total} | Pillar {P}               ║
║  Depth: {light|standard|heavy}               ║
║  Completed: {done}/{total} ({pct}%)          ║
║  Pillar progress: {pillar-done}/{pillar-total}║
╚══════════════════════════════════════════════╝
```

---

### Step 2: Plan (T1 — FREE)

**Every spec gets a full 700-1000 line plan.** No exceptions. No tiered plan sizes. The depth label (light/standard/heavy) does NOT affect planning quality — it only affects the validation tier in Step 7.

#### Planning Process

1. **Gather context:**
   - Read the spec entry from `specs/BUILD_ORDER.md` (description, depends, touches, acceptance)
   - Read `specs/PILLARS.md` for pillar context and gate criteria
   - Read `PRD.md` for product requirements context
   - Read `memory.md` for gotchas and lessons learned
   - Read `specs/build-state.json` for context from prior specs (if exists)
   - Read relevant codebase files listed in the spec's `touches` field
   - Read patterns from recently completed specs in the same pillar

2. **Judgment call on user interaction:**
   - If the spec's approach is fully covered by BUILD_ORDER + PILLARS + PRD (acceptance criteria, files touched, approach is obvious): write the plan directly without asking questions.
   - If there are real tradeoffs, ambiguity, or decisions NOT covered in existing artifacts: ask the user before writing the plan.
   - Default: most specs should NOT need user interaction — the BUILD_ORDER was already approved.

3. **Dispatch plan writing to T1 (FREE):**
   ```
   dispatch({
     mode: "agent",
     provider: "bailian-coding-plan-test",
     model: "qwen3.5-plus",
     prompt: "{full context + spec details + template}"
   })
   ```
   - The T1 model writes the plan following `templates/STRUCTURED-PLAN-TEMPLATE.md`
   - Plan MUST be 700-1000 lines — this is a hard requirement
   - Plan MUST include actual code samples (copy-pasteable), not summaries
   - Plan MUST include exact file paths, line references, import statements
   - Plan MUST include validation commands for every task
   - Save to: `requests/{spec-id}-{spec-name}-plan.md`

4. **Validate plan size:**
   - Count lines. If under 700: reject, re-dispatch with explicit "plan is too short, expand code samples and task detail"
   - If over 1000: acceptable but flag if significantly over

**Fallback:** If `bailian-coding-plan-test` 404s, use `zai-coding-plan/glm-4.7`.
**If agent mode times out:** Increase timeout or split plan writing into sections...

---

### Step 3: Review Plan (T4 — Codex)

Dispatch the completed plan to T4 for quality review:

```
dispatch({
  taskType: "codex-review",
  provider: "openai",
  model: "gpt-5.3-codex",
  prompt: "Review this implementation plan for completeness, correctness, and risks:\n\n{full plan content}\n\nContext: This is spec {id} of the Ultima Second Brain project.\n\nRespond with one of:\n- APPROVE: Plan is ready for implementation.\n- IMPROVE: {list specific improvements} — then provide the improved sections.\n- REJECT: {list critical issues that must be fixed before implementation}."
})
```

**Handle review result:**

| Codex Result | Action |
|-------------|--------|
| **APPROVE** | Proceed to Step 4 |
| **IMPROVE** | Apply Codex's improvements to the plan, proceed to Step 4 |
| **REJECT** | Re-dispatch to T1 with Codex feedback → re-review (max 2 loops) |

If Codex rejects twice: STOP and surface the issue to the user.

---

### Step 4: Commit Plan

Git save point:
```bash
git add requests/{spec}-plan.md
git commit -m "plan({spec-name}): structured implementation plan"
```

This is the rollback point. If implementation fails, `git stash` to here and retry.

---

### Step 5: Execute (T1 — FREE)

Dispatch implementation to T1:

```
dispatch({
  mode: "agent",
  provider: "bailian-coding-plan-test",
  model: "qwen3.5-plus",
  prompt: "Implement the following plan exactly as specified:\n\n{full plan content}\n\nRead all files listed in CONTEXT REFERENCES before implementing.\nFollow all patterns listed in Patterns to Follow.\nExecute tasks in the exact order specified in STEP-BY-STEP TASKS.\nRun validation commands after each task.\nReturn a summary of files changed and validation results."
})
```

**Fallback:** If agent mode can't handle large file writes, split into multiple dispatch calls per phase/task group.
**If T1 fails completely:** Try `zai-coding-plan/glm-4.7` as fallback T1.

---

### Step 6: Validate

Run the full validation pyramid:

```bash
# Level 1: Syntax & Style
cd backend && python -m ruff check src/ tests/

# Level 2: Type Safety
cd backend && python -m mypy src/second_brain/ --ignore-missing-imports

# Level 3: Unit + Integration Tests
cd backend && python -m pytest ../tests/ -q
```

**On failure:**
1. Collect all error messages
2. Dispatch to T1: "Fix these validation errors: {errors}. The plan is at {path}."
3. Re-run validation
4. Max 3 fix-validate loops
5. If still failing after 3 loops: escalate (see Step 7 failure handling)

---

### Step 7: Code Review → Fix Loop

This is the quality gate. Runs until code is clean or max iterations reached.

#### 7a: Run Code Review

Dispatch reviews based on depth label:

**Light specs (3 free models):**
```
batch-dispatch({
  batchPattern: "free-impl-validation",
  prompt: "Review this code change:\n\n{git diff}\n\nReport: Critical/Major/Minor issues only."
})
```

**Standard specs (5 free models):**
```
batch-dispatch({
  batchPattern: "free-review-gauntlet",
  prompt: "Review this implementation against the plan:\n\nPlan: {plan summary}\nCode diff: {git diff}\n\nReport: Critical/Major/Minor issues with file:line references."
})
```

**Heavy specs (5 free models + T4 + T5):**
- Run free-review-gauntlet first
- Always dispatch to T4 (Codex) for code review
- Always dispatch to T5 (Claude Sonnet) for final review

#### 7b: Process Review Results

Collect all findings from all reviewers. Deduplicate.

| Finding Level | Action |
|--------------|--------|
| **0 issues** (all reviewers clean) | Exit loop → Step 8 |
| **Only Minor issues** | Exit loop → Step 8 (minor issues logged but don't block) |
| **Critical/Major issues** | Continue to 7c |

**Consensus gating (standard specs only):**
- If 4/5 free reviewers say clean → SKIP T4, go to Step 8
- If 2-3/5 say clean → dispatch to T4 for tiebreaker
- If 0-1/5 say clean → T1 fix → re-review

#### 7c: Fix Issues

1. Collect all Critical/Major findings into a fix list
2. Dispatch to T1: "Fix these code review findings: {findings}. Plan at {path}."
3. Re-run validation (Step 6)
4. Re-run code review (Step 7a)
5. Loop until clean OR max 3 iterations

**If 3 iterations exhausted and still failing:**
- Light spec → bump to standard depth review, try once more
- Standard spec → bump to heavy depth review, try once more
- Heavy spec → STOP, surface full failure report to user:
  ```
  SPEC FAILED: {name} — 3 code review iterations exhausted

  Remaining issues:
  - {Critical issue 1}
  - {Major issue 2}

  Last reviewer feedback: {summary}
  Last validation: {pass/fail summary}

  The pipeline has stopped. Review the issues and decide:
  a) Re-plan with different approach
  b) Skip and continue (mark as blocked)
  c) Manual fix
  ```

---

### Step 8: Commit Code

On successful validation + clean review:

```bash
git add -A
git commit -m "feat({spec-name}): {description from BUILD_ORDER}"
```

**Never include `Co-Authored-By` lines.** Commits are authored solely by the user.

---

### Step 9: Update State

1. **Mark spec complete** in `specs/BUILD_ORDER.md`:
   - Change `- [ ]` to `- [x]` for the completed spec

2. **Update `specs/build-state.json`:**
   ```json
   {
     "lastSpec": "P1-02",
     "completed": ["P1-01", "P1-02"],
     "currentPillar": 1,
     "totalSpecs": 83,
     "patternsEstablished": ["mypy strict typing", "Pydantic Settings config"],
     "decisionsLog": [
       {"spec": "P1-01", "decision": "Used Protocol classes for type stubs", "reason": "Maintains compatibility"}
     ]
   }
   ```

3. **Run rolling integration check:**
   ```bash
   cd backend && python -m ruff check src/ tests/
   cd backend && python -m mypy src/second_brain/ --ignore-missing-imports
   cd backend && python -m pytest ../tests/ -q
   ```
   If integration check fails: STOP, report regression. Do not proceed to next spec.

---

### Step 10: Gate Check

**If the completed spec is a gate (P1-GATE, P2-GATE, etc.):**

1. Read gate criteria from `specs/PILLARS.md` for this pillar
2. Run EACH gate criterion:
   - Validation commands (ruff, mypy, pytest)
   - Integration tests specified in gate criteria
   - Manual checks (verify specific behaviors)
3. Report pass/fail for each criterion

**On ALL PASS:**
- Mark pillar as `[x] complete` in PILLARS.md
- Auto-continue to next pillar (Step 11 loops back to Step 1)
- Report: "Pillar {N} gate PASSED. Continuing to Pillar {N+1}."

**On ANY FAIL:**
- List which criteria failed and why
- STOP the pipeline
- Report:
  ```
  PILLAR {N} GATE FAILED

  Passed: {list}
  Failed:
  - {criterion}: {reason}
  - {criterion}: {reason}

  Fix the failures and run /build next to continue.
  ```

**If the spec is NOT a gate:** Skip this step entirely, go to Step 11.

---

### Step 11: Loop to Next Spec

1. Increment to next unchecked spec in BUILD_ORDER.md
2. **Zero interaction** — do NOT ask the user for approval between specs
3. Go back to **Step 1**
4. Repeat until a stop condition is hit

---

## Backward Repair

If implementing spec N reveals that completed spec M needs changes:

1. Emit a note: "Spec {N} needs changes to completed spec {M}"
2. Plan + execute the patch to spec M
3. Re-validate spec M (run its acceptance criteria again)
4. Continue with spec N
5. Log the backward repair in `build-state.json`

This is autonomous — do NOT ask the user unless the repair is architectural (changes to 3+ completed specs).

---

## Context Management

Pillar 1 has 64 specs. Context window management is critical:

1. **Between specs:** Clear working context but preserve:
   - `build-state.json` (always read at Step 1)
   - `memory.md` (always read at Step 1)
   - Current pillar's completed spec list (for pattern reference)

2. **Within a spec:** Full context for that spec's plan + implementation

3. **Checkpoint system:** At the end of each spec, the state is fully captured in:
   - `build-state.json` — what's done, patterns established
   - `BUILD_ORDER.md` — checkboxes
   - `PILLARS.md` — pillar status
   - Git history — every spec is a commit

If context compacts mid-spec: read `build-state.json` + current plan file to resume.

---

## Archon Integration

**If Archon is available** (check with `archon_health_check`):
- Register each spec as an Archon task
- Update task status as spec progresses (todo → doing → review → done)
- Store execution context as Archon documents

**If Archon is unavailable:**
- Continue without Archon — it's optional for `/build`
- `build-state.json` + git commits provide sufficient state tracking

---

## Cost Profile

| Step | Tier | Cost per Spec |
|------|------|---------------|
| Plan (Step 2) | T1 | FREE |
| Review Plan (Step 3) | T4 | ~$0.02-0.05 |
| Execute (Step 5) | T1 | FREE |
| Validate (Step 6) | local | FREE |
| Code Review — light | 3x free | FREE |
| Code Review — standard | 5x free | FREE |
| Code Review — heavy | 5x free + T4 + T5 | ~$0.10-0.30 |
| **Total per light spec** | | **~$0.03-0.05** |
| **Total per standard spec** | | **~$0.03-0.10** |
| **Total per heavy spec** | | **~$0.15-0.40** |
| **Full Pillar 1 (64 specs)** | | **~$3-8 estimated** |

---

## Validation Pyramid by Depth

The depth label ONLY affects the validation tier. Planning is always 700-1000 lines.

| Depth | L1 Syntax | L2 Types | L3 Unit | L4 Integration | Review Tier |
|-------|-----------|----------|---------|----------------|-------------|
| light | Required | Required | Required | — | 3-model free |
| standard | Required | Required | Required | Required | 5-model free + consensus T4 |
| heavy | Required | Required | Required | Required | 5-model free + T4 always + T5 |

---

## Notes

- `/build` is fully autonomous. You say `/build next` once and it churns through specs.
- Old commands (`/planning`, `/execute`, `/code-loop`, `/final-review`, `/commit`) remain available for manual use.
- `build-state.json` is the cross-session state bridge.
- Every spec produces: 1 plan commit + 1 code commit (minimum 2 commits per spec).
- If `opencode serve` is not running, the pipeline cannot dispatch — STOP and report.
- **Never skip planning.** Every spec gets 700-1000 lines. No shortcuts.
