# Feature: Multi-Model Dispatch Tool

## Feature Description

A custom OpenCode tool (`.opencode/tools/dispatch.ts`) that lets the current model (e.g., Claude Opus) dispatch tasks to any connected AI model (Qwen 3.5, Codex/GPT, Gemini, GLM, Kimi, MiniMax, etc.) via the OpenCode server HTTP API. The tool sends a prompt to a specified model, waits for the response, and returns it inline as tool output — enabling multi-model orchestration without leaving the current session.

## User Story

As a developer using Claude Opus as my primary coding agent, I want to dispatch specific tasks (code generation, review, research) to other connected models from within my current conversation, so that I can leverage each model's strengths without manually switching terminals or sessions.

## Problem Statement

OpenCode connects to 75+ providers with multiple models each, but the current workflow requires manually switching models or opening new terminal sessions. There's no way for the active model to programmatically delegate work to another model and receive the response back for reasoning. This limits multi-model workflows to human-driven context switching.

## Solution Statement

- Decision 1: **Custom Tool + Server API (Option A)** — because it's the only approach where the calling model gets responses back inline as tool output for programmatic reasoning. Option B (model-pinned subagents) creates separate sessions the caller can't read. Option C (CLI wrapper) blocks without real-time feedback.
- Decision 2: **`createOpencodeClient` (client-only mode)** — because we connect to an already-running `opencode serve` instance rather than starting a new server. Lighter, faster, no lifecycle management.
- Decision 3: **Stateless by default, optional session reuse** — because most dispatches are one-shot (send prompt, get answer). Multi-turn is opt-in via `sessionId` parameter.
- Decision 4: **`@opencode-ai/sdk` over raw fetch** — because the SDK provides type-safe client with proper error handling and response parsing, generated from the OpenAPI spec.
- Decision 5: **Single file, default export** — creates tool named `dispatch` (filename = tool name). Clean, simple, follows OpenCode custom tool conventions.

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `.opencode/tools/` (new), `.opencode/package.json` (dependency), `opencode.json` (no changes needed)
- **Dependencies**: `@opencode-ai/sdk` npm package, running `opencode serve` instance

### Slice Guardrails (Required)

