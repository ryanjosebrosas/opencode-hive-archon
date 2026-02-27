// Prototype: Text-Mode Tool Relay for T1-T3 free providers.
// Since free providers can't use agent mode, this relay gives them
// file/search access through a text-based loop.
// Run with: cd .opencode && bun run tools/_test-relay-mode.ts
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync, writeFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { execSync } from "node:child_process"

const BASE_URL = "http://127.0.0.1:4096"
const PROJECT_ROOT = resolve(join(import.meta.dirname ?? ".", "..", ".."))
const MAX_RELAY_TURNS = 5
const ARCHON_MCP_URL = "http://159.195.45.47:8051/mcp"
const TIMEOUT_MS = 90_000

// --- Tool Relay Instructions (prepended to the prompt) ---
const RELAY_INSTRUCTIONS = `
## Tool Relay Mode

You have access to file system and search tools through a text relay. When you need to read files, search code, or query documentation, output the appropriate <tool> tag. The orchestrator will execute it and return results.

### Available Tools:

1. **Read a file**: \`<tool name="read" path="relative/path/to/file" />\`
2. **Find files by pattern**: \`<tool name="glob" pattern="**/*.ts" />\`
3. **Search file contents**: \`<tool name="grep" pattern="regex pattern" include="*.ts" />\`
4. **Search Archon knowledge base**: \`<tool name="archon_search" query="2-5 keyword query" />\`
5. **List Archon sources**: \`<tool name="archon_sources" />\`
6. **Run shell command**: \`<tool name="bash" cmd="command here" />\`
7. **Edit a file**:
\`\`\`
<tool name="edit" path="relative/path">
OLD: exact string to find
NEW: exact replacement string
</tool>
\`\`\`

### Rules:
- You MUST use tools to get real data — NEVER answer from your own knowledge when tools are available
- Output ONE OR MORE tool tags when you need information
- After tool results are returned, continue your work
- When you're done (no more tools needed), output your final answer with NO tool tags
- Keep tool usage efficient — read what you need, don't read everything
- For Archon search, use 2-5 focused keywords (NOT long sentences)
- IMPORTANT: If the user asks you to search or read something, ALWAYS use the appropriate tool first
`

// --- Tool Tag Parser ---
interface ToolCall {
  name: string
  attrs: Record<string, string>
  body?: string // For edit tool (content between open/close tags)
}

function parseToolCalls(text: string): ToolCall[] {
  const calls: ToolCall[] = []

  // Self-closing tags: <tool name="read" path="file.ts" />
  const selfClosingRegex = /<tool\s+([^>]*?)\/>/g
  let match: RegExpExecArray | null
  while ((match = selfClosingRegex.exec(text)) !== null) {
    const attrs = parseAttrs(match[1])
    if (attrs.name) {
      calls.push({ name: attrs.name, attrs })
    }
  }

  // Block tags: <tool name="edit" path="file.ts">...body...</tool>
  const blockRegex = /<tool\s+([^>]*?)>([\s\S]*?)<\/tool>/g
  while ((match = blockRegex.exec(text)) !== null) {
    const attrs = parseAttrs(match[1])
    if (attrs.name) {
      calls.push({ name: attrs.name, attrs, body: match[2].trim() })
    }
  }

  return calls
}

function parseAttrs(attrStr: string): Record<string, string> {
  const attrs: Record<string, string> = {}
  const regex = /(\w+)="([^"]*)"/g
  let m: RegExpExecArray | null
  while ((m = regex.exec(attrStr)) !== null) {
    attrs[m[1]] = m[2]
  }
  return attrs
}

// --- Tool Executors ---

function executeRead(path: string): string {
  const fullPath = resolve(PROJECT_ROOT, path)
  if (!fullPath.startsWith(PROJECT_ROOT)) {
    return `[ERROR] Path outside project: ${path}`
  }
  try {
    const content = readFileSync(fullPath, "utf-8")
    // Truncate very large files
    if (content.length > 50_000) {
      return content.slice(0, 50_000) + `\n\n[TRUNCATED: file is ${content.length} chars, showing first 50K]`
    }
    return content
  } catch (e: any) {
    return `[ERROR] Cannot read ${path}: ${e.message}`
  }
}

