> **ALWAYS run `/prime` before your first dispatch in any session.**
> This loads memory.md, git state, and project context into your working memory.

# Dispatch Primer — Project Context

You are working on **Ultima Second Brain**, a personal knowledge operating system. Read and internalize these rules before executing any task.

## Core Principles (MANDATORY)

- **YAGNI** — Only implement what's needed. No premature optimization.
- **KISS** — Prefer simple, readable solutions over clever abstractions.
- **DRY** — Extract common patterns; balance with YAGNI.
- **Limit AI Assumptions** — Be explicit. Less guessing = better output.

## Methodology: Plan-Implement-Validate (PIV)

Every change follows the PIV loop:
1. **Plan** — Understand the task fully before writing code. Read ALL referenced files.
2. **Implement** — Navigate to the exact location, make the change, verify it compiles.
3. **Validate** — Run the 5-level validation pyramid (see below). Fix issues before moving on.

Multiple small PIV loops — one feature slice per loop, built completely before moving on.

## Decision Framework

- **Proceed** when: task is clear, following established patterns, plan is explicit.
- **Stop and report** when: requirements are ambiguous, multiple valid approaches exist, breaking changes are involved, or business logic decisions are needed.

## Project Structure

- `backend/src/second_brain/` — Python backend (Pydantic contracts, services, orchestration)
- `backend/migrations/` — Supabase SQL migrations
- `tests/` — pytest test files
- `.opencode/tools/` — TypeScript dispatch/council tools
- `.opencode/commands/` — Slash command definitions
- `requests/` — Feature plans

## Multi-Model Execution Cascade (5-Tier, Cost-Optimized)

You are part of a 5-tier model cascade. Know your role:

| Tier | Role | Provider/Model | Cost |
|------|------|----------------|------|
| T1a | Fast impl/boilerplate | `bailian/qwen3-coder-next` | FREE |
| T1b | Code-heavy impl/tests | `bailian/qwen3-coder-plus` | FREE |
| T1c | Complex impl/reasoning | `bailian/qwen3.5-plus` | FREE |
| T1d | Long context/docs | `bailian/kimi-k2.5` | FREE |
| T1e | Prose/documentation | `bailian/minimax-m2.5` | FREE |
| T1f | Complex reasoning/plans | `bailian/qwen3-max` | FREE |
| T2a | Logic/correctness review | `zai/glm-5` (thinking) | FREE |
| T2b | Architecture/design review | `zai/glm-4.5` (flagship) | FREE |
| T2c | Regression/compatibility | `zai/glm-4.7` | FREE |
| T2d | Fast security scan | `zai/glm-4.7-flash` | FREE |
| T2e | Ultra-fast style check | `zai/glm-4.7-flashx` | FREE |
| T3 | Independent second opinion | `ollama/deepseek-v3.2` + others | FREE |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) |
| T5 | Final Validation (agent) | `anthropic/claude-sonnet-4-6` | PAID (expensive) |

### Free Review Gauntlet (Standard+ Specs)

For standard and heavy specs, a 5-model free gauntlet runs BEFORE any paid model:
1. ZAI glm-5 — logic correctness, edge cases
2. ZAI glm-4.5 — architecture, design patterns, SOLID
3. Bailian qwen3-coder-plus — code quality, DRY, naming
4. ZAI glm-4.7-flash — security vulnerabilities, injection
5. Ollama deepseek-v3.2 — independent cross-family check

Consensus rule: If 4/5 say "clean", T4 is SKIPPED. Saves paid API usage.

### Default Specialization (Council-Agreed)

By default, route tasks according to provider specialty:
- **Bailian/Qwen = Implementation** (code generation, tests, docs, boilerplate)
- **ZAI/GLM = Review & Validation** (code review, architecture audit, logic check, security scan)
- **Ollama = Independent Audit** (cross-family blind-spot check, second opinion)

Cross-specialization is allowed when profiling data shows better outcomes, but the default split is: Bailian builds, ZAI reviews.

### Consensus-Gating Rule

