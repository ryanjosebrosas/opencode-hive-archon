import { tool } from "@opencode-ai/plugin"
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync, writeFileSync } from "node:fs"
import { join, dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { execSync } from "node:child_process"

// Load project primer once at module scope — prepended to every dispatched prompt
const PRIMER_FILENAME = "_dispatch-primer.md"
let _primerContent: string | null = null
try {
  const toolDir = typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url))
  _primerContent = readFileSync(join(toolDir, PRIMER_FILENAME), "utf-8")
} catch {
  // Non-fatal: primer file missing or unreadable — dispatches proceed without it
  _primerContent = null
}

const getErrorMessage = (err: unknown): string => {
  if (err instanceof Error) {
    return err.message
  }
  if (typeof err === "string") {
    return err
  }
  try {
    return JSON.stringify(err)
  } catch {
    return String(err)
  }
}

const MAX_TIMEOUT_SECONDS = 2_147_483
const MAX_RELAY_TURNS = 5
const ARCHON_MCP_URL = "http://159.195.45.47:8051/mcp"

// Relay mode tool instructions — prepended to prompts for T1-T3 free providers
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

const asRecord = (value: unknown): Record<string, unknown> | undefined => {
  if (typeof value === "object" && value !== null) {
    return value as Record<string, unknown>
  }
  return undefined
}

const extractTextFromParts = (parts: unknown): string => {
  if (!Array.isArray(parts)) {
    return ""
  }
  const texts: string[] = []
  for (const part of parts) {
    const record = asRecord(part)
    if (!record) {
      continue
    }
    if (record.type === "text" && typeof record.text === "string" && record.text) {
      texts.push(record.text)
    }
  }
  return texts.join("\n")
}

const safeStringify = (value: unknown, maxChars = 2000): string => {
  try {
    return JSON.stringify(value).slice(0, maxChars)
  } catch {
    return String(value).slice(0, maxChars)
  }
}

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

// 5-Tier Cost-Optimized Model Cascade
// T1: Implementation (FREE) — bailian-coding-plan-test / zai-coding-plan fallback
// T2: First Validation (FREE) — zai-coding-plan GLM thinking models
// T3: Second Validation (FREE) — ollama-cloud independent model family
// T4: Code Review (PAID cheap) — openai Codex
// T5: Final Review (PAID expensive) — anthropic Claude (last resort only)
const TASK_ROUTING: Record<string, { provider: string; model: string }> = {
  // === T1: Implementation (FREE — bailian-coding-plan-test) ===
  // T1a: Fast / Simple tasks → qwen3-coder-next
  "boilerplate": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "simple-fix": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "quick-check": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "general-opinion": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  // T1b: Code-heavy tasks → qwen3-coder-plus
  "test-scaffolding": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "logic-verification": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "api-analysis": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  // T1c: Complex implementation / reasoning → qwen3.5-plus
  "complex-codegen": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "complex-fix": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "research": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "architecture": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "library-comparison": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  // T1d: Long context / factual → kimi-k2.5
  "docs-lookup": { provider: "bailian-coding-plan-test", model: "kimi-k2.5" },
  // T1e: Prose / documentation → minimax-m2.5
  "docs-generation": { provider: "bailian-coding-plan-test", model: "minimax-m2.5" },

  // === T2: First Validation (FREE — zai-coding-plan GLM thinking) ===
  "thinking-review": { provider: "zai-coding-plan", model: "glm-5" },
  "first-validation": { provider: "zai-coding-plan", model: "glm-5" },
  "code-review": { provider: "zai-coding-plan", model: "glm-5" },
  "security-review": { provider: "zai-coding-plan", model: "glm-5" },

  // === T3: Second Validation (FREE — ollama-cloud independent family) ===
  "second-validation": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "deep-research": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "independent-review": { provider: "ollama-cloud", model: "deepseek-v3.2" },

  // === T4: Code Review gate (PAID cheap — openai Codex) ===
  "codex-review": { provider: "openai", model: "gpt-5.3-codex" },
  "codex-validation": { provider: "openai", model: "gpt-5.3-codex" },

  // === T5: Final Review (PAID expensive — anthropic, last resort only) ===
  "final-review": { provider: "anthropic", model: "claude-sonnet-4-6" },
  "critical-review": { provider: "anthropic", model: "claude-sonnet-4-6" },
}

