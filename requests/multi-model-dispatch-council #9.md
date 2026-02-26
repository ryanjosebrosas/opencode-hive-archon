# Feature: Multi-Model Council Tool (Slice 9)

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

---

## Feature Description

A `council` tool that orchestrates multi-model conversations in a **single shared OpenCode session**. Multiple AI models (4 by default) take turns discussing a topic, each seeing the full conversation history and building on prior responses. The user watches the debate live in the OpenCode browser UI at `localhost:4096`. Supports two modes: **structured** (proposal/rebuttal/synthesis rounds) and **freeform** (reactive chain where each model responds to what it sees). Also hooks into `/planning` Phase 4 as an optional architecture pressure-test.

## User Story

As a developer using OpenCode with multiple connected providers, I want to start a multi-model council discussion on a topic so that I get diverse perspectives (edge cases, simpler approaches, architecture critiques) from different AI models in one visible session before making decisions.

## Problem Statement

The existing `dispatch` tool sends one prompt to one model per call. The `batch-dispatch` tool sends the same prompt to N models in parallel, but each model gets its own isolated session and can't see each other's responses. There's no way to have models **discuss** a topic together — reacting to each other's arguments, challenging assumptions, and building consensus. The ice cream debate prototype proved the shared-session pattern works technically, but it requires manual scripting.

## Solution Statement

- Decision 1: **Single shared session** — all models speak in one OpenCode session so the conversation is visible as a single thread in the browser UI. Proven in the ice cream debate test.
- Decision 2: **Two modes via `mode` arg** — `structured` (default) runs explicit rounds (propose/rebut/synthesize), `freeform` chains responses reactively. Both use the same shared session.
- Decision 3: **4 default models** — picked from connected providers for diversity of perspective. User can override with custom model list.
- Decision 4: **Session preserved** — council sessions are NOT cleaned up, so the user can review and continue the conversation in the browser after the tool returns.
- Decision 5: **New standalone tool** — `.opencode/tools/council.ts`, not a modification to dispatch.ts. Keeps dispatch simple (single-model) and council focused (multi-model conversation).
- Decision 6: **Planning hook** — `/planning` Phase 4 gets optional council guidance. Not auto-triggered (user decides when multi-model input is valuable).

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `.opencode/tools/`, `.opencode/commands/planning.md`
- **Dependencies**: `@opencode-ai/plugin`, `@opencode-ai/sdk/v2/client` (already installed)

### Slice Guardrails (Required)

- **Single Outcome**: A working `council` tool that runs multi-model discussions in a shared session
- **Expected Files Touched**: `.opencode/tools/council.ts` (new), `.opencode/commands/planning.md` (update)
- **Scope Boundary**: Does NOT modify dispatch.ts, batch-dispatch.ts, or other commands. Does NOT implement persistent council history, voting, or scoring.
- **Split Trigger**: If the tool exceeds 500 lines, split into council-core and council-planning-hook

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-90) — Why: Utility functions (`getErrorMessage`, `asRecord`, `extractTextFromParts`, `safeStringify`, `getConnectedProviders`, `DEFAULT_TIMEOUT_SECONDS`) to reuse or mirror
- `.opencode/tools/dispatch.ts` (lines 91-170) — Why: Tool definition pattern (`tool()`, `tool.schema`, args structure)
- `.opencode/tools/dispatch.ts` (lines 195-240) — Why: Health check + provider pre-flight pattern to mirror
- `.opencode/tools/dispatch.ts` (lines 300-370) — Why: `session.prompt()` calling pattern with AbortController, response extraction, empty-response detection
- `.opencode/tools/batch-dispatch.ts` (lines 60-73) — Why: `ModelTarget` and `ModelResult` interfaces to reuse
- `.opencode/tools/batch-dispatch.ts` (lines 300-420) — Why: `dispatchOne` pattern for per-model prompt with timeout
- `.opencode/tools/_test-dispatch.ts` (full file) — Why: Diagnostic test pattern with provider discovery; the council tool needs similar connected-provider detection for default model selection
- `.opencode/commands/planning.md` (lines 336-358) — Why: Phase 4 (Strategic Design) where council hook will be added

### New Files to Create

- `.opencode/tools/council.ts` — Multi-model council discussion tool

### Related Memories (from memory.md)

