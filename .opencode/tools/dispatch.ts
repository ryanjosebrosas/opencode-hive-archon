import { tool } from "@opencode-ai/plugin"
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"


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

/**
 * Attempt a single dispatch with given provider/model
 * Returns success/failure result for fallback handling
 */
async function attemptDispatch(
  args: any,
  resolvedProvider: string,
  resolvedModel: string,
  client: any,
  baseUrl: string,
  effectiveTimeout: number,
  _primerContent: string | null,
  parsedFormat: any,
  isReusedSession: boolean,
  finalIsAgentMode: boolean,
  shouldCleanup: boolean,
  sessionId: string | null = null
): Promise<{
  success: boolean
  text?: string
  error?: string
  sessionId?: string
  cleanupNote?: string
}> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), effectiveTimeout * 1000)
  
  let attemptSessionId = sessionId
  let cleanupNote = ""
  
  // Create session if not provided
  if (!attemptSessionId) {
    try {
      const sessionParams: Record<string, unknown> = {
        title: finalIsAgentMode
          ? `agent → ${resolvedProvider}/${resolvedModel}`
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
          { permission: "task", pattern: "*", action: "deny" },
          { permission: "external_directory", pattern: "*", action: "deny" },
          { permission: "webfetch", pattern: "*", action: "deny" },
          { permission: "websearch", pattern: "*", action: "deny" },
        ]
      }

      const session = await client.session.create(sessionParams as any)
      attemptSessionId = session.data?.id
      if (!attemptSessionId) {
        clearTimeout(timeoutId)
        return {
          success: false,
          error: `[dispatch error] Session creation returned no ID. Response: ${safeStringify(session.data)}`
        }
      }
    } catch (err: unknown) {
      clearTimeout(timeoutId)
      return {
        success: false,
        error: `[dispatch error] Failed to create session: ${getErrorMessage(err)}`
      }
    }
  }

  // Build prompt — prepend primer in BOTH text and agent mode
  // Agent mode previously skipped primer assuming the model reads AGENTS.md itself,
  // but AGENTS.md has no Archon RAG instructions — the primer is the only way to
  // tell dispatched agents how to use the knowledge base.
  let promptText = _primerContent
    ? `${_primerContent}\n\n---\n\n${args.prompt}`
    : args.prompt

  // Send prompt
  let result: unknown
  try {
    const promptParams: Record<string, unknown> = {
      sessionID: attemptSessionId,
      model: {
        providerID: resolvedProvider,
        modelID: resolvedModel,
      },
      system: args.systemPrompt,
      format: parsedFormat,
      parts: [{ type: "text" as const, text: promptText }],
    }

    if (finalIsAgentMode) {
      promptParams.agent = "build"
    }

    result = await client.session.prompt(
      promptParams as any,
      { signal: controller.signal },
    )
  } catch (err: unknown) {
    clearTimeout(timeoutId)
    
    // Cleanup session on error
    if (shouldCleanup && attemptSessionId) {
      try {
        await client.session.delete({ sessionID: attemptSessionId })
      } catch { /* best effort */ }
    }
    
    // Check if this was a timeout abort
    if (
      (err instanceof Error && err.name === "AbortError") ||
      controller.signal.aborted
    ) {
      return {
        success: false,
        error: `[dispatch error] Timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${effectiveTimeout}s.`
      }
    }
    
    return {
      success: false,
      error: `[dispatch error] Prompt failed for ${resolvedProvider}/${resolvedModel}: ${getErrorMessage(err)}`
    }
  }

  // Clear timeout if prompt completed successfully
  clearTimeout(timeoutId)

  // Check for empty response or swallowed timeout
  const resultRecord = asRecord(result)
  const resultError = asRecord(resultRecord?.error) ?? resultRecord?.error
  const resultData = asRecord(resultRecord?.data)

  // Check if SDK swallowed a timeout abort
  if (controller.signal.aborted || (resultError && (resultError as any)?.name === "AbortError")) {
    if (shouldCleanup && attemptSessionId) {
      try { await client.session.delete({ sessionID: attemptSessionId }) } catch { /* best effort */ }
    }
    return {
      success: false,
      error: `[dispatch error] Timeout: ${resolvedProvider}/${resolvedModel} did not respond within ${effectiveTimeout}s.`
    }
  }

  if (!resultData || Object.keys(resultData).length === 0) {
    if (shouldCleanup && attemptSessionId) {
      try { await client.session.delete({ sessionID: attemptSessionId }) } catch { /* best effort */ }
    }
    return {
      success: false,
      error: `[dispatch error] Empty response from ${resolvedProvider}/${resolvedModel}.`
    }
  }

  // Extract response text
  let responseText = ""
  try {
    const data = resultData
    const info = asRecord(data?.info)
    if (parsedFormat) {
      const structured = info?.structured
      if (structured !== undefined && structured !== null) {
        responseText = typeof structured === "string"
          ? structured
          : JSON.stringify(structured, null, 2)
      } else {
        const error = asRecord(info?.error)
        const errorName = error?.name
        const errorData = asRecord(error?.data)
        if (errorName === "StructuredOutputError") {
          const retries = errorData?.retries ?? "unknown"
          const message = errorData?.message ?? "unknown error"
          responseText = `[dispatch error] Structured output failed after ${retries} retries: ${message}`
        } else {
          responseText = extractTextFromParts(data?.parts)
          if (!responseText) {
            responseText = `[dispatch warning] No structured output or text parts. Raw: ${safeStringify(data)}`
          }
        }
      }
    } else {
      responseText = extractTextFromParts(data?.parts)
      if (!responseText) {
        const infoError = asRecord(info?.error)
        if (infoError) {
          const errName = infoError.name ?? "unknown"
          const errData = asRecord(infoError.data)
          const errMsg = errData?.message ?? "unknown error"
          const statusCode = errData?.statusCode ?? ""
          responseText = (
            `[dispatch error] ${resolvedProvider}/${resolvedModel} returned an API error.\n` +
            `Error: ${errName} ${statusCode ? `(${statusCode})` : ""} — ${errMsg}`
          )
        } else {
          responseText = `[dispatch warning] No text parts in response. Raw: ${safeStringify(data)}`
        }
      }
    }
  } catch (err: unknown) {
    responseText = `[dispatch warning] Could not parse response: ${getErrorMessage(err)}. Raw: ${safeStringify(result)}`
  }

  // Cleanup session if appropriate
  if (shouldCleanup && attemptSessionId) {
    try {
      await client.session.delete({ sessionID: attemptSessionId })
    } catch {
      cleanupNote = "\n[dispatch note] Session cleanup failed (non-critical)."
    }
  } else if (!shouldCleanup && !isReusedSession) {
    cleanupNote = `\n[dispatch note] Session preserved: ${attemptSessionId} (pass sessionId to continue conversation)`
  }

  return {
    success: true,
    text: responseText,
    sessionId: attemptSessionId,
    cleanupNote
  }
}

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