// === Relay Mode Helper Functions ===

// Tool tag parser for relay mode
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

// Tool executors for relay mode
const PROJECT_ROOT = resolve(join(import.meta.dirname ?? ".", "..", ".."))

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

    return sessionId
  } catch (e: any) {
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

// Main tool executor
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

// Relay loop for T1-T3 free providers
async function relayLoop(
  client: ReturnType<typeof createOpencodeClient>,
  provider: string,
  model: string,
  userPrompt: string,
  timeoutMs: number,
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
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

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

    // Parse tool calls from response
    const toolCalls = parseToolCalls(responseText)

    if (toolCalls.length === 0) {
      // No tool calls — model is done
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
      return { finalResponse: responseText, turns: turn + 1, toolCalls: totalToolCalls }
    }

    // Execute tool calls
    totalToolCalls += toolCalls.length

    const results: string[] = []
    for (const call of toolCalls) {
      const result = await executeTool(call)
      results.push(`<tool_result name="${call.name}">\n${result}\n</tool_result>`)
    }

    // Build follow-up prompt with results
    currentPrompt = `Here are the results of your tool calls:\n\n${results.join("\n\n")}\n\nContinue your work. If you need more tools, use <tool> tags. If you're done, provide your final response with NO tool tags.`
  }

  // Max turns reached
  await client.session.delete({ sessionID: sessionId }).catch(() => {})
  return { finalResponse: "[RELAY] Max turns reached", turns: MAX_RELAY_TURNS, toolCalls: totalToolCalls }
}

