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

## ENFORCEMENT — No Step Skipping (EVER)

**This rule applies in ALL modes: autonomous, manual, `/build next`, single spec.**

Every spec — regardless of depth label — MUST run every step in order:

```
Step 1 (Pick) → Step 2 (Plan) → Step 3 (T4 Plan Review) → Step 4 (Commit Plan)
→ Step 5 (Execute) → Step 6 (Validate) → Step 7 (Code Review + T4 Panel)
→ Step 8 (Commit + Push) → Step 9 (Update State) → Step 10 (Gate Check) → Step 11 (Loop)
```

The depth label (light/standard/heavy) ONLY controls:
- How many free models run in Step 7a (3 / 5 / 5)
- Whether T5 is called in Step 7e (heavy only, as last resort)

**The depth label does NOT skip:**
- Step 3 (T4 plan review) — runs for ALL depths
- Step 6 (validate: ruff + mypy + pytest) — runs for ALL depths
- Step 7d (T4 panel: codex + sonnet-4-5 + sonnet-4-6) — runs for ALL depths

**Forbidden shortcuts (all VIOLATIONS):**
- Skipping T4 plan review because "it's a standard spec"
- Skipping the T4 panel sign-off because "gauntlet was clean"
- Skipping validation because "implementation looked clean"
- Dispatching T1 to implement before plan is written and T4-reviewed
- Committing without running the T4 panel
- Running only T5 instead of the full gauntlet + T4 panel

If you find yourself skipping any step: STOP, go back, run the skipped step.

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
   - **Embed the Archon RAG Context block fetched in Step 1b** — include it in the plan prompt as `## Archon RAG Context` so the T1 model has the pre-fetched documentation

2. **Judgment call on user interaction:**
   - If the spec's approach is fully covered by BUILD_ORDER + PILLARS + PRD (acceptance criteria, files touched, approach is obvious): write the plan directly without asking questions.
   - If there are real tradeoffs, ambiguity, or decisions NOT covered in existing artifacts: ask the user before writing the plan.
   - Default: most specs should NOT need user interaction — the BUILD_ORDER was already approved.

3. **Detect plan mode:**
   - **Single Plan Mode** (DEFAULT — 90%+ of specs): Use when spec has <10 estimated tasks OR touches <5 files OR is marked "light"/"standard"
   - **Master + Sub-Plan Mode** (EXCEPTION — rare, heavy specs): Use when spec has >=10 estimated tasks OR touches >=5 files OR is marked "heavy"
   - When in doubt: default to Single Plan Mode

#### Single Plan Mode (Default)

4. **Dispatch plan writing — thinking model cascade via native command mode:**
    ```
    // Step 1: prime
    dispatch({ mode: "command", command: "prime", prompt: "" })

    // Step 2: /planning — automatically uses thinking cascade:
    // kimi-k2-thinking → cogito-2.1:671b → qwen3-max → claude-opus-4-5
    dispatch({
      mode: "command",
      command: "planning",
      prompt: "{spec-id} {spec-name}\n\nSpec from BUILD_ORDER:\n- Description: {description}\n- Depends: {deps}\n- Touches: {files}\n- Acceptance: {criteria}",
      taskType: "planning",
      timeout: 900,
    })
    ```
    - `/planning` always uses a thinking model — reasoning produces better 700-1000 line plans
    - Cascade: `kimi-k2-thinking` (FREE) → `cogito-2.1:671b` (FREE) → `qwen3-max` (FREE) → `claude-opus-4-5` (PAID fallback)
    - Command mode invokes `/planning` natively — no model interpretation of slash commands as prose
    - The T1 model runs /planning which writes the plan following `templates/STRUCTURED-PLAN-TEMPLATE.md`
    - Plan MUST be 700-1000 lines — this is a hard requirement
    - Plan MUST include actual code samples (copy-pasteable), not summaries
    - Plan MUST include exact file paths, line references, import statements
    - Plan MUST include validation commands for every task
    - Save to: `requests/{spec-id}-{spec-name}-plan.md`

5. **Validate plan size:**
    - Count lines. If under 700: reject, re-dispatch with explicit "plan is too short, expand code samples and task detail"
    - If over 1000: acceptable but flag if significantly over

#### Master + Sub-Plan Mode (Exception)

