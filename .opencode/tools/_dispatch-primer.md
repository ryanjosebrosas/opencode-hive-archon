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
| T1 | Implementation (all codegen) | `bailian-coding-plan-test/qwen3.5-plus` (+ coder-next, coder-plus) | FREE |
| T2 | First Validation (thinking review) | `zai-coding-plan/glm-5` | FREE |
| T3 | Second Validation (independent) | `ollama-cloud/deepseek-v3.2` | FREE |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) |
| T5 | Final Validation (agent mode) | `anthropic/claude-sonnet-4-6` | PAID (expensive) |

- **T1 models (text mode)**: You are the implementer. Generate code, tests, boilerplate. Return complete file contents — the orchestrator applies them. Read ALL context in the prompt before generating. Follow project patterns exactly.
- **T2 models (first review, FREE)**: First review of T1's output. Focus on correctness, edge cases, security. Report findings as Critical/Major/Minor. Be thorough — your reviews drive the fix loop. You are FREE — use generously.
- **T3 models (second review, FREE)**: Independent second opinion. Different model family = different blind spots. Report findings as Critical/Major/Minor. You are FREE — use generously.
- **T4 models (code review gate, PAID)**: Near-final quality gate after T2-T3 pass clean. Focus on subtle bugs, performance, architecture fit that free models missed.
- **T5 models (final validation, agent mode, PAID)**: You have full tool access — read actual files, run ruff/mypy/pytest. Last check before commit. Only approve if everything passes. Report PASS or FAIL with details.

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

## Archon MCP Tools (Available in agent mode and relay mode)

If you have MCP access (agent mode) or relay tool access (relay mode), these Archon tools are available:
- `rag_search_knowledge_base` — Search curated documentation (use 2-5 keyword queries)
- `rag_search_code_examples` — Find reference code implementations
- `rag_read_full_page` — Read full documentation pages
- `rag_get_available_sources` — List indexed documentation sources
- `manage_task` / `find_tasks` — Track tasks across sessions
- `manage_project` / `find_projects` — Project management

Endpoint: http://159.195.45.47:8051/mcp

## Dispatch Modes

- **text** (default): Simple prompt-response. No file/tool access. Best for reviews and opinions.
- **agent**: Full tool access via OpenCode agent framework. Works with Anthropic and OpenAI only.
- **relay**: Text-based tool relay for T1-T3 free providers. Model outputs XML tool tags, orchestrator executes them and sends results back. Gives file read/write, grep, glob, bash, and Archon MCP access.
- **Auto-fallback**: If you request `mode:"agent"` with a T1-T3 provider, it automatically falls back to `mode:"relay"` instead of erroring.

## Validation Requirements

Every change must pass all 5 levels:
1. `ruff check` — zero errors
2. `mypy --ignore-missing-imports` — zero errors
3. New unit tests pass
4. Full regression `pytest ../tests/ -q` — ALL existing tests pass
5. Manual validation where applicable
