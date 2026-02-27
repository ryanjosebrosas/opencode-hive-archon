# Model Strategy — 5-Tier Cost-Optimized Cascade

Maximize free/cheap models. Anthropic is last resort only.

**Read this when**: dispatching to models, configuring `/council`, debugging model routing, or reviewing the tier system.

---

## 5-Tier Overview

| Tier | Role | Provider/Model | Cost | Used By |
|------|------|----------------|------|---------|
| T1 | Implementation | `bailian-coding-plan/qwen3.5-plus` (+ coder-next, coder-plus) | FREE | `/execute` dispatch |
| T2 | First Validation | `zai-coding-plan/glm-5` | FREE | `/code-review`, `/code-loop` |
| T3 | Second Validation | `ollama-cloud/deepseek-v3.2` | FREE | `/code-loop` second opinion |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) | `/code-loop` near-final |
| T5 | Final Review | `anthropic/claude-sonnet-4-6` | PAID (expensive) | `/final-review` last resort |

**Orchestrator**: Claude Opus handles ONLY exploration, planning, orchestration, strategy.
**Fallback**: If `bailian-coding-plan` 404s, use `zai-coding-plan/glm-4.7`.

---

## Task Type Routing (dispatch / batch-dispatch)

Tools: `.opencode/tools/dispatch.ts`, `.opencode/tools/batch-dispatch.ts`

| Tier | TaskTypes | Routes To | Cost |
|------|-----------|-----------|------|
| T1a (fast) | boilerplate, simple-fix, quick-check | qwen3-coder-next | FREE |
| T1b (code) | test-scaffolding, logic-verification, api-analysis | qwen3-coder-plus | FREE |
| T1c (complex) | complex-codegen, research, architecture | qwen3.5-plus | FREE |
| T1d (long-ctx) | docs-lookup | kimi-k2.5 | FREE |
| T1e (prose) | docs-generation | minimax-m2.5 | FREE |
| T2 | thinking-review, code-review, security-review | glm-5 | FREE |
| T3 | second-validation, deep-research | deepseek-v3.2 | FREE |
| T4 | codex-review, codex-validation | gpt-5.3-codex | PAID |
| T5 | final-review, critical-review | claude-sonnet-4-6 | PAID |

---

## Council Models (13 across 4 providers)

Tool: `.opencode/tools/council.ts`, Command: `.opencode/commands/council.md`

| Provider | Models | Cost |
|----------|--------|------|
| bailian-coding-plan | qwen3.5-plus, qwen3-coder-plus, qwen3-max, glm-5, kimi-k2.5 | FREE |
| ollama-cloud | deepseek-v3.2, qwen3.5:397b, kimi-k2-thinking | FREE |
| zai-coding-plan | glm-5, glm-4.7, glm-4.5, glm-4.7-flash | FREE |
| openai | gpt-5.3-codex | PAID (cheap) |

---

## Custom Tools

Three TypeScript tools in `.opencode/tools/` enable multi-model orchestration via `opencode serve`:

| Tool | Purpose | Key Feature |
|------|---------|-------------|
| `dispatch` | Send a prompt to any single AI model | Two modes: `text` (prompt-response) and `agent` (full tool access). 27 taskType auto-routes across 5 tiers |
| `batch-dispatch` | Same prompt to multiple models in parallel | Min 2 models; comparison output with wall-time reporting |
| `council` | Multi-model discussion (models see each other's responses) | Shared session; structured or freeform modes; auto-selects 4 diverse models |

**Requires**: `opencode serve` running (server at `http://127.0.0.1:4096`).
**Primer**: `_dispatch-primer.md` auto-prepended to every dispatch and council — ensures all models have project context, core principles, and methodology.

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

Free providers (`bailian-coding-plan`, `zai-coding-plan`, `ollama-cloud`) return 404 on agent mode because they don't support tool calling API format. Use text mode for these providers.

**Agent mode example:**
```
dispatch({ provider: "anthropic", model: "claude-sonnet-4-6", mode: "agent", prompt: "Implement X. Read existing code first. Run ruff/mypy after." })
```

**Text mode example (free models):**
```
dispatch({ taskType: "complex-codegen", prompt: "Generate a Python service that does X. Return only the code." })
```

---

## Cascade Review-Fix Loop

Each tier reviews, and if issues found, T1 (FREE) fixes and the same tier re-reviews. Max 3 iterations per tier.

```
T1 implement → T2 review ⟲ T1 fix → T3 review ⟲ T1 fix → T4 gate ⟲ T1 fix → T5 validate ⟲ T1 fix → commit
```

## `/build` Automation Levels by Spec Depth

| Depth | Plan Size | T1 Impl (FREE) | T2 Review (FREE) | T3 Second (FREE) | T4 Gate (PAID) | T5 Final (PAID) | Tests |
|-------|-----------|-----------------|-------------------|-------------------|----------------|-----------------|-------|
| light | ~100 lines | T1 text mode | — | — | — | — | L1-L2 |
| standard | ~300 lines | T1 text mode | T2 review ⟲ | — | T4 gate | T5 validates | L1-L3 |
| heavy | ~700 lines | T1 text mode | T2 review ⟲ | T3 review ⟲ | T4 gate ⟲ | T5 validates ⟲ | L1-L4 |

⟲ = review-fix loop (max 3 iterations per tier)

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
