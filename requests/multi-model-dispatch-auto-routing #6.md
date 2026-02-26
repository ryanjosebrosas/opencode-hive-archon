# Feature: Multi-Model Dispatch Auto-Routing

## Feature Description

Add a `taskType` arg to `dispatch.ts` (and `batch-dispatch.ts`) that auto-selects the best provider/model from a built-in routing table based on task category. This eliminates the need for every command/agent to duplicate model routing tables in their markdown guidance — the tool itself knows the best model for each task type. Calling models can simply say `taskType: "security-review"` instead of `provider: "anthropic", model: "claude-sonnet-4-20250514"`.

The routing table is consolidated from the 4 existing command-level routing tables (execute, code-review, code-loop, planning) into a single canonical map with 17 task types across 6 tiers.

## User Story

As a model running workflow commands, I want to dispatch tasks by specifying a task type (e.g., "security-review", "boilerplate", "research") instead of manually looking up the correct provider/model pair, so that dispatch calls are simpler, consistent, and automatically routed to the best model for the job.

## Problem Statement

Every workflow command (`/execute`, `/code-review`, `/code-loop`, `/planning`) has its own model routing table copy-pasted in markdown. This creates:

1. **Duplication**: 4 separate tables with the same information, spread across 4 files
2. **Drift risk**: When models change, all 4 tables must be updated manually
3. **Cognitive load**: The calling model must read the table, look up the right provider/model, and pass both args explicitly
4. **No single source of truth**: The routing "intelligence" lives in markdown guidance, not in the tool itself

Auto-routing moves the routing logic into the tool, where it belongs. The markdown tables become documentation of the defaults, not the enforcement mechanism.

## Solution Statement

- Decision 1: **New `taskType` arg** — optional string arg with predefined values. When provided, auto-resolves to `{provider, model}` from a built-in routing map.
- Decision 2: **Explicit override wins** — if `provider` AND `model` are also specified alongside `taskType`, the explicit values take precedence. `taskType` is a convenience default, not a forced route.
- Decision 3: **Make `provider`/`model` optional** — remove `.min(1)` validation. Runtime check ensures either `taskType` OR (`provider` + `model`) is provided.
- Decision 4: **Routing map as a const object** — defined at the top of dispatch.ts as a `Record<string, {provider, model}>`. Easy to update, single source of truth.
- Decision 5: **Add to both tools** — dispatch.ts and batch-dispatch.ts both get `taskType`. For batch-dispatch, `taskType` resolves to a single model (the best for that task), but `models` takes precedence if provided.
- Decision 6: **Response header shows resolved model** — when `taskType` is used, the response header shows both the task type and the resolved model: `[routed: security-review → anthropic/claude-sonnet-4-20250514]`

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `.opencode/tools/dispatch.ts`, `.opencode/tools/batch-dispatch.ts`
- **Dependencies**: None beyond existing SDK imports

### Slice Guardrails (Required)

- **Single Outcome**: Both dispatch tools support `taskType` arg with built-in routing
- **Expected Files Touched**: 2 files (`dispatch.ts`, `batch-dispatch.ts`)
- **Scope Boundary**: Does NOT update command markdown files (routing tables remain as documentation). Does NOT add dynamic routing (server-side model discovery). Does NOT modify batch-dispatch's `models` arg behavior.
- **Split Trigger**: If routing logic exceeds 30 lines, extract to a shared `_routing.ts` helper

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-330) — Why: primary file being modified. Must understand current args (lines 62-116), execute function (lines 118-329), response header format (lines 320-328)
- `.opencode/tools/batch-dispatch.ts` (lines 1-310) — Why: secondary file being modified. Same pattern — add `taskType`, make it resolve to default `models` when `models` arg not provided
- `opencode.json` (lines 11-87) — Why: available models in `bailian-coding-plan` provider. Routing table must reference exact model IDs from this config.

### New Files to Create

- None — modifications to 2 existing files only

### Related Memories (from memory.md)

- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" — Relevance: when taskType resolves to a model that's not connected, the error message should be actionable (tell them which model was resolved and how to connect it)
- Memory: "Avoid mixed-scope loops" — Relevance: this slice is tool-code only. No markdown changes.

### Relevant Documentation

- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools/)
  - Specific section: Tool args, Zod schema
  - Why: `taskType` uses `tool.schema.string().optional()` — same pattern as existing optional args

### Patterns to Follow

