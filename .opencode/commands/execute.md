---
description: Execute an implementation plan
agent: build
---

# Execute: Implement from Plan

## Plan to Execute

Read plan file: `$ARGUMENTS`

## Execution Instructions

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

Create project and tasks: `manage_project("create", ...)`, then `manage_task("create", ...)` for each plan task with dependency-based task_order. Skip if Archon unavailable.

### 2. Execute Tasks in Order

For EACH task in "Step by Step Tasks":

**a.** Read the task and any existing files being modified.

**b.** **Archon** (if available): `manage_task("update", task_id="...", status="doing")` — only ONE task in "doing" at a time.

**c.** Implement the task following specifications exactly. Maintain consistency with existing patterns.

**d.** Verify: check syntax, imports, types after each change.

**e.** **Archon** (if available): `manage_task("update", task_id="...", status="review")`

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

**Archon** (if available): `manage_task("update", task_id="...", status="done")` for all tasks. `manage_project("update", ..., description="Implementation complete, ready for commit")`

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