# OpenCode Coding System

A comprehensive AI-assisted development methodology combining systematic planning, implementation discipline, and validation strategies. Optimized for [OpenCode](https://opencode.ai).

---

## Core Principles

**YAGNI** — Only implement what's needed. No premature optimization.
**KISS** — Prefer simple, readable solutions over clever abstractions.
**DRY** — Extract common patterns; balance with YAGNI.
**Limit AI Assumptions** — Be explicit in plans and prompts. Less guessing = better output.
**Always Be Priming (ABP)** — Start every session with `/prime`. Context is everything.

---

## PIV Loop Methodology

Every feature follows the same cycle: **Plan**, **Implement**, **Validate**, then iterate.

### Key Principles

1. **Fresh sessions matter.** Planning creates exploration context. Execution needs clean context, not exploration baggage. The plan distills that into execution instructions.

2. **Multiple small loops.** Do not build entire features in one pass. Each PIV loop covers one feature slice, built completely before moving on.

3. **The handoff.** The plan is the bridge between thinking and building: 700-1000 lines capturing architecture decisions, file paths, code patterns, gotchas, and atomic tasks.

**Workflow:**
- `/planning` — Creates structured plan in `requests/{feature}-plan.md`
- `/execute` — Fresh session with plan file only
- `/code-review` — 4 parallel review agents
- `/commit` — Conventional commit with lessons to memory

---

## Context Engineering

The difference between 30% and 88% code acceptance is not AI intelligence. It's context clarity. Four pillars:

1. **Memory:** Past decisions in `memory.md`, read at `/prime`, appended at `/commit`
2. **RAG:** External docs and codebase patterns via Archon MCP (optional)
3. **Prompt Engineering:** Explicit solution statements from vibe planning
4. **Task Management:** 7-field atomic tasks (ACTION, TARGET, IMPLEMENT, PATTERN, IMPORTS, GOTCHA, VALIDATE)

---

## Git Save Points

Commit strategy for safe iteration:

- Each `/commit` creates a conventional-format commit
- Use `/undo` to revert changes if needed
- Lessons learned feed into `memory.md`

---

## Decision Framework

### Autonomy vs. Ask

| Decision Type | Autonomy Level |
|---------------|----------------|
| Code style within conventions | Full autonomy |
| File organization | Full autonomy |
| Library selection | Ask if major |
| Architecture changes | Always ask |
| Breaking changes | Always ask |

### When to Ask

- Multiple valid approaches with different tradeoffs
- Uncertainty about user intent
- Changes affecting public APIs
- Security-sensitive decisions

---

## On-Demand Guides

All guides in `reference/`. Load when the task requires it.

| Guide | When |
|-------|------|
| `layer1-guide` | New project AGENTS.md setup |
| `system-foundations` | Learning system mental models |
| `piv-loop-practice` | PIV Loop practical application |
| `validation-discipline` | 5-level validation pyramid |
| `file-structure` | File location lookup |
| `command-design-framework` | Slash command design |
| `subagents-deep-dive` | Subagent creation |
| `archon-workflow` | Archon tasks / RAG |
| `implementation-discipline` | Execution best practices |
| `global-rules-optimization` | AGENTS.md optimization patterns |

---

## Model Strategy — 5-Tier Cost-Optimized Cascade

Maximize free/cheap models. Anthropic is last resort only.

| Tier | Role | Provider/Model | Cost | Used By |
|------|------|----------------|------|---------|
| T1 | Implementation | `bailian-coding-plan/qwen3.5-plus` (+ coder-next, coder-plus) | FREE | `/execute` dispatch |
| T2 | First Validation | `zai-coding-plan/glm-5` | FREE | `/code-review`, `/code-loop` |
| T3 | Second Validation | `ollama-cloud/deepseek-v3.2` | FREE | `/code-loop` second opinion |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) | `/code-loop` near-final |
| T5 | Final Review | `anthropic/claude-sonnet-4-6` | PAID (expensive) | `/final-review` last resort |

**Orchestrator**: Claude Opus handles ONLY exploration, planning, orchestration, strategy.
**Fallback**: If `bailian-coding-plan` 404s, use `zai-coding-plan/glm-4.7`.
**Council**: `/council` dispatches to 13 real models across 4 providers for multi-model debates.

---

## Validation: 5-Level Pyramid

Each level gates the next:

1. **Syntax & Style** — Linting, formatting
2. **Type Safety** — Type checking
3. **Unit Tests** — Isolated logic
4. **Integration Tests** — System behavior
5. **Human Review** — Alignment with intent

---

## Available Commands

### MVP Build Pipeline (Primary Workflow)

The main development loop for building from empty project to working MVP:

