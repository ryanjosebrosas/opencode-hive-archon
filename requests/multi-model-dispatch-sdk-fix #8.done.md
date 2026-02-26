# Feature: Multi-Model Dispatch SDK Fix + Provider Discovery

## Feature Description

Fix the dispatch tools so `session.prompt()` actually works against the real `opencode serve` server. The tools build and pass type checks but hang indefinitely when called live. Root cause: the SDK's `session.prompt()` is a synchronous blocking POST with timeout explicitly disabled (`req.timeout = false`). When the target model is slow, not connected, or has auth issues, the promise blocks forever. This slice adds connected-provider discovery, a mandatory default timeout, empty-response detection, and a `promptAsync` + SSE fallback path for robustness.

## User Story

As a model using the dispatch tool, I want dispatch calls to either succeed with a response within a reasonable time or fail fast with an actionable error, so that I never hang indefinitely waiting for a model that will never respond.

## Problem Statement

Six slices of dispatch tooling (400+ lines of dispatch.ts, 456 lines of batch-dispatch.ts) have been built and pass all static checks, but `session.prompt()` hangs indefinitely in live testing. Specific findings:

1. **SDK disables timeout by default**: `createOpencodeClient` wraps fetch with `req.timeout = false`, meaning no safety net if the server holds the connection open (which it does — it waits for the full AI response).
2. **Empty response on failure**: Wrong model/provider doesn't throw — it returns `{ data: {}, error: undefined }`. Our error handling only catches thrown exceptions.
3. **No provider pre-check**: We create a session, send a prompt, and only then discover the model isn't connected. The server starts processing, finds no provider, and... hangs or returns empty.
4. **AbortController is opt-in**: Our timeout arg is optional. With no timeout and a bad model, the call blocks forever.
5. **Unknown connected providers**: We've been testing with `bailian-coding-plan` models but don't know if that provider is actually authenticated/connected in the current `opencode serve` instance.

## Solution Statement

- Decision 1: **Add connected provider discovery** — use `GET /provider` (returns `{ connected: string[] }`) to check what's actually connected before dispatching. Return an actionable error if the target provider isn't connected.
- Decision 2: **Mandatory default timeout** — if the caller doesn't provide a timeout, apply a 120-second default. No dispatch call should ever block indefinitely.
- Decision 3: **Empty response detection** — after `session.prompt()` returns, check for empty `data` (`{}` or `{ data: {} }`). Treat this as a model-not-responding error instead of silently returning no text.
- Decision 4: **Rewrite test script** — replace the existing `_test-dispatch.ts` with a diagnostic script that first discovers connected providers, then tests against a confirmed-connected model, and logs exact response shapes.
- Decision 5: **Keep `session.prompt()` (synchronous)** — the async+SSE path (`promptAsync` + `event.subscribe`) is more complex and unnecessary for most dispatch use cases. The synchronous POST with a timeout is sufficient. We'll add the async path as a future slice if needed.
- Decision 6: **Single file changes + test script** — modify `dispatch.ts`, `batch-dispatch.ts`, and rewrite `_test-dispatch.ts`. No command/agent changes.

## Feature Metadata

- **Feature Type**: Bug Fix + Enhancement
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `.opencode/tools/dispatch.ts`, `.opencode/tools/batch-dispatch.ts`, `.opencode/tools/_test-dispatch.ts`
- **Dependencies**: `opencode serve` running on port 4096, at least one connected provider

### Slice Guardrails (Required)