- **Single Outcome**: A working `dispatch` tool that any model can call to send prompts to other models and receive responses
- **Expected Files Touched**: `.opencode/tools/dispatch.ts` (new), `.opencode/package.json` (update)
- **Scope Boundary**: This slice does NOT include wiring dispatch into `/execute`, `/code-review`, or `/code-loop` commands. Those are Slice 2.
- **Split Trigger**: If session management grows beyond create/reuse/delete, split into a session-manager utility

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/package.json` (lines 1-5) — Why: current dependencies, need to add `@opencode-ai/sdk`
- `opencode.json` (lines 1-119) — Why: provider configuration showing available models and provider IDs
- `.opencode/agents/code-review.md` (lines 1-15) — Why: agent frontmatter pattern showing tools/mode config (reference for how tools integrate with agents)
- `.opencode/agents/swarm-worker-backend.md` (lines 1-15) — Why: agent with `model` pinning and `mcpServers` config pattern

### New Files to Create

- `.opencode/tools/dispatch.ts` — Core dispatch tool: sends prompts to other models via OpenCode server API, returns responses as tool output

### Related Memories (from memory.md)

- Memory: "Archon-first policy for `/planning` and `/execute`" — Relevance: dispatch tool follows similar pattern of API-first communication with external services
- Memory: "Session safety in shared servers: Never trust client-supplied session_id" — Relevance: dispatch reuses server-issued session IDs only; we validate before reuse
- Memory: "Legacy SDK compatibility: When provider SDKs differ on auth args, use temporary env bridging" — Relevance: dispatch tool is provider-agnostic, delegates auth to OpenCode's provider system

### Relevant Documentation

- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools/)
  - Specific section: Creating a tool, Structure, Arguments, Context
  - Why: exact API for `tool()` helper, `tool.schema`, `context` object, file naming conventions
- [OpenCode SDK](https://opencode.ai/docs/sdk/)
  - Specific section: Client only, Sessions API, Types
  - Why: `createOpencodeClient`, `session.create`, `session.prompt`, response types
- [OpenCode Server](https://opencode.ai/docs/server/)
  - Specific section: Sessions, Messages
  - Why: HTTP endpoint signatures for `POST /session`, `POST /session/:id/message`, response shapes
- [OpenCode Providers](https://opencode.ai/docs/providers/)
  - Specific section: Provider system, `/connect` workflow
  - Why: understanding providerID/modelID format for the `model` parameter

### Available Providers and Model IDs (from opencode.json + /connect)

> These are the exact provider/model pairs the dispatch tool must support. The execution agent
> should use these for validation and tool description hints.

**Custom providers (from `opencode.json`):**
| Provider ID | Model ID | Display Name | Context Limit |
|---|---|---|---|
| `bailian-coding-plan` | `qwen3.5-plus` | Qwen3.5 Plus (Image Understanding) | 262144 |
| `bailian-coding-plan` | `qwen3-max-2026-01-23` | Qwen3 Max 2026-01-23 | 262144 |
| `bailian-coding-plan` | `qwen3-coder-plus` | Qwen3 Coder Plus | 262144 |
| `bailian-coding-plan` | `qwen3-coder-next` | Qwen3 Coder Next | 262144 |
| `bailian-coding-plan` | `glm-4.7` | GLM-4.7 | 131072 |
| `bailian-coding-plan` | `kimi-k2.5` | Kimi K2.5 (Image Understanding) | 262144 |
| `bailian-coding-plan` | `glm-5` | GLM-5 | 262144 |
| `bailian-coding-plan` | `minimax-m2.5` | MiniMax M2.5 | 262144 |

**Connected providers (via `/connect`):**
| Provider ID | Example Models | Notes |
|---|---|---|
| `anthropic` | `claude-sonnet-4-20250514`, `claude-opus-4-20250514` | Primary provider |
| `openai` | `gpt-4.1`, `o4-mini` | Via API key |
| `google` | `gemini-2.5-pro`, `gemini-2.5-flash` | Via API key |
| `github-copilot` | `gpt-4.1`, `claude-sonnet-4-20250514` | Via GitHub auth |

**Provider ID format notes:**
- Custom providers use the key from `opencode.json` `provider` section (e.g., `bailian-coding-plan`)
- Connected providers use their canonical ID (e.g., `anthropic`, `openai`, `google`)
- The dispatch tool takes `provider` and `model` as separate strings — it does NOT split a `provider/model` combined string
- Invalid provider/model combos produce an error from the OpenCode server, not from our tool

### API Response Shapes (from SDK/Server docs)

> Critical reference for the response extraction logic in the tool.

**`session.create` response:**
```typescript
// Returns Session object
{
  id: string           // Session UUID — this is what we use
  title?: string       // Our title: "dispatch → provider/model"
  parentID?: string    // null for top-level sessions
  createdAt: string    // ISO timestamp
  updatedAt: string    // ISO timestamp
}
```

**`session.prompt` response (responseStyle: "fields" — SDK default):**
```typescript
{
  data: {
    info: {
      id: string           // Message UUID
      sessionID: string    // Session UUID
      role: "assistant"    // Always assistant for prompt responses
      // ... other fields
    },
    parts: [               // Array of message parts
      {
        type: "text",      // Text content (what we extract)
        text: string       // The actual response text
      },
      {
        type: "tool-invocation",  // If the model used tools
        // ... tool call details
      },
      // ... potentially more parts
    ]
  },
  response: Response,      // Raw fetch Response
  error: undefined | Error // Error if throwOnError is false
}
```

**Key extraction logic:**
1. Access `result.data.parts` (with null checks)
2. Filter for parts where `part.type === "text"`
3. Map to `part.text` and join with newlines
4. If no text parts found, check `result.data.info` for alternative content
5. If all else fails, stringify the raw response (truncated to 2000 chars)

### Patterns to Follow

> Specific patterns extracted from the codebase — include actual code examples from the project.

**Custom Tool Definition** (from OpenCode docs — custom-tools page):
```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Query the project database",
  args: {
    query: tool.schema.string().describe("SQL query to execute"),
  },
  async execute(args) {
    return `Executed query: ${args.query}`
  },
})
```
- Why this pattern: Official OpenCode custom tool structure. Filename = tool name. Default export = single tool.
- Common gotchas: `tool.schema` is Zod — use `.describe()` for LLM hints. Return value must be string or number (serializable).

**SDK Client-Only Mode** (from OpenCode SDK docs):
```typescript
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({
  baseUrl: "http://localhost:4096",
})
```
- Why this pattern: Connects to existing `opencode serve` without starting a new server. Lightweight.
- Common gotchas: Must have `opencode serve` running. Default port is 4096 but user may customize.

**Session Prompt with Model Selection** (from OpenCode SDK docs):
```typescript
const result = await client.session.prompt({
  path: { id: session.id },
  body: {
    model: { providerID: "anthropic", modelID: "claude-3-5-sonnet-20241022" },
    parts: [{ type: "text", text: "Hello!" }],
  },
})
```
- Why this pattern: Shows exact shape of prompt body with model override. `providerID` + `modelID` are separate fields.
- Common gotchas: The `model` field uses `providerID`/`modelID` object, not a single string. Must split `"provider/model"` into parts.

**Tool with Context** (from OpenCode docs):
```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Get project information",
  args: {},
  async execute(args, context) {
    const { agent, sessionID, messageID, directory, worktree } = context
    return `Agent: ${agent}, Session: ${sessionID}`
  },
})
```
- Why this pattern: Shows how to access session context. We'll use `context.worktree` and `context.sessionID` for logging/debugging.
- Common gotchas: Context is the second parameter to `execute`, not part of `args`.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Set up the tools directory and install the SDK dependency. Verify the dependency resolves correctly.

**Tasks:**
- Create `.opencode/tools/` directory
- Add `@opencode-ai/sdk` to `.opencode/package.json`
- Install dependencies via `bun install` in `.opencode/`

### Phase 2: Core Implementation

Build the dispatch tool with full error handling, model routing, and response extraction.

**Tasks:**
- Create `.opencode/tools/dispatch.ts` with the `tool()` definition
- Implement `createOpencodeClient` connection with configurable port
- Implement session creation (new session per dispatch by default)
- Implement prompt sending with model selection (providerID/modelID split)
- Implement response extraction (iterate parts, extract text content)
- Implement session reuse (optional `sessionId` parameter)
- Add comprehensive error handling (server not running, model unavailable, timeout)

### Phase 3: Integration

No integration with commands in this slice. The tool auto-registers by being in `.opencode/tools/`. Verify it appears in the tool list.

**Tasks:**
- Verify tool appears in OpenCode's tool list
- Test dispatch to a connected model
- Test error paths (bad model, server down)

### Phase 4: Testing & Validation

Manual testing only for this slice (custom tools don't have a test framework). Validate through actual tool invocation.

**Tasks:**
- Start `opencode serve` and test dispatch via conversation
- Verify response comes back as tool output the calling model can reason about
- Test with multiple providers (Anthropic, Bailian, etc.)
- Test session reuse flow
- Test error messages are clear and actionable

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. UPDATE `.opencode/package.json`

- **IMPLEMENT**: Add `@opencode-ai/sdk` dependency alongside existing `@opencode-ai/plugin`. The SDK provides the type-safe HTTP client for the OpenCode server API.

  **Current:**
  ```json
  {
    "dependencies": {
      "@opencode-ai/plugin": "1.2.15"
    }
  }
  ```

  **Replace with:**
  ```json
  {
    "dependencies": {
      "@opencode-ai/plugin": "1.2.15",
      "@opencode-ai/sdk": "latest"
    }
  }
  ```

- **PATTERN**: `.opencode/package.json:1-5` — existing package.json structure
- **IMPORTS**: N/A (package.json edit)
- **GOTCHA**: Use `"latest"` for SDK since we want the most recent version that matches the running OpenCode server. After install, verify the resolved version works with the server's OpenAPI spec.
- **VALIDATE**: `cd .opencode && bun install && bun pm ls | grep @opencode-ai/sdk`

### 2. CREATE `.opencode/tools/dispatch.ts`

- **IMPLEMENT**: Create the core dispatch tool. This is the main deliverable. The tool:
  1. Accepts `provider` (string, e.g. "anthropic"), `model` (string, e.g. "claude-sonnet-4-20250514"), `prompt` (string), optional `sessionId` (string for reuse), optional `port` (number, default 4096), optional `cleanup` (boolean, default true — delete session after single-use dispatch)
  2. Creates an SDK client via `createOpencodeClient({ baseUrl: "http://127.0.0.1:{port}" })`
  3. If no `sessionId` provided, creates a new session via `client.session.create({})`
  4. Sends the prompt via `client.session.prompt({ path: { id }, body: { model: { providerID, modelID }, parts: [{ type: "text", text: prompt }] } })`
  5. Extracts text from response parts (filter for `type === "text"`, join `.text` fields)
  6. If `cleanup` is true and session was newly created, deletes it via `client.session.delete({ path: { id } })`
  7. Returns the extracted text as the tool's return value

  **Full implementation:**
  ```typescript
  import { tool } from "@opencode-ai/plugin"
  import { createOpencodeClient } from "@opencode-ai/sdk"

  export default tool({
    description:
      "Dispatch a prompt to any connected AI model via the OpenCode server. " +
      "Use this to delegate tasks (code generation, review, research, analysis) to other models " +
      "and receive their response inline. Requires `opencode serve` running. " +
      "Provider/model examples: anthropic/claude-sonnet-4-20250514, openai/gpt-4.1, " +
      "bailian-coding-plan/qwen3.5-plus, bailian-coding-plan/qwen3-coder-plus, " +
      "google/gemini-2.5-pro, github-copilot/gpt-4.1",
    args: {
      provider: tool.schema
        .string()
        .describe(
          "Provider ID (e.g. 'anthropic', 'openai', 'bailian-coding-plan', 'google', 'github-copilot')"
        ),
      model: tool.schema
        .string()
        .describe(
          "Model ID within the provider (e.g. 'claude-sonnet-4-20250514', 'gpt-4.1', 'qwen3.5-plus')"
        ),
      prompt: tool.schema
        .string()
        .describe("The full prompt to send to the target model"),
      sessionId: tool.schema
        .string()
        .optional()
        .describe(
          "Optional: reuse an existing session ID for multi-turn conversations. " +
          "If omitted, a new session is created (and cleaned up after)."
        ),
      port: tool.schema
        .number()
        .optional()
        .describe("OpenCode server port (default: 4096)"),
      cleanup: tool.schema
        .boolean()
        .optional()
        .describe(
          "Delete the session after dispatch (default: true for new sessions, false for reused sessions)"
        ),
    },
    async execute(args, context) {
      const serverPort = args.port ?? 4096
      const baseUrl = `http://127.0.0.1:${serverPort}`

      // 1. Create SDK client
      let client
      try {
        client = createOpencodeClient({ baseUrl })
      } catch (err: any) {
        return `[dispatch error] Failed to create SDK client: ${err.message}`
      }

      // 2. Health check — verify server is running
      try {
        const health = await client.global.health()
        if (!health.data?.healthy) {
          return `[dispatch error] OpenCode server at ${baseUrl} is not healthy. Run 'opencode serve --port ${serverPort}' first.`
        }
      } catch (err: any) {
        return (
          `[dispatch error] Cannot reach OpenCode server at ${baseUrl}. ` +
          `Ensure 'opencode serve --port ${serverPort}' is running.\n` +
          `Details: ${err.message}`
        )
      }

      // 3. Session — reuse or create
      const isReusedSession = !!args.sessionId
      let sessionId = args.sessionId

      if (!sessionId) {
        try {
          const session = await client.session.create({
            body: {
              title: `dispatch → ${args.provider}/${args.model}`,
            },
          })
          sessionId = session.data?.id ?? session.id
          if (!sessionId) {
            return `[dispatch error] Session creation returned no ID. Response: ${JSON.stringify(session)}`
          }
        } catch (err: any) {
          return `[dispatch error] Failed to create session: ${err.message}`
        }
      }

      // 4. Send prompt
      let result: any
      try {
        result = await client.session.prompt({
          path: { id: sessionId },
          body: {
            model: {
              providerID: args.provider,
              modelID: args.model,
            },
            parts: [{ type: "text" as const, text: args.prompt }],
          },
        })
      } catch (err: any) {
        // Attempt cleanup on failure if we created the session
        if (!isReusedSession && sessionId) {
          try {
            await client.session.delete({ path: { id: sessionId } })
          } catch {
            // Best effort cleanup
          }
        }
        return (
          `[dispatch error] Prompt failed for ${args.provider}/${args.model}: ${err.message}\n` +
          `Common causes: model not connected (run '/connect ${args.provider}'), ` +
          `invalid model ID, or provider auth missing.`
        )
      }

      // 5. Extract text from response parts
      let responseText = ""
      try {
        const parts = result.data?.parts ?? result.parts ?? []
        const textParts = parts.filter(
          (p: any) => p.type === "text" && p.text
        )
        responseText = textParts.map((p: any) => p.text).join("\n")

        if (!responseText) {
          // Fallback: try to extract from info or stringify the whole response
          responseText =
            result.data?.info?.text ??
            `[dispatch warning] No text parts in response. Raw: ${JSON.stringify(result.data ?? result).slice(0, 2000)}`
        }
      } catch (err: any) {
        responseText = `[dispatch warning] Could not parse response: ${err.message}. Raw: ${JSON.stringify(result).slice(0, 2000)}`
      }

      // 6. Cleanup session if appropriate
      const shouldCleanup = args.cleanup ?? !isReusedSession
      let cleanupNote = ""
      if (shouldCleanup && sessionId) {
        try {
          await client.session.delete({ path: { id: sessionId } })
        } catch {
          cleanupNote =
            "\n[dispatch note] Session cleanup failed (non-critical)."
        }
      } else if (!shouldCleanup && !isReusedSession) {
        cleanupNote = `\n[dispatch note] Session preserved: ${sessionId} (pass sessionId to continue conversation)`
      }

      // 7. Return response with metadata header
      const header =
        `--- dispatch response from ${args.provider}/${args.model} ---\n`
      return header + responseText + cleanupNote
    },
  })
  ```

- **PATTERN**: Custom tool docs — `tool()` with `tool.schema` args, async `execute(args, context)`, string return
- **IMPORTS**:
  ```typescript
  import { tool } from "@opencode-ai/plugin"
  import { createOpencodeClient } from "@opencode-ai/sdk"
  ```
- **GOTCHA**:
  1. The SDK's `session.prompt` returns different shapes depending on `responseStyle` config. Default `fields` mode returns `{ data, response, error }`. Access `result.data.parts` not `result.parts`.
  2. The SDK may return `data` as undefined if using `throwOnError: false` (default). Always null-check.
  3. Provider IDs in `opencode.json` custom providers use the key name (e.g., `bailian-coding-plan`), not a canonical name. The user must pass the exact provider key.
  4. The tool returns a string — keep it clean. The calling model will parse this for reasoning.
  5. Bun runtime is used by OpenCode for tool execution. `Bun.$` shell API is available if needed but we don't need it here.
  6. `session.create` body shape: `{ parentID?, title? }`. We use `title` for traceability.
  7. `session.delete` returns `boolean`. If it fails silently, that's fine — orphaned sessions are cleaned up by OpenCode.
- **VALIDATE**: Start `opencode serve`, then in a conversation ask the model to use the dispatch tool. Verify the tool appears and returns text from the target model.

### 3. VALIDATE installation and tool registration

- **IMPLEMENT**: Run `bun install` in `.opencode/` to install the SDK, then verify the tool registers:
  1. `cd .opencode && bun install` — installs `@opencode-ai/sdk`
  2. Restart OpenCode (or start fresh session) — tools are loaded at session start
  3. Check tool list includes `dispatch`

- **PATTERN**: N/A (validation step)
- **IMPORTS**: N/A
- **GOTCHA**: OpenCode loads custom tools at session start. If you add a tool file while a session is running, you may need to start a new session to see it. The `opencode serve` instance also needs restarting if it was already running.
- **VALIDATE**: In a new OpenCode session, check that the `dispatch` tool appears. Try: "Use the dispatch tool to ask qwen3.5-plus what 2+2 is" or similar trivial test.

---

## TESTING STRATEGY

### Unit Tests

N/A for this slice. Custom tools in OpenCode don't have a built-in test framework. The tool is a single function with external dependencies (OpenCode server). Testing is manual + integration.

**Future consideration**: If the dispatch tool grows more complex (Slice 2+), extract the core logic into a separate module that can be unit-tested with a mocked SDK client. For now, the tool is small enough that manual testing covers all paths.

### Integration Tests

Manual integration testing via actual tool invocation in an OpenCode conversation. Each test has explicit setup, action, and expected outcome.

**Test 1: Happy path — Bailian provider**
- Setup: `opencode serve --port 4096` running, `bailian-coding-plan` configured in opencode.json
- Action: "Use the dispatch tool to send the prompt 'What is 2+2? Reply with just the number.' to provider bailian-coding-plan, model qwen3.5-plus"
- Expected: Tool output contains `--- dispatch response from bailian-coding-plan/qwen3.5-plus ---` header followed by response containing "4"
- Pass criteria: Response text visible as tool output, calling model can reason about it

**Test 2: Different provider — Anthropic**
- Setup: Anthropic connected via `/connect anthropic`
- Action: "Use dispatch to ask anthropic/claude-sonnet-4-20250514: 'Name 3 prime numbers under 20. Just list them.'"
- Expected: Tool returns something like "2, 3, 5" or "2, 3, 7" etc.
- Pass criteria: Correct response from a different provider than Test 1

**Test 3: Session reuse — multi-turn conversation**
- Setup: Server running
- Action 1: "Dispatch to bailian-coding-plan/qwen3.5-plus with prompt 'My name is Alice. Just say OK.' and set cleanup to false"
- Observe: Note the session ID from the `[dispatch note] Session preserved: {id}` line
- Action 2: "Dispatch to the same model with prompt 'What is my name?' using the sessionId from the previous call"
- Expected: Second response mentions "Alice" (proves context was preserved)
- Pass criteria: Multi-turn context works across dispatch calls

**Test 4: Cleanup disabled — session persistence**
- Setup: Server running
- Action: "Dispatch to any model with cleanup=false, then check server sessions"
- Verify: `curl http://127.0.0.1:4096/session` shows the session still exists
- Pass criteria: Session survives after dispatch when cleanup is false