- Memory: "OpenCode SDK swallows AbortError — puts DOMException in `result.error` and returns `{ data: {} }`" — Relevance: Council must handle per-turn timeouts the same way dispatch does
- Memory: "OpenCode provider models is Record, not Array — use `Object.values()` to iterate" — Relevance: Default model selection needs correct iteration
- Memory: "OpenCode upstream API errors in info.error" — Relevance: When a model's turn fails with upstream error, council should log it and continue with remaining models
- Memory: "Multi-model dispatch complete (slices 1-8)" — Relevance: Foundation this slice builds on. SDK patterns are established and proven.
- Memory: "Archon is the single source of truth for task tracking" — Relevance: `/execute` must use Archon, not TodoWrite

### Relevant Documentation

- OpenCode SDK v2 type definitions: `.opencode/node_modules/@opencode-ai/sdk/dist/v2/gen/sdk.gen.d.ts`
  - Specific section: `session.prompt()` type signature
  - Why: Exact params for multi-turn shared session prompting
- OpenCode API: `http://127.0.0.1:4096/doc`
  - Specific section: `POST /session/{sessionID}/message`
  - Why: Confirms session.prompt() supports switching models mid-session

### Patterns to Follow

**Tool Definition Pattern** (from `.opencode/tools/dispatch.ts:91-170`):
```typescript
export default tool({
  description: "...",
  args: {
    argName: tool.schema.string().optional().describe("..."),
  },
  execute: async (args, ctx) => {
    // 1. Validate args
    // 2. Create client + health check
    // 3. Provider pre-flight
    // 4. Core logic
    // 5. Return formatted response
  },
})
```
- Why this pattern: All OpenCode tools follow this structure. Plugin system requires it.
- Common gotchas: `tool.schema` uses Zod under the hood but imported from plugin.

**Shared Session Multi-Model Pattern** (from ice cream debate test — proven):
```typescript
const session = await client.session.create({ title: "Council: ..." })
const sid = session.data?.id

// Model A speaks
await client.session.prompt({
  sessionID: sid,
  model: { providerID: "anthropic", modelID: "claude-sonnet-4" },
  parts: [{ type: "text", text: "..." }],
}, { signal: controller.signal })

// Model B speaks — sees Model A's response in session history
await client.session.prompt({
  sessionID: sid,
  model: { providerID: "ollama-cloud", modelID: "qwen3-coder-next" },
  parts: [{ type: "text", text: "..." }],
}, { signal: controller.signal })
```
- Why this pattern: Shared `sessionID` means each model sees full conversation history.
- Common gotchas: Each `session.prompt()` is synchronous — blocks until response. Timeout is per-turn, not per-council.