- **Single Outcome**: One successful end-to-end dispatch call with a response, plus fail-fast behavior when the model isn't connected
- **Expected Files Touched**: 3 files (dispatch.ts, batch-dispatch.ts, _test-dispatch.ts)
- **Scope Boundary**: Does NOT add `promptAsync`/SSE streaming. Does NOT modify command markdown files. Does NOT change the TASK_ROUTING map. Does NOT add error classification (that's Slice 9).
- **Split Trigger**: If the connected-provider check reveals more than 3 distinct failure modes, defer complex error classification to Slice 9.

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-400) — Why: primary file being modified. Must understand current flow: routing resolution (lines 159-186), health check (lines 202-217), timeout setup (lines 219-231), session creation (lines 259-278), prompt call (lines 282-295), response extraction (lines 334-374)
- `.opencode/tools/batch-dispatch.ts` (lines 1-456) — Why: secondary file getting same fixes. Must understand `dispatchOne` (lines 291-398) which has the same prompt/response pattern
- `.opencode/tools/_test-dispatch.ts` (lines 1-100) — Why: being rewritten. Current script tests against hardcoded providers that may not be connected
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.js` (lines 912-939) — Why: shows `session.prompt()` implementation — `buildClientParams` decomposes flat params into `{ path: { sessionID }, body: { model, parts } }`, sends `POST /session/{sessionID}/message`
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.js` (lines 988-1016) — Why: shows `session.promptAsync()` — same body but `POST /session/{sessionID}/prompt_async`, returns 204 immediately
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/client.js` (lines 5-27) — Why: shows `req.timeout = false` — explicitly disables fetch timeout in the custom fetch wrapper
- `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.d.ts` (lines 473-490) — Why: `session.prompt()` type signature showing all accepted params
- `opencode.json` (lines 11-87) — Why: provider configuration. The `bailian-coding-plan` custom provider config and model IDs

### New Files to Create

- None — all changes are modifications to existing files

### Related Memories (from memory.md)

- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" — Relevance: connected-provider check should give actionable error like "Provider X not connected. Connected providers: [list]. Run '/connect X' to connect."
- Memory: "Session safety in shared servers: Never trust client-supplied session_id" — Relevance: still relevant, our session lifecycle doesn't change
- Memory: "Legacy SDK compatibility: When provider SDKs differ on auth args, use temporary env bridging" — Relevance: different providers may need different auth — the connected check catches this at the provider level

### Relevant Documentation

- [OpenCode SDK — Client Only](https://opencode.ai/docs/sdk/#client-only)
  - Specific section: Options — `createOpencodeClient` options
  - Why: confirms `fetch` can be customized, `responseStyle: "fields"` returns `{ data, response, error }`
- [OpenCode SDK — Sessions](https://opencode.ai/docs/sdk/#sessions)
  - Specific section: `session.prompt()` example
  - Why: shows official v1 calling pattern with `{ path, body }`. Our v2 flat params are equivalent (buildClientParams transforms them)
- [OpenCode Server — Provider](https://opencode.ai/docs/server/#provider)
  - Specific section: `GET /provider`
  - Why: returns `{ all: Provider[], default: {...}, connected: string[] }` — the `connected` array is what we need for provider pre-flight
- [OpenCode Server — Messages](https://opencode.ai/docs/server/#messages)
  - Specific section: `POST /session/:id/message`
  - Why: "Send a message and wait for response" — confirms this is synchronous. Body: `{ model?, agent?, noReply?, system?, tools?, parts }`
- [OpenCode Server — Messages](https://opencode.ai/docs/server/#messages)
  - Specific section: `POST /session/:id/prompt_async`
  - Why: "Send a message asynchronously (no wait)" — returns 204. Future enhancement path.

### Patterns to Follow

**Current dispatch.ts health check pattern** (from `.opencode/tools/dispatch.ts:202-217`):
```typescript
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
- Why this pattern: provider check follows the same try/catch + early return structure
- Common gotchas: `client.provider.list()` may not exist on all SDK versions — wrap in try/catch

**Current dispatch.ts response extraction** (from `.opencode/tools/dispatch.ts:334-374`):
```typescript
let responseText = ""
try {
  const resultRecord = asRecord(result)
  const data = asRecord(resultRecord?.data)
  const info = asRecord(data?.info)
  // ... extraction logic
  responseText = extractTextFromParts(data?.parts)
  if (!responseText) {
    responseText = `[dispatch warning] No text parts in response. Raw: ${safeStringify(data)}`
  }
}
```
- Why this pattern: empty-response detection goes BEFORE this — if `data` is `{}` or undefined, short-circuit with error
- Common gotchas: `result` may be `{ data: {}, error: undefined }` — the `asRecord` calls would succeed but all fields would be undefined

**SDK buildClientParams decomposition** (from `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.js:912-939`):
```javascript
prompt(parameters, options) {
    const params = buildClientParams([parameters], [
        { args: [
            { in: "path", key: "sessionID" },
            { in: "body", key: "model" },
            { in: "body", key: "parts" },
            // ... other body keys
        ] },
    ]);
    return this.client.post({
        url: "/session/{sessionID}/message",
        ...params,
        headers: { "Content-Type": "application/json" },
    });
}
```
- Why this pattern: confirms our v2 flat params `{ sessionID, model, parts }` get correctly decomposed to `POST /session/{sessionID}/message` with body `{ model, parts }`
- Common gotchas: the URL template `{sessionID}` is replaced from `params.path.sessionID` by the HTTP client

---

## IMPLEMENTATION PLAN

### Phase 1: Diagnostic — Discover connected providers and test with a known-good model

Rewrite the test script to discover what's actually connected, then test dispatch against a confirmed-connected provider.

**Tasks:**
- Rewrite `_test-dispatch.ts` to discover connected providers first
- Test `session.prompt()` with a confirmed-connected model
- Capture exact response shapes for success/failure/empty

### Phase 2: Fix — Add provider pre-flight and mandatory timeout

Add the connected-provider check and default timeout to both dispatch tools.

**Tasks:**
- Add provider discovery function to dispatch.ts
- Add mandatory default timeout (120s) when no timeout specified
- Add empty-response detection after prompt call
- Apply same fixes to batch-dispatch.ts

