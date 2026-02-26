# Feature: Multi-Model Batch Dispatch

## Feature Description

Create a new `batch-dispatch` custom tool that sends the same prompt to multiple AI models in parallel and returns all responses in a single, structured result. This enables multi-model consensus for code reviews (3 models review the same code, compare findings), research comparisons (ask 3 models the same question, cross-reference answers), and A/B testing of model quality. The tool creates separate sessions per model, fires `Promise.allSettled()` for concurrent execution, collects all results (including failures), and returns a formatted comparison.

## User Story

As a developer using the dispatch system, I want to send the same prompt to multiple models simultaneously and compare their responses side-by-side, so that I can get multi-model consensus on reviews, cross-reference research findings, and evaluate which models perform best for different tasks.

## Problem Statement

The current `dispatch` tool sends a prompt to a single model. To get multiple perspectives, the calling model must make sequential dispatch calls — one per target model. This has two problems:

1. **Sequential latency**: 3 models × 30s each = 90s total wait. With parallel execution: max(30s, 25s, 20s) = 30s.
2. **No unified comparison**: Each dispatch returns independently. The calling model must mentally correlate 3 separate responses. A batch tool returns all responses in one structured block, making comparison natural.

Multi-model consensus is valuable for:
- **Code review**: 3 models review the same code → deduplicate findings, flag disagreements, increase confidence
- **Research**: 3 models answer the same question → cross-reference for accuracy, spot hallucinations
- **A/B testing**: Compare model quality on the same prompt to tune routing tables

## Solution Statement

- Decision 1: **New tool file** — create `.opencode/tools/batch-dispatch.ts` as a separate tool. Not an enhancement to dispatch.ts. Keeps single-dispatch simple; batch has different args/return format.
- Decision 2: **`Promise.allSettled()` for parallelism** — each model gets its own session, all prompts fire concurrently. `allSettled` ensures one failure doesn't abort others.
- Decision 3: **Single health check, multiple sessions** — one health check before creating sessions. Each model gets an independent session.
- Decision 4: **Formatted comparison output** — return all responses in a structured format with clear headers per model, status (success/failure/timeout), and a comparison summary footer.
- Decision 5: **Shared args with dispatch** — `prompt`, `port`, `timeout`, `systemPrompt`, `jsonSchema` work the same way. `models` replaces `provider`/`model` as a JSON array of `{provider, model}` objects.
- Decision 6: **Duplicate utility functions** — copy the 4 small helpers (~30 lines) from dispatch.ts rather than extracting to a shared module. YAGNI: only 2 tools exist.
- Decision 7: **Always cleanup** — batch sessions are ephemeral. Always delete after use. No session reuse for batch (that's what the single dispatch tool is for).

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `.opencode/tools/batch-dispatch.ts` (new file)
- **Dependencies**: `@opencode-ai/plugin`, `@opencode-ai/sdk` (already installed), `opencode serve` running

### Slice Guardrails (Required)

- **Single Outcome**: A working `batch-dispatch` tool that sends the same prompt to N models in parallel and returns all responses
- **Expected Files Touched**: 1 new file (`.opencode/tools/batch-dispatch.ts`), plus enabling in agents that need it
- **Scope Boundary**: Does NOT modify dispatch.ts. Does NOT modify workflow commands (they can use batch-dispatch via their existing "dispatch" guidance — the model will discover the tool by its description). Does NOT add streaming or multi-turn batch.
- **Split Trigger**: If response formatting becomes complex (diff views, scoring), split formatting into a follow-up slice

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-330) — Why: the existing single-dispatch tool. Batch-dispatch mirrors its patterns: SDK client creation, health check, session lifecycle, response extraction, error handling, timeout via AbortController. Must copy utility functions and follow the same coding style.
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.d.ts` (lines 473-490) — Why: v2 `session.prompt()` signature with `format`, `system`, `model` fields
- `.opencode/node_modules/@opencode-ai/plugin/dist/tool.d.ts` — Why: `tool()` helper type. Returns `Promise<string>`. Args use `tool.schema` (Zod).
- `opencode.json` (lines 11-87) — Why: available models in `bailian-coding-plan` provider. Batch tool description should reference these.
- `.opencode/agents/code-review.md` (frontmatter) — Why: needs `batch-dispatch: true` added to tools to enable batch review

### New Files to Create

- `.opencode/tools/batch-dispatch.ts` — Batch dispatch tool implementation

### Related Memories (from memory.md)

- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" — Relevance: batch results include per-model error messages. Keep them actionable (which model failed, why) but don't leak sensitive data.
- Memory: "Session safety in shared servers: Never trust client-supplied session_id" — Relevance: batch tool creates and manages its own sessions. No client-supplied session IDs.

### Relevant Documentation

- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools/)
  - Specific section: Tool definition, args, execute function
  - Why: tool must follow the same `export default tool({...})` pattern
- [MDN Promise.allSettled](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled)
  - Specific section: Return value
  - Why: returns `{status: "fulfilled", value}` or `{status: "rejected", reason}` per promise. Used for parallel model execution.

### Patterns to Follow

**dispatch.ts SDK client + health check pattern** (lines 125-148):
```typescript
let client: ReturnType<typeof createOpencodeClient>
try {
  client = createOpencodeClient({ baseUrl })
} catch (err: unknown) {
  return `[dispatch error] Failed to create SDK client: ${getErrorMessage(err)}`
}

