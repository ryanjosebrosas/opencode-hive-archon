/**
 * Test script for agent-mode dispatch — verifies that sessions with
 * PermissionRuleset + agent:"general" give models file system + bash access.
 *
 * Run with: cd .opencode && bun run tools/_test-agent-mode.ts
 * Requires: opencode serve running on port 4096
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"
import { readFileSync } from "node:fs"
import { join, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const BASE_URL = "http://127.0.0.1:4096"

// Load primer (same as dispatch.ts does)
let primerContent: string | null = null
try {
  const toolDir = typeof import.meta.dirname === "string"
    ? import.meta.dirname
    : dirname(fileURLToPath(import.meta.url))
  primerContent = readFileSync(join(toolDir, "_dispatch-primer.md"), "utf-8")
} catch {
  primerContent = null
}

async function main() {
  console.log("=== Agent Mode Dispatch Test ===\n")

  // 1. Health check
  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  console.log("Health:", JSON.stringify(health.data))
  if (!health.data?.healthy) {
    console.error("Server not healthy. Run 'opencode serve' first.")
    process.exit(1)
  }

  // 2. Check connected providers
  let connected: string[] = []
  try {
    const resp = await fetch(`${BASE_URL}/provider`)
    const data = await resp.json() as { connected?: string[] }
    connected = data.connected ?? []
    console.log("Connected providers:", connected)
  } catch {
    console.error("Cannot list providers")
    process.exit(1)
  }

  // Test multiple providers to find which ones support agent mode (tool use)
  const testTargets = [
    { provider: "anthropic", model: "claude-sonnet-4-20250514", label: "T5 Anthropic (should work)" },
    { provider: "openai", model: "gpt-5.3-codex", label: "T4 OpenAI" },
    { provider: "zai-coding-plan", model: "glm-5", label: "T2 GLM-5" },
    { provider: "bailian-coding-plan", model: "qwen3.5-plus", label: "T1c Qwen3.5" },
    { provider: "ollama-cloud", model: "deepseek-v3.2", label: "T3 DeepSeek" },
  ].filter(t => connected.includes(t.provider))

  if (testTargets.length === 0) {
    console.error("No test targets available from connected providers")
    process.exit(1)
  }

  // Use first available for the main test
  const testProvider = testTargets[0].provider
  const testModel = testTargets[0].model
  console.log(`\nPrimary test model: ${testProvider}/${testModel} (${testTargets[0].label})`)
  console.log(`All test targets: ${testTargets.map(t => `${t.provider}/${t.model}`).join(", ")}`)

  // 3. Create session WITH permissions (agent mode)
  console.log("\n--- Test 1: Create agent-mode session with permissions ---")
  let sessionId: string | undefined
  try {
    const session = await client.session.create({
      title: "agent-mode-test",
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
      ] as any,
    } as any)
    sessionId = session.data?.id
    console.log("Session created:", sessionId)
    console.log("Session data:", JSON.stringify(session.data, null, 2).slice(0, 500))

    if (!sessionId) {
      console.error("No session ID!")
      process.exit(1)
    }
  } catch (err: any) {
    console.error("Session creation failed:", err?.message)
    console.error("Full error:", JSON.stringify(err, null, 2).slice(0, 1000))
    process.exit(1)
  }

  // 4. Send prompt with agent:"general" — ask model to read a file
  console.log("\n--- Test 2: Send prompt with agent:'general' (file read task) ---")
  try {
    const taskPrompt = primerContent
      ? `${primerContent}\n\n---\n\n`
      : ""

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120_000) // 2 min timeout

    const startTime = Date.now()
    console.log("Sending prompt (120s timeout)...")

    const result = await client.session.prompt(
      {
        sessionID: sessionId,
        model: { providerID: testProvider, modelID: testModel },
        agent: "general",
        parts: [{
          type: "text" as const,
          text: taskPrompt +
            "You have file system access. Please do the following:\n" +
            "1. Read the file 'sections/01_core_principles.md' and tell me what the first line says\n" +
            "2. List the files in the 'sections/' directory\n" +
            "3. Report back what you found\n\n" +
            "Use the tools available to you (Read, Glob) to accomplish this. Do NOT guess the contents.",
        }],
      } as any,
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)
    const duration = Date.now() - startTime

    console.log(`\nResponse received in ${duration}ms`)

    const data = (result as any)?.data
    if (!data || Object.keys(data).length === 0) {
      console.log("EMPTY RESPONSE — model may not support agent mode")
      console.log("Full result:", JSON.stringify(result, null, 2).slice(0, 2000))
    } else {
      const parts = data?.parts
      const info = data?.info
      console.log("info keys:", Object.keys(info ?? {}))
      console.log("info.agent:", info?.agent)
      console.log("info.mode:", info?.mode)
      console.log("info.error:", JSON.stringify(info?.error, null, 2))
      console.log("info.tokens:", JSON.stringify(info?.tokens))
      console.log("info.modelID:", info?.modelID)
      console.log("info.providerID:", info?.providerID)
      console.log("parts count:", Array.isArray(parts) ? parts.length : "not array")
      console.log("\nFull info:", JSON.stringify(info, null, 2).slice(0, 2000))

      if (Array.isArray(parts)) {
        for (const part of parts) {
          if (part?.type === "text") {
            console.log("\n--- MODEL RESPONSE ---")
            console.log(part.text?.slice(0, 2000))
            console.log("--- END RESPONSE ---")
          } else if (part?.type === "tool-invocation" || part?.type === "tool_use") {
            console.log(`\nTOOL CALL: ${part.name ?? part.tool ?? "unknown"}`)
            console.log("Input:", JSON.stringify(part.input ?? part.args, null, 2).slice(0, 500))
          } else if (part?.type === "tool-result" || part?.type === "tool_result") {
            console.log(`TOOL RESULT: ${JSON.stringify(part).slice(0, 500)}`)
          } else {
            console.log(`PART [${part?.type}]:`, JSON.stringify(part).slice(0, 300))
          }
        }
      }

      // Check if the model actually used tools
      const toolParts = Array.isArray(parts) ? parts.filter((p: any) =>
        p?.type === "tool-invocation" || p?.type === "tool_use" || p?.type === "tool-result"
      ) : []
      console.log(`\n=== TOOL USAGE: ${toolParts.length > 0 ? "YES (" + toolParts.length + " tool parts)" : "NO (text-only response)"} ===`)

      if (toolParts.length === 0) {
        console.log("WARNING: Model did not use tools. This means either:")
        console.log("  - The permission ruleset wasn't applied correctly")
        console.log("  - The 'agent: general' parameter wasn't recognized")
        console.log("  - The model chose not to use tools")
      }
    }
  } catch (err: any) {
    if (err?.name === "AbortError") {
      console.log("TIMEOUT — model did not respond within 120s")
    } else {
      console.error("Prompt failed:", err?.message)
      console.error("Full error:", JSON.stringify(err, null, 2).slice(0, 1000))
    }
  }

  // 5. Test 3: Simple text-mode for comparison (no agent, no permissions)
  console.log("\n\n--- Test 3: Text-mode session (no agent, no permissions) ---")
  let textSessionId: string | undefined
  try {
    const session = await client.session.create({ title: "text-mode-test" })
    textSessionId = session.data?.id
    console.log("Session created:", textSessionId)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30_000)

    const startTime = Date.now()
    const result = await client.session.prompt(
      {
        sessionID: textSessionId!,
        model: { providerID: testProvider, modelID: testModel },
        parts: [{ type: "text" as const, text: "Reply with exactly: TEXT_MODE_OK" }],
      },
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)
    const duration = Date.now() - startTime

    const data = (result as any)?.data
    const parts = data?.parts
    const text = Array.isArray(parts)
      ? parts.filter((p: any) => p?.type === "text").map((p: any) => p.text).join("")
      : ""
    console.log(`Response in ${duration}ms: ${text.slice(0, 200)}`)
    console.log(`Text mode: ${text.includes("TEXT_MODE_OK") ? "PASS" : "RESPONSE (check above)"}`)
  } catch (err: any) {
    console.error("Text mode test failed:", err?.message)
  } finally {
    if (textSessionId) {
      await client.session.delete({ sessionID: textSessionId }).catch(() => {})
    }
  }

  // Cleanup agent session (preserve for debugging)
  console.log(`\nAgent session preserved for debugging: ${sessionId}`)
  console.log("To clean up: curl -X DELETE http://127.0.0.1:4096/session/" + sessionId)

  console.log("\n=== Agent Mode Test Complete ===")
}

main().catch(console.error)
