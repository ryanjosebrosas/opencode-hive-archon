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
- Required artifact from execution is the report at `requests/execution-reports/{feature}-report.done.md`.
- Archon notes/documents are allowed for handoff but should not duplicate large markdown outputs.
- Archon is mandatory for `/execute`; do not run without Archon connectivity.

Slice gate (required):
- Execute only the current approved slice plan.
- Do not begin implementation for a new slice while unresolved Critical/Major code-review findings remain for the current slice.

Incremental execution guardrails (required):
- Deliver one concrete outcome per run.
- Keep changes narrowly scoped and avoid mixing unrelated domains in one pass.
- If execution expands beyond a small slice, stop and split remaining work into a follow-up plan.

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

### 1.4. Archon Preflight (required)

Archon is a hard requirement for `/execute`.

Required preflight:
1. Verify Archon connectivity with `archon_health_check`.
2. If Archon is unavailable/unhealthy, stop immediately and report: "Blocked: Archon MCP unavailable. `/execute` requires Archon."
3. Do not continue implementation until Archon is healthy.

### 1.5. Archon Setup (required)

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

Do not skip Archon steps.

### 1.6. Archon Knowledge Retrieval (required)

Ground implementation with curated knowledge before code changes.

Required workflow:
1. List sources with `archon_rag_get_available_sources`.
2. Run focused searches using:
   - `archon_rag_search_knowledge_base(query=..., return_mode="pages")`
   - `archon_rag_search_code_examples(query=...)`
3. Read full pages for top results using `archon_rag_read_full_page(page_id=...)`.
4. If retrieval returns no relevant results, continue using plan + codebase evidence, and record "No relevant Archon RAG hits" in the report.
5. Capture the key references (titles/URLs/page_ids) in the execution report and Archon execution document.

### 2. Execute Tasks in Order

For EACH task in "Step by Step Tasks":

**a.** Read the task and any existing files being modified.

**b.** **Archon**: `archon_manage_task(action="update", task_id="...", status="doing")` — only ONE task in "doing" at a time.

**c.** Implement the task following specifications exactly. Maintain consistency with existing patterns.

**d.** Verify: check syntax, imports, types after each change.

**e.** **Archon**: `archon_manage_task(action="update", task_id="...", status="review")`

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

Validation policy (non-skippable):
- Every execution loop must run full validation depth for the current slice.
- Minimum expected pyramid: syntax/style -> type safety -> unit tests -> integration tests -> manual verification.
- Do not treat single checks as sufficient proof of completion.

### 5. Final Verification

- All tasks completed
- All tests passing
- All validations pass
- Code follows project conventions
- Slice remained focused (single outcome, no mixed-scope spillover)

**Archon** (required):
- Mark completed tasks: `archon_manage_task(action="update", task_id="...", status="done")`
- Update project status/context: `archon_manage_project(action="update", project_id="...", description="Implementation complete, ready for commit")`
- Save execution report summary as project document: `archon_manage_document(action="create"|"update", document_type="note", ...)`

### 6. Update Plan Checkboxes

Mandatory after successful execution:
- Update the executed plan file in place.
- In `ACCEPTANCE CRITERIA` and `COMPLETION CHECKLIST`, convert completed items from `- [ ]` to `- [x]`.
- Leave unmet items unchecked and append a short blocker note on that line.
- Never mark an item `- [x]` unless validation evidence exists in this run.

### 6.5 Update Requests Index (if present)

If `requests/INDEX.md` exists, update plan status entry:
- Mark executed plan as done with strike + done tag:
  - `[done] ~~{plan-filename}~~`
- Add reference to execution report path on the same line.
- Do not create `requests/INDEX.md` if it does not exist.

### 6.6 Mark Source Markdown as Done

After successful execution, mark done status in filenames only:
- Rename the executed input file (`$ARGUMENTS`) by appending `.done` before `.md`.
  - Example: `requests/my-feature-plan.md` -> `requests/my-feature-plan.done.md`
- Save the execution report using a `.done.md` filename.
  - Example: `requests/execution-reports/{feature}-report.done.md`
- Do not modify markdown H1/title text just to mark done status.

## Output Report

Save this report to: `requests/execution-reports/{feature}-report.done.md`

Use the feature name derived in Step 1. Create the `requests/execution-reports/` directory if it doesn't exist.

**IMPORTANT**: Save the report to the file FIRST, then also display it inline for the user. The saved file is consumed by `/system-review`.

---

### Meta Information

- **Plan file**: {path to the plan that guided this implementation}
- **Plan checkboxes updated**: {yes/no}
- **Files added**: {list with full paths, or "None"}
- **Files modified**: {list with full paths}
- **Archon retrieval used**: {yes/no}
- **RAG references**: {list of page_ids/URLs used, or "None"}

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