```
/mvp → /prd → /decompose → /build next (repeat) → /ship
```

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/mvp` | Define or refine product vision → `mvp.md` | Start of a new project or major pivot |
| `/prd` | Full product requirements document → `PRD.md` | After `/mvp`, detailed what + why + user stories |
| `/decompose` | Break PRD into dependency-sorted spec list → `specs/BUILD_ORDER.md` | After `/prd`, or when re-planning |
| `/build [next\|spec]` | Semi-auto: plan spec → approve → implement → validate → commit | The main loop — repeat until all specs done |
| `/ship` | Full validation pyramid + T5 review + PR | When all specs complete |
| `/sync` | Validate build state, re-sync context between sessions | After breaks, before heavy specs, every 3rd spec |
| `/council [topic]` | Dispatch to 13 real AI models for multi-model debate | Architecture decisions, process design, validation |

### Supporting Commands

These are used internally by `/build` or available for manual use:

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/prime` | Load project context from memory + codebase | Start of every session |
| `/planning [feature]` | Interactive discovery → structured plan | Used internally by `/build` for standard/heavy specs |
| `/execute [plan]` | Implement from plan, or fix code review issues | Used internally by `/build` |
| `/code-loop` | Automated review → fix → review loop | Used internally by `/build` |
| `/commit` | Conventional-format git commit | Used internally by `/build`, or manual |
| `/pr` | Push branch, create PR | Used by `/ship`, or manual |
| `/final-review` | Pre-commit approval gate | Used by `/ship` |
| `/code-review` | Generalist review + UBS pre-scan | Manual code review |
| `/system-review` | Plan vs. reality analysis | After complex features |

### `/build` Automation Levels by Spec Depth

| Depth | Plan Size | T1 Impl | T2 Review | T3 Second | T4 Gate | Tests Required |
|-------|-----------|---------|-----------|-----------|---------|----------------|
| light | ~100 lines | Direct or T1 | — | — | — | L1-L2 (syntax, types) |
| standard | ~300 lines | T1 dispatch | T2 review | — | T4 gate | L1-L3 (+ unit tests) |
| heavy | ~700 lines | T1 dispatch | T2 review | T3 opinion | T4 gate | L1-L4 (+ integration) |

### Council Models (13 across 4 providers)

| Provider | Models | Cost |
|----------|--------|------|
| bailian-coding-plan | qwen3.5-plus, qwen3-coder-plus, qwen3-max, glm-5, kimi-k2.5 | FREE |
| ollama-cloud | deepseek-v3.2, qwen3.5:397b, kimi-k2-thinking | FREE |
| zai-coding-plan | glm-5, glm-4.7, glm-4.5, glm-4.7-flash | FREE |
| openai | gpt-5.3-codex | PAID (cheap) |

---

## Available Subagents

### Research Agents
| Agent | Purpose |
|-------|---------|
| `research-codebase` | Parallel codebase exploration, file discovery, pattern extraction |
| `research-external` | Documentation search, best practices, version compatibility |
| `research-ai-patterns` | AI/LLM integration patterns — prompts, RAG, agent orchestration |

### Code Review Agent
| Agent | What It Catches |
|-------|----------------|
| `code-review` | Bugs, security issues, performance, architecture, types (generalist) |

**Note:** Single sequential agent in a fix loop (`/code-review → /execute → /code-review → /commit`).

### Utility Agents
| Agent | Purpose |
|-------|---------|
| `plan-validator` | Validates plan structure before execution |
| `memory-curator` | Suggests what to save to memory.md after features |

### Swarm Workers (SwarmTools)
| Agent | Purpose |
|-------|---------|
| `swarm-worker-backend` | Backend services, APIs, business logic with file reservations |
| `swarm-worker-frontend` | React components, UI, styling, state management |
| `swarm-worker-database` | Schema design, migrations, queries, data modeling |
| `swarm-worker-testing` | Unit tests, integration tests, fixtures, mocks |

---

## Agent Ecosystem

**Context Window Isolation**: Each agent runs in its own context window — efficient for Ollama/Model Studio.

**When to use research agents standalone:**
- `@research-codebase` — Quick codebase exploration before planning
- `@research-external` — Documentation lookup for specific libraries
- `@research-ai-patterns` — AI feature planning (RAG, agents, prompts)
- `@memory-curator` — End of session, suggest lessons for memory.md

**Integration**: Research agents auto-called by `/planning` command (Phase 2-3).

---

## Available Skills

| Skill | Purpose |
|-------|---------|
| `planning-methodology` | 6-phase systematic planning with parallel research |

---

## Project Structure