// 5-Tier Cost-Optimized Model Cascade — 51 free models across 3 providers
// T1: Implementation (FREE) — bailian-coding-plan-test (6 models: qwen3-coder-next, qwen3-coder-plus, qwen3.5-plus, qwen3-max, kimi-k2.5, minimax-m2.5)
// T2: First Validation (FREE) — zai-coding-plan (5 GLM models: glm-5, glm-4.5, glm-4.7, glm-4.7-flash, glm-4.7-flashx)
// T3: Second Validation (FREE) — ollama-cloud (33 models: deepseek, kimi, mistral, qwen, devstral)
// T4: Code Review (PAID cheap) — openai Codex
// T5: Final Review (PAID expensive) — anthropic Claude (last resort only)
const TASK_ROUTING: Record<string, { provider: string; model: string }> = {
  // === T1: Implementation (FREE — bailian-coding-plan-test) ===
  // T1a: Fast / Simple tasks → qwen3-coder-next
  "boilerplate": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "simple-fix": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "quick-check": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "general-opinion": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "pre-commit-analysis": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  // T1b: Code-heavy tasks → qwen3-coder-plus
  "test-scaffolding": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "test-generation": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "logic-verification": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "api-analysis": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  // T1c: Complex implementation / reasoning → qwen3.5-plus
  "complex-codegen": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "complex-fix": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "research": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "architecture": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "library-comparison": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "pattern-scan": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  // T1d: Long context / factual → kimi-k2.5
  "docs-lookup": { provider: "bailian-coding-plan-test", model: "kimi-k2.5" },
  // T1e: Prose / documentation → minimax-m2.5
  "docs-generation": { provider: "bailian-coding-plan-test", model: "minimax-m2.5" },
  "docstring-generation": { provider: "bailian-coding-plan-test", model: "minimax-m2.5" },
  // T1f: Complex reasoning / plan review → qwen3-max
  "deep-plan-review": { provider: "bailian-coding-plan-test", model: "qwen3-max-2026-01-23" },
  "complex-reasoning": { provider: "bailian-coding-plan-test", model: "qwen3-max-2026-01-23" },
  // T1b expanded: code quality review
  "code-quality-review": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  // T1d expanded: long context review
  "long-context-review": { provider: "bailian-coding-plan-test", model: "kimi-k2.5" },
  // T1e expanded: changelog
  "changelog-generation": { provider: "bailian-coding-plan-test", model: "minimax-m2.5" },

  // === T2: First Validation (FREE — zai-coding-plan GLM family) ===
  "thinking-review": { provider: "zai-coding-plan", model: "glm-5" },
  "first-validation": { provider: "zai-coding-plan", model: "glm-5" },
  "code-review": { provider: "zai-coding-plan", model: "glm-5" },
  "security-review": { provider: "zai-coding-plan", model: "glm-5" },
  "plan-review": { provider: "zai-coding-plan", model: "glm-5" },
  "fast-review": { provider: "zai-coding-plan", model: "glm-4.7-flashx" },
  "style-review": { provider: "zai-coding-plan", model: "glm-4.7-flash" },
  "regression-check": { provider: "zai-coding-plan", model: "glm-4.7" },
  // T2b: Architecture / design → glm-4.5 (ZAI flagship)
  "architecture-audit": { provider: "zai-coding-plan", model: "glm-4.5" },
  "design-review": { provider: "zai-coding-plan", model: "glm-4.5" },
  // T2a expanded: logic review (separate from code-review)
  "logic-review": { provider: "zai-coding-plan", model: "glm-5" },
  // T2c expanded: compatibility check
  "compatibility-check": { provider: "zai-coding-plan", model: "glm-4.7" },
  // T2d/e expanded: more fast check roles
  "ultra-fast-check": { provider: "zai-coding-plan", model: "glm-4.7-flashx" },
  "quick-style-check": { provider: "zai-coding-plan", model: "glm-4.7-flash" },

  // === T3: Second Validation (FREE — ollama-cloud diverse models) ===
  "second-validation": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "deep-research": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "independent-review": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "architecture-review": { provider: "ollama-cloud", model: "kimi-k2:1t" },
  "deep-code-review": { provider: "ollama-cloud", model: "deepseek-v3.1:671b" },
  "reasoning-review": { provider: "ollama-cloud", model: "cogito-2.1:671b" },
  "test-review": { provider: "ollama-cloud", model: "devstral-2:123b" },
  "multi-review": { provider: "zai-coding-plan", model: "glm-4.7" },
  "fast-second-opinion": { provider: "zai-coding-plan", model: "glm-4.7" },
  "heavy-codegen": { provider: "ollama-cloud", model: "mistral-large-3:675b" },
  "big-code-review": { provider: "ollama-cloud", model: "qwen3-coder:480b" },
  "thinking-second": { provider: "ollama-cloud", model: "kimi-k2-thinking" },
  "plan-critique": { provider: "ollama-cloud", model: "qwen3.5:397b" },

  // === T4: Code Review gate (PAID cheap — openai Codex) ===
  "codex-review": { provider: "openai", model: "gpt-5.3-codex" },
  "codex-validation": { provider: "openai", model: "gpt-5.3-codex" },

  // === T5: Final Review (PAID expensive — anthropic, last resort only) ===
  "final-review": { provider: "anthropic", model: "claude-sonnet-4-6" },
  "critical-review": { provider: "anthropic", model: "claude-sonnet-4-6" },
}