4. **Dispatch master plan writing — thinking model cascade via native command mode:**
    ```
    // Step 1: prime
    dispatch({ mode: "command", command: "prime", prompt: "" })

    // Step 2: /planning master mode — same thinking cascade, longer timeout
    dispatch({
      mode: "command",
      command: "planning",
      prompt: "{spec-id} {spec-name}\n\nThis is a complex spec — use Master + Sub-Plan mode.\n\nSpec from BUILD_ORDER:\n- Description: {description}\n- Depends: {deps}\n- Touches: {files}\n- Acceptance: {criteria}",
      taskType: "planning",
      timeout: 1200,
    })
    ```
    - The T1 model runs /planning in master mode which writes the master plan + all sub-plans
    - Master plan MUST be ~400-600 lines — defines phases, task groupings, phase gates
    - Each sub-plan MUST be 700-1000 lines
    - Save to: `requests/{spec-id}-{spec-name}-master-plan.md` + `requests/{spec-id}-{spec-name}-phase-*.md`

5. **Validate master plan size:**
    - Count lines. If under 400 or over 600: reject, re-dispatch with size adjustment guidance

6. **Validate each sub-plan size:**
    - Same as single plan: 700-1000 lines required
    - /planning in master mode creates all sub-plans automatically — no separate dispatch loop needed

**Fallback:** If `bailian-coding-plan-test` 404s, use `zai-coding-plan/glm-4.7`.
**If agent mode times out:** Increase timeout or split plan writing into sections...

---

### Step 3: Review Plan (T4 — Codex)

#### Single Plan Mode (Default)

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

#### Master + Sub-Plan Mode (Exception)

1. **Review master plan first:**
   - Dispatch master plan to T4 using the same prompt format as above
   - Handle result (APPROVE → proceed, IMPROVE → apply changes, REJECT → re-dispatch)
   
2. **Then review each sub-plan sequentially:**
   - For each sub-plan: dispatch to T4 with sub-plan content
   - Include master plan context in the prompt
   - Handle each result the same way (APPROVE/IMPROVE/REJECT)
   - Max 2 review loops per sub-plan

3. **All artifacts must be approved** before proceeding to Step 4

---

### Step 4: Commit Plan

Git save point:

#### Single Plan Mode (Default)
```bash
git add requests/{spec-id}-{spec-name}-plan.md
git commit -m "plan({spec-name}): structured implementation plan"
```

#### Master + Sub-Plan Mode (Exception)
```bash
git add requests/{spec-id}-{spec-name}-master-plan.md requests/{spec-id}-{spec-name}-phase-*.md
git commit -m "plan({spec-name}): master plan + {N} sub-plans"
```

This is the rollback point. If implementation fails, `git stash` to here and retry.

---

### Step 5: Execute (T1 — FREE)

#### Single Plan Mode (Default)

Dispatch implementation to T1 using native command mode:

```
// Step 1: prime
dispatch({ mode: "command", command: "prime", prompt: "", provider: "bailian-coding-plan-test", model: "qwen3.5-plus" })

// Step 2: execute the plan
dispatch({
  mode: "command",
  command: "execute",
  prompt: "requests/{spec-id}-{spec-name}-plan.md",
  provider: "bailian-coding-plan-test",
  model: "qwen3.5-plus",
  timeout: 900,
})
```

**Fallback:** If `bailian-coding-plan-test` fails, dispatch.ts automatically tries `zai-coding-plan/glm-4.7` then `ollama-cloud/devstral-2:123b`.

#### Master + Sub-Plan Mode (Exception)

Execute with master plan — `/execute` handles sub-plan looping automatically:

```
// Step 1: prime
dispatch({ mode: "command", command: "prime", prompt: "", provider: "bailian-coding-plan-test", model: "qwen3.5-plus" })

// Step 2: execute master plan
dispatch({
  mode: "command",
  command: "execute",
  prompt: "requests/{spec-id}-{spec-name}-master-plan.md",
  provider: "bailian-coding-plan-test",
  model: "qwen3.5-plus",
  timeout: 1200,
})
```

`/execute` detects master plans automatically and loops through sub-plans sequentially (Step 0.5 + Step 2.5). No need for manual per-phase dispatch loops.

**Fallback:** Automatic via dispatch.ts fallback chain.

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

**On failure — classify before looping:**

First, classify every failing error into one of two buckets:

| Class | Examples | Action |
|-------|---------|--------|
| **Fixable** | type error in our code, import missing, test assertion wrong, ruff violation | Fix loop (Step 6a) |
| **Unresolvable** | missing DB/Supabase, missing API key, third-party stub gap (`mem0`, `voyageai`), network-dependent test, false positive from external library | Skip fix loop → escalate to T4 (Step 6b) |

**Unresolvable signals:**
- Error originates in `node_modules/`, `site-packages/`, or a known stub-gap module (`mem0`, `voyageai`, `supabase` internals)
- Test requires a live database, live API, or environment variable not set in CI
- mypy error on a line we did not touch in this spec
- Error message matches a known pre-existing issue in `memory.md`

#### 6a: Fix Loop (fixable errors only)

1. Collect all **fixable** errors
2. Dispatch to T1: "Fix these validation errors: {errors}. Plan: {path}."
3. Re-run validation
4. Repeat until all fixable errors are resolved — **no iteration cap**
5. **Stuck detection**: if the same error appears unchanged across 3 consecutive iterations without progress, classify it as potentially unresolvable and escalate to Step 6c

#### 6b: Unresolvable Bypass

For each unresolvable error:
1. Document it: `# KNOWN SKIP: {error} — reason: {why unresolvable}`
2. Dispatch to T4 (Codex) to confirm it is genuinely unresolvable:
   ```
   dispatch({
     taskType: "codex-review",
     prompt: "Is this validation error fixable within our codebase, or is it an external dependency issue that should be bypassed?\n\nError:\n{error}\n\nContext: {what the spec does}\n\nAnswer: BYPASS (with reason) or FIXABLE (with suggestion)."
   })
   ```
3. If T4 says **BYPASS**: add to known-skips list, continue to Step 7
4. If T4 says **FIXABLE**: treat as fixable, go back to Step 6a

#### 6c: Escalate to T4 After Stuck Detection

If the same fixable error repeats unchanged across 3 consecutive iterations (stuck):
1. Dispatch full error list + git diff to T4 (Codex):
   ```
   dispatch({
     taskType: "codex-review",
     prompt: "3 fix iterations failed. Remaining errors:\n{errors}\n\nDiff:\n{git diff}\n\nProvide: root cause analysis + exact fix for each remaining error."
   })
   ```
2. Apply T4's fixes via T1 dispatch
3. Re-run validation once more
4. If still failing → STOP, surface to user (cannot auto-resolve)

---

### Step 7: Code Review → Fix Loop

This is the quality gate. Runs until code is clean or issues are classified as acceptable.

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
- Always dispatch to T5 (Claude Sonnet 4) for final review

#### 7b: Process Review Results

Collect all findings. Deduplicate. Classify each finding:

| Class | Examples | Action |
|-------|---------|--------|
| **Fixable** | real bug, logic error, missing null check, bad import | Fix loop (7c) |
| **False positive** | reviewer complaining about intentional Protocol pattern, mypy limitation, pre-existing issue not introduced by this spec | Mark as acknowledged, do NOT fix |
| **External dependency** | "this will fail without a real Supabase connection", "needs live DB for integration test" | Mark as known-skip, proceed |

| Finding Level | Action |
|--------------|--------|
| **0 issues / only Minor / only false-positives** | Exit loop → Step 7d (T4 sign-off) |
| **Critical/Major fixable** | Continue to 7c |

**Consensus gating (standard specs):**
- 4/5 free reviewers say clean → skip T4 gauntlet, go directly to Step 7d
- 2-3/5 say clean → dispatch to T4 as tiebreaker
- 0-1/5 say clean → T1 fix → re-review

#### 7c: Fix Loop (unlimited — until fixed or stuck)

1. Collect all Critical/Major **fixable** findings
2. Dispatch to T1: "Fix these review findings: {findings}. Plan: {path}."
3. Re-run validation (Step 6)
4. Re-run code review (Step 7a)
5. Repeat until all fixable findings are resolved — **no iteration cap**

**Stuck detection**: if the exact same Critical/Major finding appears unchanged across 3 consecutive fix attempts without any reduction in issue count, escalate to T4:
- Dispatch to T4 (Codex) for root cause + fix:
  ```
  dispatch({
    taskType: "codex-review",
    prompt: "Stuck in fix loop. Same finding repeating:\n{finding}\n\nDiff:\n{git diff}\n\nProvide: root cause + exact fix, OR confirm as false-positive/unresolvable."
  })
  ```