**Provider Pre-flight + Default Model Selection Pattern** (from `.opencode/tools/dispatch.ts:54-63` + `_test-dispatch.ts:24-50`):
```typescript
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
- Why this pattern: Council needs to auto-select 4 models from connected providers.
- Common gotchas: `models` in provider response is a Record, not Array. Some models may have status !== "active".

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Build the council tool with core shared-session orchestration.

**Tasks:**
- Create `.opencode/tools/council.ts` with utility functions (mirror from dispatch.ts)
- Define args: `topic`, `models` (optional), `mode` (structured/freeform), `rounds`, `timeout`, `context`, `port`
- Implement default model selection from connected providers
- Implement health check + provider pre-flight

### Phase 2: Core Implementation

Implement both council modes.

**Tasks:**
- Implement structured mode: Round 1 (propose), Round 2 (rebut), Round 3 (synthesize)
- Implement freeform mode: reactive chain, each model responds to what it sees
- Handle per-turn timeouts, empty responses, and upstream errors gracefully
- Format final output with all responses organized by round/turn

### Phase 3: Integration

Wire council into the planning workflow.

**Tasks:**
- Add council guidance to `/planning` Phase 4 (Strategic Design)
- Document when to use council vs dispatch vs batch-dispatch

### Phase 4: Testing & Validation

**Tasks:**
- Build verification (bun build)
- Type check (bun -e import)
- Live test with 4 models in structured mode
- Live test freeform mode

---

## STEP-BY-STEP TASKS

### CREATE `.opencode/tools/council.ts` — Foundation + utility functions

- **IMPLEMENT**: Create new file with:
  - Import `tool` from `@opencode-ai/plugin` and `createOpencodeClient` from `@opencode-ai/sdk/v2/client`
  - Copy utility functions from dispatch.ts: `getErrorMessage`, `asRecord`, `extractTextFromParts`, `safeStringify` (tools must be self-contained)
  - Add `DEFAULT_TIMEOUT_PER_TURN = 90` (seconds, per model turn — gives models enough time to read session history and produce a thoughtful response)
  - Add `DEFAULT_ROUND_COUNT = 3` for structured mode
  - Add `getConnectedProviders` function (mirror from dispatch.ts)
  - Add `getDefaultCouncilModels` async function that:
    1. Calls `getConnectedProviders(baseUrl)` to get connected list
    2. Fetches `GET /provider` for full provider data (with models)
    3. Picks 4 models from different providers for diversity, using this priority list:
       ```typescript
       const PREFERRED_COUNCIL_MEMBERS = [
         { provider: "anthropic", model: "claude-sonnet-4-20250514", label: "Claude" },
         { provider: "ollama-cloud", model: "qwen3-coder-next", label: "Qwen" },
         { provider: "zai-coding-plan", model: "glm-4.5-flash", label: "GLM" },
         { provider: "openai", model: "gpt-5-codex", label: "GPT" },
         { provider: "opencode", model: "minimax-m2.5-free", label: "MiniMax" },
         { provider: "bailian-coding-plan", model: "qwen3.5-plus", label: "Qwen-Plus" },
       ]
       ```
    4. Iterate PREFERRED_COUNCIL_MEMBERS, include if provider is in connected list
    5. If fewer than 4 found from preferred list, fill remaining slots from connected providers not yet picked (pick first model from each via `Object.values(models)[0]`)
    6. Returns `Array<{ provider: string, model: string, label: string }>` — always 4 if possible, minimum 2
    7. If fewer than 2 available, return empty array (caller returns error)
  - Add `ModelTarget` interface: `{ provider: string, model: string, label: string }`
  - Add `TurnResult` interface: `{ model: ModelTarget, round: number, turn: number, text: string, durationMs: number, status: "success" | "error" | "timeout" }`
  - Add `ROUND_LABELS` constant: `["Proposals", "Rebuttals", "Synthesis"]` for structured mode headers

- **PATTERN**: `.opencode/tools/dispatch.ts:1-90` utility functions, `.opencode/tools/batch-dispatch.ts:60-73` interfaces
- **IMPORTS**: `import { tool } from "@opencode-ai/plugin"`, `import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"`
- **GOTCHA**: Tools must be self-contained — cannot import from dispatch.ts. Copy utilities. `models` in provider response is a Record (use `Object.values()`). Pick models with `status === "active"` or no status field.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/council.ts 2>&1 | head -5`

### UPDATE `.opencode/tools/council.ts` — Tool definition + args

- **IMPLEMENT**: Add `export default tool({...})` with:
  - `description`: "Start a multi-model council discussion. Multiple AI models take turns discussing a topic in a shared session, each seeing and building on prior responses. Watch the conversation live in the OpenCode browser UI. Two modes: 'structured' (propose/rebut/synthesize rounds) or 'freeform' (reactive chain). Default: 4 diverse models, 3 rounds."
  - Args:
    - `topic` (string, required): "The topic, question, or problem for the council to discuss. Be specific — include relevant context, constraints, and what kind of output you want."
    - `models` (string, optional): "JSON array of model targets. Each has 'provider', 'model', and optional 'label' fields. Default: 4 models auto-selected from connected providers for diversity."
    - `mode` (string, optional): "Discussion mode: 'structured' (default) runs proposal/rebuttal/synthesis rounds. 'freeform' runs a reactive chain where each model responds to the conversation."
    - `rounds` (number, optional): "Number of discussion rounds. Default: 3 for structured mode, 2 for freeform (since freeform has more turns per round — each model speaks once per round)."
    - `timeout` (number, optional): "Timeout in seconds per model turn. Default: 90. Total council time = rounds x models x timeout (worst case)."
    - `context` (string, optional): "Additional context to include in the system prompt for all models. Use to share relevant code, architecture decisions, or constraints."
    - `port` (number, optional): "OpenCode server port (default: 4096)"
  - `execute: async (args, ctx) => { ... }` — placeholder, implemented in next tasks

- **PATTERN**: `.opencode/tools/dispatch.ts:91-170` tool definition pattern
- **IMPORTS**: Already imported in previous task
- **GOTCHA**: `tool.schema` for arg definitions. Description must be clear enough that any calling model knows how to use it.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/council.ts 2>&1 | head -5`

### UPDATE `.opencode/tools/council.ts` — Execute function: setup + validation

