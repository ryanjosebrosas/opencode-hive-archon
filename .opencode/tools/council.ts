import { tool } from "@opencode-ai/plugin"
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

// Load project primer once at module scope — prepended to the first council prompt
const PRIMER_FILENAME = "_dispatch-primer.md"
let _primerContent: string | null = null
try {
  const toolDir = typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url))
  _primerContent = readFileSync(join(toolDir, PRIMER_FILENAME), "utf-8")
} catch {
  // Non-fatal: primer file missing or unreadable — council proceeds without it
  _primerContent = null
}

// --- Utility functions (duplicated from dispatch.ts — tools must be self-contained) ---

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

// --- Constants ---

const DEFAULT_TIMEOUT_PER_TURN = 90
const DEFAULT_ROUND_COUNT = 3
const MAX_TURN_TEXT_CHARS = 4000
const MAX_COUNCIL_MODELS = 10
const ROUND_LABELS = ["Proposals", "Rebuttals", "Synthesis"]

// --- Types ---

interface ModelTarget {
  provider: string
  model: string
  label: string
}

interface TurnResult {
  model: ModelTarget
  round: number
  turn: number
  text: string
  durationMs: number
  status: "success" | "error" | "timeout"
}

// --- Provider discovery ---

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

const PREFERRED_COUNCIL_MEMBERS: ModelTarget[] = [
  // Paid (use sparingly — included for diversity)
  { provider: "anthropic", model: "claude-sonnet-4-20250514", label: "Claude" },
  { provider: "openai", model: "gpt-5-codex", label: "GPT" },
  // FREE — bailian (5 models — matches council.md)
  { provider: "bailian-coding-plan-test", model: "qwen3.5-plus", label: "Qwen-Plus" },
  { provider: "bailian-coding-plan-test", model: "qwen3-coder-plus", label: "Qwen-Coder" },
  { provider: "bailian-coding-plan-test", model: "qwen3-max-2026-01-23", label: "Qwen-Max" },
  { provider: "bailian-coding-plan-test", model: "kimi-k2.5", label: "BL-Kimi" },
  { provider: "bailian-coding-plan-test", model: "glm-5", label: "BL-GLM-5" },
  // FREE — zai (4 models — matches council.md)
  { provider: "zai-coding-plan", model: "glm-5", label: "GLM-5" },
  { provider: "zai-coding-plan", model: "glm-4.7", label: "GLM-4.7" },
  { provider: "zai-coding-plan", model: "glm-4.5", label: "GLM-4.5" },
  { provider: "zai-coding-plan", model: "glm-4.7-flash", label: "GLM-Flash" },
  // FREE — ollama-cloud (diverse families)
  { provider: "ollama-cloud", model: "deepseek-v3.2", label: "DeepSeek" },
  { provider: "ollama-cloud", model: "kimi-k2:1t", label: "Kimi-1T" },
  { provider: "ollama-cloud", model: "gemini-3-pro-preview", label: "Gemini" },
  { provider: "ollama-cloud", model: "devstral-2:123b", label: "Devstral" },
  { provider: "ollama-cloud", model: "mistral-large-3:675b", label: "Mistral" },
  { provider: "ollama-cloud", model: "cogito-2.1:671b", label: "Cogito" },
  { provider: "ollama-cloud", model: "kimi-k2-thinking", label: "Kimi-Think" },
]

const getDefaultCouncilModels = async (baseUrl: string): Promise<ModelTarget[]> => {
  const connected = await getConnectedProviders(baseUrl)
  if (connected.length === 0) return []

  const selected: ModelTarget[] = []
  const usedProviders = new Set<string>()

  // Pick from preferred list first (diversity: one per provider)
  for (const member of PREFERRED_COUNCIL_MEMBERS) {
    if (selected.length >= 5) break
    if (connected.includes(member.provider) && !usedProviders.has(member.provider)) {
      selected.push(member)
      usedProviders.add(member.provider)
    }
  }

  // Fill remaining slots from connected providers not yet picked
  if (selected.length < 5) {
    try {
      const resp = await fetch(`${baseUrl}/provider`)
      if (resp.ok) {
        const data = (await resp.json()) as Record<string, unknown>
        for (const providerName of connected) {
          if (selected.length >= 5) break
          if (usedProviders.has(providerName)) continue
          const providerData = asRecord((data as any)[providerName])
          if (!providerData) continue
          const models = asRecord(providerData.models)
          if (!models) continue
          const modelEntries = Object.entries(models)
          if (modelEntries.length === 0) continue
          const [modelId] = modelEntries[0]
          selected.push({
            provider: providerName,
            model: modelId,
            label: providerName.charAt(0).toUpperCase() + providerName.slice(1),
          })
          usedProviders.add(providerName)
        }
      }
    } catch {
      // Best effort — proceed with what we have
    }
  }

  return selected
}