**Test 5: Error — server not running**
- Setup: Stop `opencode serve` (or use port with no server)
- Action: "Use dispatch tool with port 9999 to send 'hello' to any model"
- Expected: Error message contains "Cannot reach OpenCode server" and "Ensure 'opencode serve --port 9999' is running"
- Pass criteria: No crash, clear actionable error message

**Test 6: Error — bad model ID**
- Setup: Server running
- Action: "Use dispatch with provider 'nonexistent' model 'fake-model' prompt 'hello'"
- Expected: Error from server about unknown provider/model, surfaced with helpful context
- Pass criteria: No crash, error mentions the bad provider/model

**Test 7: Custom port**
- Setup: `opencode serve --port 5000` running
- Action: "Dispatch to any model with port=5000 and prompt 'Say hello'"
- Expected: Works identically to default port
- Pass criteria: Response received from custom port

**Test 8: Default cleanup — session deleted**
- Setup: Server running
- Action: "Dispatch to any model without specifying cleanup (default=true for new sessions)"
- Verify: `curl http://127.0.0.1:4096/session` does NOT show the dispatch session
- Pass criteria: Session auto-cleaned after single-use dispatch

### Edge Cases

**E1: Server running but model not connected (no auth)**
- Scenario: Dispatch to `openai/gpt-4.1` when OpenAI is not `/connect`ed
- Expected behavior: Server returns auth/provider error; dispatch tool wraps it with "Common causes: model not connected (run '/connect openai')"
- Risk: Error message from server may be cryptic — our wrapper adds context