function executeGlob(pattern: string): string {
  try {
    // Use bash find as a glob alternative
    const result = execSync(
      `powershell -Command "Get-ChildItem -Path '${PROJECT_ROOT}' -Recurse -Name -Include '${pattern}' | Select-Object -First 50"`,
      { cwd: PROJECT_ROOT, timeout: 10_000, encoding: "utf-8" }
    )
    return result.trim() || "[No matches]"
  } catch (e: any) {
    // Fallback: use node glob
    try {
      const { glob } = require("glob")
      const files = glob.sync(pattern, { cwd: PROJECT_ROOT, maxDepth: 10 })
      return files.slice(0, 50).join("\n") || "[No matches]"
    } catch {
      return `[ERROR] Glob failed: ${e.message?.slice(0, 200)}`
    }
  }
}

function executeGrep(pattern: string, include?: string): string {
  try {
    const includeArg = include ? `--include="${include}"` : ""
    const result = execSync(
      `rg --line-number --max-count=20 --max-filesize=1M ${includeArg} "${pattern.replace(/"/g, '\\"')}" .`,
      { cwd: PROJECT_ROOT, timeout: 10_000, encoding: "utf-8" }
    )
    // Truncate if too long
    if (result.length > 10_000) {
      return result.slice(0, 10_000) + "\n[TRUNCATED]"
    }
    return result.trim() || "[No matches]"
  } catch (e: any) {
    if (e.status === 1) return "[No matches]" // rg returns 1 for no matches
    return `[ERROR] Grep failed: ${e.message?.slice(0, 200)}`
  }
}

function executeBash(cmd: string): string {
  // Safety: block destructive commands
  const blocked = ["rm -rf", "format", "del /s", "rmdir /s", "git push", "git reset --hard"]
  if (blocked.some(b => cmd.toLowerCase().includes(b))) {
    return `[BLOCKED] Command contains blocked pattern. Blocked: ${blocked.join(", ")}`
  }
  try {
    const result = execSync(cmd, {
      cwd: PROJECT_ROOT,
      timeout: 30_000,
      encoding: "utf-8",
      maxBuffer: 1024 * 1024,
    })
    if (result.length > 20_000) {
      return result.slice(0, 20_000) + "\n[TRUNCATED]"
    }
    return result.trim() || "[No output]"
  } catch (e: any) {
    return `[ERROR] Command failed (exit ${e.status}): ${e.stderr?.slice(0, 500) || e.message?.slice(0, 500)}`
  }
}

function executeEdit(path: string, body: string): string {
  const fullPath = resolve(PROJECT_ROOT, path)
  if (!fullPath.startsWith(PROJECT_ROOT)) {
    return `[ERROR] Path outside project: ${path}`
  }

  // Parse OLD/NEW from body
  const oldMatch = body.match(/^OLD:\s*([\s\S]*?)(?=\nNEW:)/m)
  const newMatch = body.match(/^NEW:\s*([\s\S]*)$/m)

  if (!oldMatch || !newMatch) {
    return "[ERROR] Edit body must contain OLD: and NEW: sections"
  }

  const oldStr = oldMatch[1].trimEnd()
  const newStr = newMatch[1].trimEnd()

  try {
    const content = readFileSync(fullPath, "utf-8")
    if (!content.includes(oldStr)) {
      return `[ERROR] OLD string not found in ${path}. Make sure you're matching exact whitespace.`
    }
    const count = content.split(oldStr).length - 1
    if (count > 1) {
      return `[ERROR] OLD string found ${count} times in ${path}. Make it more specific.`
    }
    const updated = content.replace(oldStr, newStr)
    writeFileSync(fullPath, updated)
    return `[OK] Edited ${path}: replaced ${oldStr.length} chars with ${newStr.length} chars`
  } catch (e: any) {
    return `[ERROR] Edit failed: ${e.message}`
  }
}