- **IMPLEMENT**: Inside `execute`, add:
  1. Parse and validate `mode` (default "structured", must be "structured" or "freeform")
  2. Parse `models` JSON if provided, else call `getDefaultCouncilModels(baseUrl)`
  3. Validate at least 2 models
  4. Set `effectiveRounds` = `args.rounds ?? (mode === "structured" ? 3 : 2)`
  5. Set `effectiveTimeout` = `args.timeout ?? DEFAULT_TIMEOUT_PER_TURN`
  6. Create client, health check, provider pre-flight (mirror dispatch.ts pattern)
  7. Create shared session: `client.session.create({ title: \`Council: ${args.topic.slice(0, 50)}\` })`
  8. Build system prompt context string (topic + context arg + mode instructions)
  9. Log setup info: "Council started: N models, M rounds, mode, session ID"
  10. Call `runStructuredCouncil` or `runFreeformCouncil` based on mode
  11. Format results and return

  Setup code structure:
  ```typescript
  execute: async (args, ctx) => {
    const mode = args.mode ?? "structured"
    if (mode !== "structured" && mode !== "freeform") {
      return "[council error] mode must be 'structured' or 'freeform'"
    }
    
    const serverPort = args.port ?? 4096
    const baseUrl = `http://127.0.0.1:${serverPort}`
    const client = createOpencodeClient({ baseUrl })
    
    // Health check
    try {
      const health = await client.global.health()
      if (!health.data?.healthy) {
        return `[council error] OpenCode server at ${baseUrl} is not healthy.`
      }
    } catch (err) {
      return `[council error] Cannot reach OpenCode server at ${baseUrl}. Run 'opencode serve --port ${serverPort}'.`
    }
    
    // Parse or auto-select models
    let models: ModelTarget[]
    if (args.models) {
      try {
        const parsed = JSON.parse(args.models)
        if (!Array.isArray(parsed) || parsed.length < 2) {
          return "[council error] models must be a JSON array with at least 2 entries"
        }
        models = parsed.map((m: any, i: number) => ({
          provider: m.provider,
          model: m.model,
          label: m.label ?? `Model-${i + 1}`,
        }))
      } catch (parseErr) {
        return `[council error] Invalid models JSON: ${getErrorMessage(parseErr)}`
      }
    } else {
      models = await getDefaultCouncilModels(baseUrl)
      if (models.length < 2) {
        return "[council error] Need at least 2 connected providers for a council. Run '/connect <provider>' first."
      }
    }
    
    // Create shared session
    const session = await client.session.create({
      title: `Council: ${args.topic.slice(0, 50)}`,
    })
    const sessionId = session.data?.id
    if (!sessionId) {
      return `[council error] Failed to create session. Response: ${safeStringify(session.data)}`
    }
    
    const effectiveRounds = args.rounds ?? (mode === "structured" ? 3 : 2)
    const effectiveTimeout = args.timeout ?? DEFAULT_TIMEOUT_PER_TURN
    
    // Run council
    const results = mode === "structured"
      ? await runStructuredCouncil(client, sessionId, models, effectiveRounds, args.topic, args.context, effectiveTimeout)
      : await runFreeformCouncil(client, sessionId, models, effectiveRounds, args.topic, args.context, effectiveTimeout)
    
    // Format and return (session preserved — not cleaned up)
    return formatCouncilResults(results, mode, models, effectiveRounds, sessionId, args.topic)
  }
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:195-240` health check + provider pre-flight
- **IMPORTS**: No new imports
- **GOTCHA**: Don't cleanup session on error during setup — let the user see partial results in browser. If model list parse fails, return clear error with example JSON.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/council.ts 2>&1 | head -5`

### UPDATE `.opencode/tools/council.ts` — Structured mode implementation

