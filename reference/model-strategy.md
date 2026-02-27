# Model Strategy — 5-Tier Cost-Optimized Cascade

Maximize free/cheap models. Anthropic is last resort only.

**Read this when**: dispatching to models, configuring `/council`, debugging model routing, or reviewing the tier system.

---

## 5-Tier Overview

| Tier | Role | Provider/Model | Cost | Used By |
|------|------|----------------|------|---------|
| T1 | Implementation | `bailian-coding-plan-test/qwen3.5-plus` (+ coder-next, coder-plus) | FREE | `/execute` dispatch |
| T2 | First Validation | `zai-coding-plan/glm-5` | FREE | `/code-review`, `/code-loop` |
| T3 | Second Validation | `ollama-cloud/deepseek-v3.2` | FREE | `/code-loop` second opinion |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) | `/code-loop` near-final |
| T5 | Final Review | `anthropic/claude-sonnet-4-6` | PAID (expensive) | `/final-review` last resort |

**Orchestrator**: Claude Opus handles ONLY exploration, planning, orchestration, strategy.
**Fallback**: If `bailian-coding-plan-test` 404s, use `zai-coding-plan/glm-4.7`.

---

## Task Type Routing (dispatch / batch-dispatch)

Tools: `.opencode/tools/dispatch.ts`, `.opencode/tools/batch-dispatch.ts`

| Tier | TaskTypes | Routes To | Cost |
|------|-----------|-----------|------|
| T1a (fast) | boilerplate, simple-fix, quick-check, general-opinion, pre-commit-analysis | qwen3-coder-next | FREE |
| T1b (code) | test-scaffolding, test-generation, logic-verification, api-analysis, code-quality-review | qwen3-coder-plus | FREE |
| T1c (complex) | complex-codegen, complex-fix, research, architecture, library-comparison, pattern-scan | qwen3.5-plus | FREE |
| T1d (long-ctx) | docs-lookup, long-context-review | kimi-k2.5 | FREE |
| T1e (prose) | docs-generation, docstring-generation, changelog-generation | minimax-m2.5 | FREE |
| T1f (reasoning) | deep-plan-review, complex-reasoning | qwen3-max-2026-01-23 | FREE |
| T2a (thinking) | thinking-review, first-validation, code-review, security-review, plan-review, logic-review | glm-5 | FREE |
| T2b (flagship) | architecture-audit, design-review | glm-4.5 | FREE |
| T2c (standard) | regression-check, compatibility-check | glm-4.7 | FREE |
| T2d (flash) | style-review, quick-style-check | glm-4.7-flash | FREE |
| T2e (ultrafast) | fast-review, ultra-fast-check | glm-4.7-flashx | FREE |
| T3 (standard) | second-validation, deep-research, independent-review | deepseek-v3.2 | FREE |
| T3 (architecture) | architecture-review | kimi-k2:1t | FREE |
| T3 (deep-review) | deep-code-review | deepseek-v3.1:671b | FREE |
| T3 (reasoning) | reasoning-review | cogito-2.1:671b | FREE |
| T3 (code) | test-review | devstral-2:123b | FREE |
| T3 (multi) | multi-review | gemini-3-pro-preview | FREE |
| T3 (fast) | fast-second-opinion | gemini-3-flash-preview | FREE |
| T3 (heavy) | heavy-codegen | mistral-large-3:675b | FREE |
| T3 (big-code) | big-code-review | qwen3-coder:480b | FREE |
| T3 (thinking) | thinking-second | kimi-k2-thinking | FREE |
| T3 (plan) | plan-critique | qwen3.5:397b | FREE |
| T4 | codex-review, codex-validation | gpt-5.3-codex | PAID |
| T5 | final-review, critical-review | claude-sonnet-4-6 | PAID |

---

## Council Models (18 preferred across 4 providers)

Tool: `.opencode/tools/council.ts`, Command: `.opencode/commands/council.md`

| Provider | Models | Cost |
|----------|--------|------|
| anthropic | claude-sonnet-4 | PAID |
| openai | gpt-5-codex | PAID |
| bailian-coding-plan-test | qwen3.5-plus, qwen3-coder-plus, qwen3-max, kimi-k2.5, glm-5 | FREE |
| zai-coding-plan | glm-5, glm-4.7, glm-4.5, glm-4.7-flash | FREE |
| ollama-cloud | deepseek-v3.2, kimi-k2:1t, gemini-3-pro-preview, devstral-2:123b, mistral-large-3:675b, cogito-2.1:671b, kimi-k2-thinking | FREE |

Default council size: 5 models (auto-selected for provider diversity).

---

## Custom Tools

Three TypeScript tools in `.opencode/tools/` enable multi-model orchestration via `opencode serve`:

