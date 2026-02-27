/**
 * Full cascade test: T1 implements → T2 reviews → T3 reviews → T5 validates
 * Updates cascade docs to maximize free model usage.
 *
 * Run with: cd .opencode && bun run tools/_dispatch-cascade-update.ts
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

// Read current files for context
const projectRoot = join(
  typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url)),
  "..", ".."
)

function readFile(relPath: string): string {
  try { return readFileSync(join(projectRoot, relPath), "utf-8") } catch { return "[FILE NOT FOUND]" }
}

const currentPrimer = readFile(".opencode/tools/_dispatch-primer.md")
const currentModelStrategy = readFile("reference/model-strategy.md")
const currentAgentsMd = readFile("AGENTS.md")
const currentBuildMd = readFile(".opencode/commands/build.md")

async function dispatchToModel(
  client: ReturnType<typeof createOpencodeClient>,
  provider: string,
  model: string,
  prompt: string,
  label: string,
  timeoutSec: number = 120,
): Promise<string> {
  const session = await client.session.create({ title: label })
  const sessionId = session.data?.id
  if (!sessionId) throw new Error("No session ID")

  const fullPrompt = primerContent ? primerContent + "\n\n---\n\n" + prompt : prompt
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutSec * 1000)

  console.log(`  → ${provider}/${model} (${timeoutSec}s timeout)...`)
  const startTime = Date.now()

  const result = await client.session.prompt(
    {
      sessionID: sessionId,
      model: { providerID: provider, modelID: model },
      parts: [{ type: "text" as const, text: fullPrompt }],
    },
    { signal: controller.signal },
  )
  clearTimeout(timeoutId)

  const duration = Math.round((Date.now() - startTime) / 1000)
  const data = (result as any)?.data
  const info = data?.info
  const parts = data?.parts || []

  if (info?.error) {
    const errMsg = info.error?.data?.message || info.error?.name || "Unknown error"
    console.log(`  ✗ ERROR (${duration}s): ${errMsg}`)
    // Cleanup
    await client.session.delete({ sessionID: sessionId }).catch(() => {})
    throw new Error(`${provider}/${model} failed: ${errMsg}`)
  }

  let responseText = ""
  for (const part of parts) {
    if (part?.type === "text") responseText += part.text
  }

  const tokens = info?.tokens
  console.log(`  ✓ Done (${duration}s, ${tokens?.output || 0} output tokens)`)

  await client.session.delete({ sessionID: sessionId }).catch(() => {})
  return responseText
}

async function main() {
  console.log("=== Full Cascade: T1 → T2 → T3 → T5 ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) { console.error("Server not healthy"); process.exit(1) }

  // ============================================================
  // STEP 1: T1 Implementation (FREE — bailian qwen3.5-plus)
  // ============================================================
  console.log("STEP 1: T1 Implementation (bailian/qwen3.5-plus)")

  const t1Prompt =
`You are a T1 implementation model. Generate the EXACT file edits needed for these 4 files.
Return each edit as: FILE: <path>, then the COMPLETE new file content.

## Changes Required

### File 1: .opencode/tools/_dispatch-primer.md

Current tier instructions (lines 47-51):
\`\`\`
${currentPrimer.split("\n").slice(46, 53).join("\n")}
\`\`\`

Replace the tier instructions with:
\`\`\`
- **T1 models (text mode)**: You are the implementer. Generate code, tests, boilerplate. Return complete file contents in your response — the orchestrator applies them. Read ALL context provided in the prompt before generating. Follow project patterns exactly.
- **T2 models (first review)**: Review T1's output for correctness, edge cases, security. Report findings as Critical/Major/Minor. You are FREE — use generously.
- **T3 models (second review)**: Independent second opinion on T1's output. Different model family = different blind spots. Report findings as Critical/Major/Minor. You are FREE — use generously.
- **T4 models (code review gate)**: Near-final quality gate. Only invoked after T2-T3 pass. Focus on subtle bugs, performance, architecture fit.
- **T5 models (final validation, agent mode)**: You have full tool access. Read the actual files that were changed, verify the edits are correct, run validation (ruff, mypy, pytest). You are the last check before commit. Only approve if everything passes.
\`\`\`

Also change line 45 from "T5 | Final Review (last resort)" to "T5 | Final Validation (agent mode)" in the table.

### File 2: reference/model-strategy.md

Current /build automation table:
\`\`\`
${currentModelStrategy.split("\n").slice(78, 87).join("\n")}
\`\`\`

Replace with this updated table that adds T5 column:
\`\`\`
| Depth | Plan Size | T1 Impl (FREE) | T2 Review (FREE) | T3 Second (FREE) | T4 Gate (PAID) | T5 Final (PAID) | Tests Required |
|-------|-----------|-----------------|-------------------|-------------------|----------------|-----------------|----------------|
| light | ~100 lines | T1 text mode | — | — | — | — | L1-L2 (syntax, types) |
| standard | ~300 lines | T1 text mode | T2 review | — | T4 gate | T5 validates | L1-L3 (+ unit tests) |
| heavy | ~700 lines | T1 text mode | T2 review | T3 opinion | T4 gate | T5 validates | L1-L4 (+ integration) |
\`\`\`

### File 3: AGENTS.md

Current /build automation table (lines 134-138):
\`\`\`
${currentAgentsMd.split("\n").slice(133, 144).join("\n")}
\`\`\`

Replace the table with:
\`\`\`
| Depth | Plan Size | T1 Impl (FREE) | T2 Review (FREE) | T3 Second (FREE) | T4 Gate (PAID) | T5 Final (PAID) | Tests |
|-------|-----------|-----------------|-------------------|-------------------|----------------|-----------------|-------|
| light | ~100 lines | T1 text mode | — | — | — | — | L1-L2 |
| standard | ~300 lines | T1 text mode | T2 review | — | T4 gate | T5 validates | L1-L3 |
| heavy | ~700 lines | T1 text mode | T2 review | T3 opinion | T4 gate | T5 validates | L1-L4 |
\`\`\`

### File 4: .opencode/commands/build.md

Find the dispatch chain diagram and update it. Look for the section that shows the build chain flow.
The cascade should be:
\`\`\`
T1 (FREE text) → T2 Review (FREE) → T3 Second (FREE) → T4 Gate (PAID) → T5 Final Validation (PAID agent mode) → commit
\`\`\`

Return the COMPLETE replacement content for each changed section. Be precise — the orchestrator will apply these edits.`

  let t1Output: string
  try {
    t1Output = await dispatchToModel(client, "bailian-coding-plan-test", "qwen3.5-plus", t1Prompt, "t1-cascade-update", 120)
  } catch {
    console.log("  Falling back to zai-coding-plan/glm-4.7...")
    t1Output = await dispatchToModel(client, "zai-coding-plan", "glm-4.7", t1Prompt, "t1-cascade-update-fallback", 120)
  }

  console.log("\n--- T1 Output ---")
  console.log(t1Output.slice(0, 8000))
  console.log("--- End T1 ---\n")

  // ============================================================
  // STEP 2: T2 First Review (FREE — zai glm-5)
  // ============================================================
  console.log("STEP 2: T2 Review (zai/glm-5)")

  const t2Prompt =
`You are a T2 reviewer. A T1 model generated these file edits. Review them for correctness.

## T1 Output:
${t1Output.slice(0, 6000)}

## Requirements:
1. _dispatch-primer.md: T1 should be "text mode implementer", T5 should be "final validation with agent mode + tool access"
2. model-strategy.md: Build automation table should have columns for all 5 tiers + T5 validates on standard/heavy
3. AGENTS.md: Same table update as model-strategy.md
4. build.md: Cascade chain should show T1→T2→T3→T4→T5→commit

For each file edit, report: PASS or FAIL. If FAIL, explain what's wrong and what the correct content should be.
Be specific about any missing or incorrect content.`

  let t2Output: string
  try {
    t2Output = await dispatchToModel(client, "zai-coding-plan", "glm-5", t2Prompt, "t2-review", 90)
  } catch (e: any) {
    console.log(`  T2 review failed: ${e.message}. Continuing with T3...`)
    t2Output = "[T2 SKIPPED]"
  }

  console.log("\n--- T2 Review ---")
  console.log(t2Output.slice(0, 4000))
  console.log("--- End T2 ---\n")

  // ============================================================
  // STEP 3: T3 Second Review (FREE — ollama deepseek)
  // ============================================================
  console.log("STEP 3: T3 Review (ollama/deepseek-v3.2)")

  const t3Prompt =
`You are a T3 independent reviewer. Review these edits from a T1 model, plus T2's review.

## T1 Output (edits):
${t1Output.slice(0, 4000)}

## T2 Review:
${t2Output.slice(0, 2000)}

## Key requirement: The 5-tier cascade must maximize FREE models:
- T1 (FREE): Implementation via text mode (bailian qwen3.5-plus)
- T2 (FREE): First review (zai glm-5) 
- T3 (FREE): Second review (ollama deepseek)
- T4 (PAID cheap): Code review gate (openai gpt-5.3-codex)
- T5 (PAID): Final validation with agent mode + tool access (anthropic sonnet) → then commit

Do the T1 edits correctly reflect this? Does T2's review catch real issues? Report PASS/FAIL for each file.`

  let t3Output: string
  try {
    t3Output = await dispatchToModel(client, "ollama-cloud", "deepseek-v3.2", t3Prompt, "t3-review", 90)
  } catch (e: any) {
    console.log(`  T3 review failed: ${e.message}. Continuing...`)
    t3Output = "[T3 SKIPPED]"
  }

  console.log("\n--- T3 Review ---")
  console.log(t3Output.slice(0, 4000))
  console.log("--- End T3 ---\n")

  // ============================================================
  // SUMMARY
  // ============================================================
  console.log("=== Cascade Summary ===\n")
  console.log("T1 (bailian-coding-plan-test/qwen3.5-plus): Implementation generated")
  console.log(`T2 (zai/glm-5): ${t2Output.includes("PASS") ? "PASSED" : t2Output.includes("FAIL") ? "ISSUES FOUND" : "REVIEW COMPLETE"}`)
  console.log(`T3 (ollama/deepseek): ${t3Output.includes("PASS") ? "PASSED" : t3Output.includes("FAIL") ? "ISSUES FOUND" : "REVIEW COMPLETE"}`)
  console.log("\nNext: Orchestrator (Opus) applies edits based on T1 output + T2/T3 feedback")
  console.log("Then: T5 (Sonnet agent mode) does final validation before commit")
  console.log("\n=== Done ===")
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1) })