- **IMPLEMENT**: Add `runStructuredCouncil` async function:
  - Takes: `client`, `sessionId`, `models`, `rounds`, `topic`, `context`, `timeout`
  - Returns: `TurnResult[]`
  - Build per-round prompt templates as a function `getStructuredPrompt(round, totalRounds, modelCount, topic, context)`:
    ```typescript
    const getStructuredPrompt = (round: number, totalRounds: number, modelCount: number, topic: string, context?: string): string => {
      const contextBlock = context ? `\nAdditional context:\n${context}\n` : ""
      if (round === 1) {
        return (
          `You are in a council discussion with ${modelCount} AI models.\n` +
          `Topic: ${topic}\n${contextBlock}\n` +
          `This is Round 1 of ${totalRounds} (Proposals).\n` +
          `Share your perspective. Think independently — propose your approach, ` +
          `identify key concerns, and suggest solutions.\n` +
          `Keep your response focused (3-5 paragraphs max). Take a clear position.`
        )
      }
      if (round === 2) {
        return (
          `This is Round 2 of ${totalRounds} (Rebuttals).\n` +
          `You've read all proposals above. Now:\n` +
          `- Challenge the weakest arguments you've seen\n` +
          `- Point out what others missed or got wrong\n` +
          `- Defend your position if challenged, or update it if you were convinced\n` +
          `- Reference specific points from other speakers\n` +
          `Keep it focused (2-3 paragraphs).`
        )
      }
      if (round === 3) {
        return (
          `This is Round 3 of ${totalRounds} (Synthesis).\n` +
          `Based on all proposals and rebuttals above:\n` +
          `- What are the key points of agreement?\n` +
          `- What remains contested and why?\n` +
          `- Propose a final recommendation that incorporates the best ideas\n` +
          `- Note any risks or tradeoffs the group should be aware of\n` +
          `Keep it concise (2-3 paragraphs).`
        )
      }
      // Round 4+
      return (
        `This is Round ${round} of ${totalRounds}.\n` +
        `Continue the discussion. Build on what's been said.\n` +
        `Address any unresolved points or new concerns that emerged.\n` +
        `Keep it concise (1-2 paragraphs).`
      )
    }
    ```
  - **Round 1 — Propose**: For each model sequentially, call `session.prompt()` with `getStructuredPrompt(1, ...)`. First model gets full topic; subsequent models see it in session history.
  - **Round 2 — Rebut**: For each model sequentially, call with `getStructuredPrompt(2, ...)`.
  - **Round 3 — Synthesize**: For each model sequentially, call with `getStructuredPrompt(3, ...)`.
  - **Round N (custom)**: For rounds > 3, uses `getStructuredPrompt(n, ...)` which has a generic continuation prompt.
  - Each turn executes this pattern:
    ```typescript
    const executeTurn = async (
      client: any, sessionId: string, model: ModelTarget,
      prompt: string, timeout: number, round: number, turn: number
    ): Promise<TurnResult> => {
      const startTime = Date.now()
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout * 1000)
      
      try {
        const result = await client.session.prompt(
          {
            sessionID: sessionId,
            model: { providerID: model.provider, modelID: model.model },
            parts: [{ type: "text" as const, text: prompt }],
          },
          { signal: controller.signal },
        )
        clearTimeout(timeoutId)
        
        // Check swallowed AbortError
        const resultRecord = asRecord(result)
        const resultError = resultRecord?.error
        if (controller.signal.aborted || (resultError && (resultError as any)?.name === "AbortError")) {
          return { model, round, turn, text: `[timeout after ${timeout}s]`, durationMs: Date.now() - startTime, status: "timeout" }
        }
        
        // Check empty response
        const data = asRecord(resultRecord?.data)
        if (!data || Object.keys(data).length === 0) {
          return { model, round, turn, text: "[empty response — model may not be connected]", durationMs: Date.now() - startTime, status: "error" }
        }
        
        // Check upstream API error in info.error
        const info = asRecord(data?.info)
        const infoError = asRecord(info?.error)
        if (infoError && !extractTextFromParts(data?.parts)) {
          const errMsg = (asRecord(infoError.data) as any)?.message ?? "unknown"
          return { model, round, turn, text: `[API error: ${infoError.name} — ${errMsg}]`, durationMs: Date.now() - startTime, status: "error" }
        }
        
        // Extract text
        const text = extractTextFromParts(data?.parts) || "[no text in response]"
        return { model, round, turn, text, durationMs: Date.now() - startTime, status: "success" }
      } catch (err: unknown) {
        clearTimeout(timeoutId)
        return { model, round, turn, text: `[error: ${getErrorMessage(err)}]`, durationMs: Date.now() - startTime, status: "error" }
      }
    }
    ```
  - On turn failure: log error in results, continue with next model (don't abort entire council).

- **PATTERN**: `.opencode/tools/dispatch.ts:300-370` prompt + response extraction. Ice cream debate test for shared session multi-model calling.
- **IMPORTS**: No new imports
- **GOTCHA**: SDK swallows AbortError — check `controller.signal.aborted` after prompt returns, not in catch. Empty response `{ data: {} }` means timeout or model failure. Session prompt is synchronous — each turn blocks. Total time = sum of all turns. `clearTimeout` after every turn.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/council.ts 2>&1 | head -5`

### UPDATE `.opencode/tools/council.ts` — Freeform mode implementation

