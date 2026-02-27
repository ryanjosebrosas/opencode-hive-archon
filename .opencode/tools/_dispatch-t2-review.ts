/**
 * T2 review: Dispatch verification of Sonnet's changes to GLM-5 (free, text mode).
 * Run with: cd .opencode && bun run tools/_dispatch-t2-review.ts
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const BASE_URL = "http://127.0.0.1:4096"

async function main() {
  console.log("=== T2 Review: GLM-5 verifies Sonnet's changes (text mode) ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })

  // Read the files that were changed so we can include them in the review prompt
  const projectRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..")
  const agentsMd = readFileSync(join(projectRoot, "AGENTS.md"), "utf-8")
  const primer = readFileSync(join(projectRoot, ".opencode/tools/_dispatch-primer.md"), "utf-8")

  const session = await client.session.create({ title: "t2-review-role-constraint" })
  const sessionId = session.data?.id
  if (!sessionId) { console.error("No session ID"); process.exit(1) }

  const reviewPrompt =
`You are a T2 reviewer (thinking model). Review these two files that were just modified by a T1 implementation model. Check for correctness, completeness, and any issues.

## File 1: AGENTS.md (first 20 lines)

\`\`\`
${agentsMd.split("\n").slice(0, 20).join("\n")}
\`\`\`

## File 2: _dispatch-primer.md (lines 75-99)

\`\`\`
${primer.split("\n").slice(74).join("\n")}
\`\`\`

## Requirements that were given to the T1 model:

1. AGENTS.md must start with a blockquote stating Claude Opus is the orchestrator and must NEVER implement directly
2. _dispatch-primer.md must have an "Archon MCP Tools" section between "Critical Gotchas" and "Validation Requirements"
3. The Archon section must list: rag_search_knowledge_base, rag_search_code_examples, rag_read_full_page, rag_get_available_sources, manage_task/find_tasks, manage_project/find_projects
4. Endpoint must be: http://159.195.45.47:8051/mcp

## Your review:

For each requirement, report PASS or FAIL. If FAIL, explain what's wrong.
Also check: Are there any formatting issues? Missing content? Anything that looks wrong?
Be thorough but concise.`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60_000)

  console.log("Sending to zai-coding-plan/glm-5 (text mode, 60s timeout)...\n")
  const startTime = Date.now()

  const result = await client.session.prompt(
    {
      sessionID: sessionId,
      model: { providerID: "zai-coding-plan", modelID: "glm-5" },
      parts: [{ type: "text" as const, text: reviewPrompt }],
    },
    { signal: controller.signal },
  )
  clearTimeout(timeoutId)

  const duration = Math.round((Date.now() - startTime) / 1000)
  const data = (result as any)?.data
  const parts = data?.parts || []
  const info = data?.info

  console.log(`--- T2 Review (${duration}s) ---\n`)

  for (const part of parts) {
    if (part?.type === "text") {
      console.log(part.text)
    }
  }

  if (info?.error) {
    console.log("\nERROR:", JSON.stringify(info.error, null, 2))
  }

  console.log(`\nTokens: ${JSON.stringify(info?.tokens)}`)

  // Cleanup
  await client.session.delete({ sessionID: sessionId }).catch(() => {})
  console.log("\n=== T2 Review Complete ===")
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1) })