### Phase 3: Validation — Run live tests and verify fixes

Re-run the test script with hardened tools to verify end-to-end dispatch works.

**Tasks:**
- Run `_test-dispatch.ts` against real server
- Verify connected model dispatches successfully
- Verify disconnected model fails fast with actionable error
- Verify timeout works

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. REWRITE `.opencode/tools/_test-dispatch.ts` — Diagnostic test script

- **IMPLEMENT**: Replace the entire file with a diagnostic script that:
  a) Connects to server, checks health
  b) Lists connected providers via `GET /provider` (using raw fetch since `client.provider.list()` may not exist on all SDK versions)
  c) Displays connected providers + their models
  d) Picks the FIRST connected provider's first model
  e) Tests `session.prompt()` with that model using a 30s timeout
  f) Logs exact response shape on success
  g) Tests with a wrong provider to see failure shape
  h) Tests empty response detection

  **Full implementation:**
  ```typescript
  import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"

  const BASE_URL = "http://127.0.0.1:4096"

  async function main() {
    console.log("=== Dispatch Diagnostic Test ===\n")

    // 1. Create client + health check
    const client = createOpencodeClient({ baseUrl: BASE_URL })
    const health = await client.global.health()
    console.log("Health:", JSON.stringify(health.data))
    if (!health.data?.healthy) {
      console.error("Server not healthy. Aborting.")
      process.exit(1)
    }

    // 2. Discover connected providers via raw fetch
    console.log("\n--- Connected Providers ---")
    let connectedProviders: string[] = []
    let allProviders: Array<{ id: string; name?: string; models?: Array<{ id: string; name?: string }> }> = []
    try {
      const resp = await fetch(`${BASE_URL}/provider`)
      const providerData = await resp.json() as {
        all?: Array<{ id: string; name?: string; models?: Array<{ id: string; name?: string }> }>
        connected?: string[]
      }
      connectedProviders = providerData.connected ?? []
      allProviders = providerData.all ?? []
      console.log("Connected:", connectedProviders)
      console.log("Total providers:", allProviders.length)

      // Show models for connected providers
      for (const pid of connectedProviders) {
        const provider = allProviders.find((p) => p.id === pid)
        if (provider?.models) {
          const activeModels = provider.models
            .filter((m: any) => m.status === "active" || !m.status)
            .slice(0, 5)
          console.log(`  ${pid}: ${activeModels.map((m) => m.id).join(", ")}${provider.models.length > 5 ? ` (+${provider.models.length - 5} more)` : ""}`)
        }
      }
    } catch (err) {
      console.error("Failed to list providers:", err)
    }

    if (connectedProviders.length === 0) {
      console.error("\nNo connected providers! Run '/connect <provider>' first.")
      process.exit(1)
    }

    // 3. Pick first connected provider + its first model
    const testProvider = connectedProviders[0]
    const providerInfo = allProviders.find((p) => p.id === testProvider)
    const testModel = providerInfo?.models?.[0]?.id
    if (!testModel) {
      console.error(`No models found for connected provider: ${testProvider}`)
      process.exit(1)
    }
    console.log(`\n--- Testing: ${testProvider}/${testModel} ---`)

    // 4. Test session.prompt() with 30s timeout
    let sessionId: string | undefined
    try {
      const session = await client.session.create({ title: "diagnostic-test" })
      sessionId = session.data?.id
      console.log("Session created:", sessionId)
      if (!sessionId) {
        console.error("No session ID returned:", JSON.stringify(session.data))
        process.exit(1)
      }

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30_000)

      console.log("Sending prompt (30s timeout)...")
      const startTime = Date.now()
      const result = await client.session.prompt(
        {
          sessionID: sessionId,
          model: { providerID: testProvider, modelID: testModel },
          parts: [{ type: "text" as const, text: "Reply with exactly: DISPATCH_TEST_OK" }],
        },
        { signal: controller.signal },
      )
      clearTimeout(timeoutId)
      const duration = Date.now() - startTime

      console.log(`Response received in ${duration}ms`)
      console.log("result keys:", Object.keys(result ?? {}))
      console.log("result.data keys:", Object.keys((result as any)?.data ?? {}))
      console.log("result.error:", (result as any)?.error)

      // Check for empty response
      const data = (result as any)?.data
      if (!data || (typeof data === "object" && Object.keys(data).length === 0)) {
        console.log("EMPTY RESPONSE DETECTED — model may not be connected or responding")
      } else {
        const info = data?.info
        const parts = data?.parts
        console.log("info keys:", Object.keys(info ?? {}))
        console.log("parts count:", Array.isArray(parts) ? parts.length : "not array")
        if (Array.isArray(parts)) {
          for (const part of parts) {
            if (part?.type === "text") {
              console.log("TEXT:", part.text?.slice(0, 500))
            } else {
              console.log("PART:", part?.type, JSON.stringify(part).slice(0, 200))
            }
          }
        }
        console.log("\nFull response (truncated):", JSON.stringify(data, null, 2).slice(0, 3000))
      }
    } catch (err: any) {
      if (err?.name === "AbortError" || (err instanceof Error && err.name === "AbortError")) {
        console.log("TIMEOUT — model did not respond within 30s")
      } else {
        console.log("ERROR:", err?.name, err?.message)
        console.log("Full error:", JSON.stringify(err, null, 2).slice(0, 1000))
      }
    } finally {
      if (sessionId) {
        await client.session.delete({ sessionID: sessionId }).catch(() => {})
        console.log("Session cleaned up")
      }
    }

    // 5. Test with wrong provider (expect failure)
    console.log("\n--- Testing: nonexistent/fake-model ---")
    let badSessionId: string | undefined
    try {
      const session = await client.session.create({ title: "diagnostic-bad-provider" })
      badSessionId = session.data?.id
      if (!badSessionId) {
        console.error("No session ID for bad provider test")
      } else {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10_000)

        const result = await client.session.prompt(
          {
            sessionID: badSessionId,
            model: { providerID: "nonexistent-provider-xyz", modelID: "fake-model" },
            parts: [{ type: "text" as const, text: "test" }],
          },
          { signal: controller.signal },
        )
        clearTimeout(timeoutId)

        console.log("Bad provider result:", JSON.stringify(result, null, 2).slice(0, 1000))
      }
    } catch (err: any) {
      console.log("Bad provider error:", err?.name, err?.message)
    } finally {
      if (badSessionId) {
        await client.session.delete({ sessionID: badSessionId }).catch(() => {})
      }
    }

    console.log("\n=== Diagnostic Test Complete ===")
  }

  main().catch(console.error)
  ```