- **IMPLEMENT**: Add `runFreeformCouncil` async function:
  - Takes: same params as structured
  - Returns: `TurnResult[]`
  - Build freeform prompt templates:
    ```typescript
    const getFreeformPrompt = (turnIndex: number, totalTurns: number, modelCount: number, topic: string, context?: string): string => {
      const contextBlock = context ? `\nAdditional context:\n${context}\n` : ""
      if (turnIndex === 0) {
        return (
          `You are in a freeform council discussion with ${modelCount} AI models.\n` +
          `Topic: ${topic}\n${contextBlock}\n` +
          `You're speaking first. Share your perspective.\n` +
          `Be specific and take a clear position.\n` +
          `Keep it concise (2-3 paragraphs).`
        )
      }
      if (turnIndex === totalTurns - 1) {
        // Last turn — wrap up
        return (
          `This is the final turn in the discussion.\n` +
          `Summarize the key takeaways from this conversation.\n` +
          `What did the group agree on? What's still unresolved?\n` +
          `Keep it concise (2-3 paragraphs).`
        )
      }
      return (
        `Continue the discussion. You can see everything said above.\n` +
        `Respond naturally — agree, disagree, add nuance, raise new points.\n` +
        `Reference specific points from other speakers.\n` +
        `Don't repeat what's been said. Keep it concise (1-2 paragraphs).`
      )
    }
    ```
  - **Turn 1** (first model): `getFreeformPrompt(0, ...)` — full topic + context
  - **Middle turns**: `getFreeformPrompt(n, ...)` — continuation with "reference specific points"
  - **Last turn**: `getFreeformPrompt(last, ...)` — wrap-up summary
  - **Total turns**: `rounds * models.length` (each model speaks once per "round")
  - **Turn rotation**: `models[turnIndex % models.length]` — cycles through models
  - Same error handling as structured mode: swallowed AbortError, empty response, info.error — log and continue.

- **PATTERN**: Same as structured mode task
- **IMPORTS**: No new imports
- **GOTCHA**: Freeform can feel repetitive after many turns — that's why default rounds is 2 (= 8 turns with 4 models). The system prompt tells models to not repeat.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/council.ts 2>&1 | head -5`

### UPDATE `.opencode/tools/council.ts` — Response formatting + return

