# Multi-Model Dispatch — Slice Index

> **Purpose**: Quick reference for all slices. Each slice is a self-contained PIV loop.
> For full context, see `requests/multi-model-dispatch-master-plan.md`.
> For detailed per-slice plans, see the individual `requests/multi-model-dispatch-{name} #{N}.md` files.

---

## Slice Summary Table

| Slice | Name | Files Touched | Status | Committed | Detailed Plan |
|-------|------|---------------|--------|-----------|---------------|
| 1 | Dispatch Tool MVP | dispatch.ts, package.json | Done | Yes (in prior sessions) | `multi-model-dispatch #1.done.md` |
| 2 | Workflow Wiring | execute.md, code-review.md, code-loop.md | Done | Yes | `multi-model-dispatch-workflow-wiring #2.md` |
| 3 | Enhanced Args | dispatch.ts | Done | Yes | `multi-model-dispatch-enhanced-args #3.md` |
| 4 | Planning Wiring | planning.md | Done | Yes | `multi-model-dispatch-planning-wiring #4.md` |
| 5 | Batch Dispatch | batch-dispatch.ts, code-review.md | Done | Yes | `multi-model-dispatch-batch #5.done.md` |
| 6 | Auto-Routing | dispatch.ts, batch-dispatch.ts | Code-complete | **No** | `multi-model-dispatch-auto-routing #6.md` |
| 7 | Live Testing + Error Hardening | dispatch.ts, batch-dispatch.ts, _test-dispatch.ts | **Blocked** | No | `multi-model-dispatch-live-testing #7.md` |
| 8 | SDK Fix + Provider Discovery | dispatch.ts, batch-dispatch.ts, _test-dispatch.ts | **Not started** | No | `multi-model-dispatch-sdk-fix #8.md` |
| 9 | Error Hardening | dispatch.ts, batch-dispatch.ts | Not started | No | TBD |
| 10 | Final Wiring | final-review, commit, system-review commands | Not started | No | TBD |

---

## Slice Details

---

### Slice 1: Dispatch Tool MVP

**Goal**: A working `dispatch` custom tool that any model can call to send prompts to other
models and receive responses inline.

**What was built**:
- `.opencode/tools/dispatch.ts` — `tool()` export with 6 args: `provider`, `model`, `prompt`, `sessionId`, `port`, `cleanup`
- SDK client via `createOpencodeClient({ baseUrl })` with health check
- Session lifecycle: create → prompt → extract text → cleanup
- Response format: `--- dispatch response from {provider}/{model} ---\n{text}`
- 7 error paths: client creation, health check, session creation, prompt failure, response parsing, cleanup, bad model