// Fallback chains by primary provider — tried in order on timeout/error/rate-limit
// Each entry: [primaryProviderPrefix, fallbackChain[]]
const FALLBACK_CHAINS: Array<{
  matchProvider: string  // prefix match on resolvedProvider
  fallbacks: Array<{ provider: string; model: string }>
}> = [
  {
    matchProvider: "bailian-coding-plan",  // matches bailian-coding-plan AND bailian-coding-plan-test
    fallbacks: [
      { provider: "zai-coding-plan", model: "glm-4.7" },
      { provider: "ollama-cloud", model: "devstral-2:123b" },
    ],
  },
  {
    matchProvider: "zai-coding-plan",
    fallbacks: [
      { provider: "ollama-cloud", model: "deepseek-v3.2" },
      { provider: "ollama-cloud", model: "devstral-2:123b" },
    ],
  },
  {
    matchProvider: "zai",  // plain zai (non coding-plan)
    fallbacks: [
      { provider: "ollama-cloud", model: "deepseek-v3.2" },
      { provider: "ollama-cloud", model: "devstral-2:123b" },
    ],
  },
]

function getFallbackChain(provider: string): Array<{ provider: string; model: string }> {
  for (const entry of FALLBACK_CHAINS) {
    if (provider.startsWith(entry.matchProvider)) {
      return entry.fallbacks
    }
  }
  return []
}


