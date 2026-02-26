# Feature: Multi-Model Dispatch Live Testing & Error Hardening

## Feature Description

Run `opencode serve` and exercise every dispatch path against real models. Identify error shapes the SDK actually returns, harden error messages based on real failures, fix any runtime bugs discovered, and add a pre-flight provider validation step that catches "model not connected" before wasting a session.

## User Story

As a model using the dispatch tool, I want clear, actionable error messages when something goes wrong (model not connected, provider auth missing, rate limited, empty response), so that I can self-correct without human intervention.

## Problem Statement

Six slices of dispatch tooling have been built without a single live test. The error handling was written speculatively — we guessed what SDK errors look like. Real failures may have different shapes (HTTP status codes, nested error objects, rate limit headers). Additionally:

1. **No provider pre-flight**: The tool creates a session, sends a prompt, and only then discovers the model isn't connected. This wastes a session and produces a confusing error.
2. **Error messages are generic**: "Prompt failed for X" doesn't tell the calling model what to do next — retry? try a different model? check auth?
3. **No rate limit handling**: Provider APIs rate-limit. The tool has no retry or backoff, and the error message doesn't distinguish rate limits from auth failures.
4. **Response extraction untested**: The `extractTextFromParts` and structured output paths have never been validated against real SDK response shapes.
5. **batch-dispatch parallelism untested**: `Promise.allSettled` with real concurrent requests may surface race conditions or session ID conflicts.

## Solution Statement

- Decision 1: **Add provider pre-flight check** — use `client.config.providers()` to verify the target provider+model is connected before creating a session. Return actionable error if not.
- Decision 2: **Classify errors by type** — parse SDK error responses into categories: `auth_missing`, `model_not_found`, `rate_limited`, `timeout`, `server_error`, `unknown`. Each category gets a specific remediation hint.
- Decision 3: **Add retry with backoff for rate limits** — single retry after 2s delay for HTTP 429. No infinite retry. If second attempt fails, return the rate limit error with "try again later" message.
- Decision 4: **Add response size guard** — if the response text exceeds 50,000 chars, truncate with a note. Prevents the tool from returning massive responses that blow up the calling model's context.
- Decision 5: **Add duration tracking** — measure and report prompt duration in the response header (e.g., `[1.2s]`). Helps the calling model decide if a model is too slow.
- Decision 6: **Live test script** — create a Bun test script that exercises all major paths against the real server. Not a unit test framework — just a sequential runner that reports PASS/FAIL.

## Feature Metadata

- **Feature Type**: Enhancement + Bug Fix (based on live testing results)
- **Estimated Complexity**: Medium-High (live testing may surface unknown issues)
- **Primary Systems Affected**: `.opencode/tools/dispatch.ts`, `.opencode/tools/batch-dispatch.ts`
- **Dependencies**: `opencode serve` running on port 4096, at least one connected provider

### Slice Guardrails (Required)