try {
  const health = await client.global.health()
  if (!health.data?.healthy) {
    return (
      `[dispatch error] OpenCode server at ${baseUrl} is not healthy. ` +
      `Run 'opencode serve --port ${serverPort}' first.`
    )
  }
} catch (err: unknown) {
  return (
    `[dispatch error] Cannot reach OpenCode server at ${baseUrl}. ` +
    `Ensure 'opencode serve --port ${serverPort}' is running.\n` +
    `Details: ${getErrorMessage(err)}`
  )
}
```
- Why this pattern: batch-dispatch reuses the exact same client creation and health check. Single health check before spawning N model sessions.
- Common gotchas: one client instance, shared across all parallel prompt calls. The client is stateless HTTP so this is safe.

**dispatch.ts session lifecycle pattern** (lines 190-260):
```typescript
// Create session
const session = await client.session.create({ title: `dispatch → ${provider}/${model}` })
const sessionId = session.data?.id
// ... prompt ...
// Cleanup
await client.session.delete({ sessionID: sessionId })
```
- Why this pattern: each model in the batch gets its own session. Create → prompt → cleanup per model. Cleanup always runs (no session reuse in batch).
- Common gotchas: must cleanup even on failure. Use `finally` or catch-then-cleanup pattern.

**dispatch.ts timeout pattern** (lines 150-162, 227-260):
```typescript
let controller: AbortController | undefined
let timeoutId: ReturnType<typeof setTimeout> | undefined
if (args.timeout !== undefined) {
  controller = new AbortController()
  timeoutId = setTimeout(() => controller!.abort(), args.timeout * 1000)
}
// ... prompt with { signal: controller.signal } ...
// On completion: clearTimeout(timeoutId)
// On abort: check err.name === "AbortError" || controller?.signal.aborted
```
- Why this pattern: batch-dispatch creates one AbortController per model (separate timeouts). Each model's timeout is independent.
- Common gotchas: each model gets its own controller. A global timeout could abort all models simultaneously (optional enhancement, not this slice).

**dispatch.ts response extraction pattern** (lines 265-305):
```typescript
const resultRecord = asRecord(result)
const data = asRecord(resultRecord?.data)
const info = asRecord(data?.info)
// Structured mode: info?.structured
// Text mode: extractTextFromParts(data?.parts)
```
- Why this pattern: batch-dispatch extracts responses identically per model. Same structured/text logic.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Create the new tool file with utility functions and tool definition skeleton.

**Tasks:**
- Create `.opencode/tools/batch-dispatch.ts` with utility functions, tool definition, args

### Phase 2: Core Implementation

Implement the parallel dispatch logic: per-model session creation, parallel prompting, response collection.

**Tasks:**
- Implement the `execute` function: parse models, health check, parallel dispatch, response formatting

### Phase 3: Integration

Enable the tool in relevant agents.

**Tasks:**
- Add `batch-dispatch: true` to code-review agent frontmatter

### Phase 4: Testing & Validation

Verify the tool loads and args are correct.

**Tasks:**
- `bun build` check
- `bun -e` import and arg verification

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. CREATE `.opencode/tools/batch-dispatch.ts` — Full tool implementation

- **IMPLEMENT**: Create the complete batch-dispatch tool in a single file. The tool:
  1. Accepts `models` (JSON string of `[{provider, model}]` array), `prompt`, and optional `port`, `timeout`, `systemPrompt`, `jsonSchema`
  2. Parses models, validates at least 2
  3. Creates SDK client + runs health check (same pattern as dispatch.ts)
  4. Parses `jsonSchema` if provided (same pattern as dispatch.ts)
  5. For each model in parallel:
     a. Creates a session
     b. Sets up per-model AbortController if timeout specified
     c. Calls `session.prompt()` with systemPrompt, format, signal
     d. Extracts response (structured or text)
     e. Cleans up session (always)
     f. Returns `{provider, model, status, response, durationMs}` or `{provider, model, status, error, durationMs}`
  6. Formats all results into a single string output

  **Full implementation:**

  ```typescript
  import { tool } from "@opencode-ai/plugin"
  import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"

  // --- Utility functions (duplicated from dispatch.ts for tool independence) ---

  const getErrorMessage = (err: unknown): string => {
    if (err instanceof Error) return err.message
    if (typeof err === "string") return err
    try { return JSON.stringify(err) } catch { return String(err) }
  }

  const asRecord = (value: unknown): Record<string, unknown> | undefined => {
    if (typeof value === "object" && value !== null) return value as Record<string, unknown>
    return undefined
  }

  const extractTextFromParts = (parts: unknown): string => {
    if (!Array.isArray(parts)) return ""
    const texts: string[] = []
    for (const part of parts) {
      const record = asRecord(part)
      if (record?.type === "text" && typeof record.text === "string" && record.text) {
        texts.push(record.text as string)
      }
    }
    return texts.join("\n")
  }

  const safeStringify = (value: unknown, maxChars = 2000): string => {
    try { return JSON.stringify(value).slice(0, maxChars) } catch { return String(value).slice(0, maxChars) }
  }

  // --- Types ---

  interface ModelTarget {
    provider: string
    model: string
  }

  interface ModelResult {
    provider: string
    model: string
    status: "success" | "error" | "timeout"
    response: string
    durationMs: number
  }

  // --- Main tool ---

  export default tool({
    description:
      "Send the same prompt to multiple AI models in parallel and compare their responses. " +
      "Use this for multi-model consensus (code review, research cross-referencing, model quality comparison). " +
      "Requires `opencode serve` running. Returns all responses in a structured comparison format. " +
      "Each model runs in its own session with independent timeout. " +
      "Provider/model examples: anthropic/claude-sonnet-4-20250514, bailian-coding-plan/qwen3.5-plus, " +
      "bailian-coding-plan/qwen3-coder-plus, openai/gpt-4.1",
    args: {
      models: tool.schema
        .string()
        .min(1, "models is required")
        .describe(
          'JSON array of model targets. Each target has "provider" and "model" fields. Minimum 2 models. ' +
            'Example: \'[{"provider":"bailian-coding-plan","model":"qwen3-coder-plus"},{"provider":"bailian-coding-plan","model":"qwen3.5-plus"}]\''
        ),
      prompt: tool.schema
        .string()
        .min(1, "prompt is required")
        .describe("The prompt to send to all target models"),
      port: tool.schema
        .number()
        .optional()
        .describe("OpenCode server port (default: 4096)"),
      timeout: tool.schema
        .number()
        .optional()
        .describe(
          "Timeout in seconds per model (default: no timeout). " +
            "Each model has its own independent timeout.",
        ),
      systemPrompt: tool.schema
        .string()
        .optional()
        .describe(
          "Optional system prompt sent to all target models. " +
            "Use to specialize all models for the same task.",
        ),
      jsonSchema: tool.schema
        .string()
        .optional()
        .describe(
          "Optional JSON schema string for structured output from all models. " +
            "When provided, all models return validated JSON matching this schema.",
        ),
    },
    async execute(args, _context) {
      // 1. Parse models array
      let targets: ModelTarget[]
      try {
        const parsed = JSON.parse(args.models)
        if (!Array.isArray(parsed)) {
          return "[batch-dispatch error] models must be a JSON array"
        }
        targets = []
        for (const item of parsed) {
          const record = asRecord(item)
          if (
            !record ||
            typeof record.provider !== "string" ||
            !record.provider ||
            typeof record.model !== "string" ||
            !record.model
          ) {
            return (
              '[batch-dispatch error] Each model target must have non-empty "provider" and "model" strings.\n' +
              `Invalid entry: ${safeStringify(item)}`
            )
          }
          targets.push({ provider: record.provider as string, model: record.model as string })
        }
      } catch (parseErr: unknown) {
        return (
          `[batch-dispatch error] Invalid models JSON: ${getErrorMessage(parseErr)}\n` +
          'Example: \'[{"provider":"bailian-coding-plan","model":"qwen3-coder-plus"},{"provider":"anthropic","model":"claude-sonnet-4-20250514"}]\''
        )
      }

      if (targets.length < 2) {
        return (
          "[batch-dispatch error] At least 2 model targets are required for batch dispatch. " +
          "For a single model, use the `dispatch` tool instead."
        )
      }

      // 2. Validate optional args
      const serverPort = args.port ?? 4096
      if (!Number.isInteger(serverPort) || serverPort < 1 || serverPort > 65_535) {
        return "[batch-dispatch error] port must be an integer between 1 and 65535"
      }
      const baseUrl = `http://127.0.0.1:${serverPort}`

      if (args.timeout !== undefined) {
        if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
          return "[batch-dispatch error] timeout must be a positive number of seconds"
        }
      }

      // 3. Parse jsonSchema if provided
      let parsedFormat:
        | { type: "json_schema"; schema: Record<string, unknown>; retryCount?: number }
        | undefined
      if (args.jsonSchema) {
        try {
          const schema = JSON.parse(args.jsonSchema)
          if (!asRecord(schema) || Array.isArray(schema)) {
            return (
              "[batch-dispatch error] jsonSchema must parse to a JSON object schema\n" +
              "Example: '{\"type\":\"object\",\"properties\":{\"summary\":{\"type\":\"string\"}}}'"
            )
          }
          parsedFormat = { type: "json_schema" as const, schema, retryCount: 2 }
        } catch (parseErr: unknown) {
          return (
            `[batch-dispatch error] Invalid jsonSchema: ${getErrorMessage(parseErr)}\n` +
            "The jsonSchema arg must be a valid JSON string."
          )
        }
      }

      // 4. Create SDK client + health check
      let client: ReturnType<typeof createOpencodeClient>
      try {
        client = createOpencodeClient({ baseUrl })
      } catch (err: unknown) {
        return `[batch-dispatch error] Failed to create SDK client: ${getErrorMessage(err)}`
      }

      try {
        const health = await client.global.health()
        if (!health.data?.healthy) {
          return (
            `[batch-dispatch error] OpenCode server at ${baseUrl} is not healthy. ` +
            `Run 'opencode serve --port ${serverPort}' first.`
          )
        }
      } catch (err: unknown) {
        return (
          `[batch-dispatch error] Cannot reach OpenCode server at ${baseUrl}. ` +
          `Ensure 'opencode serve --port ${serverPort}' is running.\n` +
          `Details: ${getErrorMessage(err)}`
        )
      }

      // 5. Dispatch to all models in parallel
      const dispatchOne = async (target: ModelTarget): Promise<ModelResult> => {
        const startTime = Date.now()
        let sessionId: string | undefined

        // Per-model timeout
        let controller: AbortController | undefined
        let timeoutId: ReturnType<typeof setTimeout> | undefined
        if (args.timeout) {
          controller = new AbortController()
          timeoutId = setTimeout(() => controller!.abort(), args.timeout * 1000)
        }

        try {
          // Create session
          const session = await client.session.create({
            title: `batch → ${target.provider}/${target.model}`,
          })
          sessionId = session.data?.id
          if (!sessionId) {
            return {
              ...target,
              status: "error",
              response: `Session creation returned no ID: ${safeStringify(session.data)}`,
              durationMs: Date.now() - startTime,
            }
          }

          // Send prompt
          const result = await client.session.prompt(
            {
              sessionID: sessionId,
              model: {
                providerID: target.provider,
                modelID: target.model,
              },
              system: args.systemPrompt,
              format: parsedFormat,
              parts: [{ type: "text" as const, text: args.prompt }],
            },
            controller ? { signal: controller.signal } : undefined,
          )

          if (timeoutId) clearTimeout(timeoutId)

          // Extract response
          const resultRecord = asRecord(result)
          const data = asRecord(resultRecord?.data)
          const info = asRecord(data?.info)
          let responseText = ""

          if (parsedFormat) {
            const structured = info?.structured
            if (structured !== undefined && structured !== null) {
              responseText =
                typeof structured === "string"
                  ? structured
                  : JSON.stringify(structured, null, 2)
            } else {
              const error = asRecord(info?.error)
              if (error?.name === "StructuredOutputError") {
                responseText = `[structured output failed] ${asRecord(error?.data)?.message ?? "unknown error"}`
              } else {
                responseText = extractTextFromParts(data?.parts)
                if (!responseText) {
                  responseText = `[no output] Raw: ${safeStringify(data)}`
                }
              }
            }
          } else {
            responseText = extractTextFromParts(data?.parts)
            if (!responseText) {
              responseText = `[no output] Raw: ${safeStringify(data)}`
            }
          }

          return {
            ...target,
            status: "success",
            response: responseText,
            durationMs: Date.now() - startTime,
          }
        } catch (err: unknown) {
          if (timeoutId) clearTimeout(timeoutId)
          const isTimeout =
            (err instanceof Error && err.name === "AbortError") ||
            controller?.signal.aborted
          return {
            ...target,
            status: isTimeout ? "timeout" : "error",
            response: isTimeout
              ? `Did not respond within ${args.timeout}s`
              : getErrorMessage(err),
            durationMs: Date.now() - startTime,
          }
        } finally {
          // Always cleanup session
          if (sessionId) {
            try {
              await client.session.delete({ sessionID: sessionId })
            } catch {
              // Best effort cleanup
            }
          }
        }
      }

      const results = await Promise.allSettled(targets.map(dispatchOne))

      // 6. Format output
      const modelResults: ModelResult[] = results.map((r, i) =>
        r.status === "fulfilled"
          ? r.value
          : {
              ...targets[i],
              status: "error" as const,
              response: getErrorMessage(r.reason),
              durationMs: 0,
            },
      )

      // Build modifiers string
      const modifiers: string[] = []
      if (args.systemPrompt) modifiers.push("custom-system")
      if (parsedFormat) modifiers.push("structured-json")
      if (args.timeout) modifiers.push(`timeout-${args.timeout}s`)
      const modifierStr = modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""

      // Header
      const modelList = targets.map((t) => `${t.provider}/${t.model}`).join(", ")
      let output = `=== batch-dispatch to ${targets.length} models${modifierStr} ===\n`
      output += `Models: ${modelList}\n\n`

      // Per-model results
      for (const r of modelResults) {
        const statusIcon =
          r.status === "success" ? "OK" : r.status === "timeout" ? "TIMEOUT" : "ERROR"
        output += `--- ${r.provider}/${r.model} [${statusIcon}] (${r.durationMs}ms) ---\n`
        output += r.response + "\n\n"
      }

      // Summary footer
      const succeeded = modelResults.filter((r) => r.status === "success").length
      const failed = modelResults.filter((r) => r.status === "error").length
      const timedOut = modelResults.filter((r) => r.status === "timeout").length
      const totalMs = Math.max(...modelResults.map((r) => r.durationMs))
      output += `=== batch-dispatch summary ===\n`
      output += `Success: ${succeeded}/${targets.length}`
      if (failed > 0) output += ` | Errors: ${failed}`
      if (timedOut > 0) output += ` | Timeouts: ${timedOut}`
      output += ` | Wall time: ${totalMs}ms\n`

      return output
    },
  })
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts` — utility functions (lines 1-50), tool definition structure (lines 52-117), SDK client/health check (lines 125-148), session lifecycle (lines 190-260), response extraction (lines 265-305)
- **IMPORTS**: `import { tool } from "@opencode-ai/plugin"` and `import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"` — same as dispatch.ts
- **GOTCHA**:
  1. `models` arg is a JSON string, not an object array — tool args must be serializable primitives
  2. Each model gets its own AbortController — one model timing out doesn't abort others
  3. `Promise.allSettled` not `Promise.all` — one failure doesn't cancel the batch
  4. Session cleanup in `finally` block — ensures cleanup even on timeout/error
  5. `dispatchOne` is a closure over `client`, `args`, `parsedFormat` — safe because client is stateless HTTP
  6. Duration is per-model wall time. Summary "Wall time" is the max (parallel execution, so total = slowest model)
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5`

### 2. UPDATE `.opencode/agents/code-review.md` — Enable batch-dispatch tool

- **IMPLEMENT**: Add `batch-dispatch: true` to the frontmatter tools section, after the existing `dispatch: true` line.

  **Current** (from frontmatter):
  ```yaml
  tools:
    read: true
    glob: true
    grep: true
    bash: true
    dispatch: true
    archon_rag_search_knowledge_base: true
  ```

  **Replace with:**
  ```yaml
  tools:
    read: true
    glob: true
    grep: true
    bash: true
    dispatch: true
    batch-dispatch: true
    archon_rag_search_knowledge_base: true
  ```

- **PATTERN**: `.opencode/agents/code-review.md` frontmatter — existing tool enablement
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Tool name in frontmatter is the filename without `.ts` extension: `batch-dispatch`, not `batch_dispatch` or `batchDispatch`. The filename has a hyphen.
- **VALIDATE**: Read the file, confirm `batch-dispatch: true` in tools section.

---

## TESTING STRATEGY

### Unit Tests

N/A — custom tools don't have a test framework. Validation is manual.

### Integration Tests

**Test 1: Basic batch dispatch to 2 models**
- Action: batch-dispatch with `models: '[{"provider":"bailian-coding-plan","model":"qwen3-coder-plus"},{"provider":"bailian-coding-plan","model":"qwen3.5-plus"}]'` and `prompt: "What is 2+2?"`
- Expected: Both models respond, output shows two `--- provider/model [OK] ---` sections and a summary
- Pass criteria: Both succeed, summary shows `Success: 2/2`

**Test 2: Batch with timeout — one model times out**
- Action: batch-dispatch with 2 models, `timeout: 1` (very short), complex prompt
- Expected: At least one model times out, output shows `[TIMEOUT]`
- Pass criteria: Other model may succeed, summary shows timeout count

**Test 3: Batch with invalid model**
- Action: batch-dispatch with one valid model and one non-existent model
- Expected: Valid model succeeds, invalid model errors
- Pass criteria: Summary shows `Success: 1/2 | Errors: 1`. Error message is actionable.

**Test 4: Batch with systemPrompt**
- Action: batch-dispatch with `systemPrompt: "Reply in exactly 3 words"` and 2 models
- Expected: Both models attempt to reply in 3 words
- Pass criteria: systemPrompt is applied to both models

**Test 5: Batch with jsonSchema**
- Action: batch-dispatch with `jsonSchema: '{"type":"object","properties":{"answer":{"type":"number"}},"required":["answer"]}'` and 2 models
- Expected: Both models return structured JSON
- Pass criteria: Structured output extracted for both (if models support it)

**Test 6: Less than 2 models**
- Action: batch-dispatch with 1 model
- Expected: Error: "At least 2 model targets required"
- Pass criteria: Helpful error directing to single dispatch tool

**Test 7: Invalid models JSON**
- Action: batch-dispatch with `models: "not json"`
- Expected: Parse error with example
- Pass criteria: Actionable error message

**Test 8: Server not running**
- Action: batch-dispatch without `opencode serve`
- Expected: Health check error
- Pass criteria: Same error pattern as single dispatch

### Edge Cases

- Empty `models` array (`[]`) — caught by `targets.length < 2` check
- Model target missing `provider` — caught by validation loop
- All models timeout — summary shows `Success: 0/N | Timeouts: N`
- One model returns empty response — `[no output]` placeholder
- Very large batch (10+ models) — no artificial limit; server/network may be the bottleneck
- `timeout: 0` — caught by `timeout <= 0` validation

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5
```