- **PATTERN**: Existing `_test-dispatch.ts` structure but with connected-provider discovery first
- **IMPORTS**: `import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"`
- **GOTCHA**:
  1. Use raw `fetch()` for `/provider` endpoint since `client.provider.list()` may return different shape than documented
  2. The provider response has `connected: string[]` — this is the key data we need
  3. Provider `.models` array may have a `.status` field — filter for "active" if present
  4. Always use `AbortController` with timeout — never call `session.prompt()` without one
  5. Run from `.opencode/` directory: `cd .opencode && bun run tools/_test-dispatch.ts`
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/_test-dispatch.ts 2>&1 | head -5`

### 2. RUN diagnostic and analyze results

- **IMPLEMENT**: This is a manual step. Run the test script and analyze the output:
  ```bash
  cd .opencode && bun run tools/_test-dispatch.ts
  ```
  
  Document:
  a) Which providers are in the `connected` array
  b) Whether the first connected model responds to `session.prompt()`
  c) The exact response shape for success
  d) The exact response shape for wrong-provider failure
  e) Whether the timeout works (AbortError thrown)

  **If the test hangs at "Sending prompt..."**: The model isn't responding. Note which provider/model was used. Try a different connected provider. If ALL connected providers hang, the issue is server-side.

  **If the test succeeds**: Note the response shape and use it to verify our extraction logic is correct.

  This step produces no code edits. It produces the knowledge needed for steps 3-6.

- **VALIDATE**: Test script ran and produced output

### 3. UPDATE `.opencode/tools/dispatch.ts` — Add `getConnectedProviders` helper

- **IMPLEMENT**: Add a helper function after the existing utility functions (after `safeStringify`, before `TASK_ROUTING`) that fetches connected providers from the server.

  **Insert after `safeStringify` function (after line 50), before `const TASK_ROUTING`:**
  ```typescript
  const DEFAULT_TIMEOUT_SECONDS = 120

  const getConnectedProviders = async (baseUrl: string): Promise<string[]> => {
    try {
      const resp = await fetch(`${baseUrl}/provider`)
      if (!resp.ok) return []
      const data = (await resp.json()) as { connected?: string[] }
      return data.connected ?? []
    } catch {
      return [] // Non-blocking — if we can't check, proceed anyway
    }
  }
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:4-50` — existing utility function style (pure functions, defensive, no throw)
- **IMPORTS**: None — `fetch` is a global in Bun
- **GOTCHA**:
  1. Use raw `fetch()` not the SDK client — the SDK may not expose `provider.list()` in a stable way
  2. Return empty array on failure — this is non-blocking. If we can't check providers, the prompt call will reveal the issue.
  3. The `/provider` endpoint returns `{ all, default, connected }` — we only need `connected`
  4. This adds one extra HTTP call per dispatch. Fast (< 50ms) and worth it for better error messages.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 4. UPDATE `.opencode/tools/dispatch.ts` — Add provider pre-flight check after health check

- **IMPLEMENT**: After the health check block (after line 217), add a provider connectivity check. If the target provider is not in the connected list, return an actionable error immediately.

  **Insert after the health check catch block (after line 217), before the timeout setup (line 219):**
  ```typescript
  // 2.1. Provider pre-flight — verify provider is connected
  const connectedProviders = await getConnectedProviders(baseUrl)
  if (connectedProviders.length > 0 && !connectedProviders.includes(resolvedProvider)) {
    return (
      `[dispatch error] Provider '${resolvedProvider}' is not connected.\n` +
      `Connected providers: ${connectedProviders.join(", ")}\n` +
      `Run '/connect ${resolvedProvider}' in OpenCode to connect it.`
    )
  }
  ```

  The check is guarded by `connectedProviders.length > 0` — if the provider endpoint returned nothing (error or empty), we skip the check and let the prompt call handle it.

- **PATTERN**: `.opencode/tools/dispatch.ts:202-217` — existing health check early-return pattern
- **IMPORTS**: None
- **GOTCHA**:
  1. Only check if we actually got a connected list — `length > 0` guard
  2. Custom providers from `opencode.json` (like `bailian-coding-plan`) should appear in the connected list if configured correctly
  3. The error message lists ALL connected providers so the caller can choose an alternative
  4. This doesn't check if the specific MODEL is available — just the provider. Model validation requires the prompt call.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 5. UPDATE `.opencode/tools/dispatch.ts` — Add mandatory default timeout

- **IMPLEMENT**: Modify the timeout setup block (lines 219-231) to apply a default timeout when none is specified.

  **Current** (lines 219-231):
  ```typescript
  // 2.5. Set up timeout if requested
  let controller: AbortController | undefined
  let timeoutId: ReturnType<typeof setTimeout> | undefined
  if (args.timeout !== undefined) {
    if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
      return "[dispatch error] timeout must be a positive number of seconds"
    }
    if (args.timeout > MAX_TIMEOUT_SECONDS) {
      return `[dispatch error] timeout must be <= ${MAX_TIMEOUT_SECONDS} seconds`
    }
    controller = new AbortController()
    timeoutId = setTimeout(() => controller!.abort(), args.timeout * 1000)
  }
  ```

  **Replace with:**
  ```typescript
  // 2.5. Set up timeout (mandatory — default 120s to prevent indefinite hangs)
  const effectiveTimeout = args.timeout ?? DEFAULT_TIMEOUT_SECONDS
  if (!Number.isFinite(effectiveTimeout) || effectiveTimeout <= 0) {
    return "[dispatch error] timeout must be a positive number of seconds"
  }
  if (effectiveTimeout > MAX_TIMEOUT_SECONDS) {
    return `[dispatch error] timeout must be <= ${MAX_TIMEOUT_SECONDS} seconds`
  }
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), effectiveTimeout * 1000)
  ```

  Also update the timeout error message to distinguish user-specified vs default:
  In the catch block (line ~300), change the timeout return to:
  ```typescript
  return (
    `[dispatch error] Timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${effectiveTimeout}s.\n` +
    (args.timeout !== undefined
      ? `Consider increasing the timeout or using a faster model.`
      : `This was the default ${DEFAULT_TIMEOUT_SECONDS}s timeout. Set 'timeout' arg for a custom value.`)
  )
  ```

  Since `controller` and `timeoutId` are no longer optional, update the prompt call to always pass the signal:
  **Change** (line ~294):
  ```typescript
  controller ? { signal: controller.signal } : undefined,
  ```
  **To:**
  ```typescript
  { signal: controller.signal },
  ```

  And remove the `if (timeoutId)` guards before `clearTimeout(timeoutId)` calls — it's always defined now.

- **PATTERN**: `.opencode/tools/dispatch.ts:219-231` — existing timeout setup
- **IMPORTS**: None
- **GOTCHA**:
  1. `DEFAULT_TIMEOUT_SECONDS = 120` gives models up to 2 minutes — generous for most tasks
  2. The `controller` and `timeoutId` are now always defined (not optional). Remove the `?` checks.
  3. The error message changes based on whether timeout was user-specified or default
  4. All subsequent references to `args.timeout` in error messages should use `effectiveTimeout`
  5. The `clearTimeout(timeoutId)` calls no longer need `if (timeoutId)` guards
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 6. UPDATE `.opencode/tools/dispatch.ts` — Add empty-response detection

- **IMPLEMENT**: After `session.prompt()` returns (and before response extraction), check for empty/malformed response. The SDK returns `{ data: {}, error: undefined }` when the model doesn't respond.

  **Insert after `clearTimeout(timeoutId)` (line ~332), before "5. Extract response" (line ~334):**
  ```typescript
  // 4.5. Check for empty response (model not responding)
  const resultRecord = asRecord(result)
  const resultData = asRecord(resultRecord?.data)
  if (!resultData || Object.keys(resultData).length === 0) {
    if (shouldCleanup && sessionId) {
      try { await client.session.delete({ sessionID: sessionId }) } catch { /* best effort */ }
    }
    return (
      `[dispatch error] Empty response from ${resolvedProvider}/${resolvedModel}.\n` +
      `The model did not produce any output. Possible causes:\n` +
      `- Model is not connected or authenticated (run '/connect ${resolvedProvider}')\n` +
      `- Model ID '${resolvedModel}' is incorrect for provider '${resolvedProvider}'\n` +
      `- Provider is rate-limiting or temporarily unavailable`
    )
  }
  ```

  Then update the response extraction block to use `resultData` instead of re-parsing:
  **Change the response extraction** (current lines 337-339):
  ```typescript
  const resultRecord = asRecord(result)
  const data = asRecord(resultRecord?.data)
  const info = asRecord(data?.info)
  ```
  **To:**
  ```typescript
  const data = resultData  // Already parsed in step 4.5
  const info = asRecord(data?.info)
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:334-374` — existing response extraction with null checks
- **IMPORTS**: None
- **GOTCHA**:
  1. The empty check must happen AFTER the timeout is cleared but BEFORE response extraction
  2. `Object.keys(resultData).length === 0` catches `{ data: {} }` — the observed failure pattern
  3. `!resultData` catches `{ data: undefined }` or `{ data: null }` — another possible failure
  4. Must still clean up the session on empty response
  5. The `resultRecord` variable declared here replaces the one in the extraction block — remove the duplicate declaration
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5`

