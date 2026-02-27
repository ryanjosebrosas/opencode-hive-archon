---
description: Semi-automated spec builder — plan, approve, implement, validate, commit
agent: build
---

# Build: Plan + Implement One Spec

Semi-automated builder that takes the next spec from BUILD_ORDER.md, auto-generates a plan at the appropriate depth, presents a decision summary for approval, then implements, validates, and commits.

## Usage

```
/build [next | spec-number | spec-name]
```

`$ARGUMENTS` — Which spec to build:
- `next` (default) — pick the next pending spec in order
- `01` or `scaffold` — build a specific spec by number or name

---

## Pipeline Position

```
/mvp → /prd → /decompose → /build next (repeat) → /ship
```

This is Step 4 (the main loop). Repeat until all specs are done.

---

## Step 1: Read Build State

Read `specs/BUILD_ORDER.md`. If it doesn't exist, report: "No BUILD_ORDER.md found. Run `/decompose` first." and stop.

Parse the spec list. Count completed `[x]` vs pending `[ ]`.

---

## Step 2: Select Spec

**If `$ARGUMENTS` is `next` or empty:**
- Find the first `[ ]` spec whose dependencies are ALL marked `[x]`
- If no spec has all deps satisfied, report which deps are blocking and stop

**If `$ARGUMENTS` is a number or name:**
- Find that spec. Check its dependencies are satisfied.
- If deps not satisfied, report: "Spec {name} depends on {list}. Build those first." and stop.

---

## Step 3: Print Progress Dashboard

```
╔══════════════════════════════════════╗
║  BUILD: {spec-name}                  ║
║  Spec {N}/{total} | Layer {L}        ║
║  Depth: {light|standard|heavy}       ║
║  Completed: {done}/{total} ({pct}%)  ║
╚══════════════════════════════════════╝
```

---

## Step 4: Auto-Generate Plan

Based on the spec's complexity tag, generate a plan:

### Light (~100 lines)

Minimal plan for well-understood work:

```markdown
# Spec: {name}

## What
{spec purpose from BUILD_ORDER.md}

## Files
- Create: {list}
- Modify: {list}

## Tasks
1. {task with validation command}
2. {task with validation command}
3. {task with validation command}

## Acceptance
- {acceptance test from BUILD_ORDER.md}

## Validate
ruff check {paths}
mypy {paths}
```

### Standard (~300 lines)

Moderate plan with patterns and testing:

Use the existing `/planning` interactive discovery flow, trimmed for scope:
- Understand the spec intent (from BUILD_ORDER.md — no extended conversation needed)
- Explore relevant codebase patterns
- Make key design decisions
- Produce plan: Feature Description, Solution Statement, Files, Patterns, Tasks, Testing, Validation
- Each task gets: ACTION, TARGET, IMPLEMENT, VALIDATE

### Heavy (~700 lines)

Full `/planning` interactive discovery treatment:
- Run the complete `/planning` discovery process (Understand → Explore → Design → Preview → Write Plan)
- Include all fields: patterns, code samples, edge cases, testing strategy
- Consider running `/council` for architectural decisions within the spec

Save plan to: `requests/{spec-number}-{spec-name}-plan.md`

---

## Step 5: Present Decision Summary

Show the human a **concise approval prompt** (NOT the full plan):

```
┌─────────────────────────────────────────┐
│ SPEC: {number} — {name} ({depth})       │
├─────────────────────────────────────────┤
│ What:     {1-line purpose}              │
│ Creates:  {new files}                   │
│ Modifies: {existing files}              │
│ Key decision: {the main arch choice}    │
│ Risk:     {what could go wrong}         │
│ Tests:    {what gets tested}            │
│ Depends:  {completed prereqs}           │
├─────────────────────────────────────────┤
│ Full plan: requests/{spec}-plan.md      │
├─────────────────────────────────────────┤
│ Approve? [y / n / detail / retag]       │
└─────────────────────────────────────────┘
```

- **y** — proceed to implementation
- **n** — abort this spec, return to loop
- **detail** — show the full plan for review
- **retag** — change depth tag (e.g., light→standard) and regenerate plan