- **Single Outcome**: Both dispatch tools handle real-world errors gracefully with actionable messages
- **Expected Files Touched**: 2-3 files (`dispatch.ts`, `batch-dispatch.ts`, optional test script)
- **Scope Boundary**: Does NOT add streaming support. Does NOT change the TASK_ROUTING map. Does NOT modify command markdown files. Does NOT add persistent logging.
- **Split Trigger**: If live testing reveals >5 distinct bugs, fix the top 3 and defer rest to Slice 8

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-400) — Why: primary file being hardened. Must understand all error paths (lines 196-328), response extraction (lines 334-374), header formatting (lines 389-398)
- `.opencode/tools/batch-dispatch.ts` (lines 1-456) — Why: secondary file being hardened. Same error patterns but in `dispatchOne` (lines 291-398) and `Promise.allSettled` wrapper (lines 400-412)
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.d.ts` — Why: SDK type definitions. `Session2.prompt` (line 473-490) shows the exact params. `Config2.providers` (line 213-215) is the provider pre-flight API.
- `opencode.json` (lines 11-87) — Why: provider config with all model IDs. Must match routing table entries.

### New Files to Create

- `.opencode/tools/_test-dispatch.ts` — Live test script (Bun, not a tool — just `bun run .opencode/tools/_test-dispatch.ts`)

### Related Memories (from memory.md)

- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" — Relevance: error messages must help the calling model self-correct without leaking secrets
- Memory: "Session safety in shared servers: Never trust client-supplied session_id" — Relevance: reused session IDs should be validated before use
- Memory: "Legacy SDK compatibility: When provider SDKs differ on auth args, use temporary env bridging" — Relevance: different providers may return different error shapes

### Relevant Documentation

- [OpenCode Server API](https://opencode.ai/docs/api/) — Why: understand health, session, prompt endpoints
- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools/) — Why: tool return value constraints (string only)

### Patterns to Follow

**dispatch.ts existing error return pattern** (from `.opencode/tools/dispatch.ts:296-328`):
```typescript
} catch (err: unknown) {
  if (timeoutId) clearTimeout(timeoutId)
  if (
    (err instanceof Error && err.name === "AbortError") ||
    controller?.signal.aborted
  ) {
    // Cleanup + return timeout error
  }
  // Cleanup + return generic error
  return (
    `[dispatch error] Prompt failed for ${resolvedProvider}/${resolvedModel}: ${getErrorMessage(err)}\n` +
    `Common causes: model not connected (run '/connect ${resolvedProvider}'), ` +
    `invalid model ID, or provider auth missing.`
  )
}
```
- Why this pattern: we're replacing the generic catch with classified error handling
- Common gotchas: SDK errors may be plain objects, not Error instances. Must handle both.

**SDK provider list API** (from `sdk.gen.d.ts:213-215`):
```typescript
providers<ThrowOnError extends boolean = false>(parameters?: {
    directory?: string;
}): RequestResult<ConfigProvidersResponses, unknown, ThrowOnError, "fields">;
```
- Why this pattern: pre-flight check uses `client.config.providers()` to get connected models
- Common gotchas: response shape unknown — need to inspect during live testing

---

## IMPLEMENTATION PLAN

### Phase 1: Live Testing Infrastructure

Start `opencode serve`, write test script, exercise happy path, capture real response shapes.

**Tasks:**
- Create test script that runs dispatch against a known-good model
- Capture and document the exact response shape from `session.prompt()`
- Capture and document the exact response shape from `config.providers()`
- Test error paths: wrong model ID, wrong provider, missing auth

### Phase 2: Provider Pre-flight

Add `config.providers()` check before session creation.

**Tasks:**
- Add provider validation to dispatch.ts
- Add provider validation to batch-dispatch.ts

### Phase 3: Error Classification

Replace generic error catches with classified error handling.

**Tasks:**
- Create `classifyError()` helper function
- Update dispatch.ts catch blocks with classified errors
- Update batch-dispatch.ts catch blocks with classified errors

### Phase 4: Response Hardening

Add duration tracking, response truncation, and retry for rate limits.

**Tasks:**
- Add duration measurement to dispatch.ts
- Add response size guard to both tools
- Add single retry with backoff for rate limit errors

### Phase 5: Final Live Validation

Re-run all test scenarios with hardened tools, verify error messages are actionable.

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. PREREQUISITE — Start opencode serve and verify connectivity

- **IMPLEMENT**: 
  The user must start `opencode serve` in a separate terminal before execution begins.
  Verify with: `curl -s http://127.0.0.1:4096/health`
  
  If not running, stop execution and ask the user to start it.

- **VALIDATE**: `curl -s http://127.0.0.1:4096/health | head -1`

### 2. CREATE `.opencode/tools/_test-dispatch.ts` — Live test runner