### 7. UPDATE `.opencode/tools/batch-dispatch.ts` — Add same fixes

- **IMPLEMENT**: Apply the same three fixes to batch-dispatch.ts:

  a) **Add `DEFAULT_TIMEOUT_SECONDS` and `getConnectedProviders`** — copy both from dispatch.ts, after `safeStringify` (line 45), before `TASK_ROUTING` (line 64):
  ```typescript
  const DEFAULT_TIMEOUT_SECONDS = 120

  const getConnectedProviders = async (baseUrl: string): Promise<string[]> => {
    try {
      const resp = await fetch(`${baseUrl}/provider`)
      if (!resp.ok) return []
      const data = (await resp.json()) as { connected?: string[] }
      return data.connected ?? []
    } catch {
      return []
    }
  }
  ```

  b) **Add provider pre-flight** — after the health check (line ~288), before the dispatch loop (line ~290):
  ```typescript
  // 4.5. Provider pre-flight for all targets
  const connectedProviders = await getConnectedProviders(baseUrl)
  if (connectedProviders.length > 0) {
    const disconnected = targets.filter((t) => !connectedProviders.includes(t.provider))
    if (disconnected.length === targets.length) {
      return (
        `[batch-dispatch error] None of the target providers are connected.\n` +
        `Requested: ${[...new Set(disconnected.map((t) => t.provider))].join(", ")}\n` +
        `Connected: ${connectedProviders.join(", ")}\n` +
        `Run '/connect <provider>' to connect providers.`
      )
    }
    // Warn about disconnected but don't block — let individual models fail
    if (disconnected.length > 0) {
      // Continue — dispatchOne will handle individual failures
    }
  }
  ```

  c) **Add mandatory default timeout in `dispatchOne`** — change the per-model timeout setup (lines 296-304):
  
  **Current:**
  ```typescript
  let controller: AbortController | undefined
  let timeoutId: ReturnType<typeof setTimeout> | undefined
  if (args.timeout) {
    controller = new AbortController()
    timeoutId = setTimeout(() => controller!.abort(), args.timeout * 1000)
  }
  ```
  
  **Replace with:**
  ```typescript
  const effectiveTimeout = args.timeout ?? DEFAULT_TIMEOUT_SECONDS
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), effectiveTimeout * 1000)
  ```

  And update the signal passing (line ~333) to always pass it:
  ```typescript
  { signal: controller.signal },
  ```

  Update `clearTimeout` calls to remove the `if (timeoutId)` guard (it's always defined now).

  d) **Add empty-response detection in `dispatchOne`** — after `clearTimeout(timeoutId)` (line ~336), before response extraction (line ~339):
  ```typescript
  // Check for empty response
  const resultRecord = asRecord(result)
  const data = asRecord(resultRecord?.data)
  if (!data || Object.keys(data).length === 0) {
    return {
      ...target,
      status: "error" as const,
      response: `Empty response — model may not be connected or authenticated. Run '/connect ${target.provider}'.`,
      durationMs: Date.now() - startTime,
    }
  }
  ```

  Then update the subsequent extraction to reuse `data` variable (remove the duplicate `asRecord` calls at lines 339-341).