**dispatch.ts existing optional arg pattern** (lines 95-116):
```typescript
timeout: tool.schema
  .number()
  .optional()
  .describe("Timeout in seconds..."),
systemPrompt: tool.schema
  .string()
  .optional()
  .describe("Optional system prompt..."),
```
- Why this pattern: `taskType` follows the same `.string().optional().describe()` pattern.

**dispatch.ts response header modifier pattern** (lines 320-328):
```typescript
const modifiers: string[] = []
if (args.systemPrompt) modifiers.push("custom-system")
if (parsedFormat) modifiers.push("structured-json")
if (args.timeout !== undefined) modifiers.push(`timeout-${args.timeout}s`)
const modifierStr = modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""
const header = `--- dispatch response from ${args.provider}/${args.model}${modifierStr} ---\n`
```
- Why this pattern: add `routed: {taskType} → {provider}/{model}` to modifiers when taskType is used.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Define the routing map as a const object.

**Tasks:**
- Add routing map to dispatch.ts
- Add `taskType` arg to dispatch.ts
- Add routing resolution logic to dispatch.ts execute function

### Phase 2: Core Implementation

Update dispatch.ts args, validation, and response formatting.

**Tasks:**
- Make `provider`/`model` optional with runtime validation
- Add routing resolution before health check
- Update response header with routing info

### Phase 3: Integration

Apply same changes to batch-dispatch.ts.

**Tasks:**
- Add routing map + `taskType` arg to batch-dispatch.ts
- Add routing resolution for default single-model when `models` not provided

### Phase 4: Testing & Validation

Verify both tools build and args work.

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. UPDATE `.opencode/tools/dispatch.ts` — Add routing map and taskType arg

- **IMPLEMENT**: 
  a) Add the routing map as a `const TASK_ROUTING` object after the utility functions and before `export default tool({`. This is the single source of truth for task → model mapping.

  ```typescript
  const TASK_ROUTING: Record<string, { provider: string; model: string }> = {
    // Tier 1: Fast / Simple
    "boilerplate": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
    "simple-fix": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
    "quick-check": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
    "general-opinion": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
    // Tier 2: Code-Specialized
    "test-scaffolding": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
    "logic-verification": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
    "code-review": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
    "api-analysis": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
    // Tier 3: Reasoning / Architecture
    "research": { provider: "bailian-coding-plan", model: "qwen3.5-plus" },
    "architecture": { provider: "bailian-coding-plan", model: "qwen3.5-plus" },
    "library-comparison": { provider: "bailian-coding-plan", model: "qwen3.5-plus" },
    // Tier 4: Long Context / Factual
    "docs-lookup": { provider: "bailian-coding-plan", model: "kimi-k2.5" },
    // Tier 5: Prose / Documentation
    "docs-generation": { provider: "bailian-coding-plan", model: "minimax-m2.5" },
    // Tier 6: Strongest Reasoning
    "security-review": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
    "complex-codegen": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
    "complex-fix": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
    "deep-research": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
  }
  ```

  b) Add `taskType` arg to the args object, after `jsonSchema`:

  ```typescript
  taskType: tool.schema
    .string()
    .optional()
    .describe(
      "Optional: auto-route to the best model for this task type. " +
        "When provided, provider/model are resolved automatically. " +
        "Explicit provider/model args override taskType if both are given. " +
        "Values: boilerplate, simple-fix, quick-check, general-opinion, " +
        "test-scaffolding, logic-verification, code-review, api-analysis, " +
        "research, architecture, library-comparison, docs-lookup, " +
        "docs-generation, security-review, complex-codegen, complex-fix, deep-research",
    ),
  ```

  c) Make `provider` and `model` optional — change `.min(1, "...")` to just `.optional()`:

  **Current:**
  ```typescript
  provider: tool.schema
    .string()
    .min(1, "provider is required")
    .describe("Provider ID..."),
  model: tool.schema
    .string()
    .min(1, "model is required")
    .describe("Model ID..."),
  ```

  **Replace with:**
  ```typescript
  provider: tool.schema
    .string()
    .optional()
    .describe(
      "Provider ID (e.g. 'anthropic', 'bailian-coding-plan'). " +
        "Required unless taskType is provided.",
    ),
  model: tool.schema
    .string()
    .optional()
    .describe(
      "Model ID within the provider (e.g. 'claude-sonnet-4-20250514', 'qwen3.5-plus'). " +
        "Required unless taskType is provided.",
    ),
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:95-116` — existing optional arg pattern
- **IMPORTS**: None new
- **GOTCHA**: 
  1. `provider` and `model` change from required to optional. Existing callers always provide them, so no breakage.
  2. The routing map keys are short, lowercase, hyphenated — easy for the model to type.
  3. The `describe` for `taskType` lists all valid values — this is critical for model discoverability.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 2. UPDATE `.opencode/tools/dispatch.ts` — Add routing resolution to execute function