- **IMPLEMENT**: After council completes, format the return string:
  - Header: `=== Council Discussion: {topic.slice(0, 80)} ===`
  - Mode/models/rounds metadata line
  - Session ID line: `Session: {sessionId} — view the full discussion in OpenCode browser`
  - For structured mode: group by round with headers (`--- Round 1: Proposals ---`, etc.)
  - For freeform mode: sequential turns with `[Turn N] {model.label} ({provider}/{model}):`
  - Each turn shows: text content, duration, status (or error message)
  - Footer: summary stats (total time, turns completed, any failures)
  - Do NOT include full response texts in the return (they're already in the session visible in the browser). Include a **condensed summary**: for each model, their key position in 1 sentence. This keeps the orchestrator's context lean.

  Wait — actually the calling model (me) needs to see the content to use it for planning. Include full texts but with a reasonable truncation (500 chars per turn max in the return, full texts are in the browser).

  Revised: Each turn in the return shows up to 500 chars of text. Full responses visible in the browser session.

  Format template:
  ```
  === Council Discussion: {topic} ===
  Mode: {structured|freeform} | Models: {N} | Rounds: {M} | Total turns: {T}
  Session: {sessionId} — view full discussion at http://localhost:4096
  
  --- Round 1: Proposals ---
  
  [{model.label}] ({provider}/{model}) — {durationMs}ms
  {text.slice(0, 500)}{text.length > 500 ? "... (truncated, see browser for full)" : ""}
  
  [{model.label}] ({provider}/{model}) — {durationMs}ms
  {text.slice(0, 500)}
  
  --- Round 2: Rebuttals ---
  ...
  
  === Council Complete ===
  Duration: {totalMs}ms | Turns: {completed}/{total} | Failures: {N}
  ```

- **PATTERN**: `.opencode/tools/dispatch.ts:426-437` response formatting with header + metadata
- **IMPORTS**: No new imports
- **GOTCHA**: Keep return string manageable — 4 models x 3 rounds x 500 chars = ~6000 chars max, which is reasonable for context. If any model produced actionable findings (architecture concerns, edge cases), those need to be visible in the return.
- **VALIDATE**: `cd .opencode && bun build --no-bundle tools/council.ts 2>&1 | head -5`

### UPDATE `.opencode/commands/planning.md` — Add council hook to Phase 4

- **IMPLEMENT**: After Phase 4 opening paragraph (line ~340, after "Decide between alternatives with rationale"), insert new section:

  ```markdown
  Council pressure-test (optional):

  If the feature involves non-trivial architecture decisions, consider running a council discussion to pressure-test your design before writing the plan tasks:

  **When to run a council:**
  - Multiple valid architectural approaches exist (e.g., event-driven vs polling, SQL vs NoSQL)
  - Feature has security implications worth multi-perspective review
  - You're uncertain about edge cases or failure modes
  - The user explicitly asked for multi-model input

  **When to skip:**
  - Architecture is straightforward and well-established in the codebase
  - Feature is a small enhancement following existing patterns
  - Time-sensitive — council adds 2-5 minutes

  **How to run:**
  ```
  council({
    topic: "Architecture decision: {describe the choice and constraints}",
    context: "{paste relevant code patterns, constraints, and requirements}",
    mode: "structured",
    rounds: 2
  })
  ```

  **Using council results:**
  - Record key findings in the plan's "Key Design Decisions" section
  - Note any concerns raised that need mitigation in the "Risks" section
  - If the council reached consensus, note it. If they disagreed, present both sides to the user for a decision.
  - Source: "Council discussion ({list models}): {finding}"

  **Example council for architecture planning:**
  ```
  council({
    topic: "We need to implement API response caching for our Python backend. Options: Redis with TTL, in-memory LRU cache with cachetools, or HTTP-level caching with Cache-Control headers. The backend is FastAPI with Supabase as the database. We have 10-50 concurrent users. What approach should we take?",
    context: "Current stack: Python 3.12, FastAPI, Supabase pgvector, deployed on a single server (not distributed). Main bottleneck is embedding API calls (Voyage AI) which cost $0.05 per 1000 tokens.",
    mode: "structured",
    rounds: 2
  })
  ```

  **Model routing for council planning discussions:**
  | Discussion Type | Recommended Models | Why |
  |----------------|-------------------|-----|
  | Architecture decisions | anthropic + ollama-cloud + openai + zai-coding-plan | Maximum diversity of training data |
  | Security review | anthropic + openai (2 strongest at security) + 2 others | Security needs best reasoning |
  | Performance tradeoffs | Fast models (qwen, glm) + reasoning models (anthropic, openai) | Mix speed expertise + analysis |
  | API design | Code-specialized models + reasoning models | Implementation + design perspectives |
  ```

- **PATTERN**: `.opencode/commands/planning.md:241-272` existing dispatch guidance structure
- **IMPORTS**: N/A (markdown file)
- **GOTCHA**: This is guidance only — not auto-triggered. The planning agent decides if council is worth the time. Keep the section concise (not as long as the dispatch research sections).
- **VALIDATE**: Read the file and verify the section is correctly placed after Phase 4 opening paragraph

### VALIDATE — Build checks + live test

- **IMPLEMENT**:
  1. `cd .opencode && bun build --no-bundle tools/council.ts` — must be clean
  2. `bun -e "import t from './tools/council.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"` — verify args and execute
  3. If server running: live test structured mode with 3 models:
     ```
     bun -e "import t from './tools/council.ts'; const r = await t.execute({ topic: 'What is the best approach to implement a caching layer for API responses?', rounds: 2 }, {}); console.log(r)"
     ```
  4. If server running: live test freeform mode:
     ```
     bun -e "import t from './tools/council.ts'; const r = await t.execute({ topic: 'Should we use Redis or in-memory caching for short-lived API cache?', mode: 'freeform', rounds: 1 }, {}); console.log(r)"
     ```
- **PATTERN**: Slice 8 validation approach
- **GOTCHA**: Live tests require `opencode serve` running. Each test takes 1-4 minutes depending on model response times. Check browser to see sessions appear.
- **VALIDATE**: All build commands clean, live test produces multi-model responses

---

## TESTING STRATEGY

### Unit Tests

Not applicable for this slice — the tool is a TypeScript file in the OpenCode plugin system which doesn't have a unit test framework. Validation is via build checks and live testing.

### Integration Tests

- **Structured mode**: Run council with 3+ models, verify all rounds complete, responses are non-empty, session preserved
- **Freeform mode**: Run council with 3+ models, verify turn rotation, responses build on each other
- **Default model selection**: Run council without `models` arg, verify 4 models auto-selected from connected providers
- **Error handling**: Test with very short timeout (2s) to trigger timeout on at least one model, verify council continues

### Edge Cases

- Edge case 1: Only 1 connected provider — council should still work with multiple models from same provider
- Edge case 2: Model times out mid-council — should log error and continue with remaining models
- Edge case 3: `models` JSON is malformed — return clear parse error
- Edge case 4: No connected providers — return error before creating session
- Edge case 5: User provides 2 models (minimum) — should work, just fewer perspectives

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
cd .opencode && bun build --no-bundle tools/council.ts
```

### Level 2: Type Safety
```
cd .opencode && bun -e "import t from './tools/council.ts'; console.log('Args:', Object.keys(t.args).join(', ')); console.log('Execute:', typeof t.execute)"
```

### Level 3: Unit Tests
```
N/A — OpenCode plugin tools don't have a unit test framework
```

### Level 4: Integration Tests
```
# Structured mode (requires opencode serve)
cd .opencode && bun -e "import t from './tools/council.ts'; const r = await t.execute({ topic: 'Best approach for API response caching?', rounds: 2 }, {}); console.log(r)"

# Freeform mode
cd .opencode && bun -e "import t from './tools/council.ts'; const r = await t.execute({ topic: 'Redis vs in-memory cache?', mode: 'freeform', rounds: 1 }, {}); console.log(r)"
```

### Level 5: Manual Validation

1. Run a council and check the browser UI at `localhost:4096` — session should appear with the discussion visible
2. Verify each model's response references or builds on prior models' responses (shared session context works)
3. Run council without `models` arg — verify 4 models auto-selected
4. Check that the return string to the calling model contains truncated summaries (not bloating context)

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `council.ts` created with tool definition and all args
- [ ] Utility functions (getErrorMessage, asRecord, etc.) copied and working
- [ ] `getDefaultCouncilModels` selects 4 diverse models from connected providers
- [ ] Structured mode: 3 rounds (propose/rebut/synthesize) with correct prompts
- [ ] Freeform mode: reactive chain with turn rotation
- [ ] Per-turn timeout with AbortController (default 60s)
- [ ] Swallowed AbortError handled (SDK pattern)
- [ ] Empty response handled (continue council, log error)
- [ ] Upstream `info.error` handled
- [ ] Session preserved after council (not cleaned up)
- [ ] Return string includes session ID for browser viewing
- [ ] Return string truncates per-turn text to 500 chars
- [ ] `/planning` Phase 4 has council guidance section
- [ ] Tool builds clean with `bun build`
- [ ] No changes to dispatch.ts or batch-dispatch.ts

### Runtime (verify after live testing)

- [ ] Structured mode produces multi-round discussion visible in browser
- [ ] Freeform mode produces flowing conversation visible in browser
- [ ] Models reference each other's points (shared session context works)
- [ ] Default model selection picks 4 diverse models
- [ ] Timeout on one model doesn't kill the council
- [ ] Return string is readable and not too large for context

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Live test confirms multi-model discussion works
- [ ] Session visible in browser with full conversation
- [ ] Models respond to each other (not just the original topic)
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Standalone tool vs extending batch-dispatch**: Council is fundamentally different from batch-dispatch (shared session vs isolated sessions, sequential vs parallel, conversational vs one-shot). Separate tool avoids feature bloat.
- **90s per-turn timeout**: Council has many turns (4 models x 3 rounds = 12 turns). 120s per turn could mean 24 minutes worst case. 90s gives models enough time to read session history and think, while keeping total time reasonable (~18 min max).
- **Return truncation (500 chars/turn)**: Full responses are in the browser. The calling model needs enough to work with for planning, but not so much it eats context. 500 chars per turn x 12 turns = ~6k chars — manageable.
- **Session preserved**: Unlike dispatch (which cleans up by default), council sessions are always preserved. The whole point is the user can watch and continue the conversation.
- **No voting or scoring**: YAGNI. The user or calling model reads the discussion and decides. Automated consensus detection is a future slice.

### Risks

- Risk 1: **Slow models make council take too long** — Mitigation: 90s per-turn timeout, skip slow models. User can also reduce rounds or model count.
- Risk 2: **Models don't engage with each other** — Mitigation: System prompts explicitly tell models to reference prior arguments. Shared session history provides context.
- Risk 3: **Context window overflow in shared session** — Mitigation: Council discussions are naturally bounded (3 rounds x 4 models = 12 turns of 2-3 paragraphs each). If models start producing very long responses, the per-turn system prompt says "keep concise".
- Risk 4: **Default model selection picks bad models** — Mitigation: Prefer known-good providers (anthropic, ollama-cloud, zai-coding-plan, openai). User can always override with explicit models list.

### Confidence Score: 8/10
- **Strengths**: Pattern is proven (ice cream debate), SDK behavior is well-understood from Slice 8, all failure modes documented
- **Uncertainties**: Whether models will meaningfully engage with each other's arguments (vs just repeating their position), how provider-specific latency affects the flow
- **Mitigations**: Good system prompts that explicitly instruct models to reference prior arguments; per-turn timeouts prevent blocking