- **PATTERN**: `.opencode/tools/dispatch.ts` tasks 3-6 — same fixes, adapted for batch context
- **IMPORTS**: None
- **GOTCHA**:
  1. Batch has TWO levels: overall pre-flight (all targets) and per-model pre-flight (in dispatchOne)
  2. Overall pre-flight only blocks if ALL providers are disconnected — if some are disconnected, let individual models fail gracefully
  3. `effectiveTimeout` in `dispatchOne` uses the shared `args.timeout ?? DEFAULT_TIMEOUT_SECONDS`
  4. The `finally` block for session cleanup doesn't need changes — it already handles all cases
  5. `controller` and `timeoutId` in `dispatchOne` are now non-optional — update the catch block accordingly
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5`

### 8. VALIDATE — Run diagnostic test with hardened tools

- **IMPLEMENT**: Run the diagnostic test script again to verify the fixes work:
  ```bash
  cd .opencode && bun run tools/_test-dispatch.ts
  ```

  Expected outcomes:
  - Connected providers listed correctly
  - Prompt to connected model either succeeds (with response text) or times out clearly
  - Prompt to non-existent provider returns immediately with provider-not-connected error
  - No indefinite hangs

  If the diagnostic test passes, also verify the tools still build:
  ```bash
  cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5
  cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5
  ```

- **VALIDATE**: All three commands produce clean output

---

## TESTING STRATEGY

### Unit Tests

N/A — custom tools don't have a unit test framework. The diagnostic script serves as the integration test.

### Integration Tests

**Test 1: Connected provider discovery**
- Run diagnostic script → "Connected:" line shows at least one provider
- Pass criteria: connected providers listed

**Test 2: Successful dispatch to connected model**
- Dispatch to first connected provider's first model with "Reply with exactly: DISPATCH_TEST_OK"
- Expected: response contains text, duration shown
- Pass criteria: non-empty response text

**Test 3: Provider not connected**
- Dispatch to `nonexistent-provider-xyz/fake-model`
- Expected: immediate error "Provider 'nonexistent-provider-xyz' is not connected. Connected providers: [list]"
- Pass criteria: returns in < 1s, actionable error

**Test 4: Default timeout (120s)**
- Dispatch without explicit timeout to a slow model
- Expected: if model takes > 120s, clean timeout error
- Pass criteria: no indefinite hang

**Test 5: Empty response detection**
- If a model returns empty response, detect it
- Expected: "Empty response from provider/model" error with recovery hints
- Pass criteria: no hang, clear error

**Test 6: Backward compatibility**
- Dispatch with explicit `timeout: 30` to a connected model
- Expected: works as before, respects explicit timeout
- Pass criteria: response or timeout error within 30s

**Test 7: Batch dispatch with mixed providers**
- Batch dispatch with one connected + one disconnected provider
- Expected: connected model succeeds or times out, disconnected model shows error
- Pass criteria: `Promise.allSettled` returns both results

### Edge Cases

- All providers disconnected — batch returns "None of the target providers are connected"
- Provider list endpoint unavailable — silently skip pre-flight, proceed to prompt
- Server healthy but no providers configured — connected array is empty, skip pre-flight
- Model valid but slow (>120s) — default timeout fires, clean error
- `timeout: 0.5` (very short) — validates as positive, fires quickly

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style
```bash
cd .opencode && bun build --no-bundle tools/dispatch.ts 2>&1 | head -5
cd .opencode && bun build --no-bundle tools/batch-dispatch.ts 2>&1 | head -5
cd .opencode && bun build --no-bundle tools/_test-dispatch.ts 2>&1 | head -5
```

### Level 2: Type Safety
```bash
cd .opencode && bun -e "import t from './tools/dispatch.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"
cd .opencode && bun -e "import t from './tools/batch-dispatch.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"
```

### Level 3: Unit Tests
```
N/A — no unit test framework for custom tools
```

### Level 4: Integration Tests
```bash
cd .opencode && bun run tools/_test-dispatch.ts 2>&1
```

### Level 5: Manual Validation

**Prerequisites:**
1. `opencode serve --port 4096` running in a separate terminal
2. At least one provider connected

**Test script:**
```
1. Run diagnostic test: cd .opencode && bun run tools/_test-dispatch.ts
   - Verify connected providers listed
   - Verify prompt to connected model succeeds or times out cleanly
   - Verify bad provider returns error immediately
   - Verify no indefinite hangs

