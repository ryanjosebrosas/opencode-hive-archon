/**
 * T5 Final Validation: Sonnet agent mode reads actual files and validates.
 * Run with: cd .opencode && bun run tools/_dispatch-t5-validate.ts
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const BASE_URL = "http://127.0.0.1:4096"
const toolDir = typeof import.meta.dirname === "string"
  ? import.meta.dirname
  : dirname(fileURLToPath(import.meta.url))
const primerContent = (() => { try { return readFileSync(join(toolDir, "_dispatch-primer.md"), "utf-8") } catch { return "" } })()

async function main() {
  console.log("=== T5 Final Validation (Sonnet Agent Mode) ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })

  const session = await client.session.create({
    title: "t5-final-validation",
    permission: [
      { permission: "read", pattern: "*", action: "allow" },
      { permission: "glob", pattern: "*", action: "allow" },
      { permission: "grep", pattern: "*", action: "allow" },
      { permission: "list", pattern: "*", action: "allow" },
      { permission: "bash", pattern: "*", action: "allow" },
      { permission: "edit", pattern: "*", action: "deny" },
      { permission: "task", pattern: "*", action: "deny" },
    ] as any,
  } as any)

  const sessionId = session.data?.id
  if (!sessionId) { console.error("No session ID"); process.exit(1) }

  const prompt = (primerContent ? primerContent + "\n\n---\n\n" : "") +
`You are the T5 FINAL VALIDATOR. Use your tools to read the actual files and verify these changes were applied correctly.

## What was changed (by T1, reviewed by T2 + T3):

1. **.opencode/tools/_dispatch-primer.md** — Tier instructions updated:
   - T5 table row: "Final Validation (agent mode)" not "Final Review (last resort)"
   - T1: "text mode implementer"
   - T2: "first review, FREE"
   - T3: "second review, FREE"  
   - T4: "code review gate, PAID"
   - T5: "final validation, agent mode, PAID"

2. **reference/model-strategy.md** — Added cascade loop section:
   - Cascade diagram: T1→T2⟲→T3⟲→T4⟲→T5⟲→commit
   - Updated build automation table with T5 column
   - ⟲ notation explained

3. **AGENTS.md** — Updated build automation table:
   - T5 column added
   - ⟲ notation for review-fix loops
   - Note about T5 agent mode

## Your job:

1. Read each of the 3 files using your tools
2. Verify EACH change listed above is present and correct
3. Check that AGENTS.md still has the blockquote at line 1 (from previous commit)
4. Run: grep -i "last resort" on _dispatch-primer.md (should return 0 matches — that phrase was replaced)
5. Report PASS or FAIL for each file with evidence

Be thorough. This is the last gate before commit.`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 180_000)

  console.log("Dispatching to anthropic/claude-sonnet-4-20250514 (agent mode)...\n")
  const start = Date.now()

  const result = await client.session.prompt(
    { sessionID: sessionId, model: { providerID: "anthropic", modelID: "claude-sonnet-4-20250514" }, agent: "general", parts: [{ type: "text" as const, text: prompt }] } as any,
    { signal: controller.signal },
  )
  clearTimeout(timeoutId)

  const dur = Math.round((Date.now() - start) / 1000)
  const data = (result as any)?.data
  const parts = data?.parts || []

  console.log(`--- T5 Validation (${dur}s) ---\n`)
  for (const part of parts) {
    if (part?.type === "text") console.log(part.text)
  }

  if (data?.info?.error) console.log("\nERROR:", JSON.stringify(data.info.error, null, 2))
  console.log(`\nTokens: ${JSON.stringify(data?.info?.tokens)}`)
  console.log(`\n=== T5 Complete ===`)
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1) })