- **IMPLEMENT**: Add routing resolution at the top of the `execute` function, before the port validation. This resolves `taskType` to `provider`/`model` if needed, and validates that either `taskType` or explicit `provider`+`model` is provided.

  **Insert at the beginning of `async execute(args, _context) {`, before `const serverPort = ...`:**

  ```typescript
  // 0. Resolve routing: taskType → provider/model (explicit args override)
  let resolvedProvider = args.provider
  let resolvedModel = args.model
  let routedVia: string | undefined

  if (args.taskType) {
    const route = TASK_ROUTING[args.taskType]
    if (!route) {
      return (
        `[dispatch error] Unknown taskType: "${args.taskType}"\n` +
        `Valid values: ${Object.keys(TASK_ROUTING).join(", ")}`
      )
    }
    // Explicit provider/model override taskType
    if (!resolvedProvider) resolvedProvider = route.provider
    if (!resolvedModel) resolvedModel = route.model
    if (!args.provider && !args.model) {
      routedVia = args.taskType
    }
  }

  if (!resolvedProvider || !resolvedModel) {
    return (
      "[dispatch error] Either provide both 'provider' and 'model', or provide 'taskType' for auto-routing.\n" +
      `Available task types: ${Object.keys(TASK_ROUTING).join(", ")}`
    )
  }
  ```

  Then replace all subsequent uses of `args.provider` with `resolvedProvider` and `args.model` with `resolvedModel` throughout the execute function. This affects:
  - Session title: `dispatch → ${resolvedProvider}/${resolvedModel}`
  - Prompt model config: `providerID: resolvedProvider, modelID: resolvedModel`
  - Error messages: references to provider/model
  - Response header: `${resolvedProvider}/${resolvedModel}`

  Also add routing info to the modifiers:
  ```typescript
  if (routedVia) modifiers.push(`routed: ${routedVia}`)
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:118-329` — existing execute function flow
- **IMPORTS**: None new
- **GOTCHA**: 
  1. Must replace ALL occurrences of `args.provider` and `args.model` in the execute function — there are ~8 references.
  2. The `routedVia` variable is only set when taskType fully resolved both provider AND model (user didn't override either). If user provides `taskType: "research"` but also `provider: "openai"`, then `routedVia` is undefined (hybrid usage — no routing tag in header).
  3. Keep the existing `shouldCleanup` / `isReusedSession` / timeout / jsonSchema logic unchanged.
- **VALIDATE**: `cd .opencode && bun -e "import t from './tools/dispatch.ts'; console.log(Object.keys(t.args).join(', '))"`
  Expected: `provider, model, prompt, sessionId, port, cleanup, timeout, systemPrompt, jsonSchema, taskType`

### 3. UPDATE `.opencode/tools/batch-dispatch.ts` — Add routing map and taskType arg

- **IMPLEMENT**: 
  a) Add the same `TASK_ROUTING` const (duplicated — batch-dispatch is self-contained per Slice 5 design).

  b) Add `taskType` arg after `jsonSchema`:
  ```typescript
  taskType: tool.schema
    .string()
    .optional()
    .describe(
      "Optional: auto-route to the best model for this task type. " +
        "When provided and 'models' is not given, dispatches to the single best model " +
        "for this task type (use 'dispatch' tool instead for single-model with taskType). " +
        "When 'models' is also provided, taskType is ignored. " +
        "Values: boilerplate, simple-fix, quick-check, general-opinion, " +
        "test-scaffolding, logic-verification, code-review, api-analysis, " +
        "research, architecture, library-comparison, docs-lookup, " +
        "docs-generation, security-review, complex-codegen, complex-fix, deep-research",
    ),
  ```

  c) Make `models` optional — change `.min(1, "models is required")` to `.optional()`:
  ```typescript
  models: tool.schema
    .string()
    .optional()
    .describe(
      'JSON array of model targets. Each target has "provider" and "model" fields. Minimum 2 models. ' +
        "Required unless taskType is provided (which resolves to a single default model). " +
        'Example: \'[{"provider":"bailian-coding-plan","model":"qwen3-coder-plus"},' +
        '{"provider":"bailian-coding-plan","model":"qwen3.5-plus"}]\''
    ),
  ```

  d) Add resolution at the start of execute: if `taskType` is provided and `models` is NOT, resolve to a single-model target array from the routing table. If `models` IS provided, ignore `taskType`.

  ```typescript
  // 0. Resolve routing: taskType → default models array
  let modelsJson = args.models
  let routedVia: string | undefined

  if (!modelsJson && args.taskType) {
    const route = TASK_ROUTING[args.taskType]
    if (!route) {
      return (
        `[batch-dispatch error] Unknown taskType: "${args.taskType}"\n` +
        `Valid values: ${Object.keys(TASK_ROUTING).join(", ")}\n` +
        "Note: For single-model dispatch with taskType, use the `dispatch` tool instead."
      )
    }
    // Single model from routing — batch requires 2+, suggest dispatch instead
    return (
      `[batch-dispatch info] taskType "${args.taskType}" resolves to a single model: ${route.provider}/${route.model}\n` +
      "Batch dispatch requires 2+ models. Use the `dispatch` tool with taskType for single-model routing, " +
      "or provide 'models' JSON array explicitly for batch comparison."
    )
  }

  if (!modelsJson) {
    return (
      "[batch-dispatch error] Either provide 'models' (JSON array of 2+ targets), " +
      "or use the `dispatch` tool with 'taskType' for single-model auto-routing."
    )
  }
  ```

  Then use `modelsJson` instead of `args.models` for parsing.