| Tool | Purpose | Key Feature |
|------|---------|-------------|
| `dispatch` | Send a prompt to any single AI model | Three modes: `text` (prompt-response), `agent` (full tool access), `relay` (XML tag tool access for free providers). 27 taskType auto-routes across 5 tiers |
| `batch-dispatch` | Same prompt to multiple models in parallel | Min 2 models; comparison output with wall-time reporting |
| `council` | Multi-model discussion (models see each other's responses) | Shared session; structured or freeform modes; auto-selects 4 diverse models |

**Requires**: `opencode serve` running (server at `http://127.0.0.1:4096`).
**Primer**: `_dispatch-primer.md` auto-prepended to every dispatch and council — ensures all models have project context, core principles, and methodology.

**Pre-dispatch**: Always run `/prime` before your first dispatch in any session to ensure models have fresh project context.

### Shared Relay Utilities

File: `.opencode/tools/_relay-utils.ts`

Shared module extracted from dispatch.ts. Both dispatch.ts and council.ts import from it.

| Export | Purpose |
|--------|---------|
| `RELAY_INSTRUCTIONS` | Full relay mode instructions (for T1-T3 text-based tool access) |
| `ARCHON_RELAY_INSTRUCTIONS` | Archon-only instructions (for T4-T5 agent mode with Archon access) |
| `parseToolCalls()` | Parse XML `<tool>` tags from model response text |
| `executeTool()` | Execute a parsed tool call (read, glob, grep, bash, edit, archon_search, archon_sources) |
| `relayLoop()` | Full relay loop: send prompt → parse tools → execute → send results → repeat (max 5 turns) |
| `initArchonSession()` | Initialize Archon MCP session (required before tool calls) |
| `callArchonTool()` | Call an Archon MCP tool with JSON-RPC |

**Relay mode flow:**
1. Prepend RELAY_INSTRUCTIONS to prompt (teaches model XML tag format)
2. Send to model via text mode (no native tool-use API needed)
3. Parse `<tool>` tags from response
4. Execute tools locally (file read, grep, Archon MCP, etc.)
5. Send results back as `<tool_result>` blocks
6. Repeat until model responds with no tool tags (max 5 turns)

**Agent mode Archon access:**
- T4/T5 agent mode sessions get native file tools from OpenCode
- ARCHON_RELAY_INSTRUCTIONS is prepended so they can also query Archon via XML tags
- Post-response loop checks for archon_search/archon_sources tags and executes them

### Dispatch Modes

| Mode | Tool Access | Use Case | Default Timeout |
|------|-------------|----------|-----------------|
| `text` (default) | None — prompt in, text out | Reviews, opinions, research, boilerplate generation | 120s |
| `agent` | Full — file read/write, bash, glob, grep | Implementation tasks where model needs to navigate codebase, edit code, run validation | 300s |

**Agent mode permissions**: read, edit, bash, glob, grep, list, todoread, todowrite. Denies: task (no recursive dispatch), external_directory, webfetch, websearch.

**Agent mode provider compatibility**: Agent mode requires tool-use API support. Only these providers work:
- `anthropic` — Confirmed working (Claude Sonnet)
- `openai` — Expected to work (GPT/Codex)
- `opencode` — Expected to work (built-in)

Free providers (`bailian-coding-plan-test`, `zai-coding-plan`, `ollama-cloud`) don't support native agent mode (tool-use API). Use **relay mode** instead — it gives them file read/write, grep, glob, bash, and Archon MCP access through a text-based XML tag relay loop.

**Auto-fallback**: If you request `mode:"agent"` with a free provider, dispatch automatically falls back to `mode:"relay"` instead of erroring.

**Three dispatch modes:**
| Mode | Tool Access | Providers | Use For |
|------|------------|-----------|---------|
| `text` (default) | None | All | Reviews, opinions, analysis |
| `agent` | Full (native API) | Anthropic, OpenAI | T4-T5 implementation, validation |
| `relay` | Full (XML tag relay) | All (designed for T1-T3) | T1-T3 implementation with file/Archon access |

**Agent mode example (T4-T5):**
```
dispatch({ provider: "anthropic", model: "claude-sonnet-4-6", mode: "agent", prompt: "Implement X. Read existing code first. Run ruff/mypy after." })
```

**Relay mode example (T1-T3 — auto-fallback from agent):**
```
dispatch({ provider: "bailian-coding-plan-test", model: "qwen3.5-plus", mode: "agent", prompt: "Read src/main.py, then implement feature X" })
// Auto-falls back to relay mode. Model uses <tool name="read" path="src/main.py" /> to read files.
```

**Text mode example (reviews):**
```
dispatch({ taskType: "thinking-review", prompt: "Review this code for bugs: ..." })
```

---

## Cascade Review-Fix Loop

Each tier reviews, and if issues found, T1 (FREE) fixes and the same tier re-reviews. Max 3 iterations per tier.

```
T1 implement → T2 review ⟲ T1 fix → T3 review ⟲ T1 fix → T4 gate ⟲ T1 fix → T5 validate ⟲ T1 fix → commit
```

## Batch Dispatch Patterns (10 pre-defined workflows)

Pre-defined multi-model workflows in `batch-dispatch.ts`. Invoke via `batchPattern` arg.

| Pattern | Models | Use Case |
|---------|--------|----------|
| `free-review-gauntlet` | glm-5, glm-4.5, qwen3-coder-plus, glm-4.7-flash, deepseek-v3.2 | 5-model consensus review — core of smart escalation |
| `free-heavy-architecture` | glm-4.5, qwen3-max, kimi-k2:1t, deepseek-v3.1:671b, cogito-2.1:671b | Architecture decisions with ZAI+Bailian+Ollama flagships |
| `free-security-audit` | glm-4.7-flash, glm-5, qwen3-coder-plus | 3-model security-focused review |
| `free-plan-review` | glm-5, glm-4.5, qwen3-max, deepseek-v3.2 | 4-model plan critique before approval |
| `free-impl-validation` | glm-5, glm-4.7-flash, deepseek-v3.2 | Quick 3-model check after T1 implementation |
| `free-regression-sweep` | glm-4.7, qwen3-coder-plus, devstral-2:123b | 3-model regression check |
| `multi-review` | glm-5, glm-4.5, deepseek-v3.2, kimi-k2-thinking | Multi-family code review (4 free models) |
| `plan-review` | glm-5, qwen3-max, qwen3.5:397b, deepseek-v3.2 | Plan critique with Bailian flagship |
| `pre-impl-scan` | glm-4.7-flash, qwen3-coder-next, deepseek-v3.2 | Pre-implementation pattern scan |
| `heavy-architecture` | glm-4.5, qwen3-max, kimi-k2:1t, deepseek-v3.1:671b, cogito-2.1:671b | Deep architecture with ZAI+Bailian+Ollama |

## Smart Escalation (Free Gauntlet)

Consensus-based escalation minimizes paid API usage by running free models first.

### Consensus Rules

After the Free Review Gauntlet runs (5 models in parallel), count Critical/Major findings:

| Free Models Finding Issues | Action | Paid Cost |
|---------------------------|--------|-----------|
| 0-1 out of 5 | SKIP T4, commit directly | $0 |
| 2 out of 5 | Run T4 gate only | Low |
| 3+ out of 5 | T1 fix + re-gauntlet (max 3x), then T4 | Low |

### Per Spec Depth

| Depth | Free Validation | Paid Models | Estimated Savings |
|-------|----------------|-------------|-------------------|
| light | `free-impl-validation` (3 models) | None | 100% — zero paid |
| standard | `free-review-gauntlet` (5 models) + consensus | T4 only if disagreement | ~70% fewer T4 calls |
| heavy | `free-review-gauntlet` (5 models) | T4 always + T5 always | Full cascade, but free gauntlet catches issues early |

## `/build` Automation Levels by Spec Depth

| Depth | Plan Size | T1 Impl (FREE) | Free Gauntlet (FREE) | T4 Gate (PAID) | T5 Final (PAID) | Tests |
|-------|-----------|-----------------|----------------------|----------------|-----------------|-------|
| light | ~100 lines | T1 text mode | 3-model impl-validation | — | — | L1-L2 |
| standard | ~300 lines | T1 text mode | 5-model review-gauntlet | Consensus-gated | — | L1-L3 |
| heavy | ~700 lines | T1 text mode | 5-model review-gauntlet | Always | Always (agent) | L1-L4 |

Gauntlet ⟲ = if issues found, T1 fixes (FREE) and gauntlet re-runs (max 3 iterations)

---

## MCP Server: Archon (Remote — RAG + Task Management)

[Archon MCP](https://github.com/coleam00/archon) provides curated knowledge base and task tracking.

| Tool | Purpose |
|------|---------|
| `rag_search_knowledge_base` | Search curated documentation (2-5 keyword queries) |
| `rag_search_code_examples` | Find reference code implementations |
| `rag_read_full_page` | Read full documentation pages |
| `rag_get_available_sources` | List indexed documentation sources |
| `manage_task` / `find_tasks` | Persistent task tracking across sessions |
| `manage_project` / `find_projects` | Project and version management |

**Endpoint**: `http://159.195.45.47:8051/mcp`
**Status**: Optional — all commands degrade gracefully if unavailable.
