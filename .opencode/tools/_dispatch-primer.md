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
| T1 | Implementation (all codegen) | `bailian-coding-plan/qwen3.5-plus` (+ coder-next, coder-plus) | FREE |
| T2 | First Validation (thinking review) | `zai-coding-plan/glm-5` | FREE |
| T3 | Second Validation (independent) | `ollama-cloud/deepseek-v3.2` | FREE |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) |
| T5 | Final Review (last resort) | `anthropic/claude-sonnet-4-6` | PAID (expensive) |

- **T1 models (agent mode)**: You have full tool access — read files, edit code, run bash. Use it. Read ALL relevant codebase files BEFORE making changes. Execute tasks in order. Run `ruff check` and `mypy` after each change. Run `pytest` for affected tests. Report what you changed and validation results.
- **T1 models (text mode)**: Implement code, generate tests, write boilerplate. Return the code in your response — the orchestrator will apply it.
- **T2-T3 models**: Review T1's output. Focus on correctness, edge cases, security. Report findings as Critical/Major/Minor.
- **T4 models**: Near-final quality gate. Only invoked after T2-T3 pass.
- **T5 models**: Last resort. Only invoked for critical decisions or when lower tiers disagree.

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
- If `bailian-coding-plan` returns 404, fall back to `zai-coding-plan/glm-4.7`

## Archon MCP Tools (Available in agent mode)

If you have MCP access, these Archon tools are available for RAG search and task management:
- `rag_search_knowledge_base` — Search curated documentation (use 2-5 keyword queries)
- `rag_search_code_examples` — Find reference code implementations
- `rag_read_full_page` — Read full documentation pages
- `rag_get_available_sources` — List indexed documentation sources
- `manage_task` / `find_tasks` — Track tasks across sessions
- `manage_project` / `find_projects` — Project management

Endpoint: http://159.195.45.47:8051/mcp

## Validation Requirements

Every change must pass all 5 levels:
1. `ruff check` — zero errors
2. `mypy --ignore-missing-imports` — zero errors
3. New unit tests pass
4. Full regression `pytest ../tests/ -q` — ALL existing tests pass
5. Manual validation where applicable
