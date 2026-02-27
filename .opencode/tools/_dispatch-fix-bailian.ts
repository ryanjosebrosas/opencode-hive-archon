/**
 * Dispatches task to rename bailian-coding-plan → bailian-coding-plan-test
 * across all project files, and remove the broken provider from opencode.json.
 *
 * Run with: cd .opencode && bun run tools/_dispatch-fix-bailian.ts
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"

const BASE_URL = "http://127.0.0.1:4096"

async function main() {
  console.log("=== Dispatching Bailian Provider Fix ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) {
    console.error("Server not healthy")
    process.exit(1)
  }

  // Create agent-mode session with edit permissions
  const session = await client.session.create({
    title: "fix-bailian-provider-rename",
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

  const taskPrompt = `You have file read/write access. Perform these tasks precisely:

## Task 1: Rename all references of bailian-coding-plan to bailian-coding-plan-test

The provider "bailian-coding-plan" is broken (returns 404). The working provider is "bailian-coding-plan-test".
You need to find and replace "bailian-coding-plan" with "bailian-coding-plan-test" in ALL of these files:

1. .opencode/tools/dispatch.ts — multiple references in TASK_ROUTES and elsewhere
2. .opencode/tools/batch-dispatch.ts — same pattern as dispatch.ts
3. .opencode/tools/council.ts — model list
4. .opencode/tools/_dispatch-primer.md — tier table and fallback note
5. .opencode/tools/_dispatch-cascade-loop.ts — dispatch calls
6. .opencode/tools/_dispatch-cascade-update.ts — dispatch calls
7. AGENTS.md — tier table and fallback line
8. reference/model-strategy.md — tier table, fallback, provider table, text mode note
9. .opencode/commands/execute.md — tier table and fallback
10. .opencode/commands/build.md — dispatch references
11. .opencode/commands/code-loop.md — tier table
12. .opencode/commands/code-review.md — model references
13. .opencode/commands/council.md — model list
14. .opencode/agents/code-review.md — model references

IMPORTANT: Be careful with the replacement! The string "bailian-coding-plan-test" already contains "bailian-coding-plan" as a substring. You must NOT double-replace — i.e. don't turn "bailian-coding-plan-test" into "bailian-coding-plan-test-test".

Strategy: In each file, replace the exact string "bailian-coding-plan" with "bailian-coding-plan-test" BUT skip any occurrence that is already "bailian-coding-plan-test".

Do NOT modify:
- opencode.json (I'll handle that separately)
- Any files in .opencode/tools/_test-*.ts (test files)
- Any files in .opencode/.tmp/

## Task 2: Report what you changed

After making all edits, list every file you modified and how many replacements you made in each.

Do NOT run git commands.`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 600_000) // 10 min

  // Use bailian-coding-plan-test (the working one) for this task
  console.log("Dispatching to bailian-coding-plan-test/qwen3.5-plus (agent mode, 10min timeout)...\n")
  const startTime = Date.now()

  try {
    const result = await client.session.prompt(
      {
        sessionID: sessionId,
        model: { providerID: "bailian-coding-plan-test", modelID: "qwen3.5-plus" },
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

    // Check tool usage
    const toolParts = parts.filter((p: any) =>
      p?.type === "tool-invocation" || p?.type === "tool_use" ||
      p?.type === "tool-result" || p?.type === "tool_result"
    )
    console.log(`\nTools used: ${toolParts.length > 0 ? `YES (${toolParts.length} parts)` : "NO"}`)
    console.log(`Tokens: ${JSON.stringify(info?.tokens)}`)
  } catch (err: any) {
    clearTimeout(timeoutId)
    if (err?.name === "AbortError") {
      console.log("TIMEOUT")
    } else {
      console.error("Error:", err?.message)
    }
  }

  console.log(`\nSession: ${sessionId}`)
  console.log("\n=== Dispatch Complete ===")
}

main().catch(e => {
  console.error("Fatal:", e.message)
  process.exit(1)
})
