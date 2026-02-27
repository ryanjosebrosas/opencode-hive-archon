> **THIS MODEL (Claude Opus) IS THE ORCHESTRATOR.**
> It handles ONLY: planning, architecture, orchestration, exploration, strategy.
> ALL implementation (file edits, code writing, refactoring) MUST be dispatched to T1-T5 models.
> Opus writing code directly is a VIOLATION. No exceptions.
> If dispatch tools are unavailable, write a plan to `requests/` and STOP.

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

| Tier | Role | Models | Cost |
|------|------|--------|------|
| T1 | Implementation | `bailian`: qwen3-coder-next, qwen3-coder-plus, qwen3.5-plus, qwen3-max, kimi-k2.5, minimax-m2.5 | FREE |
| T2 | First Validation | `zai`: glm-5, glm-4.5, glm-4.7, glm-4.7-flash, glm-4.7-flashx | FREE |
| T3 | Second Validation | `ollama`: deepseek-v3.2, kimi-k2:1t, cogito:671b, devstral-2:123b, gemini-3-pro, mistral-large:675b, qwen3-coder:480b | FREE |
| T4 | Code Review gate | `openai/gpt-5.3-codex` | PAID (cheap) |
| T5 | Final Review | `anthropic/claude-sonnet-4-6` | PAID (expensive) |

**Orchestrator**: Claude Opus handles ONLY exploration, planning, orchestration, strategy.
**Fallback**: If `bailian-coding-plan-test` 404s, use `zai-coding-plan/glm-4.7`.
**Council**: `/council` dispatches to 18 preferred models across 4 providers (51 free models available) for multi-model debates.
**Full details**: Read `reference/model-strategy.md` for task routing, council models, MCP tools, and dispatch configuration.

**Dispatch rule**: Always `/prime` before first dispatch in a session — ensures models have fresh project context.

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
/mvp → /prd → /pillars → /decompose → /build next (repeat) → /ship
```

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/mvp` | Define or refine product vision → `mvp.md` | Start of a new project or major pivot |
| `/prd` | Full product requirements document → `PRD.md` | After `/mvp`, detailed what + why + user stories |
| `/pillars` | Analyze PRD → infrastructure pillar definitions → `specs/PILLARS.md` | After `/prd`, define infrastructure layers and gate criteria |
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

| Depth | Plan Size | T1 (FREE) | Free Gauntlet | T4 (PAID) | T5 (PAID) | Tests |
|-------|-----------|-----------|---------------|-----------|-----------|-------|
| light | ~100 lines | T1 text | 3-model validation | — | — | L1-L2 |
| standard | ~300 lines | T1 text | 5-model gauntlet | Consensus-gated | — | L1-L3 |
| heavy | ~700 lines | T1 text | 5-model gauntlet | Always | Always | L1-L4 |

Gauntlet = `free-review-gauntlet` batch pattern (5 free models in parallel). If 4/5 say clean, T4 is SKIPPED.

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
3. **Pillars** (`/pillars`) → Produces `specs/PILLARS.md` (infrastructure layers with gate criteria)
4. **Decompose** (`/decompose`) → Creates `specs/BUILD_ORDER.md` (pillar-grouped spec list)
5. **Build** (`/build next`) → Plan + approve + implement + validate + commit (one spec per loop)
6. **Sync** (`/sync`) → Checkpoint: validate state between sessions or before heavy specs
7. **Ship** (`/ship`) → Full validation pyramid + T5 review + PR when all specs done

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

4. **Define infrastructure pillars** (once, re-runnable):
   ```
   > /pillars
   ```

5. **Decompose into specs** (once, re-runnable):
   ```
   > /decompose
   ```

6. **Build specs** (the main loop — repeat until done):
   ```
   > /build next
   ```

7. **Ship when complete**:
   ```
   > /ship
   ```

**Full pipeline**: `/prime` → `/mvp` → `/prd` → `/pillars` → `/decompose` → `/build next` (repeat) → `/ship`