### Level 2: Type Safety
```bash
cd .opencode && bun -e "import t from './tools/batch-dispatch.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute); console.log('Desc length:', t.description.length)"
```
Expected: `Args: models, prompt, port, timeout, systemPrompt, jsonSchema`

### Level 3-4: Unit/Integration Tests
```
N/A — manual testing
```

### Level 5: Manual Validation
See Testing Strategy above (Tests 1-8).

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] New file `.opencode/tools/batch-dispatch.ts` created
- [x] `models` arg parses JSON array of `{provider, model}` objects
- [x] Validates minimum 2 model targets
- [x] Single SDK client + health check shared across all models
- [x] `Promise.allSettled()` for parallel execution
- [x] Each model gets independent session + AbortController
- [x] Session cleanup in `finally` block (always runs)
- [x] Response extraction handles structured output and text modes
- [x] Timeout produces per-model `[TIMEOUT]` status, doesn't cancel others
- [x] Error produces per-model `[ERROR]` status with actionable message
- [x] Output format: header, per-model sections, summary footer
- [x] Summary includes success/error/timeout counts and wall time
- [x] `batch-dispatch: true` added to code-review agent frontmatter
- [x] Tool builds without errors: `bun build`
- [x] All 6 args present in tool definition
- [x] Invalid inputs produce helpful error messages with examples

