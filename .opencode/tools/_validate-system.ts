/**
 * Dispatches a coding system validation task to Anthropic Sonnet in agent mode.
 * Run with: cd .opencode && bun run tools/_validate-system.ts
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const BASE_URL = "http://127.0.0.1:4096"

// Load primer
let primerContent = ""
try {
  const toolDir = typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url))
  primerContent = readFileSync(join(toolDir, "_dispatch-primer.md"), "utf-8")
} catch { /* proceed without */ }

async function main() {
  console.log("=== Dispatching System Validation to Sonnet (Agent Mode) ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) {
    console.error("Server not healthy")
    process.exit(1)
  }

  // Create agent-mode session (read-only — no edit permission)
  const session = await client.session.create({
    title: "validate-coding-system",
    permission: [
      { permission: "read", pattern: "*", action: "allow" },
      { permission: "glob", pattern: "*", action: "allow" },
      { permission: "grep", pattern: "*", action: "allow" },
      { permission: "list", pattern: "*", action: "allow" },
      { permission: "bash", pattern: "*", action: "allow" },
      { permission: "edit", pattern: "*", action: "deny" },
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

  const taskPrompt = (primerContent ? primerContent + "\n\n---\n\n" : "") +
    "You are validating the coding system infrastructure after a major refactor. " +
    "Use your tools (Read, Glob, Grep) to check actual files. Do NOT guess.\n\n" +
    "Perform these checks and report PASS or FAIL for each:\n\n" +
    "1. Read AGENTS.md — verify it uses @sections/ references (should have 5 @sections/ lines pointing to 01-05)\n" +
    "2. Read sections/01_core_principles.md — confirm the HARD RULE about 'Opus Never Implements' is the first line\n" +
    "3. Read .opencode/tools/dispatch.ts — verify 'mode' arg exists and 'agent' mode creates sessions with permissions\n" +
    "4. Read .opencode/tools/council.ts — verify primer loading (readFileSync of _dispatch-primer.md) is present near the top\n" +
    "5. Read .opencode/tools/_dispatch-primer.md — confirm it has 'Core Principles' and 'PIV' sections\n" +
    "6. List .opencode/agents/ — confirm exactly 5 agent .md files (no swarm-worker files)\n" +
    "7. List .opencode/commands/ — report the count\n" +
    "8. Search README.md for 'swarm' (case-insensitive) — should be zero matches\n" +
    "9. List sections/ — confirm exactly 5 files (no 06_archon_workflow.md)\n" +
    "10. Read reference/model-strategy.md — verify 'Dispatch Modes' section exists with agent mode documentation\n\n" +
    "Format your response as a checklist. Be thorough."

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 180_000) // 3 min

  console.log("Sending validation task (180s timeout)...\n")
  const startTime = Date.now()

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
    if (part?.type === "text") {
      console.log(part.text)
    }
  }

  if (info?.error) {
    console.log("\nERROR:", JSON.stringify(info.error, null, 2))
  }

  console.log(`\nTokens: ${JSON.stringify(info?.tokens)}`)
  console.log(`Cost: ${info?.cost}`)
  console.log(`Session: ${sessionId}`)
  console.log("\n=== Validation Complete ===")
}

main().catch(e => {
  console.error("Fatal:", e.message)
  process.exit(1)
})