Wait for explicit human response.

---

## Step 6: Implement

On approval, implement using the 5-tier cascade:

### For light specs:
1. Implement directly (or dispatch to T1 for simple work)
2. Run validation: `ruff check`, `mypy`
3. If issues: fix and retry (max 3x)

### For standard specs:
1. Dispatch implementation to T1 (bailian-coding-plan-test/qwen3.5-plus)
2. Run T2 review (zai-coding-plan/glm-5)
3. Run actual tests: `ruff check`, `mypy`, `pytest`
4. If T2 finds issues: T1 fixes, loop max 3x
5. T4 gate (openai/gpt-5.3-codex) before commit

### For heavy specs:
1. Dispatch implementation to T1 (bailian-coding-plan-test/qwen3.5-plus)
2. Run T2 review (zai-coding-plan/glm-5)
3. Run T3 second opinion (ollama-cloud/deepseek-v3.2)
4. Run actual tests: `ruff check`, `mypy`, `pytest`
5. If issues: T1 fixes, loop max 3x
6. T4 gate (openai/gpt-5.3-codex) before commit

### Validation Pyramid by Depth

| Depth | L1 Syntax | L2 Types | L3 Unit Tests | L4 Integration | L5 Human |
|-------|-----------|----------|---------------|----------------|----------|
| light | Required | Required | — | — | Approval gate |
| standard | Required | Required | Required | — | Approval gate |
| heavy | Required | Required | Required | Required | Approval gate |

---

## Step 7: Handle Failures

### 3x Validation Failure Escalation

If implementation fails validation 3 times:

1. **If light spec:** Bump to standard depth, regenerate plan, re-approve
2. **If standard spec:** Bump to heavy depth, regenerate plan, re-approve
3. **If heavy spec:** Surface full failure report to human:
   ```
   SPEC FAILED: {name} — 3 validation attempts exhausted
   
   Last T2 feedback: {summary}
   Last test errors: {summary}
   
   Options:
   a) Re-plan with different approach
   b) Split into smaller specs (/decompose --focus {name})
   c) Skip and continue (mark as blocked)
   d) Manual implementation
   ```

### Backward Repair

If implementing spec N reveals that completed spec M needs changes:

1. Emit a patch note: "Spec {N} needs changes to completed spec {M}"
2. Ask human: "Allow patch to spec {M}? [y/n]"
3. On yes: plan + execute patch, re-validate spec M, continue spec N
4. On no: work around the issue in spec N

---

## Step 8: Commit and Update State

On successful validation:

1. Run `/commit` with message: `feat({spec-name}): {description}`
2. Mark spec `[x]` in `specs/BUILD_ORDER.md`
3. Update `specs/build-state.json`:

```json
{
  "lastSpec": "04-retrieval",
  "completed": ["01-scaffold", "02-core-types", "03-database", "04-retrieval"],
  "patternsEstablished": ["lazy-init services", "Pydantic v2 models"],
  "decisionsLog": [
    { "spec": "03", "decision": "Use Supabase pgvector", "reason": "Already in stack" }
  ],
  "totalSpecs": 12,
  "currentLayer": 2
}
```

4. Report completion:

```
SPEC COMPLETE: {number} — {name}
Progress: {done}/{total} ({pct}%)
Layer: {current}/{max}
Next: /build next → {next-spec-name}
```

---

## Step 9: Rolling Integration Check

After every `/build` commit, run a lightweight integration sanity check:

```bash
# Syntax + types across full project
ruff check backend/src tests
mypy backend/src/second_brain

# Full test regression
PYTHONPATH=backend/src pytest tests/ -q
```

If the integration check fails, report immediately — don't proceed to next spec.

---

## Notes

- `/build` wraps existing commands internally: `/planning` → `/execute` → `/code-loop` → `/final-review` → `/commit`
- The old commands remain available for manual use outside the `/build` flow
- `build-state.json` is the cross-session context bridge — read it at the start of every `/build`
- Light specs should take 5-10 minutes. Standard: 15-25 minutes. Heavy: 30-60 minutes.
- If `opencode serve` is not running, implementation falls back to direct execution (no dispatch)