```
opencode-coding-system/
├── AGENTS.md                    # Primary rules file (this file)
├── CLAUDE.md                    # Claude Code compatibility (references AGENTS.md)
├── memory.md                    # Cross-session memory (gitignored)
├── mvp.md                       # Product vision and scope (Ultima Second Brain)
│
├── sections/                    # Core methodology (loaded via opencode.json instructions)
│   ├── 01_core_principles.md    # YAGNI, KISS, DRY, Limit AI Assumptions, ABP
│   ├── 02_piv_loop.md           # Plan → Implement → Validate methodology
│   ├── 03_context_engineering.md# 4 Pillars: Memory, RAG, Prompts, Tasks
│   ├── 04_git_save_points.md    # Commit plans before implementing
│   └── 05_decision_framework.md # When to proceed vs ask
│
├── reference/                   # Deep guides (on-demand)
│   ├── system-foundations.md
│   ├── piv-loop-practice.md
│   ├── validation-discipline.md
│   ├── file-structure.md
│   ├── archon-workflow.md
│   ├── command-design-framework.md
│   ├── subagents-deep-dive.md
│   ├── implementation-discipline.md
│   ├── global-rules-optimization.md
│   ├── layer1-guide.md
│   └── sustainable-agent-architecture.md
│
├── specs/                       # Build order and state (created by /decompose)
│   ├── BUILD_ORDER.md           # Dependency-sorted spec list (single source of truth)
│   └── build-state.json         # Cross-session context (patterns, decisions, progress)
│
├── templates/                   # Reusable templates (9 files)
│   ├── BUILD-ORDER-TEMPLATE.md  # Template for /decompose output
│   ├── STRUCTURED-PLAN-TEMPLATE.md
│   ├── PRD-TEMPLATE.md
│   ├── SUB-PLAN-TEMPLATE.md
│   ├── VIBE-PLANNING-GUIDE.md
│   ├── PLAN-OVERVIEW-TEMPLATE.md
│   ├── MEMORY-TEMPLATE.md
│   ├── COMMAND-TEMPLATE.md
│   └── AGENT-TEMPLATE.md
│
├── requests/                    # Feature plans (gitignored)
│   ├── {feature}-plan.md        # Layer 2: Feature plans
│   └── execution-reports/       # Implementation reports
│
├── backend/                     # Backend application (Second Brain implementation)
│   ├── pyproject.toml           # Python project config
│   └── src/second_brain/        # Application code
│       ├── contracts/           # Typed contracts (ContextPacket, NextAction)
│       ├── orchestration/       # Retrieval router, fallback emitters
│       ├── agents/              # Recall agent and other agents
│       ├── services/            # Memory, Voyage rerank services
│       ├── schemas.py           # Pydantic schemas
│       ├── deps.py              # Dependency injection
│       └── mcp_server.py        # MCP tool exposure
│
├── docs/                        # Architecture documentation
│   └── architecture/            # System design docs
│       ├── conversational-retrieval-contract.md
│       ├── retrieval-planning-separation.md
│       └── retrieval-overlap-policy.md
│
├── tests/                       # Test files
│   ├── test_context_packet_contract.py
│   ├── test_retrieval_router_policy.py
│   └── ...
│
├── .opencode/                   # OpenCode configuration
│   ├── commands/                # Slash commands
│   ├── agents/                  # Custom subagents
│   └── skills/                  # Agent skills
│
└── .claude/                     # Claude Code compatibility (symlinks to .opencode)
```

---

## Current Implementation Status

### Active Feature Work

**Hybrid Retrieval Conversational Orchestrator** (Validated)

- **Goal**: Conversation-first retrieval with separated retrieval/planning responsibilities
- **Status**: Foundation complete, validated with evidence
- **Completed**:
  - Contract architecture docs (3 files)
  - Typed context packet models (ContextPacket, NextAction)
  - Deterministic retrieval router with Mem0 rerank policy
  - Fallback emitters (EMPTY_SET, LOW_CONFIDENCE, CHANNEL_MISMATCH, RERANK_BYPASSED, SUCCESS)
  - Mem0 real provider adapter with fallback hardening
  - Comprehensive tests (133 passing: 83 unit + 20 integration + 30 validation)
  - Manual branch validation evidence (13/13 scenarios PASS)
- **Evidence**: `requests/execution-reports/hybrid-retrieval-manual-validation-evidence #1.md`
- **Pending**: Runtime rollout to production environment

### Workflow Pattern

1. **Vision** (`/mvp`) → Defines `mvp.md` (what to build, who for, success signals)
2. **Requirements** (`/prd`) → Produces `PRD.md` (detailed product requirements, user stories, success criteria)
3. **Decompose** (`/decompose`) → Creates `specs/BUILD_ORDER.md` (dependency-sorted spec list from PRD)
4. **Build** (`/build next`) → Plan + approve + implement + validate + commit (one spec per loop)
5. **Sync** (`/sync`) → Checkpoint: validate state between sessions or before heavy specs
6. **Ship** (`/ship`) → Full validation pyramid + T5 review + PR when all specs done

## Optional: Archon MCP

[Archon MCP](https://github.com/coleam00/archon) provides task management and RAG search. **Completely optional.** When available, adds:
- Persistent task tracking across sessions
- RAG search over curated documentation
- Project and version management

---

## Quick Start

1. **Start OpenCode** and prime the system:
   ```
   opencode
   > /prime
   ```

2. **Define your MVP** (once per project):
   ```
   > /mvp
   ```

3. **Decompose into specs** (once, re-runnable):
   ```
   > /decompose
   ```

4. **Build specs** (the main loop — repeat until done):
   ```
   > /build next
   ```

5. **Ship when complete**:
   ```
   > /ship
   ```

**Full pipeline**: `/prime` → `/mvp` → `/prd` → `/decompose` → `/build next` (repeat) → `/ship`