- **IMPLEMENT**: Create a Bun script (not a tool — no `export default tool()`) that exercises dispatch paths. The script imports the SDK directly and tests:

  ```typescript
  import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"

  const client = createOpencodeClient({ baseUrl: "http://127.0.0.1:4096" })

  async function test(name: string, fn: () => Promise<void>) {
    try {
      await fn()
      console.log(`PASS: ${name}`)
    } catch (err) {
      console.log(`FAIL: ${name}`)
      console.log(`  Error: ${err instanceof Error ? err.message : JSON.stringify(err)}`)
      // Log the full error shape for inspection
      console.log(`  Full error: ${JSON.stringify(err, null, 2)}`)
    }
  }

  // Test 1: Health check
  await test("health check", async () => {
    const health = await client.global.health()
    if (!health.data?.healthy) throw new Error("not healthy")
  })

  // Test 2: List providers (for pre-flight design)
  await test("list providers", async () => {
    const providers = await client.config.providers()
    console.log("  Provider response shape:", JSON.stringify(providers.data, null, 2).slice(0, 2000))
  })

  // Test 3: Create session + prompt with known-good model
  await test("prompt qwen3-coder-next", async () => {
    const session = await client.session.create({ title: "test-dispatch" })
    const sessionId = session.data?.id
    if (!sessionId) throw new Error("no session ID")
    try {
      const result = await client.session.prompt({
        sessionID: sessionId,
        model: { providerID: "bailian-coding-plan", modelID: "qwen3-coder-next" },
        parts: [{ type: "text" as const, text: "Reply with exactly: DISPATCH_TEST_OK" }],
      })
      console.log("  Response shape:", JSON.stringify(result.data, null, 2).slice(0, 3000))
    } finally {
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
    }
  })

  // Test 4: Error shape — wrong model ID
  await test("wrong model ID (expect error)", async () => {
    const session = await client.session.create({ title: "test-bad-model" })
    const sessionId = session.data?.id
    if (!sessionId) throw new Error("no session ID")
    try {
      await client.session.prompt({
        sessionID: sessionId,
        model: { providerID: "bailian-coding-plan", modelID: "nonexistent-model-xyz" },
        parts: [{ type: "text" as const, text: "test" }],
      })
      throw new Error("Expected error but got success")
    } catch (err) {
      if (err instanceof Error && err.message === "Expected error but got success") throw err
      console.log("  Error shape (wrong model):", JSON.stringify(err, null, 2).slice(0, 2000))
    } finally {
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
    }
  })

  // Test 5: Error shape — wrong provider
  await test("wrong provider (expect error)", async () => {
    const session = await client.session.create({ title: "test-bad-provider" })
    const sessionId = session.data?.id
    if (!sessionId) throw new Error("no session ID")
    try {
      await client.session.prompt({
        sessionID: sessionId,
        model: { providerID: "nonexistent-provider", modelID: "gpt-4" },
        parts: [{ type: "text" as const, text: "test" }],
      })
      throw new Error("Expected error but got success")
    } catch (err) {
      if (err instanceof Error && err.message === "Expected error but got success") throw err
      console.log("  Error shape (wrong provider):", JSON.stringify(err, null, 2).slice(0, 2000))
    } finally {
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
    }
  })

  // Test 6: Structured output
  await test("structured output", async () => {
    const session = await client.session.create({ title: "test-structured" })
    const sessionId = session.data?.id
    if (!sessionId) throw new Error("no session ID")
    try {
      const result = await client.session.prompt({
        sessionID: sessionId,
        model: { providerID: "bailian-coding-plan", modelID: "qwen3-coder-next" },
        format: {
          type: "json_schema",
          schema: { type: "object", properties: { answer: { type: "string" } }, required: ["answer"] },
        },
        parts: [{ type: "text" as const, text: 'Return JSON with answer="hello"' }],
      })
      console.log("  Structured response shape:", JSON.stringify(result.data, null, 2).slice(0, 3000))
    } finally {
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
    }
  })

  // Test 7: Timeout (short — 1 second)
  await test("timeout test (1s)", async () => {
    const session = await client.session.create({ title: "test-timeout" })
    const sessionId = session.data?.id
    if (!sessionId) throw new Error("no session ID")
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 1000)
    try {
      await client.session.prompt(
        {
          sessionID: sessionId,
          model: { providerID: "bailian-coding-plan", modelID: "qwen3.5-plus" },
          parts: [{ type: "text" as const, text: "Write a 5000 word essay about the history of computing." }],
        },
        { signal: controller.signal },
      )
      clearTimeout(timeoutId)
      console.log("  Note: model responded within 1s (fast!)")
    } catch (err) {
      clearTimeout(timeoutId)
      console.log("  Timeout error shape:", JSON.stringify(err, null, 2).slice(0, 1000))
      console.log("  err.name:", err instanceof Error ? err.name : "not Error")
      console.log("  controller.aborted:", controller.signal.aborted)
    } finally {
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
    }
  })

  console.log("\n--- Test run complete ---")
  ```

  This script is exploratory — its output will inform the exact error classification logic in subsequent tasks.

