# Multi-Model Dispatch — Master Plan

> **Purpose**: Single source of truth for the entire multi-model dispatch feature.
> This document captures the vision, architecture, all slices, current state, and
> remaining work. Individual slice plans reference this for context.

---

## Vision

Build a **multi-model orchestration system** for the OpenCode coding workflow. The primary
model (Claude Opus) can **dispatch tasks to other AI models** (Qwen 3.5, Codex/GPT, Gemini,
GLM, Kimi, MiniMax, etc.) via the `opencode serve` HTTP API, receive responses inline, and
course-correct — all without leaving the current session.

## User Story

As a developer using Claude Opus as my primary coding agent, I want to dispatch specific
tasks (code generation, review, research, analysis) to other connected models from within
my current conversation, so that I can leverage each model's strengths without manually
switching terminals or sessions.

## Problem Statement

OpenCode connects to 75+ providers with multiple models each, but the current workflow
requires manually switching models or opening new terminal sessions. There's no way for the
active model to programmatically delegate work to another model and receive the response
back for reasoning. This limits multi-model workflows to human-driven context switching.

---

## Architecture

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **dispatch** tool | `.opencode/tools/dispatch.ts` (~400 lines) | Send a prompt to one model, get response inline |
| **batch-dispatch** tool | `.opencode/tools/batch-dispatch.ts` (~456 lines) | Send same prompt to N models in parallel, compare |
| **Task routing map** | `TASK_ROUTING` const in both tools | 17 task types across 6 tiers, auto-resolve provider/model |
| **Workflow wiring** | Markdown sections in commands/agents | Dispatch guidance in `/execute`, `/code-review`, `/code-loop`, `/planning` |

### Technology Stack

- **Runtime**: Bun 1.3.6 (OpenCode tool runtime)
- **SDK**: `@opencode-ai/sdk` v2 (`createOpencodeClient` from `@opencode-ai/sdk/v2/client`)
- **Server**: `opencode serve` on port 4096 (must be running)
- **Plugin API**: `@opencode-ai/plugin` (`tool()` helper, `tool.schema` Zod args)

### SDK Calling Convention (v2)

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
const client = createOpencodeClient({ baseUrl: "http://127.0.0.1:4096" })

// Health check
const health = await client.global.health()

// Create session
const session = await client.session.create({ title: "dispatch → provider/model" })

// Send prompt (v2 flat params)
const result = await client.session.prompt({
  sessionID: session.data.id,
  model: { providerID: "anthropic", modelID: "claude-sonnet-4-20250514" },
  system: "optional system prompt",
  format: { type: "json_schema", schema: {...}, retryCount: 2 },  // optional
  parts: [{ type: "text", text: "Hello!" }],
}, { signal: controller.signal })  // optional timeout

