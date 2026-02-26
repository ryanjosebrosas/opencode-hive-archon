import { tool } from "@opencode-ai/plugin"
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"

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

const TASK_ROUTING: Record<string, { provider: string; model: string }> = {
  // Tier 1: Fast / Simple
  "boilerplate": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
  "simple-fix": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
  "quick-check": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
  "general-opinion": { provider: "bailian-coding-plan", model: "qwen3-coder-next" },
  // Tier 2: Code-Specialized
  "test-scaffolding": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
  "logic-verification": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
  "code-review": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
  "api-analysis": { provider: "bailian-coding-plan", model: "qwen3-coder-plus" },
  // Tier 3: Reasoning / Architecture
  "research": { provider: "bailian-coding-plan", model: "qwen3.5-plus" },
  "architecture": { provider: "bailian-coding-plan", model: "qwen3.5-plus" },
  "library-comparison": { provider: "bailian-coding-plan", model: "qwen3.5-plus" },
  // Tier 4: Long Context / Factual
  "docs-lookup": { provider: "bailian-coding-plan", model: "kimi-k2.5" },
  // Tier 5: Prose / Documentation
  "docs-generation": { provider: "bailian-coding-plan", model: "minimax-m2.5" },
  // Tier 6: Strongest Reasoning
  "security-review": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
  "complex-codegen": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
  "complex-fix": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
  "deep-research": { provider: "anthropic", model: "claude-sonnet-4-20250514" },
}

export default tool({
  description:
    "Dispatch a prompt to any connected AI model via the OpenCode server. " +
    "Use this to delegate tasks (code generation, review, research, analysis) to other models " +
    "and receive their response inline. Requires `opencode serve` running. " +
    "Supports: auto-routing via taskType (e.g., 'security-review', 'boilerplate', 'research'), " +
    "custom system prompts, structured JSON output (via jsonSchema), and timeouts. " +
    "Either provide taskType for auto-routing, or explicit provider/model. " +
    "Provider/model examples: anthropic/claude-sonnet-4-20250514, openai/gpt-4.1, " +
    "bailian-coding-plan/qwen3.5-plus, bailian-coding-plan/qwen3-coder-plus",
  args: {
    provider: tool.schema
      .string()
      .optional()
      .describe(
        "Provider ID (e.g. 'anthropic', 'bailian-coding-plan'). " +
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
        "Delete the session after dispatch (default: true for new sessions, false for reused sessions)",
      ),
    timeout: tool.schema
      .number()
      .optional()
      .describe(
        "Timeout in seconds for the dispatch call (default: 120s). " +
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
          "Values: boilerplate, simple-fix, quick-check, general-opinion, " +
          "test-scaffolding, logic-verification, code-review, api-analysis, " +
          "research, architecture, library-comparison, docs-lookup, " +
          "docs-generation, security-review, complex-codegen, complex-fix, deep-research",
      ),
  },
  async execute(args, _context) {
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
    const shouldCleanup = args.cleanup ?? !isReusedSession
    let sessionId = args.sessionId

    if (!sessionId) {
      try {
        const session = await client.session.create({
          title: `dispatch → ${resolvedProvider}/${resolvedModel}`,
        })
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

    // 4. Send prompt to target model
    let result: unknown
    try {
      result = await client.session.prompt(
        {
          sessionID: sessionId,
          model: {
            providerID: resolvedProvider,
            modelID: resolvedModel,
          },
          system: args.systemPrompt,
          format: parsedFormat,
          parts: [{ type: "text" as const, text: args.prompt }],
        },
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
    if (routedVia) modifiers.push(`routed: ${routedVia}`)
    if (args.systemPrompt) modifiers.push("custom-system")
    if (parsedFormat) modifiers.push("structured-json")
    if (args.timeout !== undefined) modifiers.push(`timeout-${effectiveTimeout}s`)
    const modifierStr =
      modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""
    const header = `--- dispatch response from ${resolvedProvider}/${resolvedModel}${modifierStr} ---\n`
    return header + responseText + cleanupNote
  },
})