- Apply T4 fixes via T1, re-validate, re-review
- If T4 says unresolvable/false-positive → classify as known-skip, proceed to 7d
- If T4 fix resolves it → continue normal fix loop for any remaining findings

#### 7d: T4 Panel Sign-off (always runs)

Before committing, run all three T4 reviewers in parallel:

```
batch-dispatch({
  models: "openai/gpt-5.3-codex,anthropic/claude-sonnet-4-5,anthropic/claude-sonnet-4-6",
  prompt: "Final review before commit.\n\nSpec: {spec-name}\nPlan summary: {plan summary}\nDiff:\n{git diff}\nKnown skips (if any):\n{known-skips list}\n\nVerdict: APPROVE (safe to commit) or REJECT (critical issue found — describe exact fix needed)."
})
```

**T4 panel consensus:**

| Result | Action |
|--------|--------|
| **3/3 APPROVE** | Commit + push (Step 8) |
| **2/3 APPROVE** | Commit + push — log the single dissent in commit message |
| **2/3 REJECT** | Collect all REJECT findings → T1 fix → re-run validation → re-submit T4 panel (unlimited until resolved or stuck) |
| **3/3 REJECT** | Collect all findings → T1 fix → re-submit T4 panel |
| **Stuck** (same REJECT findings across 2 panel runs unchanged) | Escalate to T5 |

#### 7e: T5 Escalation (last resort — stuck T4 panel only)

Only reached when T4 panel is stuck on the same findings across 2 consecutive runs:

```
dispatch({
  taskType: "final-review",
  provider: "anthropic",
  model: "claude-sonnet-4-6",
  prompt: "T4 panel stuck on same findings across 2 runs. Make the final call.\n\nSpec: {spec-name}\nDiff:\n{git diff}\nT4 findings:\n{t4-findings}\nKnown skips:\n{known-skips}\n\nVerdict: APPROVE (commit as-is), APPROVE-WITH-NOTES (commit, log issues in message), or REJECT (exact blocker — must be something we can fix)."
})
```

| T5 Verdict | Action |
|-----------|--------|
| **APPROVE** | Commit + push |
| **APPROVE-WITH-NOTES** | Commit + push, include T5 notes in commit message |
| **REJECT** | Apply T5's exact fix via T1 → re-run validation → re-submit T4 panel → if still stuck, STOP and surface to user |

---

### Step 8: Commit + Push

On successful validation + clean review:

**8a. Generate commit message via Haiku:**
```
dispatch({
  taskType: "commit-message",
  prompt: "Write a conventional commit message for spec {spec-name}.\n\nSpec description: {description from BUILD_ORDER}\nFiles changed: {touches list}\nGit diff summary:\n{git diff --stat HEAD}\nKnown skips (if any): {known-skips}\n\nFormat: feat({spec-name}): short description (imperative, max 50 chars)\n\nBody (3 bullets max): what was implemented and why.\n\nReturn ONLY the commit message."
})
```

**8b. Commit and push:**
```bash
git add -A
git commit --no-verify -m "{haiku-generated message}"
git push
```

**Never include `Co-Authored-By` lines.** Commits are authored solely by the user.

Push immediately after every spec — keeps remote in sync, enables rollback from any point, incremental delivery best practice.

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
| Plan (Step 2) | T0 thinking cascade | FREE (haiku fallback ~$0.01) |
| Review Plan (Step 3) | T4 Codex | ~$0.02-0.05 |
| Execute (Step 5) | T1 FREE | FREE |
| Validate (Step 6) | local | FREE |
| Code Review — light | 3x free | FREE |
| Code Review — standard | 5x free | FREE |
| Code Review — heavy | 5x free + T4 panel + T5 | ~$0.10-0.30 |
| T4 panel sign-off (Step 7d) | codex + sonnet-4-5 + sonnet-4-6 | ~$0.05-0.10 |
| Commit message (Step 8) | Haiku | ~$0.001 |
| **Total per light spec** | | **~$0.08-0.15** |
| **Total per standard spec** | | **~$0.10-0.20** |
| **Total per heavy spec** | | **~$0.20-0.50** |
| **Full Pillar 1 (64 specs)** | | **~$6-13 estimated** |

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