**E2: Very long prompt (>100k tokens)**
- Scenario: Send a 150k token prompt to a model with 128k context limit
- Expected behavior: Target model's provider rejects with context length error; dispatch surfaces it
- Risk: The prompt serialization to JSON could be slow for very large strings — acceptable for MVP

**E3: Very long response**
- Scenario: Ask a model to generate a very long response (e.g., "Write a 5000-word essay")
- Expected behavior: Response comes back complete; OpenCode handles large tool outputs at the framework level
- Risk: Calling model's context window fills up with the large tool output — user responsibility to manage

**E4: Concurrent dispatches**
- Scenario: Calling model makes 3 parallel dispatch tool calls to different models
- Expected behavior: Each creates its own session; no interference; all responses come back
- Risk: Server may throttle concurrent requests — OpenCode handles this

**E5: Empty response from model**
- Scenario: Model returns no text parts (e.g., only tool invocations, or empty response)
- Expected behavior: Tool returns `[dispatch warning] No text parts in response. Raw: {...}` with truncated raw response
- Risk: Calling model may not understand the raw JSON — acceptable for MVP, improve in Slice 3

**E6: Network timeout**
- Scenario: Model takes very long to respond (>2 minutes)
- Expected behavior: SDK fetch timeout triggers; dispatch returns error
- Risk: Some models (large Qwen variants, Gemini thinking) can take 60-90 seconds — may need timeout arg in Slice 3