export default tool({
  description:
    "Dispatch a prompt to any connected AI model via the OpenCode server. " +
    "Three modes: 'text' (default) for prompt-response, 'agent' for full tool access, " +
    "'command' to invoke a slash command natively (e.g. /prime, /execute, /planning). " +
    "Agent mode lets models read files, edit code, run bash commands, and search the knowledge base. " +
    "Command mode uses the OpenCode command API directly — more reliable than asking a model to interpret slash commands as text. " +
    "5-tier cost-optimized cascade: T1 Implementation (FREE: bailian-coding-plan-test qwen3), " +
    "T2 First Validation (FREE: zai glm-5), T3 Second Validation (FREE: ollama deepseek), " +
    "T4 Code Review (PAID cheap: openai codex), T5 Final Review (PAID: anthropic, last resort). " +
    "Auto-routes via taskType or explicit provider/model. " +
    "Use mode:'command' + command:'execute' + prompt:'requests/plan.md' to run /execute natively. " +
    "Use mode:'agent' for implementation tasks, mode:'text' for reviews/opinions. " +
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
      .describe(
        "In text/agent mode: the full prompt to send to the model. " +
        "In command mode: the arguments to pass to the slash command " +
        "(e.g. 'requests/P1-11-plan.md' for /execute, 'P1-11 transaction-management' for /planning)."
      ),
    mode: tool.schema
      .string()
      .optional()
      .describe(
        "Dispatch mode: " +
        "'text' (default) for prompt-response only, " +
        "'agent' for full tool access (model reads/edits files, runs bash, searches knowledge base), " +
        "'command' to invoke a slash command natively via the OpenCode command API. " +
        "Use 'command' + command arg for /prime, /execute, /planning — more reliable than text instructions. " +
        "Use 'agent' for implementation tasks, 'text' for reviews/opinions.",
      ),
    command: tool.schema
      .string()
      .optional()
      .describe(
        "Slash command name to invoke in command mode (without the leading /). " +
        "Examples: 'prime', 'execute', 'planning', 'build', 'code-review'. " +
        "Only used when mode is 'command'. " +
        "The 'prompt' arg becomes the command arguments.",
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
    const DEFAULT_AGENT_TIMEOUT = 300 // 5 minutes for agent mode (multi-step)

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
    if (args.mode && args.mode !== "text" && args.mode !== "agent" && args.mode !== "command") {
      return `[dispatch error] Invalid mode: "${args.mode}". Must be "text", "agent", or "command".`
    }

    // Command mode validation
    const isCommandMode = effectiveMode === "command"
    if (isCommandMode && !args.command) {
      return `[dispatch error] mode:'command' requires a 'command' arg (e.g. command:'execute', command:'prime').`
    }
    if (args.command && !isCommandMode) {
      return `[dispatch error] 'command' arg is only valid when mode is 'command'.`
    }

    // Update mode flags after potential fallback
    const finalIsAgentMode = effectiveMode === "agent"

    // Validate steps arg
    if (args.steps !== undefined) {
      if (!Number.isInteger(args.steps) || args.steps < 1 || args.steps > 100) {
        return "[dispatch error] steps must be an integer between 1 and 100"
      }
      if (!finalIsAgentMode) {
        return "[dispatch error] 'steps' is only valid in agent mode"
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

    // 2.2. COMMAND MODE — invoke slash command natively via OpenCode command API
    // More reliable than asking a model to interpret "/execute ..." as prose instructions.
    // Use for: /prime, /execute <plan>, /planning <spec>, /build <spec>, /code-review, etc.
    if (isCommandMode) {
      const cmdTimeout = args.timeout ?? 600 // commands can take a while
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), cmdTimeout * 1000)

      let cmdSessionId: string | undefined
      try {
        // Create a session for the command
        const sessionResp = await client.session.create({
          title: `cmd → /${args.command} ${args.prompt.slice(0, 40)}`,
        } as any)
        cmdSessionId = sessionResp.data?.id
        if (!cmdSessionId) {
          clearTimeout(timeoutId)
          return `[dispatch error] command mode: failed to create session.`
        }

        // Invoke the slash command via the command API
        const cmdResult = await (client.session as any).command(
          {
            sessionID: cmdSessionId,
            command: args.command,
            arguments: args.prompt,
            ...(resolvedProvider && resolvedModel
              ? { model: { providerID: resolvedProvider, modelID: resolvedModel } }
              : {}),
          },
          { signal: controller.signal }
        )
        clearTimeout(timeoutId)

        // Cleanup
        try { await client.session.delete({ sessionID: cmdSessionId }) } catch { /* best effort */ }

        // Extract text
        const cmdData = asRecord(asRecord(cmdResult)?.data)
        const responseText =
          extractTextFromParts(cmdData?.parts) ||
          `[dispatch note] /${args.command} executed (no text output).`

        return (
          `--- dispatch response: /${args.command} [command-mode, ${resolvedProvider}/${resolvedModel}] ---\n` +
          responseText
        )
      } catch (err: unknown) {
        clearTimeout(timeoutId)
        if (cmdSessionId) {
          try { await client.session.delete({ sessionID: cmdSessionId }) } catch { /* best effort */ }
        }
        if ((err instanceof Error && err.name === "AbortError") || controller.signal.aborted) {
          return `[dispatch error] command mode timeout: /${args.command} did not complete within ${cmdTimeout}s.`
        }
        return `[dispatch error] command mode: /${args.command} failed: ${getErrorMessage(err)}`
      }
    }

    // 2.5. Set up timeout (mandatory — agent mode gets longer default)
    const effectiveTimeout = args.timeout ?? (finalIsAgentMode ? DEFAULT_AGENT_TIMEOUT : DEFAULT_TIMEOUT_SECONDS)
    if (!Number.isFinite(effectiveTimeout) || effectiveTimeout <= 0) {
      return "[dispatch error] timeout must be a positive number of seconds"
    }
    if (effectiveTimeout > MAX_TIMEOUT_SECONDS) {
      return `[dispatch error] timeout must be <= ${MAX_TIMEOUT_SECONDS} seconds`
    }

    // 2.6. Parse structured output format if requested
    let parsedFormat:
      | { type: "json_schema"; schema: Record<string, unknown>; retryCount?: number }
      | undefined
    if (args.jsonSchema) {
      try {
        const schema = JSON.parse(args.jsonSchema)
        if (!asRecord(schema) || Array.isArray(schema)) {
          return (
            "[dispatch error] jsonSchema must parse to a JSON object schema\n" +
            `Example:\n` +
            `'{"type":"object","properties":{"summary":{"type":"string"}}}'`
          )
        }
        parsedFormat = { type: "json_schema" as const, schema, retryCount: 2 }
      } catch (parseErr: unknown) {
        return (
          `[dispatch error] Invalid jsonSchema: ${getErrorMessage(parseErr)}\n` +
          `The jsonSchema arg must be a valid JSON string. Example:\n` +
          `'{"type":"object","properties":{"summary":{"type":"string"}}}'`
        )
      }
    }

    // 3. Session — reuse or create
    const isReusedSession = !!args.sessionId
    // Agent mode: default to preserving session (for multi-turn). Text mode: cleanup by default.
    const shouldCleanup = args.cleanup ?? (finalIsAgentMode ? false : !isReusedSession)
    let sessionId = args.sessionId

    // Get fallback chain for this provider
    const fallbackChain = getFallbackChain(resolvedProvider)
    const attemptedModels: Array<{ provider: string; model: string; error?: string }> = []

    // Try primary model first
    attemptedModels.push({ provider: resolvedProvider, model: resolvedModel })
    
    let finalResult: {
      success: boolean
      text?: string
      error?: string
      sessionId?: string
      cleanupNote?: string
    }

    // Attempt primary dispatch
    finalResult = await attemptDispatch(
      args, resolvedProvider, resolvedModel, client, baseUrl, effectiveTimeout,
      _primerContent, parsedFormat, isReusedSession, finalIsAgentMode, shouldCleanup, sessionId
    )

    // If primary failed, try fallbacks
    if (!finalResult.success && fallbackChain.length > 0) {
      for (const fallback of fallbackChain) {
        attemptedModels.push({ 
          provider: fallback.provider, 
          model: fallback.model 
        })
        
        // Try fallback dispatch
        finalResult = await attemptDispatch(
          args, fallback.provider, fallback.model, client, baseUrl, effectiveTimeout,
          _primerContent, parsedFormat, isReusedSession, finalIsAgentMode, shouldCleanup
        )
        
        if (finalResult.success) {
          // Update to the fallback model that succeeded
          resolvedProvider = fallback.provider
          resolvedModel = fallback.model
          break
        } else {
          // Record the error for this fallback attempt
          attemptedModels[attemptedModels.length - 1].error = finalResult.error
        }
      }
    }

    // If all attempts failed, return comprehensive error
    if (!finalResult.success) {
      const errorMessages = attemptedModels.map(attempt => {
        if (attempt.error) {
          // Extract just the error type (timeout, rate-limit, etc.)
          const match = attempt.error.match(/\[(dispatch error)\]\s*(\w+):/)
          return match ? match[2].toLowerCase() : "error"
        }
        return "unknown"
      })

      const attemptedList = attemptedModels.map(attempt => 
        `${attempt.provider}/${attempt.model}`
      ).join(", ")

      const errorList = attemptedModels.map((attempt, index) => 
        `${attempt.provider}/${attempt.model} (${errorMessages[index]})`
      ).join(", ")

      return (
        `--- dispatch error: all models failed ---\n` +
        `Tried: ${errorList}\n` +
        `\nPrimary attempt failed: ${attemptedModels[0].error}\n` +
        (attemptedModels.length > 1 ? `Fallback attempts also failed.\n` : "")
      )
    }

    // 7. Return response with metadata header
    const modifiers: string[] = []
    if (finalIsAgentMode) modifiers.push("agent-mode")
    if (_primerContent) modifiers.push("primer")
    if (routedVia) modifiers.push(`routed: ${routedVia}`)
    if (args.systemPrompt) modifiers.push("custom-system")
    if (parsedFormat) modifiers.push("structured-json")
    if (args.timeout !== undefined) modifiers.push(`timeout-${effectiveTimeout}s`)
    if (finalIsAgentMode && args.steps) modifiers.push(`steps-${args.steps}`)
    
    // Add fallback indicator if we used a fallback
    if (attemptedModels.length > 1) {
      const primaryModel = `${attemptedModels[0].provider}/${attemptedModels[0].model}`
      modifiers.push(`fallback-from: ${primaryModel}`)
    }
    
    const modifierStr =
      modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""
    const header = `--- dispatch response from ${resolvedProvider}/${resolvedModel}${modifierStr} ---\n`
    return header + finalResult.text! + (finalResult.cleanupNote || "")
  },
})