- **PATTERN**: Standard Bun script, no tool framework
- **IMPORTS**: `@opencode-ai/sdk/v2/client`
- **GOTCHA**: Run from `.opencode/` directory so node_modules resolve. Use `bun run tools/_test-dispatch.ts` not `bun tools/_test-dispatch.ts`.
- **VALIDATE**: `cd .opencode && bun run tools/_test-dispatch.ts 2>&1 | head -50`

### 3. ANALYZE test results and document error shapes

- **IMPLEMENT**: This is a manual analysis step. After running the test script, document:
  a) The exact shape of `config.providers()` response — what fields identify connected vs disconnected models
  b) The exact shape of successful `session.prompt()` response — confirm `data.parts[].text` extraction works
  c) The exact shape of wrong-model/wrong-provider errors — HTTP status, error class, message format
  d) The exact shape of timeout/abort errors — confirm `AbortError` detection works
  e) The exact shape of structured output response — confirm `data.info.structured` extraction works

  This step produces no code edits. It produces the knowledge needed for steps 4-8.

- **VALIDATE**: Test script ran and produced output for all 7 tests

### 4. UPDATE `.opencode/tools/dispatch.ts` — Add provider pre-flight check

- **IMPLEMENT**: After the health check (line ~217), add a provider validation step that uses `client.config.providers()` to verify the target provider+model is available.

  Insert after the health check block and before the timeout setup:

  ```typescript
  // 2.1. Provider pre-flight — verify model is available before creating session
  try {
    const providersResp = await client.config.providers()
    const providers = providersResp.data
    // Shape TBD from test results — adapt based on actual response
    // Look for resolvedProvider in the providers list
    // If provider exists but model doesn't, give specific error
    // If provider doesn't exist, suggest available providers
    // NOTE: This block will be filled in after Step 3 analysis
  } catch {
    // Pre-flight failed — proceed anyway (non-blocking)
    // The prompt call will fail with a more specific error if model is truly unavailable
  }
  ```

  **IMPORTANT**: The exact implementation depends on the response shape discovered in Step 3. The test script output will reveal whether `config.providers()` returns a map of `{providerID: {models: [...]}}` or a flat array or something else. The execution agent MUST adapt the code based on real output.

- **PATTERN**: `.opencode/tools/dispatch.ts:202-217` — existing health check block (try/catch with early return)
- **IMPORTS**: None new — `client.config` already available from SDK
- **GOTCHA**: 
  1. Pre-flight should be non-blocking — if `config.providers()` itself fails (e.g., endpoint not available in older server versions), silently proceed and let the prompt call handle it.
  2. Don't cache the provider list — it can change between calls (models connected/disconnected dynamically).
  3. The pre-flight adds one extra HTTP call per dispatch. Acceptable for better error messages.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 5. UPDATE `.opencode/tools/dispatch.ts` — Add error classification helper