- **PATTERN**: `.opencode/tools/dispatch.ts` Task 2 — same routing resolution pattern
- **IMPORTS**: None new
- **GOTCHA**: 
  1. `taskType` in batch-dispatch is a convenience error message — it guides the user to use `dispatch` instead. Batch inherently requires explicit multi-model selection.
  2. An alternative design would be to have `taskType` resolve to a "tier" (e.g., all Tier 2 models). But that couples the routing map to batch logic too tightly. KISS: batch requires explicit models.
- **VALIDATE**: `cd .opencode && bun -e "import t from './tools/batch-dispatch.ts'; console.log(Object.keys(t.args).join(', '))"`
  Expected: `models, prompt, port, timeout, systemPrompt, jsonSchema, taskType`

### 4. UPDATE `.opencode/tools/dispatch.ts` — Update tool description for taskType

- **IMPLEMENT**: Update the description string to mention taskType auto-routing:

  **Current:**
  ```typescript
  description:
    "Dispatch a prompt to any connected AI model via the OpenCode server. " +
    "Use this to delegate tasks (code generation, review, research, analysis) to other models " +
    "and receive their response inline. Requires `opencode serve` running. " +
    "Supports: custom system prompts, structured JSON output (via jsonSchema), and timeouts. " +
    "Provider/model examples: anthropic/claude-sonnet-4-20250514, openai/gpt-4.1, " +
    "bailian-coding-plan/qwen3.5-plus, bailian-coding-plan/qwen3-coder-plus, " +
    "google/gemini-2.5-pro, github-copilot/gpt-4.1",
  ```

  **Replace with:**
  ```typescript
  description:
    "Dispatch a prompt to any connected AI model via the OpenCode server. " +
    "Use this to delegate tasks (code generation, review, research, analysis) to other models " +
    "and receive their response inline. Requires `opencode serve` running. " +
    "Supports: auto-routing via taskType (e.g., 'security-review', 'boilerplate', 'research'), " +
    "custom system prompts, structured JSON output (via jsonSchema), and timeouts. " +
    "Either provide taskType for auto-routing, or explicit provider/model. " +
    "Provider/model examples: anthropic/claude-sonnet-4-20250514, openai/gpt-4.1, " +
    "bailian-coding-plan/qwen3.5-plus, bailian-coding-plan/qwen3-coder-plus",
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:53-60` — existing description
- **IMPORTS**: N/A
- **GOTCHA**: Keep under 600 chars. The description is what the model reads to decide whether to use the tool.
- **VALIDATE**: Read the file, confirm description mentions taskType.

---

## TESTING STRATEGY

### Unit Tests

N/A — custom tools don't have a test framework.

### Integration Tests

**Test 1: taskType auto-routing**
- dispatch with `taskType: "security-review"`, no provider/model
- Expected: resolves to `anthropic/claude-sonnet-4-20250514`, header shows `[routed: security-review]`

**Test 2: taskType with explicit override**
- dispatch with `taskType: "security-review"`, `provider: "openai"`, `model: "gpt-4.1"`
- Expected: uses `openai/gpt-4.1` (explicit wins), no routing tag in header

**Test 3: Invalid taskType**
- dispatch with `taskType: "nonexistent"`
- Expected: error listing valid values