// Delete session
await client.session.delete({ sessionID: session.data.id })
```

**IMPORTANT**: v1 SDK uses `{ path: { id }, body: { model, parts } }` pattern. v2 uses flat
params `{ sessionID, model, parts }`. Our tools use v2.

### Task Routing Map (17 task types, 6 tiers)

| Tier | Task Types | Default Model | Rationale |
|------|-----------|---------------|-----------|
| 1: Fast/Simple | boilerplate, simple-fix, quick-check, general-opinion | `bailian-coding-plan/qwen3-coder-next` | Fast response, good patterns |
| 2: Code-Specialized | test-scaffolding, logic-verification, code-review, api-analysis | `bailian-coding-plan/qwen3-coder-plus` | Code-specialized with thinking |
| 3: Reasoning | research, architecture, library-comparison | `bailian-coding-plan/qwen3.5-plus` | Strong reasoning, broad knowledge |
| 4: Long Context | docs-lookup | `bailian-coding-plan/kimi-k2.5` | Long context, factual recall |
| 5: Prose | docs-generation | `bailian-coding-plan/minimax-m2.5` | Good prose generation |
| 6: Strongest | security-review, complex-codegen, complex-fix, deep-research | `anthropic/claude-sonnet-4-20250514` | Best reasoning |

### Available Providers

**Custom (from `opencode.json`):**
| Provider ID | Models |
|---|---|
| `bailian-coding-plan` | qwen3.5-plus, qwen3-max-2026-01-23, qwen3-coder-plus, qwen3-coder-next, glm-4.7, kimi-k2.5, glm-5, minimax-m2.5 |

**Connected (via `/connect`):**
| Provider ID | Example Models |
|---|---|
| `anthropic` | claude-sonnet-4-20250514, claude-opus-4-20250514 |
| `openai` | gpt-4.1, o4-mini |
| `google` | gemini-2.5-pro, gemini-2.5-flash |
| `github-copilot` | gpt-4.1, claude-sonnet-4-20250514 |

### Design Principles

1. **Optional, not mandatory** — if `opencode serve` isn't running, all commands work exactly as before
2. **Inline results** — dispatch returns text to the calling model's context (not a subagent, not a separate window)
3. **Stateless by default** — each dispatch creates/destroys a session. Multi-turn is opt-in via `sessionId`
4. **Task-type routing** — models can say `taskType: "security-review"` instead of memorizing provider/model pairs
5. **Explicit override wins** — `taskType` is convenience; explicit `provider`/`model` always takes precedence

---

## Slice Inventory

### Completed Slices

| # | Name | Scope | Status | Key Deliverable |
|---|------|-------|--------|-----------------|
| 1 | Dispatch Tool MVP | `.opencode/tools/dispatch.ts`, `.opencode/package.json` | **Done** | Core dispatch tool: 6 args (provider, model, prompt, sessionId, port, cleanup), health check, session lifecycle, response extraction |
| 2 | Workflow Wiring | execute.md, code-review.md, code-loop.md | **Done** | Dispatch guidance sections + model routing tables in 3 workflow commands. `dispatch: true` in code-review agent frontmatter |
| 3 | Enhanced Args | `.opencode/tools/dispatch.ts` | **Done** | 3 new args: timeout (AbortController), systemPrompt (SDK system field), jsonSchema (structured JSON output) |
| 4 | Planning Wiring | `.opencode/commands/planning.md` | **Done** | Dispatch research guidance in Phase 2+3, clarified dispatch ≠ subagent, model routing table, dispatch report tracking |
| 5 | Batch Dispatch | `.opencode/tools/batch-dispatch.ts`, code-review.md | **Done** | New batch-dispatch tool: parallel multi-model dispatch, `Promise.allSettled`, per-model timeout, structured comparison output |
| 6 | Auto-Routing | dispatch.ts, batch-dispatch.ts | **Done (code-complete, not committed)** | `taskType` arg, 17-entry TASK_ROUTING map, provider/model now optional, routing resolution with explicit override |

### In-Progress Slices

| # | Name | Scope | Status | Blocker |
|---|------|-------|--------|---------|
| 7 | Live Testing + Error Hardening | dispatch.ts, batch-dispatch.ts, test script | **Blocked** | `session.prompt()` hangs — likely wrong SDK calling convention or wrong provider/model IDs |

### Planned Slices (Not Started)

| # | Name | Scope | Description |
|---|------|-------|-------------|
| 8 | SDK Fix + Connected Provider Discovery | dispatch.ts, batch-dispatch.ts | Fix the SDK calling convention based on official docs, discover which providers are actually connected, verify with a working dispatch call |
| 9 | Error Hardening (post-live-test) | dispatch.ts, batch-dispatch.ts | Provider pre-flight check, error classification (auth/model/rate-limit/server), rate-limit retry, response truncation, duration tracking |
| 10 | Final Review + Commit Wiring | `/final-review`, `/commit`, `/system-review` | Wire dispatch into remaining secondary commands |
| 11 | Dispatch Dashboard (optional) | New command or tool | List active sessions, dispatch history, model usage stats |

---

## Current State

### What Works (verified)
- Both tools build clean: `bun build --no-bundle tools/dispatch.ts` and `tools/batch-dispatch.ts`
- Health check: `client.global.health()` returns `{ healthy: true, version: "1.2.15" }`
- Session creation: `client.session.create()` returns valid session IDs
- All 4 workflow commands have dispatch guidance sections
- `TASK_ROUTING` map resolves all 17 task types correctly
- Input validation (bad taskType, missing provider/model, invalid JSON) all produce actionable errors

### What Doesn't Work Yet (Slice 7 blockers)
- `session.prompt()` hangs indefinitely — 2+ minutes, 0 tokens generated, returns `{ data: {}, error: undefined }`
- Tested with multiple providers: `bailian-coding-plan/qwen3-coder-next`, `anthropic/claude-sonnet-4-20250514`
- Sessions show as `busy` but with 0 output tokens
- AbortController abort returns `{ data: undefined, error: { line, column, sourceURL } }` — no proper Error thrown
- Wrong model/provider — no throw, returns empty `{}`

### Critical Discovery: SDK v1 vs v2

The official docs show **v1 calling convention**:
```typescript
client.session.prompt({
  path: { id: session.id },
  body: { model: { providerID, modelID }, parts: [...] }
})
```

Our tools use **v2 calling convention**:
```typescript
client.session.prompt({
  sessionID: sessionId,
  model: { providerID, modelID },
  parts: [...]
})
```

Both import from different paths:
- v1: `import { createOpencodeClient } from "@opencode-ai/sdk"`
- v2: `import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"`

