# Model Strategy — 5-Tier Cost-Optimized Cascade

Maximize free/cheap models. Anthropic is last resort only.

**Read this when**: dispatching to models, configuring `/council`, debugging model routing, or reviewing the tier system.

---

## 5-Tier Overview

| Tier | Role | Provider/Model | Cost | Used By |
|------|------|----------------|------|---------|
| T0 | Planning (thinking) | `ollama-cloud/kimi-k2-thinking` → `cogito-2.1:671b` → `qwen3-max` → `claude-opus-4-5` | FREE→PAID | `/planning` dispatch |
| T1 | Implementation | `bailian-coding-plan-test/qwen3.5-plus` (+ coder-next, coder-plus) | FREE | `/execute` dispatch |
| T2 | First Validation | `zai-coding-plan/glm-5` | FREE | `/code-review`, `/code-loop` |
| T3 | Second Validation | `ollama-cloud/deepseek-v3.2` | FREE | `/code-loop` second opinion |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) | `/code-loop` near-final |
| T5 | Final Review | `anthropic/claude-sonnet-4-6` | PAID (expensive) | `/final-review` last resort |

**Orchestrator**: Claude Opus handles ONLY exploration, planning, orchestration, strategy.
**Planning cascade**: `kimi-k2-thinking` (FREE) → `cogito-2.1:671b` (FREE) → `qwen3-max` (FREE) → `claude-opus-4-5` (PAID). Thinking models produce significantly better 700-1000 line plans.
**Fallback**: If `bailian-coding-plan-test` 404s, use `zai-coding-plan/glm-4.7`.
**Push cadence**: Push after every spec commit — do not batch to `/ship`.

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
| T0 (thinking/planning) | planning | kimi-k2-thinking → cogito-2.1:671b → qwen3-max → claude-opus-4-5 | FREE→PAID |
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
| `dispatch` | Send a prompt to any single AI model | Two modes: `text` (prompt-response), `agent` (full tool access via native OpenCode infrastructure - free providers too). 27 taskType auto-routes across 5 tiers |
| `batch-dispatch` | Same prompt to multiple models in parallel | Min 2 models; comparison output with wall-time reporting |
| `council` | Multi-model discussion (models see each other's responses) | Shared session; structured or freeform modes; auto-selects 4 diverse models |

**Requires**: `opencode serve` running (server at `http://127.0.0.1:4096`).
**Primer**: `_dispatch-primer.md` auto-prepended to every dispatch and council — ensures all models have project context, core principles, and methodology.

**Pre-dispatch**: Always run `/prime` before your first dispatch in any session to ensure models have fresh project context.


### Dispatch Modes

| Mode | Tool Access | Use Case | Default Timeout |
|------|-------------|----------|-----------------|
| `text` (default) | None — prompt in, text out | Reviews, opinions, research, boilerplate generation | 120s |
| `agent` | Full — file read/write, bash, glob, grep | Implementation tasks where model needs to navigate codebase, edit code, run validation | 300s |

**Agent mode permissions**: read, edit, bash, glob, grep, list, todoread, todowrite. Denies: task (no recursive dispatch), external_directory, webfetch, websearch.

**Agent mode works with ALL providers.** OpenCode's native infrastructure gives all providers (free and paid) the same capabilities: file read/write, grep, glob, bash, Archon MCP access. No fallback required.

**Two dispatch modes:**
| Mode | Tool Access | Providers | Use For |
|------|------------|-----------|---------|
| `text` (default) | None | All | Reviews, opinions, analysis |
| `agent` | Full (native agent infrastructure) | All (free and paid via OpenCode native tools) | Implementation tasks for all providers |

**Agent mode example (any provider):**
```
dispatch({ provider: "bailian-coding-plan-test", model: "qwen3.5-plus", mode: "agent", prompt: "Implement X. Read existing code first. Run ruff/mypy after." })
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

| Depth | Plan Format | T1 Impl (FREE) | Free Gauntlet (FREE) | T4 Gate (PAID) | T5 Final (PAID) | Tests |
|-------|-------------|-----------------|----------------------|----------------|-----------------|-------|
| light | Single plan (700-1000 lines) | T1 agent mode | 3-model impl-validation | — | — | L1-L3 |
| standard | Single plan (700-1000 lines) | T1 agent mode | 5-model review-gauntlet | Consensus-gated | — | L1-L4 |
| heavy | Master + sub-plans (500 + 700-1000 each) | T1 agent mode | 5-model review-gauntlet | Always | Always | L1-L4 |

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