// MCP session ID for Archon
let archonSessionId: string | null = null

async function initArchonSession(): Promise<string | null> {
  try {
    // Step 1: Initialize
    const resp = await fetch(ARCHON_MCP_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          protocolVersion: "2024-11-05",
          capabilities: {},
          clientInfo: { name: "relay-dispatch", version: "0.1" },
        },
      }),
    })
    const sessionId = resp.headers.get("mcp-session-id")
    if (!sessionId) {
      console.log("  [Archon: no session ID in response headers]")
      return null
    }

    // Step 2: Send initialized notification (required before tool calls)
    await fetch(ARCHON_MCP_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": sessionId,
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "notifications/initialized",
      }),
    })

    console.log(`  [Archon session initialized: ${sessionId.slice(0, 8)}...]`)
    return sessionId
  } catch (e: any) {
    console.log(`  [Archon init failed: ${e.message}]`)
    return null
  }
}

async function callArchonTool(toolName: string, args: Record<string, unknown>): Promise<string> {
  if (!archonSessionId) {
    archonSessionId = await initArchonSession()
    if (!archonSessionId) return "[ERROR] Cannot connect to Archon MCP"
  }

  try {
    const resp = await fetch(ARCHON_MCP_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": archonSessionId,
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method: "tools/call",
        params: { name: toolName, arguments: args },
      }),
    })
    const text = await resp.text()
    const dataLine = text.split("\n").find(l => l.startsWith("data: "))
    if (dataLine) {
      const data = JSON.parse(dataLine.slice(6))
      if (data.result?.content) {
        return data.result.content.map((c: any) => c.text || JSON.stringify(c)).join("\n")
      }
      if (data.error) {
        return `[ERROR] Archon: ${data.error.message}`
      }
    }
    // Try raw JSON parse
    const json = JSON.parse(text)
    if (json.result?.content) {
      return json.result.content.map((c: any) => c.text || JSON.stringify(c)).join("\n")
    }
    return `[Archon response]: ${text.slice(0, 2000)}`
  } catch (e: any) {
    return `[ERROR] Archon call failed: ${e.message}`
  }
}

async function executeArchonSearch(query: string): Promise<string> {
  return callArchonTool("rag_search_knowledge_base", { query, match_count: 5 })
}

async function executeArchonSources(): Promise<string> {
  return callArchonTool("rag_get_available_sources", {})
}

// --- Main Tool Executor ---
async function executeTool(call: ToolCall): Promise<string> {
  switch (call.name) {
    case "read":
      return executeRead(call.attrs.path || "")
    case "glob":
      return executeGlob(call.attrs.pattern || "")
    case "grep":
      return executeGrep(call.attrs.pattern || "", call.attrs.include)
    case "bash":
      return executeBash(call.attrs.cmd || "")
    case "edit":
      return executeEdit(call.attrs.path || "", call.body || "")
    case "archon_search":
      return executeArchonSearch(call.attrs.query || "")
    case "archon_sources":
      return executeArchonSources()
    default:
      return `[ERROR] Unknown tool: ${call.name}`
  }
}

