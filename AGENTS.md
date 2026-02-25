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

## Model Strategy

Separate thinking from doing. Use the right model for each phase:

| Phase | Recommended Model | Why |
|-------|-------------------|-----|
| `/planning` | Smart model (e.g., claude-sonnet, opencode/opus) | Deep reasoning produces better plans |
| `/execute` | Fast model (default) | Follows plans well at lower cost |
| `/code-review` | Fast model (via subagents) | 4 parallel agents |
| `/commit`, `/prime` | Fast model | General-purpose tasks |

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

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/prime` | Dispatches 2 parallel agents for context | Start of every session |
| `/planning [feature]` | 6-phase analysis with conditional research, mvp.md workflow | Before building any feature |
| `/execute [plan]` | Implements plan OR fixes code review issues | After planning, or after code review |
| `/code-loop` | Automated review → fix → review loop until clean, then commit | After implementation (replaces manual fix loop) |
| `/commit` | Creates conventional-format git commit | After implementation passes review |
| `/code-review` | 1 generalist agent + UBS pre-scan | After implementation (or use `/code-loop`) |
| `/system-review` | Plan vs. reality analysis, memory suggestions | After complex features, periodic audits |

**Note:** `/execute` handles both plan execution and code review fixes (fix mode auto-detected).

**Solo Developer Mode**: Focus on `/prime` → `/planning` → `/execute` → `/code-loop` → `/commit`.

**Manual Fix Loop** (alternative to `/code-loop`): `/code-review` → `/execute` (fix mode) → `/code-review` until clean → `/commit`.

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
├── templates/                   # Reusable templates (8 files)
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

**Hybrid Retrieval Conversational Orchestrator** (Foundation Complete)

- **Goal**: Conversation-first retrieval with separated retrieval/planning responsibilities
- **Status**: Foundation implemented, integration pending
- **Completed**:
  - Contract architecture docs (3 files)
  - Typed context packet models (ContextPacket, NextAction)
  - Deterministic retrieval router with Mem0 rerank policy
  - Fallback emitters (EMPTY_SET, LOW_CONFIDENCE, CHANNEL_MISMATCH, RERANK_BYPASSED, SUCCESS)
  - Comprehensive tests (41 passing)
- **Pending**:
  - Integration with existing recall flow
  - Manual branch validation

### Workflow Pattern

1. **Plan** (`/planning`) → Creates `requests/{feature}-plan.md`
2. **Execute** (`/execute`) → Implements from plan, creates backend structure
3. **Validate** → Lint, typecheck, test (5-level pyramid)
4. **Report** → Saves execution report to `requests/execution-reports/`
5. **Commit** (`/commit`) → Conventional commit with lessons to memory.md

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

2. **Plan your first feature**:
   ```
   > /planning my-feature
   ```

3. **Execute the plan** (fresh session for clean context):
   ```
   > /execute requests/my-feature-plan.md
   ```

4. **Review and commit**:
   ```
   > /code-review
   > /commit
   ```

**Workflow**: `/prime` → `/planning` → `/execute` → `/code-review` → `/system-review` (optional) → `/commit`
   ```