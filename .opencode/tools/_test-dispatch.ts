/**
 * Diagnostic test script for dispatch tools.
 * NOT a tool (no export default tool()) — run with: cd .opencode && bun run tools/_test-dispatch.ts
 * Purpose: discover connected providers, test session.prompt() with timeout, capture response shapes.
 */
import { createOpencodeClient } from "@opencode-ai/sdk/v2/client"

const BASE_URL = "http://127.0.0.1:4096"

async function main() {
  console.log("=== Dispatch Diagnostic Test ===\n")

  // 1. Create client + health check
  const client = createOpencodeClient({ baseUrl: BASE_URL })
  const health = await client.global.health()
  console.log("Health:", JSON.stringify(health.data))
  if (!health.data?.healthy) {
    console.error("Server not healthy. Aborting.")
    process.exit(1)
  }

  // 2. Discover connected providers via raw fetch
  console.log("\n--- Connected Providers ---")
  let connectedProviders: string[] = []
  let allProviders: Array<{ id: string; name?: string; models?: Record<string, { id: string; name?: string; status?: string }> }> = []
  try {
    const resp = await fetch(`${BASE_URL}/provider`)
    const providerData = await resp.json() as {
      all?: Array<{ id: string; name?: string; models?: Record<string, { id: string; name?: string; status?: string }> }>
      connected?: string[]
    }
    connectedProviders = providerData.connected ?? []
    allProviders = providerData.all ?? []
    console.log("Connected:", connectedProviders)
    console.log("Total providers:", allProviders.length)

    // Show models for connected providers (models is a Record, not Array)
    for (const pid of connectedProviders) {
      const provider = allProviders.find((p) => p.id === pid)
      if (provider?.models && typeof provider.models === "object") {
        const modelEntries = Object.values(provider.models)
        const activeModels = modelEntries
          .filter((m) => m.status === "active" || !m.status)
          .slice(0, 5)
        console.log(`  ${pid}: ${activeModels.map((m) => m.id).join(", ")}${modelEntries.length > 5 ? ` (+${modelEntries.length - 5} more)` : ""}`)
      }
    }
  } catch (err) {
    console.error("Failed to list providers:", err)
  }

  if (connectedProviders.length === 0) {
    console.error("\nNo connected providers! Run '/connect <provider>' first.")
    process.exit(1)
  }

  // 3. Pick first connected provider + its first model
  const testProvider = connectedProviders[0]
  const providerInfo = allProviders.find((p) => p.id === testProvider)
  const modelValues = providerInfo?.models ? Object.values(providerInfo.models) : []
  const testModel = modelValues[0]?.id
  if (!testModel) {
    console.error(`No models found for connected provider: ${testProvider}`)
    process.exit(1)
  }
  console.log(`\n--- Testing: ${testProvider}/${testModel} ---`)

  // 4. Test session.prompt() with 30s timeout
  let sessionId: string | undefined
  try {
    const session = await client.session.create({ title: "diagnostic-test" })
    sessionId = session.data?.id
    console.log("Session created:", sessionId)
    if (!sessionId) {
      console.error("No session ID returned:", JSON.stringify(session.data))
      process.exit(1)
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30_000)

    console.log("Sending prompt (30s timeout)...")
    const startTime = Date.now()
    const result = await client.session.prompt(
      {
        sessionID: sessionId,
        model: { providerID: testProvider, modelID: testModel },
        parts: [{ type: "text" as const, text: "Reply with exactly: DISPATCH_TEST_OK" }],
      },
      { signal: controller.signal },
    )
    clearTimeout(timeoutId)
    const duration = Date.now() - startTime

    console.log(`Response received in ${duration}ms`)
    console.log("result keys:", Object.keys(result ?? {}))
    console.log("result.data keys:", Object.keys((result as any)?.data ?? {}))
    console.log("result.error:", (result as any)?.error)

    // Check for empty response
    const data = (result as any)?.data
    if (!data || (typeof data === "object" && Object.keys(data).length === 0)) {
      console.log("EMPTY RESPONSE DETECTED — model may not be connected or responding")
    } else {
      const info = data?.info
      const parts = data?.parts
      console.log("info keys:", Object.keys(info ?? {}))
      console.log("parts count:", Array.isArray(parts) ? parts.length : "not array")
      if (Array.isArray(parts)) {
        for (const part of parts) {
          if (part?.type === "text") {
            console.log("TEXT:", part.text?.slice(0, 500))
          } else {
            console.log("PART:", part?.type, JSON.stringify(part).slice(0, 200))
          }
        }
      }
      console.log("\nFull response (truncated):", JSON.stringify(data, null, 2).slice(0, 3000))
    }
  } catch (err: any) {
    if (err?.name === "AbortError" || (err instanceof Error && err.name === "AbortError")) {
      console.log("TIMEOUT — model did not respond within 30s")
    } else {
      console.log("ERROR:", err?.name, err?.message)
      console.log("Full error:", JSON.stringify(err, null, 2).slice(0, 1000))
    }
  } finally {
    if (sessionId) {
      await client.session.delete({ sessionID: sessionId }).catch(() => {})
      console.log("Session cleaned up")
    }
  }

  // 5. Test with wrong provider (expect failure)
  console.log("\n--- Testing: nonexistent/fake-model ---")
  let badSessionId: string | undefined
  try {
    const session = await client.session.create({ title: "diagnostic-bad-provider" })
    badSessionId = session.data?.id
    if (!badSessionId) {
      console.error("No session ID for bad provider test")
    } else {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10_000)

      const result = await client.session.prompt(
        {
          sessionID: badSessionId,
          model: { providerID: "nonexistent-provider-xyz", modelID: "fake-model" },
          parts: [{ type: "text" as const, text: "test" }],
        },
        { signal: controller.signal },
      )
      clearTimeout(timeoutId)

      console.log("Bad provider result:", JSON.stringify(result, null, 2).slice(0, 1000))
    }
  } catch (err: any) {
    console.log("Bad provider error:", err?.name, err?.message)
  } finally {
    if (badSessionId) {
      await client.session.delete({ sessionID: badSessionId }).catch(() => {})
    }
  }

  console.log("\n=== Diagnostic Test Complete ===")
}

main().catch(console.error)