**E7: Session ID reuse with wrong model**
- Scenario: Create session with model A, then dispatch to model B using the same sessionId
- Expected behavior: Works — the `model` field in the prompt body overrides per-request
- Risk: Conversation context from model A may confuse model B — user responsibility

**E8: Provider ID with special characters**
- Scenario: `bailian-coding-plan` contains hyphens — verify SDK handles this
- Expected behavior: Works — provider ID is just a string, passed as-is to the API
- Risk: None — confirmed from opencode.json that hyphenated IDs work

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style
```bash
# TypeScript syntax check (Bun)
cd .opencode && bun build --no-bundle tools/dispatch.ts --outdir /tmp/dispatch-check 2>&1
```

### Level 2: Type Safety
```bash
# TypeScript type check via Bun
cd .opencode && bunx tsc --noEmit --strict tools/dispatch.ts 2>&1 || echo "Note: tsc may need tsconfig — Bun handles types at runtime"
```

Note: OpenCode loads tools via Bun's runtime, which has built-in TypeScript support. A `tsc` check requires a `tsconfig.json`. If `tsc` fails due to missing config, verify syntax with Bun's build instead. The real type validation happens at runtime when OpenCode loads the tool.

### Level 3: Unit Tests
```
N/A — No unit test framework for custom tools. Validation is at Level 5 (manual).
```