- **IMPLEMENT**: Add a `classifyError` function after the existing utility functions (after `safeStringify`, before `TASK_ROUTING`). This function parses SDK errors into actionable categories.

  ```typescript
  type ErrorCategory = "auth_missing" | "model_not_found" | "rate_limited" | "timeout" | "server_error" | "unknown"

  interface ClassifiedError {
    category: ErrorCategory
    message: string
    hint: string
    retryable: boolean
  }

  const classifyError = (err: unknown, provider: string, model: string): ClassifiedError => {
    const msg = getErrorMessage(err)
    const lower = msg.toLowerCase()

    // Rate limit detection (HTTP 429 or common messages)
    if (lower.includes("429") || lower.includes("rate limit") || lower.includes("too many requests")) {
      return {
        category: "rate_limited",
        message: msg,
        hint: `${provider}/${model} is rate-limited. Wait 5-10 seconds and retry, or use a different model.`,
        retryable: true,
      }
    }

    // Auth detection (401, 403, api key, unauthorized)
    if (lower.includes("401") || lower.includes("403") || lower.includes("unauthorized") || lower.includes("api key") || lower.includes("authentication")) {
      return {
        category: "auth_missing",
        message: msg,
        hint: `${provider} auth is missing or invalid. Run '/connect ${provider}' to set up credentials.`,
        retryable: false,
      }
    }

    // Model not found (404, not found, unknown model)
    if (lower.includes("404") || lower.includes("not found") || lower.includes("unknown model") || lower.includes("does not exist")) {
      return {
        category: "model_not_found",
        message: msg,
        hint: `Model '${model}' not found on provider '${provider}'. Check model ID or try a different model.`,
        retryable: false,
      }
    }

    // Server errors (500, 502, 503)
    if (lower.includes("500") || lower.includes("502") || lower.includes("503") || lower.includes("internal server error") || lower.includes("service unavailable")) {
      return {
        category: "server_error",
        message: msg,
        hint: `${provider} server error. This is usually temporary — retry in a few seconds.`,
        retryable: true,
      }
    }

    return {
      category: "unknown",
      message: msg,
      hint: `Unexpected error from ${provider}/${model}. Check server logs for details.`,
      retryable: false,
    }
  }
  ```

  **NOTE**: The exact string patterns (429, 401, etc.) will be refined based on Step 3 test results. The execution agent should update the patterns if the real errors use different formats.

- **PATTERN**: `.opencode/tools/dispatch.ts:4-50` — existing utility function style
- **IMPORTS**: None
- **GOTCHA**:
  1. SDK errors may be nested objects, not flat strings. `getErrorMessage` already handles this via `JSON.stringify`.
  2. The classification is heuristic — based on substring matching. It won't catch every edge case, but covers the common ones.
  3. `retryable` flag is informational for the calling model, not enforcement.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 6. UPDATE `.opencode/tools/dispatch.ts` — Replace generic error catch with classified errors + retry