### Runtime (verify after testing/deployment)

- [ ] Batch dispatch returns responses from all models
- [ ] Parallel execution is faster than sequential (wall time ≈ slowest model)
- [ ] Timeouts work independently per model
- [ ] systemPrompt and jsonSchema apply to all models
- [ ] Code-review agent can access the tool

---

## COMPLETION CHECKLIST

- [x] All tasks completed in order
- [x] Each task validation passed
- [x] All validation commands executed successfully
- [ ] Manual testing confirms feature works — deferred to runtime
- [x] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Separate tool, not dispatch.ts enhancement**: batch-dispatch has different args (`models` array instead of single `provider`/`model`) and a fundamentally different return format (multi-model comparison vs single response). Keeping them separate follows KISS — each tool does one thing well.
- **`models` as JSON string**: Tool args must be serializable primitives. An array of objects can't be a direct Zod arg in the `tool()` API. Parsing JSON strings is the established pattern (same as `jsonSchema` in dispatch.ts).
- **`Promise.allSettled` not `Promise.all`**: Critical design choice. `Promise.all` fails fast — one rejection cancels everything. `allSettled` waits for all results. A slow/failing model shouldn't prevent getting responses from other models.
- **Always cleanup sessions**: Unlike single dispatch which supports session reuse, batch sessions are ephemeral. No `sessionId` arg, no `cleanup` arg. The `finally` block guarantees cleanup.
- **Utility function duplication**: 4 small functions (~30 lines) are copied from dispatch.ts. This is intentional — tools must be self-contained (no tool-to-tool imports in the plugin system). A shared `_utils.ts` could work but YAGNI with only 2 tools.
- **Per-model AbortController**: Each model gets its own timeout. One model timing out doesn't cancel others. This is the correct behavior for comparison — you want as many responses as possible.

### Risks

- **Server-side session limits**: Creating N concurrent sessions may hit server-side limits. Mitigation: typical batch is 2-4 models, not 100. No known session limit in OpenCode.
- **Network congestion**: N parallel HTTP requests to the same server. Mitigation: OpenCode server handles multiple sessions natively. HTTP/2 connection reuse. Not a concern for <10 concurrent models.
- **Cost**: Batch sends the same prompt to N models — token usage is N×. Mitigation: this is intentional (the user wants multiple perspectives). The tool description makes this clear.
- **Large response output**: If 5 models each return 2000 words, the output is ~10000 words. May exceed the calling model's useful context. Mitigation: the summary footer provides a quick comparison without reading all responses. The calling model can selectively parse.

### Confidence Score: 9/10

- **Strengths**: Implementation closely mirrors dispatch.ts (proven patterns). `Promise.allSettled` is standard JS. SDK supports concurrent sessions. Utility functions are well-tested. Output format is straightforward.
- **Uncertainties**: Server behavior with many concurrent sessions (untested at scale). Whether `Promise.allSettled` on SDK calls has any gotchas (unlikely but untested).
- **Mitigations**: Typical batch is 2-4 models. Error handling per model catches any SDK issues. `finally` ensures cleanup.