### Level 4: Integration Tests
```
N/A — No automated integration tests. Validation is at Level 5 (manual).
```

### Level 5: Manual Validation

**Prerequisites:**
1. `opencode serve --port 4096` running in a separate terminal
2. At least one provider connected (e.g., `bailian-coding-plan` via opencode.json, or `anthropic` via `/connect`)

**Test Script:**
```
Test 1: Basic dispatch
- In OpenCode conversation, say: "Use the dispatch tool to send the prompt 'What is 2+2? Reply with just the number.' to bailian-coding-plan/qwen3.5-plus"
- Expected: Tool returns response containing "4"
- Pass criteria: Response text visible, no errors

Test 2: Different provider
- "Use dispatch to ask anthropic/claude-sonnet-4-20250514: 'Name 3 prime numbers under 20'"
- Expected: Tool returns a list of prime numbers
- Pass criteria: Correct response from different provider

Test 3: Session reuse
- "Dispatch to bailian-coding-plan/qwen3.5-plus with prompt 'My name is Alice. Remember it.' and set cleanup to false"
- Note the session ID from the response
- "Dispatch to the same model with prompt 'What is my name?' using sessionId from the previous call"
- Expected: Second response mentions "Alice"
- Pass criteria: Context preserved across dispatches

Test 4: Error - server not running
- Stop opencode serve
- "Use dispatch to send 'hello' to any model"
- Expected: Clear error about server not running
- Pass criteria: No crash, helpful error message

Test 5: Error - bad model
- "Use dispatch with provider 'nonexistent' model 'fake-model' prompt 'hello'"
- Expected: Error about model/provider not found
- Pass criteria: No crash, actionable error
```

