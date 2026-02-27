// Dispatch: Integrate relay mode into dispatch.ts
// Uses T5 Sonnet agent mode to read and modify dispatch.ts
// Run with: cd .opencode && bun run tools/_dispatch-integrate-relay.ts
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"

const BASE_URL = "http://127.0.0.1:4096"

async function main() {
  console.log("=== Dispatching Relay Mode Integration ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) {
    console.error("Server not healthy")
    process.exit(1)
  }

  // Load the relay prototype as reference
  const toolDir = typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(import.meta.url.replace("file:///", ""))
  const relayPrototype = readFileSync(join(toolDir, "_test-relay-mode.ts"), "utf-8")

  const session = await client.session.create({
    title: "integrate-relay-mode",
    permission: [
      { permission: "read", pattern: "*", action: "allow" },
      { permission: "edit", pattern: "*", action: "allow" },
      { permission: "glob", pattern: "*", action: "allow" },
      { permission: "grep", pattern: "*", action: "allow" },
      { permission: "list", pattern: "*", action: "allow" },
      { permission: "bash", pattern: "*", action: "allow" },
      { permission: "task", pattern: "*", action: "deny" },
      { permission: "external_directory", pattern: "*", action: "deny" },
      { permission: "webfetch", pattern: "*", action: "deny" },
      { permission: "websearch", pattern: "*", action: "deny" },
    ] as any,
  } as any)

  const sessionId = session.data?.id
  if (!sessionId) {
    console.error("No session ID")
    process.exit(1)
  }
  console.log(`Session: ${sessionId}\n`)

  const taskPrompt = `You have file read/write access. Integrate a "relay" mode into the dispatch tool.

## Context

The dispatch tool (.opencode/tools/dispatch.ts) currently supports two modes:
- "text" (default): Simple prompt-response, no tool access
- "agent": Full tool access via OpenCode agent framework (only works with Anthropic/OpenAI)

Free providers (T1-T3: bailian, zai, ollama) can't use agent mode. We've built a "relay" mode prototype that gives them tool access through text-based XML tags. The relay loop:
1. Sends prompt with relay instructions (how to use tool tags)
2. Model outputs <tool> tags when it needs file/search/Archon access
3. Script parses tags, executes locally, sends results back
4. Loops until model has no more tool requests (max 5 turns)

## Working Prototype

Here's the working prototype (tested and passing):

\`\`\`typescript
${relayPrototype}
\`\`\`

## What to implement

Add mode:"relay" to dispatch.ts. Specifically:

### 1. Add "relay" to the mode validation (around line 272)
Change the mode check to accept "text", "agent", or "relay".

### 2. Add relay constants after the existing constants (around line 34)
- MAX_RELAY_TURNS = 5
- ARCHON_MCP_URL = "http://159.195.45.47:8051/mcp" 
- RELAY_INSTRUCTIONS string (copy from prototype, the one prepended to prompts)

### 3. Add relay helper functions before the tool export (around line 125)
Extract from the prototype:
- parseToolCalls() and parseAttrs() — XML tag parser
- executeRead(), executeGlob(), executeGrep(), executeBash(), executeEdit() — file ops
- initArchonSession(), callArchonTool(), executeArchonSearch(), executeArchonSources() — MCP
- executeTool() — dispatcher

Important: The PROJECT_ROOT in dispatch.ts should resolve to the project directory, not .opencode/tools/.
Use: resolve(join(import.meta.dirname ?? ".", "..", ".."))

### 4. Add the relay loop in the prompt section (around line 428-487)
After building the prompt text and before sending it:
- If mode is "relay", run the relay loop instead of the single prompt
- The relay loop creates a session (no permissions needed), sends the prompt with RELAY_INSTRUCTIONS prepended, parses tool calls, executes them, sends follow-ups
- Return the final response text

### 5. Update the agent mode blocklist (around line 279)
The AGENT_COMPATIBLE_PROVIDERS check should NOT block relay mode. Only block agent mode.
Actually, for relay mode we should AUTO-SELECT it: if the user requests agent mode but the provider is not in AGENT_COMPATIBLE_PROVIDERS, automatically fall back to relay mode instead of erroring. Add a note in the response header showing "relay (auto-fallback from agent)".

### 6. Add "relay" to the mode arg description
Update the arg description to mention relay mode.

### 7. Update the response metadata
Add relay-specific metadata: turns count, tool calls count.

## Constraints
- Keep the existing text and agent modes working exactly as they are
- Use the EXACT same tool parsing and execution code from the prototype (it's tested)
- The relay instructions string must be embedded in dispatch.ts (not loaded from a file)
- Add proper error handling (timeout per turn, max turns, tool execution errors)
- Do NOT add new imports beyond what's already used (readFileSync, writeFileSync, execSync, join, resolve, dirname)
- Add writeFileSync and execSync imports since they're needed for relay

## Files to modify
- .opencode/tools/dispatch.ts — the main integration

Do NOT modify any other files. Do NOT run git commands.`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 600_000) // 10 min

  console.log("Dispatching to anthropic/claude-sonnet-4-20250514 (agent mode, 10min timeout)...\n")
  const startTime = Date.now()

  try {
    const result = await client.session.prompt(
      {
        sessionID: sessionId,
        model: { providerID: "anthropic", modelID: "claude-sonnet-4-20250514" },
        agent: "general",
        parts: [{ type: "text" as const, text: taskPrompt }],
      } as any,
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)

    const duration = Math.round((Date.now() - startTime) / 1000)
    const data = (result as any)?.data
    const parts = data?.parts || []
    const info = data?.info

    console.log(`--- Response (${duration}s) ---\n`)
    for (const part of parts) {
      if (part?.type === "text") console.log(part.text)
    }
    if (info?.error) console.log("\nERROR:", JSON.stringify(info.error, null, 2))

    const toolParts = parts.filter((p: any) =>
      p?.type === "tool-invocation" || p?.type === "tool_use" || p?.type === "tool-result"
    )
    console.log(`\nTools used: ${toolParts.length > 0 ? `YES (${toolParts.length} parts)` : "NO"}`)
    console.log(`Tokens: ${JSON.stringify(info?.tokens)}`)
  } catch (err: any) {
    clearTimeout(timeoutId)
    console.error(err?.name === "AbortError" ? "TIMEOUT" : `Error: ${err?.message}`)
  }

  console.log(`\nSession: ${sessionId}`)
  console.log("\n=== Dispatch Complete ===")
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1) })
