# Feature: Multi-Model Dispatch Enhanced Args

## Feature Description

Enhance the `dispatch` custom tool with three new capabilities: `timeout` (abort long-running dispatches), `systemPrompt` (override target model's system instructions), and `jsonSchema` (request structured JSON output from the target model). All three map directly to existing OpenCode SDK v2 features — this is wiring, not inventing.

## User Story

As a developer using the dispatch tool, I want to set timeouts on slow models, provide custom system prompts for specialized tasks, and request structured JSON responses for programmatic parsing, so that dispatch is production-ready for all orchestration scenarios.

## Problem Statement

The current dispatch tool has 6 args (provider, model, prompt, sessionId, port, cleanup) but lacks three features that are critical for real-world multi-model orchestration:

1. **No timeout**: If a model takes 5 minutes, the caller is stuck waiting. No way to abort.
2. **No system prompt**: The dispatched model uses its default system instructions. Can't specialize it (e.g., "You are a security reviewer. Only report vulnerabilities.").
3. **No structured output**: Responses come back as free-form text. Can't request JSON conforming to a schema for programmatic parsing.

All three features are already supported by the OpenCode SDK v2 — we just need to expose them as tool args.

## Solution Statement

- Decision 1: **`timeout` via AbortController** — create an `AbortController`, set `setTimeout` to trigger `abort()`, pass `signal` to the SDK's `options` parameter. Clean, standard approach.
- Decision 2: **`systemPrompt` via SDK `system` field** — the v2 `session.prompt()` already accepts `system?: string`. Pass it through directly.
- Decision 3: **`jsonSchema` via SDK `format` field** — the v2 `session.prompt()` already accepts `format?: OutputFormat`. When `jsonSchema` arg is provided, set `format: { type: "json_schema", schema: JSON.parse(jsonSchema) }`. Return `result.data.info.structured` instead of text parts.
- Decision 4: **Backward compatible** — all three args are optional. Existing dispatch calls work exactly as before.
- Decision 5: **Single file change** — only `.opencode/tools/dispatch.ts` is modified.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Low
- **Primary Systems Affected**: `.opencode/tools/dispatch.ts`
- **Dependencies**: None new — uses existing SDK v2 features

### Slice Guardrails (Required)

- **Single Outcome**: dispatch tool supports timeout, systemPrompt, and jsonSchema args
- **Expected Files Touched**: 1 file (`.opencode/tools/dispatch.ts`)
- **Scope Boundary**: Does NOT modify workflow commands (Slice 2 already done). Does NOT add new tools. Does NOT change session lifecycle.
- **Split Trigger**: If structured output parsing grows complex (custom validators, retry logic), split into a separate utility

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-152) — Why: the file being modified. Must understand current structure: args definition (lines 12-42), execute function (lines 44-151), SDK import (line 2), response extraction (lines 118-132)
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.d.ts` (lines 473-490) — Why: v2 `session.prompt()` parameter types showing `format?: OutputFormat`, `system?: string`
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/types.gen.d.ts` (lines 80-91) — Why: `OutputFormat`, `OutputFormatJsonSchema`, `JsonSchema` type definitions
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/types.gen.d.ts` (lines 178-211) — Why: `AssistantMessage` type with `structured?: unknown` field (line 208)
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/client/types.gen.d.ts` (lines 6, 47-63) — Why: `Config` extends `RequestInit` (includes `signal?: AbortSignal`); `RequestOptions` accepts config overrides

### New Files to Create

- None — single file modification

### Related Memories (from memory.md)

- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" — Relevance: timeout errors need clear messages ("Model took longer than Xs, consider increasing timeout")
- Memory: "Session safety in shared servers: Never trust client-supplied session_id" — Relevance: jsonSchema is client-supplied but goes to the SDK, not our server — SDK validates it

### Relevant Documentation