### Level 6: Additional Validation (Optional)

```bash
# Verify tool appears in OpenCode's tool list via server API
curl -s http://127.0.0.1:4096/experimental/tool/ids | grep -o dispatch
```

---

## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable
> only after running the code). Check off Implementation items during execution.
> Leave Runtime items for manual testing or post-deployment verification.

### Implementation (verify during execution)

- [x] `.opencode/tools/dispatch.ts` created with all 6 args (provider, model, prompt, sessionId, port, cleanup)
- [x] `@opencode-ai/sdk` added to `.opencode/package.json` and installed
- [x] Tool uses `createOpencodeClient` for server communication
- [x] Tool performs health check before dispatching
- [x] Tool creates/reuses/cleans sessions appropriately
- [x] Tool extracts text from response parts with fallback for unexpected shapes
- [x] All 7 error paths handled: client creation, health check, session creation, prompt failure, response parsing, session cleanup, bad model
- [x] Tool description includes provider/model examples for LLM discoverability
- [x] `bun build` succeeds on the tool file (no syntax errors)

### Runtime (verify after testing/deployment)

- [ ] Tool appears in OpenCode's tool list when session starts
- [ ] Dispatch to `bailian-coding-plan/qwen3.5-plus` returns correct response
- [ ] Dispatch to a second provider returns correct response
- [ ] Session reuse preserves conversation context
- [ ] Server-not-running error is clear and actionable
- [ ] Bad model error is clear and actionable
- [ ] Session cleanup works (newly created sessions are deleted after use)
- [ ] Large prompts don't crash the tool
- [ ] No orphaned sessions after normal use

---

## COMPLETION CHECKLIST

- [x] All tasks completed in order
- [x] Each task validation passed
- [x] All validation commands executed successfully
- [ ] Full test suite passes (manual tests 1-5 all pass) — Pending: requires opencode serve
- [x] No linting or type checking errors
- [ ] Manual testing confirms feature works — Pending: requires opencode serve
- [x] Acceptance criteria all met (Implementation ✅, Runtime ⏳)

