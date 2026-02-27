/**
 * Full cascade: T1 implement → T2 review → T3 review → (apply) → T5 validate
 * Updates tier docs to reflect the cascade review-fix loop.
 *
 * Run with: cd .opencode && bun run tools/_dispatch-cascade-loop.ts
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const BASE_URL = "http://127.0.0.1:4096"

const toolDir = typeof import.meta.dirname === "string"
  ? import.meta.dirname
  : dirname(fileURLToPath(import.meta.url))
const projectRoot = join(toolDir, "..", "..")

function readFile(relPath: string): string {
  try { return readFileSync(join(projectRoot, relPath), "utf-8") } catch { return "[NOT FOUND]" }
}

const primerContent = readFile(".opencode/tools/_dispatch-primer.md")

async function dispatchText(
  client: ReturnType<typeof createOpencodeClient>,
  provider: string,
  model: string,
  prompt: string,
  label: string,
  timeoutSec = 120,
): Promise<string> {
  const session = await client.session.create({ title: label })
  const sessionId = session.data?.id
  if (!sessionId) throw new Error("No session ID")

  const fullPrompt = primerContent ? primerContent + "\n\n---\n\n" + prompt : prompt
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutSec * 1000)

  console.log(`  → ${provider}/${model} (${timeoutSec}s)...`)
  const start = Date.now()

  try {
    const result = await client.session.prompt(
      { sessionID: sessionId, model: { providerID: provider, modelID: model }, parts: [{ type: "text" as const, text: fullPrompt }] },
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)
    const dur = Math.round((Date.now() - start) / 1000)
    const data = (result as any)?.data
    const info = data?.info
    if (info?.error) {
      const msg = info.error?.data?.message || info.error?.name || "Error"
      console.log(`  ✗ ERROR (${dur}s): ${msg}`)
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
      throw new Error(msg)
    }
    const text = (data?.parts || []).filter((p: any) => p?.type === "text").map((p: any) => p.text).join("")
    console.log(`  ✓ Done (${dur}s, ${info?.tokens?.output || 0} tokens)`)
    await client.session.delete({ sessionID: sessionId }).catch(() => {})
    return text
  } catch (e: any) {
    clearTimeout(timeoutId)
    if (e?.name === "AbortError") {
      console.log(`  ✗ TIMEOUT (${timeoutSec}s)`)
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
      throw new Error("Timeout")
    }
    throw e
  }
}

async function dispatchAgent(
  client: ReturnType<typeof createOpencodeClient>,
  prompt: string,
  label: string,
  timeoutSec = 180,
): Promise<string> {
  const session = await client.session.create({
    title: label,
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
  if (!sessionId) throw new Error("No session ID")

  const fullPrompt = primerContent ? primerContent + "\n\n---\n\n" + prompt : prompt
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutSec * 1000)

  console.log(`  → anthropic/claude-sonnet-4-20250514 AGENT MODE (${timeoutSec}s)...`)
  const start = Date.now()

  const result = await client.session.prompt(
    { sessionID: sessionId, model: { providerID: "anthropic", modelID: "claude-sonnet-4-20250514" }, agent: "general", parts: [{ type: "text" as const, text: fullPrompt }] } as any,
    { signal: controller.signal },
  )
  clearTimeout(timeoutId)

  const dur = Math.round((Date.now() - start) / 1000)
  const data = (result as any)?.data
  const text = (data?.parts || []).filter((p: any) => p?.type === "text").map((p: any) => p.text).join("")
  console.log(`  ✓ Done (${dur}s, ${data?.info?.tokens?.output || 0} tokens)`)
  await client.session.delete({ sessionID: sessionId }).catch(() => {})
  return text
}

async function main() {
  console.log("=== Cascade Review-Fix Loop: T1 → T2 → T3 → T5 ===\n")

  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  if (!health.data?.healthy) { console.error("Not healthy"); process.exit(1) }

  // Current file contents for T1 context
  const currentPrimer = readFile(".opencode/tools/_dispatch-primer.md")
  const currentModelStrategy = readFile("reference/model-strategy.md")
  const currentAgentsMd = readFile("AGENTS.md")

  // ============ T1: IMPLEMENT (FREE) ============
  console.log("── T1: Implementation (bailian/qwen3.5-plus, FREE) ──\n")

  const t1Prompt =
`You are a T1 implementation model. Generate replacement content for 3 file sections.
Return each as: === FILE: <path> === then the replacement text for that section only.

## Edit 1: .opencode/tools/_dispatch-primer.md — Replace tier instructions

CURRENT (lines 45-51):
\`\`\`
${currentPrimer.split("\n").slice(44, 52).join("\n")}
\`\`\`

REPLACE WITH these 2 changes:
a) Line 45: Change "T5 | Final Review (last resort)" to "T5 | Final Validation (agent mode)"
b) Lines 47-51: Replace all 5 bullet points with:

- **T1 models (text mode)**: You are the implementer. Generate code, tests, boilerplate. Return complete file contents — the orchestrator applies them. Read ALL context in the prompt before generating. Follow project patterns exactly.
- **T2 models (first review, FREE)**: First review of T1's output. Focus on correctness, edge cases, security. Report findings as Critical/Major/Minor. Be thorough — your reviews drive the fix loop. You are FREE — use generously.
- **T3 models (second review, FREE)**: Independent second opinion. Different model family = different blind spots. Report findings as Critical/Major/Minor. You are FREE — use generously.
- **T4 models (code review gate, PAID)**: Near-final quality gate after T2-T3 pass clean. Focus on subtle bugs, performance, architecture fit that free models missed.
- **T5 models (final validation, agent mode, PAID)**: You have full tool access — read actual files, run ruff/mypy/pytest. Last check before commit. Only approve if everything passes. Report PASS or FAIL with details.

## Edit 2: reference/model-strategy.md — Replace build automation table

CURRENT (lines 96-102):
\`\`\`
${currentModelStrategy.split("\n").slice(95, 103).join("\n")}
\`\`\`

REPLACE WITH:
\`\`\`
## Cascade Review-Fix Loop

Each tier reviews, and if issues found, T1 (FREE) fixes and the same tier re-reviews. Max 3 iterations per tier.

\\\`\\\`\\\`
T1 implement → T2 review ⟲ T1 fix → T3 review ⟲ T1 fix → T4 gate ⟲ T1 fix → T5 validate ⟲ T1 fix → commit
\\\`\\\`\\\`

## /build Automation Levels by Spec Depth

| Depth | Plan Size | T1 Impl (FREE) | T2 Review (FREE) | T3 Second (FREE) | T4 Gate (PAID) | T5 Final (PAID) | Tests |
|-------|-----------|-----------------|-------------------|-------------------|----------------|-----------------|-------|
| light | ~100 lines | T1 text mode | — | — | — | — | L1-L2 |
| standard | ~300 lines | T1 text mode | T2 review ⟲ | — | T4 gate | T5 validates | L1-L3 |
| heavy | ~700 lines | T1 text mode | T2 review ⟲ | T3 review ⟲ | T4 gate ⟲ | T5 validates ⟲ | L1-L4 |

⟲ = review-fix loop (max 3 iterations per tier)
\`\`\`

## Edit 3: AGENTS.md — Replace build automation table

CURRENT (lines 132-138):
\`\`\`
${currentAgentsMd.split("\n").slice(131, 145).join("\n")}
\`\`\`

REPLACE WITH:
\`\`\`
### \\\`/build\\\` Automation Levels by Spec Depth

| Depth | Plan Size | T1 (FREE) | T2 (FREE) | T3 (FREE) | T4 (PAID) | T5 (PAID) | Tests |
|-------|-----------|-----------|-----------|-----------|-----------|-----------|-------|
| light | ~100 lines | T1 text | — | — | — | — | L1-L2 |
| standard | ~300 lines | T1 text | T2 ⟲ | — | T4 gate | T5 validates | L1-L3 |
| heavy | ~700 lines | T1 text | T2 ⟲ | T3 ⟲ | T4 ⟲ | T5 ⟲ | L1-L4 |

⟲ = review-fix loop with T1 (max 3 iterations). T5 uses agent mode (reads files, runs tests).
\`\`\`

Return ONLY the replacement text for each section. Be precise.`

  let t1Output: string
  try {
    t1Output = await dispatchText(client, "bailian-coding-plan-test", "qwen3.5-plus", t1Prompt, "t1-cascade-docs", 120)
  } catch {
    console.log("  Falling back to zai-coding-plan/glm-4.7...")
    try {
      t1Output = await dispatchText(client, "zai-coding-plan", "glm-4.7", t1Prompt, "t1-cascade-docs-fallback", 120)
    } catch {
      console.log("  Second fallback to bailian/qwen3-coder-plus...")
      t1Output = await dispatchText(client, "bailian-coding-plan-test", "qwen3-coder-plus", t1Prompt, "t1-cascade-docs-fb2", 120)
    }
  }

  console.log("\n--- T1 Output (truncated) ---")
  console.log(t1Output.slice(0, 5000))
  console.log("\n--- End T1 ---\n")

  // ============ T2: FIRST REVIEW (FREE) ============
  console.log("── T2: First Review (zai/glm-5, FREE) ──\n")

  const t2Prompt =
`You are a T2 reviewer. A T1 model generated replacement content for 3 files. Review for correctness.

## T1 Output:
${t1Output.slice(0, 5000)}

## Requirements:
1. _dispatch-primer.md: T1 = "text mode implementer", T2-T3 = "FREE reviewers", T4 = "gate", T5 = "final validation agent mode with tool access"
2. model-strategy.md: Must show the cascade loop diagram (T1→T2⟲→T3⟲→T4⟲→T5⟲→commit) and updated table with T5 column
3. AGENTS.md: Same updated table, ⟲ symbol for review-fix loops, T5 uses agent mode note

For each file, report PASS or FAIL. If FAIL, provide the corrected text.`

  let t2Output: string
  try {
    t2Output = await dispatchText(client, "zai-coding-plan", "glm-5", t2Prompt, "t2-review-cascade", 90)
  } catch (e: any) {
    console.log(`  T2 failed: ${e.message}`)
    t2Output = "[T2 SKIPPED - " + e.message + "]"
  }

  console.log("\n--- T2 Review ---")
  console.log(t2Output.slice(0, 3000))
  console.log("\n--- End T2 ---\n")

  // ============ T3: SECOND REVIEW (FREE) ============
  console.log("── T3: Second Review (ollama/deepseek-v3.2, FREE) ──\n")

  const t3Prompt =
`You are a T3 independent reviewer. Different model family from T2 — look for things T2 might have missed.

## T1 Output (implementation):
${t1Output.slice(0, 4000)}

## T2 Review:
${t2Output.slice(0, 2000)}

## The cascade loop structure:
T1 (FREE) implement → T2 (FREE) review⟲ → T3 (FREE) review⟲ → T4 (PAID) gate⟲ → T5 (PAID agent) validate⟲ → commit
Each ⟲ means: if issues, T1 fixes (FREE), reviewer re-reviews, max 3 iterations.

Do the edits correctly reflect this cascade? Report PASS/FAIL per file. Focus on accuracy of the cascade loop description.`

  let t3Output: string
  try {
    t3Output = await dispatchText(client, "ollama-cloud", "deepseek-v3.2", t3Prompt, "t3-review-cascade", 90)
  } catch (e: any) {
    console.log(`  T3 failed: ${e.message}`)
    t3Output = "[T3 SKIPPED - " + e.message + "]"
  }

  console.log("\n--- T3 Review ---")
  console.log(t3Output.slice(0, 3000))
  console.log("\n--- End T3 ---\n")

  // ============ SUMMARY ============
  console.log("=== CASCADE SUMMARY ===")
  console.log(`T1 (FREE bailian-coding-plan-test/qwen3.5-plus): Generated edits for 3 files`)
  console.log(`T2 (FREE zai/glm-5): ${t2Output.includes("SKIPPED") ? "SKIPPED" : "Reviewed"}`)
  console.log(`T3 (FREE ollama/deepseek): ${t3Output.includes("SKIPPED") ? "SKIPPED" : "Reviewed"}`)
  console.log(`\nNext steps:`)
  console.log(`1. Orchestrator (Opus) applies T1 edits with T2/T3 feedback`)
  console.log(`2. T5 (Sonnet agent mode) reads actual files and validates`)
  console.log(`3. Commit after T5 approves`)
  console.log("\n=== Done ===")
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1) })