- **IMPLEMENT**: Replace the catch block in the prompt section (currently lines ~296-328) with classified error handling and a single retry for rate limits.

  **Current** (the catch after `client.session.prompt`):
  ```typescript
  } catch (err: unknown) {
    if (timeoutId) clearTimeout(timeoutId)
    if (...AbortError...) { ... }
    // Generic error
    return (
      `[dispatch error] Prompt failed for ${resolvedProvider}/${resolvedModel}: ${getErrorMessage(err)}\n` +
      `Common causes: model not connected...`
    )
  }
  ```

  **Replace with**:
  ```typescript
  } catch (err: unknown) {
    if (timeoutId) clearTimeout(timeoutId)
    // Timeout detection (unchanged)
    if (
      (err instanceof Error && err.name === "AbortError") ||
      controller?.signal.aborted
    ) {
      if (shouldCleanup && sessionId) {
        try { await client.session.delete({ sessionID: sessionId }) } catch { /* best effort */ }
      }
      return (
        `[dispatch error] Timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${args.timeout}s.\n` +
        `Consider increasing the timeout or using a faster model.`
      )
    }

    // Classify the error
    const classified = classifyError(err, resolvedProvider, resolvedModel)

    // Single retry for rate limits
    if (classified.retryable && classified.category === "rate_limited") {
      await new Promise(r => setTimeout(r, 2000))
      try {
        result = await client.session.prompt(
          {
            sessionID: sessionId!,
            model: { providerID: resolvedProvider, modelID: resolvedModel },
            system: args.systemPrompt,
            format: parsedFormat,
            parts: [{ type: "text" as const, text: args.prompt }],
          },
          controller ? { signal: controller.signal } : undefined,
        )
        // Retry succeeded — fall through to response extraction
      } catch (retryErr: unknown) {
        if (shouldCleanup && sessionId) {
          try { await client.session.delete({ sessionID: sessionId }) } catch { /* best effort */ }
        }
        const retryClassified = classifyError(retryErr, resolvedProvider, resolvedModel)
        return (
          `[dispatch error] ${retryClassified.category}: ${retryClassified.message}\n` +
          `Hint: ${retryClassified.hint}\n` +
          `(Retried once after rate limit — still failing)`
        )
      }
    } else {
      // Non-retryable error
      if (shouldCleanup && sessionId) {
        try { await client.session.delete({ sessionID: sessionId }) } catch { /* best effort */ }
      }
      return (
        `[dispatch error] ${classified.category}: ${classified.message}\n` +
        `Hint: ${classified.hint}`
      )
    }
  }
  ```

  **CRITICAL**: After the retry succeeds, execution must NOT return — it must fall through to the existing response extraction code (step 5 in the current flow). This means the `result` variable is assigned in the retry block and the code continues past the catch.

- **PATTERN**: `.opencode/tools/dispatch.ts:296-328` — existing catch block structure
- **IMPORTS**: None
- **GOTCHA**:
  1. The retry block assigns to `result` (declared with `let` before the try). After retry success, the code falls through to response extraction.
  2. Only rate_limited gets a retry. auth_missing, model_not_found, server_error get immediate actionable error return.
  3. The retry uses the same sessionId — no need to create a new session for retry.
  4. If the retry itself times out (AbortController still active), it will throw AbortError — the inner catch handles this via classifyError returning "unknown" (timeout detection is only in the outer catch).
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 7. UPDATE `.opencode/tools/dispatch.ts` — Add duration tracking + response truncation

- **IMPLEMENT**: 
  a) Add `const startTime = Date.now()` right after the routing resolution block (after `resolvedProvider`/`resolvedModel` are set).
  
  b) After the response is extracted (after the "Extract response" try/catch block), add truncation:
  ```typescript
  // 5.5. Response size guard
  const MAX_RESPONSE_CHARS = 50_000
  if (responseText.length > MAX_RESPONSE_CHARS) {
    responseText = responseText.slice(0, MAX_RESPONSE_CHARS) +
      `\n\n[dispatch note] Response truncated from ${responseText.length} to ${MAX_RESPONSE_CHARS} chars.`
  }
  ```

  c) Add duration to the response header modifiers:
  ```typescript
  const durationMs = Date.now() - startTime
  const durationStr = durationMs >= 1000
    ? `${(durationMs / 1000).toFixed(1)}s`
    : `${durationMs}ms`
  ```
  
  Then add `durationStr` to the header (append after modifierStr):
  ```typescript
  const header = `--- dispatch response from ${resolvedProvider}/${resolvedModel}${modifierStr} (${durationStr}) ---\n`
  ```

- **PATTERN**: `.opencode/tools/batch-dispatch.ts:292` — batch already has `const startTime = Date.now()` and `durationMs` tracking
- **IMPORTS**: None
- **GOTCHA**:
  1. `startTime` must be declared before any async work (health check, provider check, session creation, prompt) so it captures total wall time.
  2. The truncation happens AFTER response extraction but BEFORE the header is built. This order matters for the note placement.
  3. 50,000 chars is ~12,500 tokens — generous but prevents multi-MB responses from models that generate endlessly.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 8. UPDATE `.opencode/tools/batch-dispatch.ts` — Add classified errors + response truncation

