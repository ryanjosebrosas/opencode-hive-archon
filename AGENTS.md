# Claude Code Coding System

A comprehensive AI-assisted development methodology combining systematic planning, implementation discipline, and validation strategies. Optimized for [Claude Code](https://Claude.ai).

---

## Core Principles

@sections/01_core_principles.md

---

## PIV Loop Methodology

@sections/02_piv_loop.md

---

## Context Engineering

@sections/03_context_engineering.md

---

## Git Save Points

@sections/04_git_save_points.md

---

## Decision Framework

@sections/05_decision_framework.md

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
| `plan-quality-assessment` | Plan scoring rubric |
| `system-review-integration` | System review deep workflow |
| `model-strategy` | 5-tier cascade, task routing, council models, MCP tools |

---

## Model Strategy — 5-Tier Cost-Optimized Cascade

Maximize free/cheap models. Anthropic is last resort only.

| Tier | Role | Provider/Model | Cost |
|------|------|----------------|------|
| T1 | Implementation | `bailian-coding-plan/qwen3.5-plus` (+ coder-next, coder-plus) | FREE |
| T2 | First Validation | `zai-coding-plan/glm-5` | FREE |
| T3 | Second Validation | `ollama-cloud/deepseek-v3.2` | FREE |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) |
| T5 | Final Review | `anthropic/claude-sonnet-4-6` | PAID (expensive) |

**Orchestrator**: Claude Opus handles ONLY exploration, planning, orchestration, strategy.
**Fallback**: If `bailian-coding-plan` 404s, use `zai-coding-plan/glm-4.7`.
**Council**: `/council` dispatches to 13 real models across 4 providers for multi-model debates.
**Full details**: Read `reference/model-strategy.md` for task routing, council models, MCP tools, and dispatch configuration.

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
| `/code-review` | Generalist review — bugs, security, quality | Manual code review |
| `/system-review` | Plan vs. reality analysis | After complex features |

### `/build` Automation Levels by Spec Depth

| Depth | Plan Size | T1 Impl | T2 Review | T3 Second | T4 Gate | Tests Required |
|-------|-----------|---------|-----------|-----------|---------|----------------|
| light | ~100 lines | Direct or T1 | — | — | — | L1-L2 (syntax, types) |
| standard | ~300 lines | T1 dispatch | T2 review | — | T4 gate | L1-L3 (+ unit tests) |
| heavy | ~700 lines | T1 dispatch | T2 review | T3 opinion | T4 gate | L1-L4 (+ integration) |

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
| `memory-curator` | Suggests what to save to memory.md after features |

---

## Agent Ecosystem

**Context Window Isolation**: Each agent runs in its own context window — efficient for Ollama/Model Studio.

**When to use research agents standalone:**
- `@research-codebase` — Quick codebase exploration before planning
- `@research-external` — Documentation lookup for specific libraries
- `@research-ai-patterns` — AI feature planning (RAG, agents, prompts)
- `@memory-curator` — End of session, suggest lessons for memory.md

**Integration**: Research agents available during `/planning` discovery for targeted exploration.

---

## Available Skills

| Skill | Purpose |
|-------|---------|
| `planning-methodology` | Systematic planning with template-driven output and confidence scoring |

---

## Current Implementation Status

**Hybrid Retrieval Conversational Orchestrator** (Validated)
- Foundation complete, 133 passing tests, 13/13 manual validation scenarios PASS
- Pending: Runtime rollout to production environment

### Workflow Pattern

1. **Vision** (`/mvp`) → Defines `mvp.md` (what to build, who for, success signals)
2. **Requirements** (`/prd`) → Produces `PRD.md` (detailed product requirements, user stories, success criteria)
3. **Decompose** (`/decompose`) → Creates `specs/BUILD_ORDER.md` (dependency-sorted spec list from PRD)
4. **Build** (`/build next`) → Plan + approve + implement + validate + commit (one spec per loop)
5. **Sync** (`/sync`) → Checkpoint: validate state between sessions or before heavy specs
6. **Ship** (`/ship`) → Full validation pyramid + T5 review + PR when all specs done

---

## Quick Start

1. **Start Claude Code** and prime the system:
   ```
   Claude
   > /prime
   ```

2. **Define your MVP** (once per project):
   ```
   > /mvp
   ```

3. **Write detailed requirements** (once per project):
   ```
   > /prd
   ```

4. **Decompose into specs** (once, re-runnable):
   ```
   > /decompose
   ```

5. **Build specs** (the main loop — repeat until done):
   ```
   > /build next
   ```

6. **Ship when complete**:
   ```
   > /ship
   ```

**Full pipeline**: `/prime` → `/mvp` → `/prd` → `/decompose` → `/build next` (repeat) → `/ship`