- [OpenCode SDK — Structured Output](https://opencode.ai/docs/sdk/#structured-output)
  - Specific section: Basic Usage, JSON Schema Format, Error Handling
  - Why: exact API for `format: { type: "json_schema", schema: {...}, retryCount?: number }` and response access via `result.data.info.structured`
- [OpenCode Server — Messages](https://opencode.ai/docs/server/#messages)
  - Specific section: POST /session/:id/message body
  - Why: confirms `system`, `format` fields in message body

### Patterns to Follow

**Current dispatch.ts args pattern** (lines 12-42):
```typescript
args: {
  provider: tool.schema
    .string()
    .describe("Provider ID (e.g. 'anthropic', ...)"),
  model: tool.schema
    .string()
    .describe("Model ID within the provider (e.g. 'claude-sonnet-4-20250514', ...)"),
  // ... more args with .optional() for non-required
  cleanup: tool.schema
    .boolean()
    .optional()
    .describe("Delete the session after dispatch (default: true for new sessions, false for reused sessions)"),
},
```
- Why this pattern: all new args follow the same `tool.schema.{type}().optional().describe()` pattern
- Common gotchas: `tool.schema` is Zod. Use `.describe()` for LLM hints. Optional args use `.optional()`.

**Current prompt call** (lines 93-101):
```typescript
result = await client.session.prompt({
  sessionID: sessionId,
  model: {
    providerID: args.provider,
    modelID: args.model,
  },
  parts: [{ type: "text" as const, text: args.prompt }],
})
```
- Why this pattern: new fields (`system`, `format`) are added to this same object
- Common gotchas: v2 SDK uses flat params, not `{ body, path }`. `format` and `system` are top-level fields.

**SDK v2 session.prompt signature** (from sdk.gen.d.ts:473-490):
```typescript
prompt<ThrowOnError extends boolean = false>(parameters: {
    sessionID: string;
    directory?: string;
    messageID?: string;
    model?: { providerID: string; modelID: string; };
    agent?: string;
    noReply?: boolean;
    tools?: { [key: string]: boolean; };
    format?: OutputFormat;   // <-- structured output
    system?: string;          // <-- system prompt
    variant?: string;
    parts?: Array<TextPartInput | FilePartInput | AgentPartInput | SubtaskPartInput>;
}, options?: Options<never, ThrowOnError>)
```
- Why this pattern: shows exactly where `format` and `system` go in the prompt call
- Common gotchas: `format` accepts `OutputFormat` which is `{ type: "text" } | { type: "json_schema", schema: JsonSchema, retryCount?: number }`. Must construct the right shape.

**SDK v2 Options with signal** (from client/types.gen.d.ts:6,47):
```typescript
// Config extends RequestInit (which has signal?: AbortSignal)
interface Config extends Omit<RequestInit, "body" | "headers" | "method">, CoreConfig { ... }

// Options passed as second arg to SDK methods
type Options = RequestOptions & { client?: Client; meta?: Record<string, unknown>; }
```
- Why this pattern: the second parameter of `client.session.prompt(params, options)` accepts `signal` from `RequestInit`
- Common gotchas: `signal` goes in the `options` (2nd arg), NOT in `parameters` (1st arg). Must pass `{ signal: controller.signal }` as the second argument.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Add three new args to the tool definition.

**Tasks:**
- Add `timeout` arg (number, optional, in seconds)
- Add `systemPrompt` arg (string, optional)
- Add `jsonSchema` arg (string, optional — JSON string of the schema)

### Phase 2: Core Implementation

Wire each arg into the execute function.

**Tasks:**
- Implement timeout via AbortController + setTimeout
- Pass systemPrompt through to SDK `system` field
- Parse jsonSchema and pass as `format` field
- Handle structured output extraction when jsonSchema is used
- Update response header to indicate structured output mode

### Phase 3: Error Handling

Add specific error handling for each new feature.

**Tasks:**
- Handle timeout abort with clear message
- Handle invalid jsonSchema (JSON parse failure)
- Handle StructuredOutputError from SDK

### Phase 4: Testing & Validation

Manual testing of each new arg.

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. UPDATE `.opencode/tools/dispatch.ts` — Add three new args

- **IMPLEMENT**: Add `timeout`, `systemPrompt`, and `jsonSchema` to the args object. Insert after the existing `cleanup` arg (line 38-42).

  **Insert after the `cleanup` arg:**
  ```typescript
  timeout: tool.schema
    .number()
    .optional()
    .describe(
      "Timeout in seconds for the dispatch call (default: no timeout). " +
        "If the target model doesn't respond within this time, the dispatch aborts.",
    ),
  systemPrompt: tool.schema
    .string()
    .optional()
    .describe(
      "Optional system prompt to override the target model's default instructions. " +
        "Use this to specialize the model (e.g., 'You are a security reviewer. Only report vulnerabilities.').",
    ),
  jsonSchema: tool.schema
    .string()
    .optional()
    .describe(
      "Optional JSON schema string for structured output. When provided, the target model " +
        "returns validated JSON matching this schema instead of free-form text. " +
        'Example: \'{"type":"object","properties":{"summary":{"type":"string"},"score":{"type":"number"}},"required":["summary"]}\'',
    ),
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:12-42` — existing args pattern with `tool.schema.{type}().optional().describe()`
- **IMPORTS**: No new imports needed
- **GOTCHA**: `jsonSchema` is a string (not an object) because tool args must be serializable primitives. We parse it inside `execute`. The `.describe()` must include an example so the LLM knows the format.
- **VALIDATE**: `bun -e "import t from './tools/dispatch.ts'; console.log(Object.keys(t.args))"` — should show all 9 args

### 2. UPDATE `.opencode/tools/dispatch.ts` — Implement timeout via AbortController

- **IMPLEMENT**: In the `execute` function, after the health check (around line 70) and before the session creation (line 73), set up the AbortController if `timeout` is provided. Then pass the signal to the prompt call's `options` (2nd argument).

  **Add after the health check block (after the `catch` for health check):**
  ```typescript
  // 2.5. Set up timeout if requested
  let controller: AbortController | undefined
  let timeoutId: ReturnType<typeof setTimeout> | undefined
  if (args.timeout) {
    controller = new AbortController()
    timeoutId = setTimeout(() => controller!.abort(), args.timeout * 1000)
  }
  ```

  **Modify the prompt call to pass the signal as the 2nd arg:**

  Change from:
  ```typescript
  result = await client.session.prompt({
    sessionID: sessionId,
    model: { ... },
    parts: [{ type: "text" as const, text: args.prompt }],
  })
  ```

  Change to:
  ```typescript
  result = await client.session.prompt(
    {
      sessionID: sessionId,
      model: {
        providerID: args.provider,
        modelID: args.model,
      },
      system: args.systemPrompt,
      format: parsedFormat,
      parts: [{ type: "text" as const, text: args.prompt }],
    },
    controller ? { signal: controller.signal } : undefined,
  )
  ```

  **Add cleanup for the timeout after the prompt call succeeds (before response extraction):**
  ```typescript
  // Clear timeout if prompt completed
  if (timeoutId) clearTimeout(timeoutId)
  ```

  **Add timeout-specific error handling in the prompt's catch block:**
  ```typescript
  } catch (err: any) {
    if (timeoutId) clearTimeout(timeoutId)
    // Check if this was a timeout abort
    if (err.name === "AbortError" || controller?.signal.aborted) {
      // Cleanup session on timeout
      if (!isReusedSession && sessionId) {
        try { await client.session.delete({ sessionID: sessionId }) } catch {}
      }
      return (
        `[dispatch error] Timeout: ${args.provider}/${args.model} did not respond within ${args.timeout}s.\n` +
        `Consider increasing the timeout or using a faster model.`
      )
    }
    // ... existing error handling
  ```

- **PATTERN**: Standard `AbortController` + `setTimeout` pattern. Signal passed via SDK's second `options` parameter.
- **IMPORTS**: No new imports — `AbortController` and `setTimeout` are globals in Bun
- **GOTCHA**: 
  1. `clearTimeout` MUST run after prompt completes (success or failure) to prevent memory leak
  2. The abort signal goes in the `options` (2nd arg of `prompt()`), not in `parameters` (1st arg)
  3. `err.name === "AbortError"` is the standard check — also check `controller?.signal.aborted` as fallback
  4. `args.timeout` is in seconds (user-friendly) but `setTimeout` takes milliseconds — multiply by 1000
- **VALIDATE**: `bun -e "import t from './tools/dispatch.ts'; console.log('OK')"` — should load without errors

### 3. UPDATE `.opencode/tools/dispatch.ts` — Implement systemPrompt and jsonSchema

- **IMPLEMENT**: Before the prompt call, parse `jsonSchema` if provided and construct the `format` object. Then pass both `system` and `format` to the prompt call (already wired in Task 2).

  **Add before the prompt call (after timeout setup, before `result = await client.session.prompt(...)`):**
  ```typescript
  // 2.6. Parse structured output format if requested
  let parsedFormat: { type: "json_schema"; schema: Record<string, unknown>; retryCount?: number } | undefined
  if (args.jsonSchema) {
    try {
      const schema = JSON.parse(args.jsonSchema)
      parsedFormat = { type: "json_schema" as const, schema, retryCount: 2 }
    } catch (parseErr: any) {
      if (timeoutId) clearTimeout(timeoutId)
      return (
        `[dispatch error] Invalid jsonSchema: ${parseErr.message}\n` +
        `The jsonSchema arg must be a valid JSON string. Example:\n` +
        `'{"type":"object","properties":{"summary":{"type":"string"}}}'`
      )
    }
  }
  ```

  Note: `system: args.systemPrompt` and `format: parsedFormat` are already in the prompt call from Task 2. If `systemPrompt` is `undefined`, the SDK ignores it. If `parsedFormat` is `undefined`, no format override happens.

- **PATTERN**: `JSON.parse` with try/catch for validation. SDK `OutputFormat` type: `{ type: "json_schema", schema: JsonSchema, retryCount?: number }`.
- **IMPORTS**: No new imports
- **GOTCHA**: 
  1. `retryCount: 2` gives the model 2 retries to produce valid JSON. Default in SDK is also 2.
  2. `JSON.parse` will throw on invalid JSON — catch it and return a helpful error with example
  3. The schema object goes directly to the SDK — no additional validation needed (the model validates against it)
  4. `system: undefined` is fine — SDK skips undefined fields
- **VALIDATE**: `bun -e "import t from './tools/dispatch.ts'; console.log('OK')"` — should load without errors

### 4. UPDATE `.opencode/tools/dispatch.ts` — Handle structured output in response extraction

- **IMPLEMENT**: Modify the response extraction block (currently lines 118-132) to check for structured output when `jsonSchema` was provided. Structured output lives in `result.data.info.structured`, not in `result.data.parts`.

  **Replace the current response extraction block with:**
  ```typescript
  // 5. Extract response
  let responseText = ""
  try {
    if (parsedFormat) {
      // Structured output mode — extract from info.structured
      const structured = (result.data as any)?.info?.structured
      if (structured !== undefined && structured !== null) {
        responseText = typeof structured === "string"
          ? structured
          : JSON.stringify(structured, null, 2)
      } else {
        // Check for StructuredOutputError
        const error = (result.data as any)?.info?.error
        if (error?.name === "StructuredOutputError") {
          responseText = `[dispatch error] Structured output failed after ${error.data?.retries ?? "unknown"} retries: ${error.data?.message ?? "unknown error"}`
        } else {
          // Fallback to text parts even in structured mode
          const parts = result.data?.parts ?? []
          const textParts = parts.filter((p: any) => p.type === "text" && p.text)
          responseText = textParts.map((p: any) => p.text).join("\n")
          if (!responseText) {
            responseText = `[dispatch warning] No structured output or text parts. Raw: ${JSON.stringify(result.data).slice(0, 2000)}`
          }
        }
      }
    } else {
      // Text mode — existing extraction logic
      const parts = result.data?.parts ?? []
      const textParts = parts.filter((p: any) => p.type === "text" && p.text)
      responseText = textParts.map((p: any) => p.text).join("\n")
      if (!responseText) {
        responseText = `[dispatch warning] No text parts in response. Raw: ${JSON.stringify(result.data).slice(0, 2000)}`
      }
    }
  } catch (err: any) {
    responseText = `[dispatch warning] Could not parse response: ${err.message}. Raw: ${JSON.stringify(result).slice(0, 2000)}`
  }
  ```

- **PATTERN**: SDK returns structured output in `AssistantMessage.structured` (type `unknown`). Check for `StructuredOutputError` in `AssistantMessage.error`.
- **IMPORTS**: No new imports
- **GOTCHA**: 
  1. `structured` can be any JSON value (object, array, string, number). Stringify objects, pass strings through.
  2. `StructuredOutputError` has `{ name: "StructuredOutputError", data: { message, retries } }` — check `info.error.name`
  3. Fallback to text parts even in structured mode — some models may not support structured output
  4. `(result.data as any)` needed because `info` type varies between response modes
- **VALIDATE**: `bun -e "import t from './tools/dispatch.ts'; console.log('OK')"` — should load without errors

### 5. UPDATE `.opencode/tools/dispatch.ts` — Update response header for mode indication

- **IMPLEMENT**: Modify the response header (currently line 149) to indicate when structured output or system prompt was used.

  **Replace:**
  ```typescript
  const header = `--- dispatch response from ${args.provider}/${args.model} ---\n`
  ```

  **With:**
  ```typescript
  const modifiers: string[] = []
  if (args.systemPrompt) modifiers.push("custom-system")
  if (parsedFormat) modifiers.push("structured-json")
  if (args.timeout) modifiers.push(`timeout-${args.timeout}s`)
  const modifierStr = modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""
  const header = `--- dispatch response from ${args.provider}/${args.model}${modifierStr} ---\n`
  ```

  This produces headers like:
  - `--- dispatch response from anthropic/claude-sonnet-4-20250514 ---` (no modifiers)
  - `--- dispatch response from anthropic/claude-sonnet-4-20250514 [custom-system, structured-json] ---`
  - `--- dispatch response from bailian-coding-plan/qwen3.5-plus [timeout-30s] ---`

- **PATTERN**: Existing header format with optional modifier tags
- **IMPORTS**: No new imports
- **GOTCHA**: Keep the `---` prefix/suffix for easy parsing by the calling model. Modifiers are informational only.
- **VALIDATE**: `bun -e "import t from './tools/dispatch.ts'; console.log('OK')"` — should load without errors

### 6. UPDATE `.opencode/tools/dispatch.ts` — Update tool description

- **IMPLEMENT**: Update the tool description (lines 5-11) to mention the new capabilities.

  **Replace current description:**
  ```typescript
  description:
    "Dispatch a prompt to any connected AI model via the OpenCode server. " +
    "Use this to delegate tasks (code generation, review, research, analysis) to other models " +
    "and receive their response inline. Requires `opencode serve` running. " +
    "Provider/model examples: anthropic/claude-sonnet-4-20250514, openai/gpt-4.1, " +
    "bailian-coding-plan/qwen3.5-plus, bailian-coding-plan/qwen3-coder-plus, " +
    "google/gemini-2.5-pro, github-copilot/gpt-4.1",
  ```

  **With:**
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

- **PATTERN**: Existing description with added capability summary
- **IMPORTS**: N/A
- **GOTCHA**: Keep description under 500 chars for token efficiency. Just mention the capabilities, don't explain them (the arg descriptions handle that).
- **VALIDATE**: `bun -e "import t from './tools/dispatch.ts'; console.log('desc length:', t.description.length)"` — should be under 500

---

## TESTING STRATEGY

### Unit Tests

N/A — custom tools don't have a test framework. Validation is manual.

### Integration Tests

**Test 1: Timeout — model responds in time**
- Action: Dispatch with `timeout: 60` to a fast model with a simple prompt
- Expected: Response returns normally, header shows `[timeout-60s]`
- Pass criteria: No timeout error, response received

**Test 2: Timeout — model exceeds timeout**
- Action: Dispatch with `timeout: 1` (1 second) to any model with a complex prompt
- Expected: Abort error: "did not respond within 1s"
- Pass criteria: Clean error message, session cleaned up

**Test 3: System prompt**
- Action: Dispatch with `systemPrompt: "You are a pirate. Reply in pirate speak."` and `prompt: "What is 2+2?"`
- Expected: Response in pirate-themed language
- Pass criteria: Response reflects custom system prompt

**Test 4: Structured JSON output**
- Action: Dispatch with `jsonSchema: '{"type":"object","properties":{"answer":{"type":"number"}},"required":["answer"]}'` and `prompt: "What is 2+2?"`
- Expected: Response is JSON like `{ "answer": 4 }`
- Pass criteria: Valid JSON matching schema

**Test 5: Invalid jsonSchema**
- Action: Dispatch with `jsonSchema: "not valid json"`
- Expected: Error: "Invalid jsonSchema: ..."
- Pass criteria: Helpful error with example

**Test 6: All three combined**
- Action: Dispatch with `timeout: 30`, `systemPrompt: "Return only JSON"`, and `jsonSchema: '{"type":"object","properties":{"result":{"type":"string"}}}'`
- Expected: Structured JSON response with all modifiers in header
- Pass criteria: `[custom-system, structured-json, timeout-30s]` in header

**Test 7: Backward compatibility**
- Action: Dispatch with only original args (provider, model, prompt) — no new args
- Expected: Works exactly as before
- Pass criteria: No regressions

### Edge Cases

- `timeout: 0` — should be treated as no timeout (falsy)
- `jsonSchema` with deeply nested schema — SDK handles validation
- Model doesn't support structured output — may return text anyway, fallback extraction handles it
- `systemPrompt` is empty string — SDK may treat as no system prompt
- Timeout fires during session creation (before prompt) — timeout only wraps the prompt call, not session creation

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5
```

### Level 2: Type Safety
```bash
cd .opencode && bun -e "import t from './tools/dispatch.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"
```
Expected: `Args: provider, model, prompt, sessionId, port, cleanup, timeout, systemPrompt, jsonSchema`

### Level 3-4: Unit/Integration Tests
```
N/A — manual testing
```

### Level 5: Manual Validation
See Testing Strategy above (Tests 1-7).

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `timeout` arg added (number, optional, with descriptive help text)
- [ ] `systemPrompt` arg added (string, optional, with descriptive help text)
- [ ] `jsonSchema` arg added (string, optional, with example in help text)
- [ ] AbortController created when timeout is provided
- [ ] Signal passed to SDK prompt call's options (2nd arg)
- [ ] clearTimeout called on success and failure
- [ ] Timeout abort produces clear error message with model name and timeout value
- [ ] systemPrompt passed through to SDK `system` field
- [ ] jsonSchema parsed with JSON.parse, invalid JSON caught with helpful error
- [ ] Structured output extracted from `result.data.info.structured`
- [ ] StructuredOutputError detected and surfaced
- [ ] Text parts fallback when structured output is empty
- [ ] Response header includes modifier tags when new args used
- [ ] Tool description updated to mention new capabilities
- [ ] Tool loads without errors: `bun -e "import t from './tools/dispatch.ts'"`
- [ ] All 9 args present in tool definition
- [ ] Backward compatible — existing dispatch calls work unchanged

### Runtime (verify after testing/deployment)

- [ ] Timeout aborts as expected
- [ ] System prompt affects model behavior
- [ ] Structured JSON output is returned and parseable
- [ ] All three features work together
- [ ] No regressions in basic dispatch functionality

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **jsonSchema as string, not object**: Tool args must be JSON-serializable primitives for LLM tool calling. A JSON schema object can't be passed directly as a tool arg — it must be a string that we `JSON.parse` internally.
- **Timeout wraps prompt only**: The AbortController signal is passed only to the `session.prompt()` call, not to `session.create()` or `session.delete()`. Session creation is fast; prompt execution is where the wait happens.
- **retryCount: 2 hardcoded**: The SDK defaults to 2 retries for structured output validation. We match that default. Could be exposed as an arg in a future slice if needed.
- **Modifier tags in header**: `[custom-system, structured-json, timeout-30s]` in the response header helps the calling model understand what configuration was used for this dispatch.

### Risks

- **AbortController + SDK compatibility**: The SDK uses `@hey-api/openapi-ts` generated client which extends `RequestInit`. Signal should propagate to the underlying fetch. If not, timeout won't work — but no crash, just no timeout.
- **Structured output model support**: Not all models support structured output. Some may ignore the schema and return free-form text. The fallback to text parts extraction handles this gracefully.
- **System prompt interference**: Custom system prompts may conflict with OpenCode's own system instructions for the session. Since dispatch creates ephemeral sessions, this should be minimal.

### Confidence Score: 9/10

- **Strengths**: All three features map directly to existing SDK v2 fields. Types verified from actual `d.ts` files. Implementation is straightforward wiring. Single file change, backward compatible.
- **Uncertainties**: AbortController signal propagation through the SDK's fetch layer (untested at runtime). Structured output availability varies by model.
- **Mitigations**: Timeout has clean error handling if abort doesn't propagate. Structured output falls back to text extraction.