**Key decisions**:
- Client-only SDK mode (connects to running `opencode serve`, doesn't start a server)
- Health check before dispatch (fail fast)
- Session title for traceability: `dispatch → provider/model`
- Generous error messages with recovery hints

**Dependencies**: `@opencode-ai/sdk` added to `.opencode/package.json`

---

### Slice 2: Workflow Wiring

**Goal**: All three execution-path commands contain dispatch guidance that models can follow
at runtime.

**What was built**:
- `.opencode/agents/code-review.md` — `dispatch: true` in frontmatter + "Multi-Model Dispatch (Second Opinions)" section + "Dispatch-Informed Observations" in output format
- `.opencode/commands/execute.md` — Section 1.7 "Multi-Model Dispatch (optional acceleration)" + model routing table + prompt templates + "Dispatch used" in report
- `.opencode/commands/code-loop.md` — "Multi-Model Dispatch in Loop" section (review dispatch + fix dispatch) + model routing table + dispatch tracking in loop report

**Key decisions**:
- Instructions-only pattern (markdown, no code changes)
- Optional, not mandatory — commands work identically without `opencode serve`
- Model routing tables with concrete provider/model recommendations
- Prompt templates for common dispatch scenarios

---

### Slice 3: Enhanced Args

**Goal**: dispatch tool supports timeout, systemPrompt, and jsonSchema args.

**What was built**:
- `timeout` — AbortController + setTimeout, signal passed via SDK options (2nd arg)
- `systemPrompt` — passed through to SDK `system` field
- `jsonSchema` — parsed with `JSON.parse`, passed as `format: { type: "json_schema", schema, retryCount: 2 }`
- Structured output extraction from `result.data.info.structured` with StructuredOutputError detection
- Response header modifiers: `[custom-system, structured-json, timeout-30s]`
- Backward compatible — all 3 args optional

**Key decisions**:
- `jsonSchema` is a string arg (tool args must be serializable primitives), parsed internally
- Timeout wraps prompt only (not session creation)
- `retryCount: 2` hardcoded (SDK default)
- Modifier tags in response header for calling model awareness

---

### Slice 4: Planning Wiring

**Goal**: `/planning` command contains dispatch guidance for research acceleration during
Phases 2-3.

**What was built**:
- Preamble exception: dispatch tool is allowed (≠ subagent — returns inline)
- Phase 2 subsection 6: "Dispatch research acceleration" — when to dispatch, when NOT to, prompt template with `timeout: 30` + `systemPrompt`, using dispatch results
- Phase 3 block: documentation dispatch research — separate prompt template focused on API docs
- Model routing table for planning research tasks (5 models)
- "Dispatch research summary" in report section

**Key decisions**:
- Integrated into existing phases (not a new phase)
- Research only, not generation — planning model writes the plan
- Trust hierarchy: local evidence > Archon > dispatch
- Archon first, dispatch second

---

### Slice 5: Batch Dispatch

**Goal**: A working `batch-dispatch` tool that sends the same prompt to N models in parallel
and returns all responses in a structured comparison.

**What was built**:
- `.opencode/tools/batch-dispatch.ts` (~456 lines) — new tool
- `models` arg (JSON string of `[{provider, model}]` array), minimum 2 targets
- `Promise.allSettled()` for parallel execution — one failure doesn't cancel others
- Per-model: independent session, AbortController, timeout, response extraction
- `finally` block ensures session cleanup even on error
- Formatted output: header, per-model sections (`[OK]`/`[TIMEOUT]`/`[ERROR]`), summary footer
- `batch-dispatch: true` added to code-review agent frontmatter
- Utility functions duplicated (tools must be self-contained)

**Key decisions**:
- Separate tool (not a dispatch.ts enhancement) — different args and return format
- Always cleanup sessions (no reuse in batch — ephemeral)
- `Promise.allSettled` not `Promise.all`
- Per-model AbortController (one timeout doesn't cancel others)

---

### Slice 6: Auto-Routing

**Goal**: Both dispatch tools support `taskType` arg with built-in routing to best model.

**What was built**:
- `TASK_ROUTING` const: 17 entries across 6 tiers (duplicated in both tools)
- `taskType` arg: optional string, lists all valid values in `.describe()`
- `provider`/`model` changed from required to optional (runtime validation: need taskType OR both)
- Routing resolution: `taskType` → provider/model, explicit args override
- Response header shows `[routed: {taskType}]` when auto-routed
- batch-dispatch with taskType (no models): helpful redirect to single dispatch tool
- Updated tool descriptions to mention taskType

**Key decisions**:
- Routing map in the tool, not extracted (YAGNI with only 2 tools)
- 17 canonical task types consolidated from 4 command-level routing tables
- batch-dispatch with taskType returns guidance (not auto-expansion to tier)
- No dynamic discovery — routing is deterministic

**STATUS**: Code-complete, builds clean, NOT committed.

---

### Slice 7: Live Testing + Error Hardening (BLOCKED)

**Goal**: Run `opencode serve`, exercise every dispatch path against real models, harden
error messages based on real failures.

**What was attempted**:
- Test script created: `.opencode/tools/_test-dispatch.ts`
- Server confirmed healthy (v1.2.15)
- `session.prompt()` hangs indefinitely — 2+ minutes, 0 tokens, returns `{}`
- Tested multiple providers: bailian-coding-plan, anthropic — all hang
- Sessions show `busy` with 0 output tokens
- AbortController abort returns `{ data: undefined, error: { line, column, sourceURL } }`

**Blocker**: The prompt never reaches the model. Likely cause: SDK v1/v2 calling convention
mismatch or wrong provider/model IDs.

**What was planned but not executed**:
- Provider pre-flight check via `client.config.providers()`
- Error classification helper (auth_missing, model_not_found, rate_limited, timeout, server_error)
- Rate limit retry (single attempt, 2s delay)
- Response truncation (50K chars)
- Duration tracking in response header

---

### Slice 8: SDK Fix + Provider Discovery (NEW — next priority)

**Goal**: Fix the SDK calling convention so dispatch actually works against the real server.

**Scope**:
1. Check which providers are actually `connected` via `client.provider.list()`
2. Verify v2 SDK flat params match what the server expects (check OpenAPI spec at `/doc`)
3. Try v1 calling convention (`path`/`body` pattern) if v2 doesn't work
4. Test with a confirmed-connected provider (user says Codex is connected)
5. Get ONE successful dispatch call end-to-end
6. Update dispatch.ts and batch-dispatch.ts if calling convention needs to change

**Key investigation areas**:
- Is `session.prompt()` the right method? Or should we use raw HTTP `POST /session/:id/message`?
- Does the v2 client's `session.prompt()` internally hit the right endpoint?
- Are the `bailian-coding-plan` models actually reachable, or is auth missing?

---

### Slice 9: Error Hardening (after SDK fix)

**Goal**: Production-ready error handling based on real error shapes discovered in Slice 8.

**Scope**:
1. Provider pre-flight check (`config.providers()` or `provider.list()`)
2. Error classification helper with real error patterns
3. Rate limit retry (single attempt, 2s delay)
4. Response size guard (50K chars)
5. Duration tracking in response header: `(1.2s)`
6. Apply same hardening to batch-dispatch.ts

---

### Slice 10: Final Wiring (optional)

**Goal**: Wire dispatch into remaining secondary commands.

**Scope**:
- `/final-review` — dispatch for second-opinion on final approval
- `/commit` — no dispatch needed (git operations)
- `/system-review` — dispatch for plan-vs-reality analysis

---

## Dependency Graph

```
Slice 1 (MVP)
  └─ Slice 2 (Workflow Wiring)
  └─ Slice 3 (Enhanced Args)
       └─ Slice 4 (Planning Wiring)
  └─ Slice 5 (Batch Dispatch)
  └─ Slice 6 (Auto-Routing) ← code-complete, not committed
       └─ Slice 8 (SDK Fix) ← NEXT PRIORITY
            └─ Slice 9 (Error Hardening)
                 └─ Slice 10 (Final Wiring)
```

Slice 7 (Live Testing) is being superseded by Slice 8 (SDK Fix) + Slice 9 (Error Hardening)
since the original plan assumed the SDK would work correctly.

---

## For `/planning` Sessions

When planning the next slice, reference this file + the master plan:
```
/planning multi-model-dispatch-sdk-fix
> Context: requests/multi-model-dispatch-master-plan.md + requests/multi-model-dispatch-slices.md
```

The planner should:
1. Read the master plan for full architecture context
2. Read the relevant slice in this index for scope
3. Read the current `dispatch.ts` and `batch-dispatch.ts` for code context
4. Focus on the specific slice's deliverables