export default tool({
  description:
    "Dispatch a prompt to any connected AI model via the OpenCode server. " +
    "Three modes: 'text' (default) for prompt-response, 'agent' for full tool access " +
    "(Anthropic/OpenAI only), 'relay' for text-based tool access (T1-T3 free providers). " +
    "Relay mode gives T1-T3 models file read/write, search, and Archon access through XML tags. " +
    "5-tier cost-optimized cascade: T1 Implementation (FREE: bailian-coding-plan-test qwen3), " +
    "T2 First Validation (FREE: zai glm-5), T3 Second Validation (FREE: ollama deepseek), " +
    "T4 Code Review (PAID cheap: openai codex), T5 Final Review (PAID: anthropic, last resort). " +
    "Auto-routes via taskType or explicit provider/model. Auto-fallback: agent→relay for T1-T3. " +
    "Use mode:'agent'/'relay' for T1 implementation, mode:'text' for reviews/opinions. " +
    "taskType examples: boilerplate, complex-codegen, code-review, thinking-review, " +
    "second-validation, codex-review, final-review. " +
    "Provider/model examples: bailian-coding-plan-test/qwen3.5-plus, zai-coding-plan/glm-5, " +
    "ollama-cloud/deepseek-v3.2, openai/gpt-5.3-codex, anthropic/claude-sonnet-4-6",
  args: {
    provider: tool.schema
      .string()
      .optional()
      .describe(
        "Provider ID (e.g. 'anthropic', 'bailian-coding-plan-test'). " +
          "Required unless taskType is provided.",
      ),
    model: tool.schema
      .string()
      .optional()
      .describe(
        "Model ID within the provider (e.g. 'claude-sonnet-4-20250514', 'qwen3.5-plus'). " +
          "Required unless taskType is provided.",
      ),
    prompt: tool.schema
      .string()
      .min(1, "prompt is required")
      .describe("The full prompt to send to the target model"),
    mode: tool.schema
      .string()
      .optional()
      .describe(
        "Dispatch mode: 'text' (default) for prompt-response only, " +
          "'agent' for full tool access (Anthropic/OpenAI only), " +
          "'relay' for text-based tool access (T1-T3 free providers via XML tags). " +
          "Agent/relay modes let the model read code, make edits, and run validation autonomously. " +
          "Auto-fallback: agent→relay for incompatible providers. " +
          "Use 'agent'/'relay' for implementation tasks, 'text' for reviews/opinions.",
      ),
    steps: tool.schema
      .number()
      .optional()
      .describe(
        "Max agentic iterations in agent mode (default: 25). " +
          "Each step is one tool call + response cycle. " +
          "Higher values let the model do more work autonomously. " +
          "Ignored in text mode.",
      ),
    sessionId: tool.schema
      .string()
      .optional()
      .describe(
        "Optional: reuse an existing session ID for multi-turn conversations. " +
          "If omitted, a new session is created (and cleaned up after).",
      ),
    port: tool.schema
      .number()
      .optional()
      .describe("OpenCode server port (default: 4096)"),
    cleanup: tool.schema
      .boolean()
      .optional()
      .describe(
        "Delete the session after dispatch (default: true for text mode new sessions, " +
          "false for agent mode and reused sessions)",
      ),
    timeout: tool.schema
      .number()
      .optional()
      .describe(
        "Timeout in seconds for the dispatch call (default: 120s for text, 300s for agent). " +
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
    taskType: tool.schema
      .string()
      .optional()
      .describe(
        "Optional: auto-route to the best model for this task type. " +
          "When provided, provider/model are resolved automatically. " +
          "Explicit provider/model args override taskType if both are given. " +
          "T1 Implementation (FREE): boilerplate, simple-fix, quick-check, general-opinion, " +
          "test-scaffolding, logic-verification, api-analysis, complex-codegen, complex-fix, " +
          "research, architecture, library-comparison, docs-lookup, docs-generation. " +
          "T2 First Validation (FREE): thinking-review, first-validation, code-review, security-review. " +
          "T3 Second Validation (FREE): second-validation, deep-research, independent-review. " +
          "T4 Code Review (PAID cheap): codex-review, codex-validation. " +
          "T5 Final Review (PAID expensive): final-review, critical-review.",
      ),
  },
  async execute(args, _context) {
    // 0. Resolve mode and routing
    let effectiveMode = args.mode || "text"
    const isAgentMode = effectiveMode === "agent"
    const isRelayMode = effectiveMode === "relay"
    const DEFAULT_AGENT_TIMEOUT = 300 // 5 minutes for agent/relay mode (multi-step)
    const DEFAULT_AGENT_STEPS = 25

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

    // Validate mode arg
    if (args.mode && args.mode !== "text" && args.mode !== "agent" && args.mode !== "relay") {
      return `[dispatch error] Invalid mode: "${args.mode}". Must be "text", "agent", or "relay".`
    }

    // Agent mode provider compatibility with auto-fallback to relay
    // Agent mode requires providers that support tool-use API (Anthropic, OpenAI).
    // Free providers (bailian-coding-plan-test, zai, ollama) return 404 on agent mode — they don't support tool calling.
    const AGENT_COMPATIBLE_PROVIDERS = ["anthropic", "openai", "opencode"]
    let autoFallbackNote = ""
    
    if (isAgentMode && resolvedProvider && !AGENT_COMPATIBLE_PROVIDERS.includes(resolvedProvider)) {
      // Auto-fallback from agent to relay for incompatible providers
      effectiveMode = "relay"
      autoFallbackNote = " (auto-fallback from agent)"
    }

    // Update mode flags after potential fallback
    const finalIsAgentMode = effectiveMode === "agent"
    const finalIsRelayMode = effectiveMode === "relay"

    // Validate steps arg
    if (args.steps !== undefined) {
      if (!Number.isInteger(args.steps) || args.steps < 1 || args.steps > 100) {
        return "[dispatch error] steps must be an integer between 1 and 100"
      }
      if (!finalIsAgentMode && !finalIsRelayMode) {
        return "[dispatch error] 'steps' is only valid in agent or relay mode"
      }
    }

    const serverPort = args.port ?? 4096
    if (!Number.isInteger(serverPort) || serverPort < 1 || serverPort > 65_535) {
      return "[dispatch error] port must be an integer between 1 and 65535"
    }
    const baseUrl = `http://127.0.0.1:${serverPort}`

    // 1. Create SDK client (v2 — flat parameter style with health check)
    let client: ReturnType<typeof createOpencodeClient>
    try {
      client = createOpencodeClient({ baseUrl })
    } catch (err: unknown) {
      return `[dispatch error] Failed to create SDK client: ${getErrorMessage(err)}`
    }

    // 2. Health check — verify server is running
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

    // 2.1. Provider pre-flight — verify provider is connected
    const connectedProviders = await getConnectedProviders(baseUrl)
    if (connectedProviders.length > 0 && !connectedProviders.includes(resolvedProvider)) {
      return (
        `[dispatch error] Provider '${resolvedProvider}' is not connected.\n` +
        `Connected providers: ${connectedProviders.join(", ")}\n` +
        `Run '/connect ${resolvedProvider}' in OpenCode to connect it.`
      )
    }

    // 2.5. Set up timeout (mandatory — agent/relay mode gets longer default)
    const effectiveTimeout = args.timeout ?? ((finalIsAgentMode || finalIsRelayMode) ? DEFAULT_AGENT_TIMEOUT : DEFAULT_TIMEOUT_SECONDS)
    if (!Number.isFinite(effectiveTimeout) || effectiveTimeout <= 0) {
      return "[dispatch error] timeout must be a positive number of seconds"
    }
    if (effectiveTimeout > MAX_TIMEOUT_SECONDS) {
      return `[dispatch error] timeout must be <= ${MAX_TIMEOUT_SECONDS} seconds`
    }
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), effectiveTimeout * 1000)

    // 2.6. Parse structured output format if requested
    let parsedFormat:
      | { type: "json_schema"; schema: Record<string, unknown>; retryCount?: number }
      | undefined
    if (args.jsonSchema) {
      try {
        const schema = JSON.parse(args.jsonSchema)
        if (!asRecord(schema) || Array.isArray(schema)) {
          clearTimeout(timeoutId)
          return (
            "[dispatch error] jsonSchema must parse to a JSON object schema\n" +
            `Example:\n` +
            `'{"type":"object","properties":{"summary":{"type":"string"}}}'`
          )
        }
        parsedFormat = { type: "json_schema" as const, schema, retryCount: 2 }
      } catch (parseErr: unknown) {
        clearTimeout(timeoutId)
        return (
          `[dispatch error] Invalid jsonSchema: ${getErrorMessage(parseErr)}\n` +
          `The jsonSchema arg must be a valid JSON string. Example:\n` +
          `'{"type":"object","properties":{"summary":{"type":"string"}}}'`
        )
      }
    }

    // 3. Session — reuse or create
    const isReusedSession = !!args.sessionId
    // Agent/relay mode: default to preserving session (for multi-turn). Text mode: cleanup by default.
    const shouldCleanup = args.cleanup ?? ((finalIsAgentMode || finalIsRelayMode) ? false : !isReusedSession)
    let sessionId = args.sessionId

    if (!sessionId) {
      try {
        // Agent mode: create session with tool permissions so the model can
        // read files, edit code, run bash (ruff/mypy/pytest), and search the codebase
        const sessionParams: Record<string, unknown> = {
          title: finalIsAgentMode
            ? `agent → ${resolvedProvider}/${resolvedModel}`
            : finalIsRelayMode
              ? `relay → ${resolvedProvider}/${resolvedModel}`
              : `dispatch → ${resolvedProvider}/${resolvedModel}`,
        }

        if (finalIsAgentMode) {
          sessionParams.permission = [
            { permission: "read", pattern: "*", action: "allow" },
            { permission: "edit", pattern: "*", action: "allow" },
            { permission: "bash", pattern: "*", action: "allow" },
            { permission: "glob", pattern: "*", action: "allow" },
            { permission: "grep", pattern: "*", action: "allow" },
            { permission: "list", pattern: "*", action: "allow" },
            { permission: "todoread", pattern: "*", action: "allow" },
            { permission: "todowrite", pattern: "*", action: "allow" },
            // Deny recursive dispatch and external access
            { permission: "task", pattern: "*", action: "deny" },
            { permission: "external_directory", pattern: "*", action: "deny" },
            { permission: "webfetch", pattern: "*", action: "deny" },
            { permission: "websearch", pattern: "*", action: "deny" },
          ]
        }

        const session = await client.session.create(sessionParams as any)
        sessionId = session.data?.id
        if (!sessionId) {
          clearTimeout(timeoutId)
          return `[dispatch error] Session creation returned no ID. Response: ${safeStringify(session.data)}`
        }
      } catch (err: unknown) {
        clearTimeout(timeoutId)
        return `[dispatch error] Failed to create session: ${getErrorMessage(err)}`
      }
    }

    // 4. Build prompt with optional primer prefix
    const promptText = _primerContent
      ? `${_primerContent}\n\n---\n\n${args.prompt}`
      : args.prompt

    // 4.1. Handle relay mode vs normal prompt
    let result: unknown
    let relayMetadata: { turns: number; toolCalls: number } | undefined

    if (finalIsRelayMode) {
      // Relay mode: run the relay loop
      try {
        const relayResult = await relayLoop(
          client,
          resolvedProvider,
          resolvedModel,
          promptText,
          effectiveTimeout * 1000
        )
        relayMetadata = { turns: relayResult.turns, toolCalls: relayResult.toolCalls }
        // Construct a result object that matches the expected format
        result = {
          data: {
            parts: [{ type: "text", text: relayResult.finalResponse }],
            info: {
              tokens: { output: relayResult.finalResponse.length },
            }
          }
        }
      } catch (err: unknown) {
        clearTimeout(timeoutId)
        if (
          (err instanceof Error && err.name === "AbortError") ||
          controller.signal.aborted
        ) {
          // Cleanup session on timeout
          if (shouldCleanup && sessionId) {
            try {
              await client.session.delete({ sessionID: sessionId })
            } catch {
              // Best effort cleanup
            }
          }
          return (
            `[dispatch error] Relay timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${effectiveTimeout}s.\n` +
            (args.timeout !== undefined
              ? `Consider increasing the timeout or using a faster model.`
              : `This was the default ${DEFAULT_AGENT_TIMEOUT}s timeout. Set 'timeout' arg for a custom value.`)
          )
        }
        // Attempt cleanup on failure
        if (shouldCleanup && sessionId) {
          try {
            await client.session.delete({ sessionID: sessionId })
          } catch {
            // Best effort cleanup
          }
        }
        return (
          `[dispatch error] Relay failed for ${resolvedProvider}/${resolvedModel}: ${getErrorMessage(err)}\n` +
          `Common causes: model not connected (run '/connect ${resolvedProvider}'), ` +
          `invalid model ID, or provider auth missing.`
        )
      }
    } else {
      // Normal mode (text or agent)
      try {
        // Agent mode: set agent to "general" for tool access, pass steps limit
        const promptParams: Record<string, unknown> = {
          sessionID: sessionId,
          model: {
            providerID: resolvedProvider,
            modelID: resolvedModel,
          },
          system: args.systemPrompt,
          format: parsedFormat,
          parts: [{ type: "text" as const, text: promptText }],
        }

        if (finalIsAgentMode) {
          // "general" agent has full tool access in OpenCode
          promptParams.agent = "general"
        }

        result = await client.session.prompt(
          promptParams as any,
          { signal: controller.signal },
        )
      } catch (err: unknown) {
        clearTimeout(timeoutId)
        // Check if this was a timeout abort
        if (
          (err instanceof Error && err.name === "AbortError") ||
          controller.signal.aborted
        ) {
          // Cleanup session on timeout
          if (shouldCleanup && sessionId) {
            try {
              await client.session.delete({ sessionID: sessionId })
            } catch {
              // Best effort cleanup
            }
          }
          return (
            `[dispatch error] Timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${effectiveTimeout}s.\n` +
            (args.timeout !== undefined
              ? `Consider increasing the timeout or using a faster model.`
              : `This was the default ${DEFAULT_TIMEOUT_SECONDS}s timeout. Set 'timeout' arg for a custom value.`)
          )
        }
        // Attempt cleanup on failure if we created the session
        if (shouldCleanup && sessionId) {
          try {
            await client.session.delete({ sessionID: sessionId })
          } catch {
            // Best effort cleanup
          }
        }
        return (
          `[dispatch error] Prompt failed for ${resolvedProvider}/${resolvedModel}: ${getErrorMessage(err)}\n` +
          `Common causes: model not connected (run '/connect ${resolvedProvider}'), ` +
          `invalid model ID, or provider auth missing.`
        )
      }
    }

    // Clear timeout if prompt completed successfully
    clearTimeout(timeoutId)

    // 4.5. Check for empty response or swallowed timeout
    // SDK doesn't throw on AbortError — it puts it in result.error and returns { data: {} }
    const resultRecord = asRecord(result)
    const resultError = asRecord(resultRecord?.error) ?? resultRecord?.error
    const resultData = asRecord(resultRecord?.data)

    // Check if SDK swallowed a timeout abort (AbortError in result.error, data is empty)
    if (controller.signal.aborted || (resultError && (resultError as any)?.name === "AbortError")) {
      if (shouldCleanup && sessionId) {
        try { await client.session.delete({ sessionID: sessionId }) } catch { /* best effort */ }
      }
      return (
        `[dispatch error] Timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${effectiveTimeout}s.\n` +
        (args.timeout !== undefined
          ? `Consider increasing the timeout or using a faster model.`
          : `This was the default ${DEFAULT_TIMEOUT_SECONDS}s timeout. Set 'timeout' arg for a custom value.`)
      )
    }

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

    // 5. Extract response
    let responseText = ""
    try {
      const data = resultData  // Already parsed in step 4.5
      const info = asRecord(data?.info)
      if (parsedFormat) {
        // Structured output mode — extract from info.structured
        const structured = info?.structured
        if (structured !== undefined && structured !== null) {
          responseText =
            typeof structured === "string"
              ? structured
              : JSON.stringify(structured, null, 2)
        } else {
          // Check for StructuredOutputError
          const error = asRecord(info?.error)
          const errorName = error?.name
          const errorData = asRecord(error?.data)
          if (errorName === "StructuredOutputError") {
            const retries = errorData?.retries ?? "unknown"
            const message = errorData?.message ?? "unknown error"
            responseText = `[dispatch error] Structured output failed after ${retries} retries: ${message}`
          } else {
            // Fallback to text parts even in structured mode
            responseText = extractTextFromParts(data?.parts)
            if (!responseText) {
              responseText = `[dispatch warning] No structured output or text parts. Raw: ${safeStringify(data)}`
            }
          }
        }
      } else {
        // Text mode — existing extraction logic
        responseText = extractTextFromParts(data?.parts)
        if (!responseText) {
          // Check for upstream API error in info.error (server returns 200 but model errored)
          const infoError = asRecord(info?.error)
          if (infoError) {
            const errName = infoError.name ?? "unknown"
            const errData = asRecord(infoError.data)
            const errMsg = errData?.message ?? "unknown error"
            const statusCode = errData?.statusCode ?? ""
            responseText = (
              `[dispatch error] ${resolvedProvider}/${resolvedModel} returned an API error.\n` +
              `Error: ${errName} ${statusCode ? `(${statusCode})` : ""} — ${errMsg}\n` +
              `This usually means the model ID is invalid or the provider has an upstream issue.`
            )
          } else {
            responseText = `[dispatch warning] No text parts in response. Raw: ${safeStringify(data)}`
          }
        }
      }
    } catch (err: unknown) {
      responseText = `[dispatch warning] Could not parse response: ${getErrorMessage(err)}. Raw: ${safeStringify(result)}`
    }

    // 6. Cleanup session if appropriate
    let cleanupNote = ""
    if (shouldCleanup && sessionId) {
      try {
        await client.session.delete({ sessionID: sessionId })
      } catch {
        cleanupNote =
          "\n[dispatch note] Session cleanup failed (non-critical)."
      }
    } else if (!shouldCleanup && !isReusedSession) {
      cleanupNote = `\n[dispatch note] Session preserved: ${sessionId} (pass sessionId to continue conversation)`
    }

    // 7. Return response with metadata header
    const modifiers: string[] = []
    if (finalIsAgentMode) modifiers.push("agent-mode")
    if (finalIsRelayMode) modifiers.push(`relay-mode${autoFallbackNote}`)
    if (relayMetadata) modifiers.push(`${relayMetadata.turns} turns, ${relayMetadata.toolCalls} tools`)
    if (_primerContent) modifiers.push("primer")
    if (routedVia) modifiers.push(`routed: ${routedVia}`)
    if (args.systemPrompt) modifiers.push("custom-system")
    if (parsedFormat) modifiers.push("structured-json")
    if (args.timeout !== undefined) modifiers.push(`timeout-${effectiveTimeout}s`)
    if ((finalIsAgentMode || finalIsRelayMode) && args.steps) modifiers.push(`steps-${args.steps}`)
    const modifierStr =
      modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""
    const header = `--- dispatch response from ${resolvedProvider}/${resolvedModel}${modifierStr} ---\n`
    return header + responseText + cleanupNote
  },
})
