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
  _primerContent = null
}

// --- Utility functions (duplicated from dispatch.ts for tool independence) ---

const getErrorMessage = (err: unknown): string => {
  if (err instanceof Error) return err.message
  if (typeof err === "string") return err
  try {
    return JSON.stringify(err)
  } catch {
    return String(err)
  }
}

const asRecord = (value: unknown): Record<string, unknown> | undefined => {
  if (typeof value === "object" && value !== null) {
    return value as Record<string, unknown>
  }
  return undefined
}

const extractTextFromParts = (parts: unknown): string => {
  if (!Array.isArray(parts)) return ""
  const texts: string[] = []
  for (const part of parts) {
    const record = asRecord(part)
    if (
      record?.type === "text" &&
      typeof record.text === "string" &&
      record.text
    ) {
      texts.push(record.text as string)
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

// --- Task routing (duplicated from dispatch.ts — tools must be self-contained) ---
// 5-Tier Cost-Optimized Model Cascade (mirrors dispatch.ts)

const TASK_ROUTING: Record<string, { provider: string; model: string }> = {
  // === T1: Implementation (FREE — bailian-coding-plan-test) ===
  "boilerplate": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "simple-fix": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "quick-check": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "general-opinion": { provider: "bailian-coding-plan-test", model: "qwen3-coder-next" },
  "test-scaffolding": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "logic-verification": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "api-analysis": { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus" },
  "complex-codegen": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "complex-fix": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "research": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "architecture": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "library-comparison": { provider: "bailian-coding-plan-test", model: "qwen3.5-plus" },
  "docs-lookup": { provider: "bailian-coding-plan-test", model: "kimi-k2.5" },
  "docs-generation": { provider: "bailian-coding-plan-test", model: "minimax-m2.5" },
  // === T2: First Validation (FREE — zai-coding-plan GLM thinking) ===
  "thinking-review": { provider: "zai-coding-plan", model: "glm-5" },
  "first-validation": { provider: "zai-coding-plan", model: "glm-5" },
  "code-review": { provider: "zai-coding-plan", model: "glm-5" },
  "security-review": { provider: "zai-coding-plan", model: "glm-5" },
  // === T3: Second Validation (FREE — ollama-cloud) ===
  "second-validation": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "deep-research": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  "independent-review": { provider: "ollama-cloud", model: "deepseek-v3.2" },
  // === T4: Code Review (PAID cheap — openai Codex) ===
  "codex-review": { provider: "openai", model: "gpt-5.3-codex" },
  "codex-validation": { provider: "openai", model: "gpt-5.3-codex" },
  // === T5: Final Review (PAID expensive — anthropic) ===
  "final-review": { provider: "anthropic", model: "claude-sonnet-4-6" },
  "critical-review": { provider: "anthropic", model: "claude-sonnet-4-6" },
}

// --- Main tool ---

export default tool({
  description:
    "Send the same prompt to multiple AI models in parallel and compare their responses. " +
    "Use this for multi-model consensus (code review, research cross-referencing, model quality comparison). " +
    "Requires `opencode serve` running. Returns all responses in a structured comparison format. " +
    "Each model runs in its own session with independent timeout. " +
    "Provider/model examples: anthropic/claude-sonnet-4-20250514, bailian-coding-plan-test/qwen3.5-plus, " +
    "bailian-coding-plan-test/qwen3-coder-plus, openai/gpt-4.1",
  args: {
    models: tool.schema
      .string()
      .optional()
      .describe(
        'JSON array of model targets. Each target has "provider" and "model" fields. Minimum 2 models. ' +
          "Required unless taskType is provided (which resolves to a single default model). " +
          'Example: \'[{"provider":"bailian-coding-plan-test","model":"qwen3-coder-plus"},' +
          '{"provider":"bailian-coding-plan-test","model":"qwen3.5-plus"}]\'',
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
        "Timeout in seconds per model (default: 120s). " +
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
    taskType: tool.schema
      .string()
      .optional()
      .describe(
        "Optional: auto-route to the best model for this task type. " +
          "When provided and 'models' is not given, dispatches to the single best model " +
          "for this task type (use 'dispatch' tool instead for single-model with taskType). " +
          "When 'models' is also provided, taskType is ignored. " +
          "Values: boilerplate, simple-fix, quick-check, general-opinion, " +
          "test-scaffolding, logic-verification, code-review, api-analysis, " +
          "research, architecture, library-comparison, docs-lookup, " +
          "docs-generation, security-review, complex-codegen, complex-fix, deep-research",
      ),
  },
  async execute(args, _context) {
    // 0. Resolve routing: taskType → helpful redirect (batch requires explicit models)
    let modelsJson = args.models

    if (!modelsJson && args.taskType) {
      const route = TASK_ROUTING[args.taskType]
      if (!route) {
        return (
          `[batch-dispatch error] Unknown taskType: "${args.taskType}"\n` +
          `Valid values: ${Object.keys(TASK_ROUTING).join(", ")}\n` +
          "Note: For single-model dispatch with taskType, use the `dispatch` tool instead."
        )
      }
      // Single model from routing — batch requires 2+, suggest dispatch instead
      return (
        `[batch-dispatch info] taskType "${args.taskType}" resolves to a single model: ${route.provider}/${route.model}\n` +
        "Batch dispatch requires 2+ models. Use the `dispatch` tool with taskType for single-model routing, " +
        "or provide 'models' JSON array explicitly for batch comparison."
      )
    }

    if (!modelsJson) {
      return (
        "[batch-dispatch error] Either provide 'models' (JSON array of 2+ targets), " +
        "or use the `dispatch` tool with 'taskType' for single-model auto-routing."
      )
    }

    // 1. Parse models array
    let targets: ModelTarget[]
    try {
      const parsed = JSON.parse(modelsJson)
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
        targets.push({
          provider: record.provider as string,
          model: record.model as string,
        })
      }
    } catch (parseErr: unknown) {
        return (
          `[batch-dispatch error] Invalid models JSON: ${getErrorMessage(parseErr)}\n` +
          'Example: \'[{"provider":"bailian-coding-plan-test","model":"qwen3-coder-plus"},' +
          '{"provider":"anthropic","model":"claude-sonnet-4-20250514"}]\''
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
    if (
      !Number.isInteger(serverPort) ||
      serverPort < 1 ||
      serverPort > 65_535
    ) {
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
      | {
          type: "json_schema"
          schema: Record<string, unknown>
          retryCount?: number
        }
      | undefined
    if (args.jsonSchema) {
      try {
        const schema = JSON.parse(args.jsonSchema)
        if (!asRecord(schema) || Array.isArray(schema)) {
          return (
            "[batch-dispatch error] jsonSchema must parse to a JSON object schema\n" +
            'Example: \'{"type":"object","properties":{"summary":{"type":"string"}}}\''
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
    }

    // 5. Dispatch to all models in parallel
    const dispatchOne = async (target: ModelTarget): Promise<ModelResult> => {
      const startTime = Date.now()
      let sessionId: string | undefined

      // Per-model timeout (mandatory — default 120s)
      const effectiveTimeout = args.timeout ?? DEFAULT_TIMEOUT_SECONDS
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), effectiveTimeout * 1000)

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

        // Build prompt with optional primer prefix
        const promptText = _primerContent
          ? `${_primerContent}\n\n---\n\n${args.prompt}`
          : args.prompt

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
            parts: [{ type: "text" as const, text: promptText }],
          },
          { signal: controller.signal },
        )

        clearTimeout(timeoutId)

        // Check for swallowed timeout (SDK puts AbortError in result.error, doesn't throw)
        const resultRecord = asRecord(result)
        const resultError = asRecord(resultRecord?.error) ?? resultRecord?.error
        const data = asRecord(resultRecord?.data)

        if (controller.signal.aborted || (resultError && (resultError as any)?.name === "AbortError")) {
          return {
            ...target,
            status: "timeout" as const,
            response: `Did not respond within ${effectiveTimeout}s`,
            durationMs: Date.now() - startTime,
          }
        }

        // Check for empty response
        if (!data || Object.keys(data).length === 0) {
          return {
            ...target,
            status: "error" as const,
            response: `Empty response — model may not be connected or authenticated. Run '/connect ${target.provider}'.`,
            durationMs: Date.now() - startTime,
          }
        }

        // Extract response
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
            // Check for upstream API error in info.error
            const infoError = asRecord(info?.error)
            if (infoError) {
              const errData = asRecord(infoError.data)
              const errMsg = errData?.message ?? "unknown error"
              const statusCode = errData?.statusCode ?? ""
              responseText = `[API error] ${infoError.name ?? "unknown"} ${statusCode ? `(${statusCode})` : ""} — ${errMsg}`
            } else {
              responseText = `[no output] Raw: ${safeStringify(data)}`
            }
          }
        }

        return {
          ...target,
          status: "success",
          response: responseText,
          durationMs: Date.now() - startTime,
        }
      } catch (err: unknown) {
        clearTimeout(timeoutId)
        const isTimeout =
          (err instanceof Error && err.name === "AbortError") ||
          controller.signal.aborted
        return {
          ...target,
          status: isTimeout ? "timeout" : "error",
          response: isTimeout
            ? `Did not respond within ${effectiveTimeout}s`
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
    if (_primerContent) modifiers.push("primer")
    if (args.systemPrompt) modifiers.push("custom-system")
    if (parsedFormat) modifiers.push("structured-json")
    if (args.timeout) modifiers.push(`timeout-${args.timeout}s`)
    const modifierStr =
      modifiers.length > 0 ? ` [${modifiers.join(", ")}]` : ""

    // Header
    const modelList = targets
      .map((t) => `${t.provider}/${t.model}`)
      .join(", ")
    let output = `=== batch-dispatch to ${targets.length} models${modifierStr} ===\n`
    output += `Models: ${modelList}\n\n`

    // Per-model results
    for (const r of modelResults) {
      const statusIcon =
        r.status === "success"
          ? "OK"
          : r.status === "timeout"
            ? "TIMEOUT"
            : "ERROR"
      output += `--- ${r.provider}/${r.model} [${statusIcon}] (${r.durationMs}ms) ---\n`
      output += r.response + "\n\n"
    }

    // Summary footer
    const succeeded = modelResults.filter(
      (r) => r.status === "success",
    ).length
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