// --- Prompt templates ---

const getStructuredPrompt = (
  round: number,
  totalRounds: number,
  modelCount: number,
  topic: string,
  context?: string,
): string => {
  const contextBlock = context ? `\nAdditional context:\n${context}\n` : ""
  if (round === 1) {
    return (
      `You are in a council discussion with ${modelCount} AI models.\n` +
      `Topic: ${topic}\n${contextBlock}\n` +
      `This is Round 1 of ${totalRounds} (Proposals).\n` +
      `You have full tool access. Use your read, grep, and search tools to examine the codebase before forming your opinion.\n` +
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

const getFreeformPrompt = (
  turnIndex: number,
  totalTurns: number,
  modelCount: number,
  topic: string,
  context?: string,
): string => {
  const contextBlock = context ? `\nAdditional context:\n${context}\n` : ""
  if (turnIndex === 0) {
    return (
      `You are in a freeform council discussion with ${modelCount} AI models.\n` +
      `Topic: ${topic}\n${contextBlock}\n` +
      `You have full tool access. Use your read, grep, and search tools to examine the codebase before forming your opinion.\n` +
      `You're speaking first. Share your perspective.\n` +
      `Be specific and take a clear position.\n` +
      `Keep it concise (2-3 paragraphs).`
    )
  }
  if (turnIndex === totalTurns - 1) {
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

// --- Turn execution ---

const executeTurn = async (
  client: ReturnType<typeof createOpencodeClient>,
  sessionId: string,
  model: ModelTarget,
  prompt: string,
  timeout: number,
  round: number,
  turn: number,
): Promise<TurnResult> => {
  const startTime = Date.now()
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout * 1000)

  try {
    let result = await client.session.prompt(
      {
        sessionID: sessionId,
        model: { providerID: model.provider, modelID: model.model },
        agent: "build",
        parts: [{ type: "text" as const, text: prompt }],
      },
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)

    // Check swallowed AbortError (SDK doesn't throw — puts it in result.error)
    const resultRecord = asRecord(result)
    const resultError = resultRecord?.error
    if (
      controller.signal.aborted ||
      (resultError && (resultError as any)?.name === "AbortError")
    ) {
      return {
        model, round, turn,
        text: `[timeout after ${timeout}s]`,
        durationMs: Date.now() - startTime,
        status: "timeout",
      }
    }

    // Check empty response
    let data = asRecord(resultRecord?.data)
    if (!data || Object.keys(data).length === 0) {
      return {
        model, round, turn,
        text: "[empty response — model may not be connected]",
        durationMs: Date.now() - startTime,
        status: "error",
      }
    }

    // Check upstream API error in info.error
    const info = asRecord(data?.info)
    const infoError = asRecord(info?.error)
    if (infoError && !extractTextFromParts(data?.parts)) {
      const errMsg = (asRecord(infoError.data) as any)?.message ?? "unknown"
      return {
        model, round, turn,
        text: `[API error: ${infoError.name} — ${errMsg}]`,
        durationMs: Date.now() - startTime,
        status: "error",
      }
    }

    // Extract initial response text
    let responseText = extractTextFromParts(data?.parts) || "[no text in response]"

    // Direct response (no more XML relay loop - models can access tools natively via agent mode)
    return {
      model, round, turn,
      text: responseText,
      durationMs: Date.now() - startTime,
      status: "success",
    }
  } catch (err: unknown) {
    clearTimeout(timeoutId)
    return {
      model, round, turn,
      text: `[error: ${getErrorMessage(err)}]`,
      durationMs: Date.now() - startTime,
      status: "error",
    }
  }
}

// --- Council modes ---

const runStructuredCouncil = async (
  client: ReturnType<typeof createOpencodeClient>,
  sessionId: string,
  models: ModelTarget[],
  rounds: number,
  topic: string,
  context: string | undefined,
  timeout: number,
): Promise<TurnResult[]> => {
  const results: TurnResult[] = []
  let turnCounter = 0

  for (let round = 1; round <= rounds; round++) {
    const basePrompt = getStructuredPrompt(round, rounds, models.length, topic, context)
    // Prepend primer to first round so all models see project context in shared session
    const prompt = (round === 1 && _primerContent)
      ? `${_primerContent}\n\n---\n\n${basePrompt}`
      : basePrompt
    for (const model of models) {
      turnCounter++
      const turnResult = await executeTurn(
        client, sessionId, model, prompt, timeout, round, turnCounter,
      )
      results.push(turnResult)
    }
  }

  return results
}

const runFreeformCouncil = async (
  client: ReturnType<typeof createOpencodeClient>,
  sessionId: string,
  models: ModelTarget[],
  rounds: number,
  topic: string,
  context: string | undefined,
  timeout: number,
): Promise<TurnResult[]> => {
  const results: TurnResult[] = []
  const totalTurns = rounds * models.length

  for (let i = 0; i < totalTurns; i++) {
    const model = models[i % models.length]
    const roundNum = Math.floor(i / models.length) + 1
    const basePrompt = getFreeformPrompt(i, totalTurns, models.length, topic, context)
    // Prepend primer to first turn so all models see project context in shared session
    const prompt = (i === 0 && _primerContent)
      ? `${_primerContent}\n\n---\n\n${basePrompt}`
      : basePrompt
    const turnResult = await executeTurn(
      client, sessionId, model, prompt, timeout, roundNum, i + 1,
    )
    results.push(turnResult)
  }

  return results
}

// --- Response formatting ---

const formatCouncilResults = (
  results: TurnResult[],
  mode: string,
  models: ModelTarget[],
  rounds: number,
  sessionId: string,
  topic: string,
): string => {
  const totalMs = results.reduce((sum, r) => sum + r.durationMs, 0)
  const completed = results.filter((r) => r.status === "success").length
  const failures = results.filter((r) => r.status !== "success").length
  const truncatedTopic = topic.length > 80 ? topic.slice(0, 80) + "..." : topic

  const lines: string[] = [
    `=== Council Discussion: ${truncatedTopic} ===`,
    `Mode: ${mode} | Models: ${models.length} | Rounds: ${rounds} | Total turns: ${results.length}`,
    `Session: ${sessionId} — view full discussion at http://localhost:4096`,
    "",
  ]

  if (mode === "structured") {
    // Iterate sequentially, tracking round boundaries
    let currentRound = 0
    for (const r of results) {
      // Derive round from position: every models.length turns is a new round
      const derivedRound = Math.floor((results.indexOf(r)) / models.length) + 1
      if (derivedRound !== currentRound) {
        currentRound = derivedRound
        const label = ROUND_LABELS[currentRound - 1] ?? `Round ${currentRound}`
        lines.push(`--- Round ${currentRound}: ${label} ---`)
        lines.push("")
      }

      const statusTag = r.status !== "success" ? ` [${r.status.toUpperCase()}]` : ""
      lines.push(`[${r.model.label}] (${r.model.provider}/${r.model.model}) — ${r.durationMs}ms${statusTag}`)
      const truncated = r.text.length > MAX_TURN_TEXT_CHARS
        ? r.text.slice(0, MAX_TURN_TEXT_CHARS) + "... (truncated, see browser for full)"
        : r.text
      lines.push(truncated)
      lines.push("")
    }
  } else {
    // Freeform: sequential turns
    for (const r of results) {
      const statusTag = r.status !== "success" ? ` [${r.status.toUpperCase()}]` : ""
      lines.push(`[Turn ${r.turn}] ${r.model.label} (${r.model.provider}/${r.model.model}) — ${r.durationMs}ms${statusTag}`)
      const truncated = r.text.length > MAX_TURN_TEXT_CHARS
        ? r.text.slice(0, MAX_TURN_TEXT_CHARS) + "... (truncated, see browser for full)"
        : r.text
      lines.push(truncated)
      lines.push("")
    }
  }

  lines.push(`=== Council Complete ===`)
  lines.push(`Duration: ${totalMs}ms | Turns: ${completed}/${results.length} | Failures: ${failures}`)

  return lines.join("\n")
}

// --- Tool definition ---

export default tool({
  description:
    "Start a multi-model council discussion. Multiple AI models take turns discussing a topic " +
    "in a shared session, each seeing and building on prior responses. Watch the conversation " +
    "live in the OpenCode browser UI. Two modes: 'structured' (propose/rebut/synthesize rounds) " +
    "or 'freeform' (reactive chain). Default: 4 diverse models, 3 rounds.",
  args: {
    topic: tool.schema
      .string()
      .min(1, "topic is required")
      .describe(
        "The topic, question, or problem for the council to discuss. " +
        "Be specific — include relevant context, constraints, and what kind of output you want.",
      ),
    models: tool.schema
      .string()
      .optional()
      .describe(
        "JSON array of model targets. Each has 'provider', 'model', and optional 'label' fields. " +
        "Default: 4 models auto-selected from connected providers for diversity. " +
        'Example: \'[{"provider":"anthropic","model":"claude-sonnet-4-20250514","label":"Claude"}]\'',
      ),
    mode: tool.schema
      .string()
      .optional()
      .describe(
        "Discussion mode: 'structured' (default) runs proposal/rebuttal/synthesis rounds. " +
        "'freeform' runs a reactive chain where each model responds to the conversation.",
      ),
    rounds: tool.schema
      .number()
      .optional()
      .describe(
        "Number of discussion rounds. Default: 3 for structured mode, 2 for freeform " +
        "(since freeform has more turns per round — each model speaks once per round).",
      ),
    timeout: tool.schema
      .number()
      .optional()
      .describe(
        "Timeout in seconds per model turn. Default: 90. " +
        "Total council time = rounds x models x timeout (worst case).",
      ),
    context: tool.schema
      .string()
      .optional()
      .describe(
        "Additional context to include in the system prompt for all models. " +
        "Use to share relevant code, architecture decisions, or constraints.",
      ),
    port: tool.schema
      .number()
      .optional()
      .describe("OpenCode server port (default: 4096)"),
  },
  async execute(args, _context) {
    // 1. Validate mode
    const mode = args.mode ?? "structured"
    if (mode !== "structured" && mode !== "freeform") {
      return "[council error] mode must be 'structured' or 'freeform'"
    }

    const serverPort = args.port ?? 4096
    const baseUrl = `http://127.0.0.1:${serverPort}`

    // 2. Create client + health check
    let client: ReturnType<typeof createOpencodeClient>
    try {
      client = createOpencodeClient({ baseUrl })
    } catch (err: unknown) {
      return `[council error] Failed to create SDK client: ${getErrorMessage(err)}`
    }

    try {
      const health = await client.global.health()
      if (!health.data?.healthy) {
        return `[council error] OpenCode server at ${baseUrl} is not healthy.`
      }
    } catch (err: unknown) {
      return (
        `[council error] Cannot reach OpenCode server at ${baseUrl}. ` +
        `Run 'opencode serve --port ${serverPort}'.`
      )
    }

    // 3. Parse or auto-select models
    let models: ModelTarget[]
    if (args.models) {
      try {
        let parsed = JSON.parse(args.models)
        if (!Array.isArray(parsed) || parsed.length < 2) {
          return "[council error] models must be a JSON array with at least 2 entries"
        }
        if (parsed.length > MAX_COUNCIL_MODELS) {
          parsed = parsed.slice(0, MAX_COUNCIL_MODELS)
        }
        models = parsed.map((m: any, i: number) => ({
          provider: m.provider,
          model: m.model,
          label: m.label ?? `Model-${i + 1}`,
        }))
      } catch (parseErr: unknown) {
        return `[council error] Invalid models JSON: ${getErrorMessage(parseErr)}`
      }
    } else {
      models = await getDefaultCouncilModels(baseUrl)
      if (models.length < 2) {
        return (
          "[council error] Need at least 2 connected providers for a council. " +
          "Connect more providers in OpenCode, or provide explicit models via the 'models' arg."
        )
      }
    }

    // COUNCIL DISCIPLINE: Hard cap at 10 models to prevent spam
    if (models.length > MAX_COUNCIL_MODELS) {
      models = models.slice(0, MAX_COUNCIL_MODELS)
    }

    // 4. Provider pre-flight — verify all model providers are connected
    const connected = await getConnectedProviders(baseUrl)
    if (connected.length > 0) {
      const disconnected = models.filter((m) => !connected.includes(m.provider))
      if (disconnected.length > 0) {
        const names = disconnected.map((m) => `${m.provider}/${m.model}`).join(", ")
        return (
          `[council error] These providers are not connected: ${names}\n` +
          `Connected providers: ${connected.join(", ")}`
        )
      }
    }

    // 5. Create shared session
    const truncatedTitle = args.topic.length > 50 ? args.topic.slice(0, 50) + "..." : args.topic
    let sessionId: string
    try {
      const session = await client.session.create({
        title: `Council: ${truncatedTitle}`,
        permission: [
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
      })
      sessionId = session.data?.id ?? ""
      if (!sessionId) {
        return `[council error] Failed to create session. Response: ${safeStringify(session.data)}`
      }
    } catch (err: unknown) {
      return `[council error] Failed to create session: ${getErrorMessage(err)}`
    }

    // 6. Configure rounds + timeout
    const effectiveRounds = args.rounds ?? (mode === "structured" ? DEFAULT_ROUND_COUNT : 2)
    const effectiveTimeout = args.timeout ?? DEFAULT_TIMEOUT_PER_TURN

    // 7. Run council
    const results = mode === "structured"
      ? await runStructuredCouncil(client, sessionId, models, effectiveRounds, args.topic, args.context, effectiveTimeout)
      : await runFreeformCouncil(client, sessionId, models, effectiveRounds, args.topic, args.context, effectiveTimeout)

    // 8. Format and return (session preserved — never cleaned up)
    return formatCouncilResults(results, mode, models, effectiveRounds, sessionId, args.topic)
  },
})