**Test 4: No provider, no model, no taskType**
- dispatch with only `prompt`
- Expected: error telling user to provide either taskType or provider+model

**Test 5: Partial args (provider only, no model, no taskType)**
- Expected: error (need both provider+model or taskType)

**Test 6: batch-dispatch with taskType**
- batch-dispatch with `taskType: "code-review"`, no models
- Expected: helpful message directing to single dispatch tool

**Test 7: batch-dispatch with models (taskType ignored)**
- batch-dispatch with `models` array AND `taskType`
- Expected: `models` used, `taskType` ignored

**Test 8: Backward compatibility**
- dispatch with `provider: "bailian-coding-plan"`, `model: "qwen3.5-plus"`, no taskType
- Expected: works exactly as before — no routing, no routing tag

### Edge Cases

- `taskType` with only `provider` (no model): resolves model from route, keeps explicit provider
- `taskType` with only `model` (no provider): resolves provider from route, keeps explicit model
- Empty string `taskType: ""`: treated as not provided (optional, falsy)
- All 17 task types: each resolves to the correct provider/model pair

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5
cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5
```

### Level 2: Type Safety
```bash
cd .opencode && bun -e "import t from './tools/dispatch.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"
cd .opencode && bun -e "import t from './tools/batch-dispatch.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"
```

### Level 3-4: N/A (manual testing)

### Level 5: Manual Validation
Verify routing map covers all 17 task types. Verify existing dispatch calls still work.

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `TASK_ROUTING` const with 17 entries in dispatch.ts
- [ ] `taskType` arg added to dispatch.ts with all valid values listed in description
- [ ] `provider` and `model` changed from required to optional in dispatch.ts
- [ ] Runtime validation: either taskType or provider+model required
- [ ] Routing resolution: taskType → provider/model with explicit override
- [ ] All `args.provider`/`args.model` replaced with `resolvedProvider`/`resolvedModel`
- [ ] Response header shows `[routed: {taskType}]` when auto-routed
- [ ] Invalid taskType returns error with valid values list
- [ ] `TASK_ROUTING` const duplicated in batch-dispatch.ts
- [ ] `taskType` arg added to batch-dispatch.ts
- [ ] `models` changed from required to optional in batch-dispatch.ts
- [ ] batch-dispatch with taskType (no models) returns helpful redirect to dispatch tool
- [ ] dispatch.ts description updated to mention taskType
- [ ] Both tools build without errors
- [ ] Backward compatible: existing calls with provider+model still work

### Runtime (verify after testing/deployment)

- [ ] dispatch with taskType auto-routes correctly
- [ ] dispatch with taskType + explicit provider/model uses explicit values
- [ ] batch-dispatch with models works as before
- [ ] All 17 task types resolve to correct provider/model

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Routing map in the tool, not extracted**: The routing table lives directly in dispatch.ts (and duplicated in batch-dispatch.ts). YAGNI: a shared `_routing.ts` would be premature with only 2 tools. Extract when a third tool needs routing.
- **17 canonical task types**: Consolidated from 18 original types across 4 commands. Reduced to short, memorable, hyphenated keys. Easy for models to type and discover.
- **Explicit override wins**: `taskType` is a convenience, not a mandate. The calling model can always specify exact `provider`/`model` to override routing. This preserves full flexibility.
- **batch-dispatch redirect**: Rather than auto-expanding taskType to multiple models (which models? how many?), batch-dispatch with taskType gives a helpful message directing to single dispatch. Batch inherently requires explicit multi-model selection.
- **No dynamic discovery**: The routing map is static. It doesn't query the server for connected models. This is intentional — routing should be deterministic and not depend on runtime state beyond what's in the code.

### Risks

- **Routing map becomes stale**: Models get added/removed, routing preferences change. Mitigation: routing is in a single const at the top of dispatch.ts — easy to update.
- **`provider`/`model` now optional**: Existing tool callers always provide them, but the type system now allows omitting them. Mitigation: runtime validation catches the case where neither taskType nor provider+model is given.
- **Task type naming**: Models may not match exact task type names. Mitigation: the `describe` field lists ALL valid values. The error message for invalid taskType also lists all values.

### Confidence Score: 9/10

- **Strengths**: Single file changes (well-understood tools), routing map derived from validated cross-command analysis, backward compatible, clear validation commands.
- **Uncertainties**: Whether models will prefer taskType over explicit provider/model (depends on how well the description communicates the feature). Whether 17 task types is too many or too few.
- **Mitigations**: Both approaches work. taskType is optional — the model can use whichever is more convenient. Task types can be added/removed by editing one const.