The hanging may be caused by a mismatch between our v2 flat params and what the server expects. **This is the #1 investigation priority.**

### Uncommitted Work
- Slice 6 edits (TASK_ROUTING, taskType arg) are code-complete but not committed
- Slice 7 test script exists but doesn't produce useful results due to the hanging issue
- Slice 6 plan file needs rename to `.done.md`

---

## Discoveries Log

### SDK API
- `client.global.health()` — works, returns `{ healthy: true, version: string }`
- `client.provider.list()` — returns `{ all: Provider[], default: {...}, connected: string[] }` — `connected` array lists which providers work
- `client.config.providers()` — returns `{ providers: Provider[], default: {...} }` — different from `provider.list()`
- `client.session.prompt()` — uses `ResponseStyle: "fields"` by default: returns `{ data: { info, parts }, response, error }`
- Server API: `POST /session/:id/message` (sync), `POST /session/:id/prompt_async` (async, 204), `POST /session/:id/command`
- OpenAPI spec at `http://localhost:4096/doc`

### Error Shapes (observed from live testing)
- Wrong model/provider: **no throw**, returns `{ data: {}, error: undefined }` — silent failure
- AbortController abort: **no throw**, returns `{ data: undefined, error: { line, column, sourceURL } }`
- Session hangs at 0 tokens with `busy` status — prompt never reaches the model

### Environment
- Bun 1.3.6 + Node v22.19.0
- OpenCode server v1.2.15
- SDK installed at `.opencode/node_modules/@opencode-ai/sdk/`
- SDK type definitions at `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.d.ts` (1133 lines)

---

## File Inventory

### Tools
| File | Lines | Purpose |
|------|-------|---------|
| `.opencode/tools/dispatch.ts` | ~400 | Core single-model dispatch with taskType routing |
| `.opencode/tools/batch-dispatch.ts` | ~456 | Parallel multi-model dispatch |
| `.opencode/tools/_test-dispatch.ts` | ~100 | Live test runner (Bun script, not a tool) |

### Commands & Agents (dispatch-wired)
| File | Dispatch Section |
|------|-----------------|
| `.opencode/commands/execute.md` | Section 1.7: Multi-Model Dispatch |
| `.opencode/commands/code-loop.md` | Section: Multi-Model Dispatch in Loop |
| `.opencode/commands/planning.md` | Phase 2+3: Dispatch research acceleration |
| `.opencode/agents/code-review.md` | Section: Multi-Model Dispatch (Second Opinions) + `dispatch: true` + `batch-dispatch: true` in frontmatter |

### Plans
| File | Slice | Status |
|------|-------|--------|
| `requests/multi-model-dispatch #1.done.md` | 1 | Done |
| `requests/multi-model-dispatch-workflow-wiring #2.md` | 2 | Done (needs .done rename) |
| `requests/multi-model-dispatch-enhanced-args #3.md` | 3 | Done (needs .done rename) |
| `requests/multi-model-dispatch-planning-wiring #4.md` | 4 | Done (needs .done rename) |
| `requests/multi-model-dispatch-batch #5.done.md` | 5 | Done |
| `requests/multi-model-dispatch-auto-routing #6.md` | 6 | Code-complete (needs .done rename) |
| `requests/multi-model-dispatch-live-testing #7.md` | 7 | Blocked |

### Configuration
| File | Role |
|------|------|
| `opencode.json` | Provider config (bailian-coding-plan + 8 models), agent config, MCP servers |
| `.opencode/package.json` | Dependencies: `@opencode-ai/plugin`, `@opencode-ai/sdk` |

---

## Next Steps (Priority Order)

1. **Fix SDK calling convention** (Slice 8) — check connected providers, verify v1 vs v2 params, get a single working dispatch call
2. **Error hardening** (Slice 9) — provider pre-flight, error classification, retry, truncation, duration tracking (originally part of Slice 7)
3. **Commit Slices 6+** — once dispatch actually works, commit all pending work
4. **Wire remaining commands** (Slice 10) — `/final-review`, `/commit`, `/system-review`

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| SDK v1/v2 mismatch causing hangs | **High** — dispatch doesn't work at all | Test both calling conventions, check OpenAPI spec |
| Provider not actually connected | **Medium** — dispatches to wrong model | Use `provider.list()` connected array, check with `/connect` |
| Rate limiting from providers | **Low** — transient failures | Single retry with 2s backoff, classified error messages |
| Response too large for context | **Low** — blows caller's context | 50K char truncation guard |
| TASK_ROUTING map becomes stale | **Low** — wrong model for task type | Easy to update, explicit override always available |
| Tool builds but runtime fails | **Medium** — type checks pass but actual calls fail | Live testing is the whole point of Slice 7/8 |