2. Build check:
   - bun build --no-bundle tools/dispatch.ts → clean
   - bun build --no-bundle tools/batch-dispatch.ts → clean

3. If connected model returned text, verify the response format:
   - Response starts with "--- dispatch response from provider/model ---"
   - Response includes duration
   - Response includes actual text from the model
```

### Level 6: Additional Validation (Optional)

```bash
# Verify tools still register in OpenCode
curl -s http://127.0.0.1:4096/experimental/tool/ids 2>/dev/null | grep -o "dispatch"
```

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] `_test-dispatch.ts` rewritten with connected-provider discovery
- [x] `getConnectedProviders` helper added to dispatch.ts
- [x] `DEFAULT_TIMEOUT_SECONDS = 120` constant added to dispatch.ts
- [x] Provider pre-flight check added after health check in dispatch.ts
- [x] Mandatory default timeout (120s) applied when no timeout arg specified
- [x] `controller` and `timeoutId` are always defined (not optional)
- [x] Empty-response detection added between prompt and extraction in dispatch.ts
- [x] Empty-response error includes actionable recovery hints
- [x] Same three fixes applied to batch-dispatch.ts
- [x] Batch pre-flight only blocks when ALL providers are disconnected
- [x] Both tools build without errors: `bun build`
- [x] Backward compatible: explicit `timeout` still works, explicit `provider`/`model` still works
- [x] No changes to TASK_ROUTING, command markdown, or agent config

### Runtime (verify after live testing)

- [x] Diagnostic test lists connected providers
- [x] Dispatch to connected model returns text response (or times out cleanly)
- [x] Dispatch to non-existent provider fails fast with provider-not-connected error
- [x] No dispatch call hangs indefinitely (120s max)
- [x] Empty responses are caught with actionable error
- [x] Batch dispatch handles mixed connected/disconnected providers

---

## COMPLETION CHECKLIST

- [x] All tasks completed in order
- [x] Each task validation passed
- [x] All validation commands executed successfully
- [x] Diagnostic test script produces meaningful output
- [x] No indefinite hangs in any test scenario
- [x] Both tools build clean
- [x] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Raw `fetch` for provider discovery instead of SDK client**: The SDK's `provider.list()` method may return a different shape than the raw HTTP endpoint. Using `fetch` directly is more reliable and doesn't depend on SDK method availability.
- **Default timeout of 120s**: Generous enough for slow models (Qwen thinking, Gemini Pro) but prevents indefinite hangs. The SDK's `req.timeout = false` is the root cause of hangs — our default timeout is the safety net.
- **Provider pre-flight is non-blocking**: If `/provider` endpoint fails, we proceed to the prompt call. Better to try and fail with a specific error than block on a pre-flight that itself is broken.
- **Empty response detection before extraction**: Catching `{ data: {} }` early avoids confusing "No text parts" warnings. The empty pattern is a specific failure mode (model not responding) that deserves its own error message.
- **No `promptAsync` in this slice**: The synchronous `session.prompt()` with timeout is sufficient. The async+SSE path is more complex and would change the tool's contract (fire-and-forget vs sync response). Defer to future slice if needed.

### Risks

- **No connected providers**: If the user hasn't `/connect`ed any providers, all dispatches will fail. Mitigation: actionable error message with `/connect` instructions.
- **Provider list endpoint returns unexpected shape**: Different OpenCode server versions may return different shapes. Mitigation: defensive parsing with fallback to empty array.
- **Default timeout too short for some models**: 120s may not be enough for models doing deep reasoning (Claude Opus, Gemini thinking). Mitigation: the caller can always specify a longer timeout via the `timeout` arg.
- **Empty response pattern may change**: The `{ data: {} }` pattern is observed behavior, not documented. If the server changes, our detection may miss it. Mitigation: the extraction logic still has fallback warnings for other unexpected shapes.

### SDK Internals Summary (from research)

| Aspect | Detail |
|--------|--------|
| `session.prompt()` endpoint | `POST /session/{sessionID}/message` |
| Blocking behavior | Synchronous — waits for full AI response |
| Timeout | Explicitly disabled (`req.timeout = false`) |
| Response shape (success) | `{ data: { info: AssistantMessage, parts: Part[] }, response: Response, error: undefined }` |
| Response shape (failure) | `{ data: {}, error: undefined }` — NO throw, NO error field |
| `session.promptAsync()` endpoint | `POST /session/{sessionID}/prompt_async` — returns 204 immediately |
| SSE events | `client.event.subscribe()` → `GET /event` — for tracking async prompt progress |
| v2 param decomposition | `buildClientParams` splits `{ sessionID, model, parts }` into `{ path: { sessionID }, body: { model, parts } }` |

### Confidence Score: 8/10

- **Strengths**: Root cause identified (SDK timeout disabled + synchronous POST). Fix is straightforward (default timeout + provider check + empty detection). All SDK internals researched with exact line numbers. Solution is backward compatible. Three clear, independently testable changes.
- **Uncertainties**: Don't know which providers are actually connected (diagnostic test will reveal). Don't know if the connected model will respond (depends on auth and provider availability). Empty response pattern is observed, not documented.
- **Mitigations**: Diagnostic test runs first (task 1-2) before code changes. All checks are non-blocking with fallbacks. Default timeout guarantees no indefinite hang regardless of model behavior.
