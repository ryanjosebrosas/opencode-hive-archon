/**
 * Dispatches implementation task to Sonnet agent mode:
 * 1. Hardcode Opus role constraint at top of AGENTS.md
 * 2. Add Archon MCP tools to agent-mode sessions in dispatch.ts
 * 3. Update primer with Archon tool reference
 *
 * Run with: cd .opencode && bun run tools/_dispatch-hardcode-role.ts
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const BASE_URL = "http://127.0.0.1:4096"

let primerContent = ""
try {
  const toolDir = typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url))
  primerContent = readFileSync(join(toolDir, "_dispatch-primer.md"), "utf-8")
} catch { /* proceed without */ }

async function main() {
  console.log("=== Dispatching Role Constraint + Archon Integration ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) {
    console.error("Server not healthy")
    process.exit(1)
  }

  // Agent mode session with EDIT access
  const session = await client.session.create({
    title: "hardcode-role-archon-integration",
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

  const taskPrompt = (primerContent ? primerContent + "\n\n---\n\n" : "") +
`You have file read/write access. Implement these 3 changes precisely:

## Task 1: Hardcode Opus role constraint at the TOP of AGENTS.md

Read AGENTS.md first. Then prepend a new block BEFORE the title. The file should start with:

\`\`\`
> **THIS MODEL (Claude Opus) IS THE ORCHESTRATOR.**
> It handles ONLY: planning, architecture, orchestration, exploration, strategy.
> ALL implementation (file edits, code writing, refactoring) MUST be dispatched to T1-T5 models.
> Opus writing code directly is a VIOLATION. No exceptions.
> If dispatch tools are unavailable, write a plan to \`requests/\` and STOP.

# Claude Code Coding System
\`\`\`

Make sure the existing content after the title line stays exactly the same. This blockquote MUST be the very first thing in the file.

## Task 2: Add Archon MCP tools section to _dispatch-primer.md

Read .opencode/tools/_dispatch-primer.md first. Then add this section AFTER the "Critical Gotchas" section and BEFORE the "Validation Requirements" section:

\`\`\`
## Archon MCP Tools (Available in agent mode)

If you have MCP access, these Archon tools are available for RAG search and task management:
- \`rag_search_knowledge_base\` — Search curated documentation (use 2-5 keyword queries)
- \`rag_search_code_examples\` — Find reference code implementations
- \`rag_read_full_page\` — Read full documentation pages
- \`rag_get_available_sources\` — List indexed documentation sources
- \`manage_task\` / \`find_tasks\` — Track tasks across sessions
- \`manage_project\` / \`find_projects\` — Project management

Endpoint: http://159.195.45.47:8051/mcp
\`\`\`

## Task 3: Verify and report

After making the edits:
1. Read the first 10 lines of AGENTS.md to confirm the blockquote is there
2. Read _dispatch-primer.md to confirm the Archon section is there
3. Report what you changed

Do NOT modify any other files. Do NOT run git commands.`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 300_000) // 5 min

  console.log("Dispatching to anthropic/claude-sonnet-4-20250514 (agent mode, 300s timeout)...\n")
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
  console.log(`Session: ${sessionId}`)
  console.log("\n=== Dispatch Complete ===")
}

main().catch(e => {
  console.error("Fatal:", e.message)
  process.exit(1)
})
