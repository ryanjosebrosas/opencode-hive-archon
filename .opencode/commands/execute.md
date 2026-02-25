---
description: Execute an implementation plan
agent: build
---

# Execute: Implement from Plan

## Plan to Execute

Read plan file: `$ARGUMENTS`

## Execution Instructions

Lean mode (default):
- Do not create extra documentation files during execution unless explicitly required by the plan.
- Required artifact from execution is the report at `requests/execution-reports/{feature}-report.md`.
- Archon notes/documents are allowed for handoff but should not duplicate large markdown outputs.

Slice gate (required):
- Execute only the current approved slice plan.
- Do not begin implementation for a new slice while unresolved Critical/Major code-review findings remain for the current slice.

### 0.5. Detect Plan Type

Read the plan file.

**If file contains `<!-- PLAN-SERIES -->`**: Extract sub-plan paths from PLAN INDEX. Report: "Detected plan series with N sub-plans." Proceed to Series Mode (Step 2.5).

**If no marker**: Standard single plan — proceed normally, skip series-specific steps.

### 1. Read and Understand

- Read the ENTIRE plan carefully — all tasks, dependencies, validation commands, testing strategy
- Check `memory.md` for gotchas related to this feature area
- **Derive feature name** from the plan path: strip directory prefix and `-plan.md` suffix.
  Example: `requests/user-auth-plan.md` → `user-auth`. For plan series: `requests/big-feature-plan-overview.md` → `big-feature`.
  Store this — you'll use it when saving the execution report.

### 1.5. Archon Setup (if available)

Use Archon as the execution bridge so another LLM/agent can continue from structured state.

Required workflow:
1. Resolve project:
   - Find existing project via `archon_find_projects(query=...)`
   - If none, create project via `archon_manage_project(action="create", ...)`
2. Register execution tasks from plan:
   - Create one Archon task per Step-by-Step task via `archon_manage_task(action="create", ...)`
   - Set `task_order` to preserve dependency order
   - Keep only one task in `doing` at a time
3. Store execution context document:
   - Save or update an execution note/spec via `archon_manage_document(action="create"|"update", document_type="note", ...)`
   - Include plan path, spec lock summary, and routing/fallback policy highlights

Skip Archon steps only if Archon is unavailable.

### 2. Execute Tasks in Order

For EACH task in "Step by Step Tasks":

**a.** Read the task and any existing files being modified.

**b.** **Archon** (if available): `archon_manage_task(action="update", task_id="...", status="doing")` — only ONE task in "doing" at a time.

**c.** Implement the task following specifications exactly. Maintain consistency with existing patterns.

**d.** Verify: check syntax, imports, types after each change.

**e.** **Archon** (if available): `archon_manage_task(action="update", task_id="...", status="review")`

### 2.5. Series Mode Execution (if plan series detected)

For each sub-plan in PLAN INDEX order:

1. Read sub-plan file and shared context from overview
2. Execute tasks using Step 2 process (a → e)
3. Run sub-plan's validation commands
4. Read HANDOFF NOTES for state to carry forward
5. Report: "Sub-plan {N}/{total} complete."

**If a sub-plan fails**: Stop, report which sub-plan/task failed. Don't continue — failed state propagates.

### 3. Implement Testing Strategy

Create all test files specified in the plan. Implement test cases. Ensure edge case coverage.

### 4. Run Validation Commands

Execute ALL validation commands from the plan in order. Fix failures before continuing.

### 5. Final Verification

- All tasks completed
- All tests passing
- All validations pass
- Code follows project conventions

**Archon** (if available):
- Mark completed tasks: `archon_manage_task(action="update", task_id="...", status="done")`
- Update project status/context: `archon_manage_project(action="update", project_id="...", description="Implementation complete, ready for commit")`
- Save execution report summary as project document: `archon_manage_document(action="create"|"update", document_type="note", ...)`

### 6. Update Plan Checkboxes

Check off met items in ACCEPTANCE CRITERIA (`- [ ]` → `- [x]`) and COMPLETION CHECKLIST. Note unmet criteria in Output Report.

## Output Report

Save this report to: `requests/execution-reports/{feature}-report.md`

Use the feature name derived in Step 1. Create the `requests/execution-reports/` directory if it doesn't exist.

**IMPORTANT**: Save the report to the file FIRST, then also display it inline for the user. The saved file is consumed by `/system-review`.

---

### Meta Information

- **Plan file**: {path to the plan that guided this implementation}
- **Files added**: {list with full paths, or "None"}
- **Files modified**: {list with full paths}

### Completed Tasks

For each task in the plan:
- Task N: {brief description} — {completed / skipped with reason}

### Divergences from Plan

For each divergence (if any):
- **What**: {what changed from the plan}
- **Planned**: {what the plan specified}
- **Actual**: {what was implemented instead}
- **Reason**: {why the divergence occurred}

If no divergences: "None — implementation matched plan exactly."

### Validation Results

```bash
# Output from each validation command run in Step 4
```

### Tests Added

- {test files created, number of test cases, pass/fail status}
- If no tests: "No tests specified in plan."

### Issues & Notes

- {any issues not addressed in the plan}
- {challenges encountered during implementation}
- {recommendations for plan or process improvements}
- If none: "No issues encountered."

### Ready for Commit

- All changes complete: {yes/no}
- All validations pass: {yes/no}
- Ready for `/commit`: {yes/no — if no, explain what's blocking}

### Archon Handoff

- Project ID: {id or "not used"}
- Tasks synced: {count}
- Execution document updated: {yes/no}
- Next assignee suggestion: {User / Coding Agent / specific agent name}