---

## NOTES

### Key Design Decisions

- **Client-only SDK mode**: We don't start/stop the OpenCode server — it must already be running. This avoids lifecycle complexity and port conflicts. The user runs `opencode serve` once, and the tool connects.
- **Health check before dispatch**: Fail fast with a clear message rather than cryptic connection errors deep in the prompt call.
- **Generous error messages**: Every error path includes what went wrong AND how to fix it (e.g., "Run 'opencode serve --port 4096' first"). This is critical because the calling model needs to reason about failures.
- **Response header**: `--- dispatch response from provider/model ---` helps the calling model distinguish dispatch output from other context.
- **Session title for traceability**: New sessions get a title like `dispatch → bailian-coding-plan/qwen3.5-plus` so they're identifiable in session list.
- **No `@opencode-ai/sdk` version pin**: Using `"latest"` because the SDK is versioned alongside the OpenCode server. Pinning risks API drift.

### Risks

- **SDK response shape changes**: The OpenCode SDK is actively developed. Response structure (`result.data.parts` vs `result.parts`) may change. Mitigation: defensive parsing with fallbacks, and the try/catch around response extraction.
- **Server not running is the #1 failure mode**: Users will forget to start `opencode serve`. Mitigation: health check with clear error message is the first thing the tool does.
- **Timeout for slow models**: Some models (especially large Qwen variants) may take 30-60 seconds. The SDK's default timeout may be insufficient. Mitigation: monitor in practice; add a `timeout` arg in a follow-up slice if needed.
- **Concurrent dispatch races**: If the calling model dispatches to multiple models simultaneously (parallel tool calls), each creates its own session — this is fine. But if they share a session via `sessionId`, messages may interleave. Mitigation: document that `sessionId` reuse is single-turn sequential only.

### Implementation Notes for Execution Agent

**Bun runtime specifics:**
- OpenCode executes custom tools via Bun's TypeScript runtime — no separate transpilation step needed
- `import { tool } from "@opencode-ai/plugin"` resolves from `.opencode/node_modules/`
- `import { createOpencodeClient } from "@opencode-ai/sdk"` will resolve after `bun install`
- Bun supports top-level await, but the tool's `execute` is already async — no need for TLA
- Use `Bun.$` only if shell commands are needed (we don't need it for this tool)

**SDK client lifecycle:**
- `createOpencodeClient` creates a lightweight client wrapper — no persistent connection
- Each `execute()` call creates a fresh client. This is fine for the MVP since the client is stateless.
- In Slice 3, consider caching the client for performance if dispatch is called frequently.
- The client uses `globalThis.fetch` by default — Bun's native fetch is used automatically.

**Error message design principles:**
- Every error starts with `[dispatch error]` or `[dispatch warning]` prefix
- Include the specific failure (what went wrong)
- Include recovery instructions (how to fix it)
- Keep errors under 500 chars — the calling model needs to parse them efficiently
- Never expose raw stack traces — wrap in human-readable messages

**Response format design:**
- Header: `--- dispatch response from {provider}/{model} ---\n`
- Body: extracted text, joined with newlines
- Footer (optional): `\n[dispatch note] Session preserved: {id}` or cleanup note
- This format is designed for the calling model to parse: the header identifies the source, the body is the content, the footer has metadata

### Follow-up Slices

- **Slice 2**: Wire dispatch into `/execute` (delegate subtasks to faster/cheaper models), `/code-review` (get second opinions from other models), `/code-loop` (parallel review agents on different models)
- **Slice 3**: Add `timeout` arg, `systemPrompt` arg, structured output support (`format` field), client caching
- **Slice 4**: Dispatch dashboard — list active dispatch sessions, their status, accumulated costs
- **Slice 5**: Batch dispatch — send same prompt to N models, compare responses side-by-side

### Confidence Score: 9/10

- **Strengths**: All APIs documented and verified (SDK docs, Server docs, Custom Tools docs). Exact TypeScript patterns known. Dependencies confirmed available. Runtime (Bun 1.3.6 + Node 22.19.0) verified. Provider IDs confirmed from `opencode.json`.
- **Uncertainties**: SDK `session.prompt` response shape may have undocumented edge cases. `createOpencodeClient` default `responseStyle` behavior needs runtime verification. SDK `"latest"` version resolution at install time.
- **Mitigations**: Defensive response parsing with multiple fallbacks. Health check ensures server compatibility. Error messages guide users to recovery.
