---
description: Execute an implementation plan
agent: build
---

# Execute: Implement from Plan

## Hard Entry Gate (Non-Skippable)

`/execute` is plan-bound only.

Before any implementation or validation work:

1. Verify `$ARGUMENTS` is provided and points to an existing markdown file under `requests/`.
2. Verify the input is a planning artifact (feature plan / sub-plan / plan overview), not an ad-hoc prompt.
3. If either check fails, stop immediately and report:
   - `Blocked: /execute requires a /planning-generated plan file in requests/. Run /planning first.`

Never execute code changes directly from chat intent without a plan artifact.

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

### 1.6. Archon Knowledge Retrieval (recovery path only)

The plan produced by `/planning` is the source of truth. It already contains all researched
patterns, code samples, and external references needed for one-pass execution.

**Default behavior**: Trust the plan. Do NOT run upfront RAG searches before implementation.

**Recovery trigger**: If during task execution you encounter any of these:
- A plan reference that is ambiguous, incomplete, or conflicts with actual codebase state
- A library API or pattern not covered by the plan's code samples
- An integration point the plan didn't anticipate (e.g., new import path, changed function signature)

Then — and only then — do targeted Archon RAG research:
1. List sources with `archon_rag_get_available_sources` (if not already cached from preflight).
2. Run a focused 2-5 keyword search using:
   - `archon_rag_search_knowledge_base(query=..., return_mode="pages")`
   - `archon_rag_search_code_examples(query=...)`
3. Read full pages for top results using `archon_rag_read_full_page(page_id=...)`.
4. Record what gap triggered the research and what was found in the execution report.

If no gaps are encountered, record "No RAG recovery needed — plan was self-contained" in the report.

### 1.7. Multi-Model Dispatch (optional acceleration)

The `dispatch` tool sends prompts to other connected AI models via the OpenCode server.
Use it to accelerate execution by delegating appropriate subtasks or gathering pre-implementation research.

**Default behavior**: Execute tasks yourself. Dispatch is an optional optimization, not a requirement.

**When to consider dispatching:**

1. **Subtask delegation** — delegate simple/repetitive tasks to faster, cheaper models:
   - Boilerplate code generation (CRUD, schemas, type definitions)
   - Test file scaffolding (fixtures, basic test cases)
   - Configuration file generation
   - Documentation generation
   - Repetitive pattern application across multiple files

2. **Pre-implementation research** — ask another model for context before implementing:
   - "How does library X handle Y?" — when the plan doesn't cover a specific API
   - "What's the recommended pattern for Z?" — when facing an unfamiliar integration
   - "Review this approach before I implement it" — sanity check on complex logic

**When NOT to dispatch:**
- Core business logic that requires understanding the full plan context
- Tasks that require reading many project files (the dispatched model has no file access)
- Quick, simple changes (dispatch overhead > doing it yourself)
- When the plan explicitly specifies how to implement something (trust the plan)
- When `opencode serve` is not running (dispatch will error — that's fine, do it yourself)

**Model routing for execution tasks (5-Tier Cascade — maximize free models):**
| Task Type | Tier | Provider/Model | Cost |
|-----------|------|----------------|------|
| Boilerplate / simple fixes | T1a | `bailian-coding-plan/qwen3-coder-next` | FREE |
| Test scaffolding / code-heavy | T1b | `bailian-coding-plan/qwen3-coder-plus` | FREE |
| Complex codegen / research | T1c | `bailian-coding-plan/qwen3.5-plus` | FREE |
| Documentation | T1e | `bailian-coding-plan/minimax-m2.5` | FREE |
| First validation / thinking review | T2 | `zai-coding-plan/glm-5` | FREE |
| Second validation / independent | T3 | `ollama-cloud/deepseek-v3.2` | FREE |
| Code review gate | T4 | `openai/gpt-5.3-codex` | PAID (cheap) |
| Final review (last resort only) | T5 | `anthropic/claude-sonnet-4-6` | PAID (expensive) |

**Fallback**: If `bailian-coding-plan` 404s, use `zai-coding-plan/glm-4.7` for T1 tasks.

**How to dispatch a subtask:**
```
dispatch({
   taskType: "boilerplate",
   prompt: "Generate a Python {type} that:\n- {requirement 1}\n- {requirement 2}\n\nFollow this pattern:\n```python\n{paste example from plan}\n```\n\nReturn only the code, no explanations."
})
```

**How to dispatch research:**
```
dispatch({
   taskType: "research",
   prompt: "I need to implement {task description}.\nQuestion: {specific question about API/pattern/approach}\nContext: {relevant context from the plan}"
})
```

**Using dispatch results:**
- Review dispatched code before using it — never blindly paste
- Adapt generated code to match project patterns (imports, naming, style)
- If dispatch fails or returns unhelpful results, implement the task yourself
- Note in the execution report if dispatch was used: "Task N: delegated boilerplate to {model}, reviewed and integrated"

**If dispatch fails:** Implement the task yourself. Dispatch is optional. Never block execution because dispatch is unavailable.

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

Completion sweep (required):
- Before finishing `/execute`, rename any same-feature artifacts in `requests/code-reviews/` and `requests/code-loops/` from `.md` to `.done.md` when they are no longer active.
- Never leave a completed same-feature review/loop artifact as plain `.md`.

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
- **Archon RAG recovery used**: {yes — describe gap that triggered it / no — plan was self-contained}
- **RAG references**: {list of page_ids/URLs used during recovery, or "None"}
- **Dispatch used**: {yes — list tasks delegated and models used / no — all tasks self-executed}

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