// --- Relay Loop ---
async function relayLoop(
  client: ReturnType<typeof createOpencodeClient>,
  provider: string,
  model: string,
  userPrompt: string,
): Promise<{ finalResponse: string; turns: number; toolCalls: number }> {
  // Create session (no permissions needed — text mode)
  const session = await client.session.create({
    title: `relay → ${provider}/${model}`,
  })
  const sessionId = session.data?.id
  if (!sessionId) throw new Error("No session ID")

  let currentPrompt = RELAY_INSTRUCTIONS + "\n\n---\n\n" + userPrompt
  let totalToolCalls = 0

  for (let turn = 0; turn < MAX_RELAY_TURNS; turn++) {
    console.log(`\n  [Turn ${turn + 1}/${MAX_RELAY_TURNS}] Sending prompt (${currentPrompt.length} chars)...`)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS)

    const res = await client.session.prompt(
      {
        sessionID: sessionId,
        model: { providerID: provider, modelID: model },
        parts: [{ type: "text" as const, text: currentPrompt }],
      },
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)

    const data = (res as any)?.data
    const info = data?.info
    if (info?.error) {
      throw new Error(`API error: ${JSON.stringify(info.error).slice(0, 300)}`)
    }

    const responseText = (data?.parts || [])
      .filter((p: any) => p?.type === "text")
      .map((p: any) => p.text)
      .join("")

    console.log(`  [Turn ${turn + 1}] Got ${responseText.length} chars, ${info?.tokens?.output || 0} output tokens`)

    // Parse tool calls from response
    const toolCalls = parseToolCalls(responseText)

    if (toolCalls.length === 0) {
      // No tool calls — model is done
      console.log(`  [Turn ${turn + 1}] No tool calls — relay complete`)
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
      return { finalResponse: responseText, turns: turn + 1, toolCalls: totalToolCalls }
    }

    // Execute tool calls
    console.log(`  [Turn ${turn + 1}] Found ${toolCalls.length} tool call(s): ${toolCalls.map(c => c.name).join(", ")}`)
    totalToolCalls += toolCalls.length

    const results: string[] = []
    for (const call of toolCalls) {
      console.log(`    Executing: ${call.name}(${JSON.stringify(call.attrs).slice(0, 100)})`)
      const result = await executeTool(call)
      results.push(`<tool_result name="${call.name}">\n${result}\n</tool_result>`)
      console.log(`    Result: ${result.slice(0, 100)}...`)
    }

    // Build follow-up prompt with results
    currentPrompt = `Here are the results of your tool calls:\n\n${results.join("\n\n")}\n\nContinue your work. If you need more tools, use <tool> tags. If you're done, provide your final response with NO tool tags.`
  }

  // Max turns reached
  await client.session.delete({ sessionID: sessionId }).catch(() => {})
  return { finalResponse: "[RELAY] Max turns reached", turns: MAX_RELAY_TURNS, toolCalls: totalToolCalls }
}

// --- Main Test ---
async function main() {
  console.log("=== Text-Mode Tool Relay Prototype ===\n")
  console.log(`Project root: ${PROJECT_ROOT}`)

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) {
    console.error("Server not healthy")
    process.exit(1)
  }

  // Test 1: File reading via relay
  console.log("\n--- Test 1: Read a file via relay (T1 Bailian) ---")
  try {
    const result = await relayLoop(
      client,
      "bailian-coding-plan-test",
      "qwen3.5-plus",
      "Read the file `mvp.md` and tell me:\n1. What is the project name?\n2. What is the main goal?\n3. How many sections does it have?\n\nUse the read tool to get the file contents first.",
    )
    console.log(`\n  RESULT (${result.turns} turns, ${result.toolCalls} tool calls):`)
    console.log(`  ${result.finalResponse.slice(0, 500)}`)
    console.log(`  Status: ${result.toolCalls > 0 ? "PASS (used tools)" : "FAIL (no tools used)"}`)
  } catch (e: any) {
    console.error(`  ERROR: ${e.message}`)
  }

  // Test 2: Archon search via relay
  console.log("\n--- Test 2: Archon search via relay (T1 Bailian) ---")
  try {
    const result = await relayLoop(
      client,
      "bailian-coding-plan-test",
      "qwen3.5-plus",
      "I need you to search the Archon knowledge base. Do NOT answer from your own knowledge.\n\nStep 1: Use archon_search tool with query 'retrieval augmented generation'\nStep 2: Summarize what you find\n\nYou MUST output a tool tag first. Do not skip this step.",
    )
    console.log(`\n  RESULT (${result.turns} turns, ${result.toolCalls} tool calls):`)
    console.log(`  ${result.finalResponse.slice(0, 500)}`)
    console.log(`  Status: ${result.toolCalls > 0 ? "PASS (used tools)" : "FAIL (no tools used)"}`)
  } catch (e: any) {
    console.error(`  ERROR: ${e.message}`)
  }

  console.log("\n=== Relay Test Complete ===")
}

main().catch(e => {
  console.error("Fatal:", e.message)
  process.exit(1)
})