- **IMPLEMENT**: Apply the same hardening to batch-dispatch:
  
  a) Copy the `classifyError` function and `ErrorCategory`/`ClassifiedError` types into batch-dispatch.ts (after `safeStringify`, before `TASK_ROUTING`). Tools must be self-contained.
  
  b) In `dispatchOne` catch block (lines ~375-387), replace the generic error handling:
  
  **Current**:
  ```typescript
  return {
    ...target,
    status: isTimeout ? "timeout" : "error",
    response: isTimeout
      ? `Did not respond within ${args.timeout}s`
      : getErrorMessage(err),
    durationMs: Date.now() - startTime,
  }
  ```
  
  **Replace with**:
  ```typescript
  if (isTimeout) {
    return {
      ...target,
      status: "timeout",
      response: `Did not respond within ${args.timeout}s. Consider increasing timeout or using a faster model.`,
      durationMs: Date.now() - startTime,
    }
  }
  const classified = classifyError(err, target.provider, target.model)
  return {
    ...target,
    status: "error",
    response: `${classified.category}: ${classified.message}\nHint: ${classified.hint}`,
    durationMs: Date.now() - startTime,
  }
  ```

  c) Add response truncation after text extraction in `dispatchOne` (before the `return { status: "success" }` block):
  ```typescript
  const MAX_RESPONSE_CHARS = 50_000
  if (responseText.length > MAX_RESPONSE_CHARS) {
    responseText = responseText.slice(0, MAX_RESPONSE_CHARS) +
      `\n[truncated from ${responseText.length} chars]`
  }
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts` Task 5-6 — same classifyError function
- **IMPORTS**: None
- **GOTCHA**:
  1. `classifyError` is duplicated, not shared. Tools are self-contained.
  2. Batch doesn't retry on rate limits — individual model failures are reported, not retried. The calling model can decide whether to re-dispatch.
  3. Response truncation per-model, not total. If 3 models each return 50K chars, total output is 150K+. This is acceptable — batch responses are inherently larger.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5`

### 9. VALIDATE — Re-run live test script with hardened tools

- **IMPLEMENT**: Run the test script from Step 2 again. Verify:
  a) Happy path still works — response extracted correctly
  b) Wrong model/provider now shows classified error with hint
  c) Timeout still detected correctly
  d) Duration appears in headers
  e) No regressions
  
  Additionally, test the actual dispatch tool via opencode if the server is running with TUI.

- **VALIDATE**: `cd .opencode && bun run tools/_test-dispatch.ts 2>&1`

---

## TESTING STRATEGY

### Unit Tests

N/A — custom tools don't have a unit test framework. The live test script serves this role.

### Integration Tests

**Test 1: Happy path dispatch**
- `dispatch(taskType: "quick-check", prompt: "Say hello")` → success response with `[routed: quick-check]` header

**Test 2: Provider pre-flight rejection**
- `dispatch(provider: "nonexistent", model: "foo", prompt: "test")` → actionable error before session creation

**Test 3: Classified error — wrong model**
- `dispatch(provider: "bailian-coding-plan", model: "nonexistent", prompt: "test")` → `model_not_found` category with hint

**Test 4: Timeout**
- `dispatch(provider: "bailian-coding-plan", model: "qwen3.5-plus", prompt: "Write a 10000 word essay", timeout: 1)` → timeout error

**Test 5: Batch dispatch — mixed results**
- `batch-dispatch(models: [good-model, bad-model], prompt: "test")` → one success, one classified error

**Test 6: Response truncation**
- `dispatch(prompt: "Generate 100000 characters of text")` → response truncated note at end

**Test 7: Duration tracking**
- Any successful dispatch → header contains duration like `(1.2s)`

**Test 8: Backward compatibility**
- `dispatch(provider: "bailian-coding-plan", model: "qwen3-coder-next", prompt: "hello")` → works exactly as before, now with duration

### Edge Cases

- Provider returns empty response (no parts) → existing `[dispatch warning]` message
- SDK throws non-Error object (plain string or object) → `getErrorMessage` handles it
- `config.providers()` endpoint doesn't exist on older server → pre-flight silently skipped
- Rate limit on retry attempt → classified error with "(Retried once)" note
- Response exactly at 50,000 char boundary → no truncation (only > triggers it)

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

### Level 3-4: Live Tests
```bash
cd .opencode && bun run tools/_test-dispatch.ts 2>&1
```

### Level 5: Manual Validation
- Verify dispatch via opencode TUI with `taskType: "quick-check"` 
- Verify error message when using wrong model ID
- Verify duration appears in response header
- Verify batch-dispatch with 2+ models returns comparison format

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] Test script created and produces output for all 7 test scenarios
- [ ] Provider pre-flight check added to dispatch.ts (non-blocking)
- [ ] `classifyError` function added to both tools with 5 categories
- [ ] Prompt catch block uses classified errors with actionable hints
- [ ] Rate limit retry (single attempt, 2s delay) added to dispatch.ts
- [ ] Duration tracking added to dispatch.ts response header
- [ ] Response truncation (50K chars) added to both tools
- [ ] Both tools build without errors
- [ ] Backward compatible — existing calls work unchanged
- [ ] Error messages include specific remediation hints

### Runtime (verify after live testing)

- [ ] Happy path dispatch returns correct response with duration
- [ ] Wrong model → `model_not_found` with hint
- [ ] Wrong provider → appropriate classified error
- [ ] Timeout → clear timeout message (unchanged behavior)
- [ ] Batch dispatch with bad model → classified error per-model
- [ ] Structured output → correctly extracted from response

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Live test script passes all scenarios
- [ ] No regressions in existing functionality
- [ ] Acceptance criteria all met
- [ ] Test script output documented (for future reference)

---

## NOTES

### Key Design Decisions

- **Provider pre-flight is non-blocking**: If `config.providers()` fails (endpoint missing, network issue), we silently proceed. The prompt call will fail with a more specific error anyway. This prevents the pre-flight from being a fragile gate.
- **Error classification is heuristic**: Substring matching on error messages isn't perfect, but it's pragmatic. The alternative (parsing HTTP status codes from SDK internals) is brittle and SDK-version-dependent.
- **Single retry, not exponential backoff**: For a tool that returns a string, implementing proper backoff is overkill. One retry after 2s catches most transient rate limits. Persistent rate limits return an error with "try again later" hint.
- **50K char response limit**: Conservative. Most useful responses are under 10K. The limit prevents pathological cases where a model generates endlessly (some models do this with long code generation prompts).
- **Duration in header, not separate field**: Tools return strings, not objects. Adding duration to the header string is the only option. Format: `(1.2s)` at the end of the header line.

### Risks

- **Real error shapes may differ**: The test script discovers actual shapes. If they're radically different from expectations, Steps 4-8 will need adaptation. Mitigation: Step 3 is an explicit analysis step.
- **Provider pre-flight API may not exist**: Older OpenCode server versions may not support `config.providers()`. Mitigation: wrapped in try/catch with silent fallthrough.
- **Rate limit retry may mask persistent issues**: If a provider is consistently rate-limited, the 2s retry just delays the error. Mitigation: the error message explicitly says "Retried once" so the calling model knows retry was attempted.

### Confidence Score: 7/10

- **Strengths**: Clear test-first approach, real error shapes will inform implementation, backward compatible, each step has explicit validation
- **Uncertainties**: Unknown SDK error shapes (the whole point of this slice), `config.providers()` response format, whether rate limit detection patterns match real provider behavior
- **Mitigations**: Test script runs first, analysis step before implementation, all new code is additive (no destructive changes to working paths)