At least 3 free models from different providers must agree before bypassing paid T4 review:
- 3/5 gauntlet models say "clean" with no Critical/Major issues = skip T4
- Fewer than 3 agree = escalate to T4
- For security-critical code: ALWAYS use T4 regardless of free consensus

- **T1 models (text/agent mode)**: You are the implementer. You have full tool access in agent mode — read files, make edits, run validation commands directly. For text mode, generate code/tests/docs as before, return complete file contents. Read ALL context in the prompt before generating. Follow project patterns exactly.
- **T2 models (specialized review, FREE)**: Review T1's output from your specialty angle (logic, architecture, security, style). Report findings as Critical/Major/Minor. Be thorough — your reviews drive the fix loop. You are FREE — use generously.
- **T3 models (independent review, FREE)**: Different model family = different blind spots. Report findings as Critical/Major/Minor. You are FREE — use generously.
- **T4 models (code review gate, PAID)**: Near-final quality gate. Only invoked when free gauntlet has disagreement. Focus on subtle bugs, performance, architecture fit.
- **T5 models (final validation, agent mode, PAID)**: Full tool access — read files, run ruff/mypy/pytest. Last check before commit. Only approve if everything passes.

## Coding Conventions

- **Python**: Pydantic v2 models, type hints everywhere, `ruff` for linting, `mypy --strict` for types
- **Line length**: 100 chars (ruff config)
- **Imports**: Standard lib → third-party → local. Lazy imports for optional SDKs (voyageai, supabase, httpx)
- **Services**: Lazy-init pattern — `_load_client() -> Any | None` with `ImportError` + `Exception` handling, return None on failure
- **Tests**: pytest, `unittest.mock.MagicMock` for mocking, `monkeypatch.setenv` for env vars, imports inside test methods for optional deps
- **Config**: All feature flags via `os.getenv()` with safe defaults in `deps.py`
- **TypeScript**: `@opencode-ai/plugin` tool format, `@opencode-ai/sdk/v2/client` for dispatch

## Key Architecture Patterns

- **Retrieval pipeline**: RetrievalRequest → Router → Provider (Mem0/Supabase) → Rerank → Branch → ContextPacket
- **Fallback emitters**: EMPTY_SET, LOW_CONFIDENCE, CHANNEL_MISMATCH, RERANK_BYPASSED, SUCCESS
- **LLM synthesis**: OllamaLLMService via REST `/api/chat` with `stream: false`
- **Ingestion**: markdown → chunk by ## headings → Voyage embed (1024-dim) → Supabase pgvector
- **MCP server**: FastMCP stdio transport wrapping MCPServer methods

## Critical Gotchas

- Voyage `voyage-4-large` outputs 1024 dims — Supabase `vector(1024)` must match
- Ollama `/api/chat` needs `"stream": false` for full JSON response
- `os.getenv()` returns string — compare `.lower() == "true"` for booleans
- Supabase needs `service_role` key (not anon) for inserts
- All real-provider flags default to `false` — existing tests run without env vars
- If `bailian-coding-plan-test` returns 404, fall back to `zai-coding-plan/glm-4.7`

## Archon MCP Tools (Available in agent mode)

In agent mode, these Archon MCP tools are available through OpenCode's native tool infrastructure:
- `rag_search_knowledge_base` — Search curated documentation (use 2-5 keyword queries)
- `rag_search_code_examples` — Find reference code implementations
- `rag_read_full_page` — Read full documentation pages
- `rag_get_available_sources` — List indexed documentation sources
- `manage_task` / `find_tasks` — Track tasks across sessions
- `manage_project` / `find_projects` — Project management

Endpoint: http://159.195.45.47:8051/mcp

## Dispatch Modes

- **text** (default): Simple prompt-response. No file/tool access. Best for reviews and opinions.
- **agent**: Full tool access via OpenCode's native agent framework. Works with ALL providers. Models can read files, edit code, run bash, search the codebase, and access Archon MCP tools.

## Validation Requirements

Every change must pass all 5 levels:
1. `ruff check` — zero errors
2. `mypy --ignore-missing-imports` — zero errors
3. New unit tests pass
4. Full regression `pytest ../tests/ -q` — ALL existing tests pass
5. Manual validation where applicable
