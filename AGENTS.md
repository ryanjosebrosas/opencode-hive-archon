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
| `/prime` | Dispatches 5-6 parallel agents for context | Start of every session |
| `/planning [feature]` | 6-phase deep analysis, structured plan | Before building any feature |
| `/execute [plan]` | Implements plan file task-by-task | After planning, fresh session |
| `/commit` | Creates conventional-format git commit | After implementation passes review |
| `/code-review` | 4 parallel review agents | After implementation |
| `/code-review-fix` | Applies fixes from code review | After code review surfaces issues |
| `/end-to-end-feature` | Full autonomous pipeline | Trusted, well-defined features |
| `/rca [issue]` | Root cause analysis | Investigating bugs |
| `/implement-fix` | Implements fix from RCA | After root cause analysis |
| `/create-prd` | Generates PRD | Defining new product/feature |
| `/create-pr` | Creates GitHub Pull Request | After pushing a branch |
| `/execution-report` | Post-implementation report | Reviewing what was built |
| `/init-c` | Customizes AGENTS.md for new project | New project setup |
| `/agents` | Creates new subagent definition | Extending the system |
| `/system-review` | Audits system state | Periodic health checks |

---

## Available Subagents

### Research Agents
| Agent | Purpose |
|-------|---------|
| `research-codebase` | Parallel codebase exploration, file discovery, pattern extraction |
| `research-external` | Documentation search, best practices, version compatibility |

### Code Review Agents (run in parallel)
| Agent | What It Catches |
|-------|----------------|
| `code-review-type-safety` | Missing type hints, unsafe casts |
| `code-review-security` | SQL injection, XSS, exposed secrets |
| `code-review-architecture` | Pattern violations, layer breaches |
| `code-review-performance` | N+1 queries, memory leaks |

### Utility Agents
| Agent | Purpose |
|-------|---------|
| `plan-validator` | Validates plan structure before execution |
| `test-generator` | Suggests test cases for changed code |

### Swarm Workers (SwarmTools)
| Agent | Purpose |
|-------|---------|
| `swarm-worker-backend` | Backend services, APIs, business logic with file reservations |
| `swarm-worker-frontend` | React components, UI, styling, state management |
| `swarm-worker-database` | Schema design, migrations, queries, data modeling |
| `swarm-worker-testing` | Unit tests, integration tests, fixtures, mocks |

### Specialist Agents
| Agent | Purpose |
|-------|---------|
| `specialist-devops` | CI/CD, Docker, IaC, deployments |
| `specialist-data` | Database design, migrations, queries |
| `specialist-copywriter` | UI copy, error messages |
| `specialist-tech-writer` | API docs, READMEs, changelogs |

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
│
├── sections/                    # Core methodology (loaded via opencode.json instructions)
│
├── reference/                   # Deep guides (on-demand)
│   ├── system-foundations.md
│   ├── piv-loop-practice.md
│   └── ...8 more guides
│
├── templates/                   # Reusable templates (8 files)
│   ├── STRUCTURED-PLAN-TEMPLATE.md
│   ├── PRD-TEMPLATE.md
│   └── ...6 more templates
│
├── requests/                    # Feature plans (gitignored)
│   └── execution-reports/
│
├── .opencode/                   # OpenCode configuration
│   ├── commands/                # Slash commands
│   ├── agents/                  # Custom subagents
│   └── skills/                  # Agent skills
│
└── .claude/                     # Claude Code compatibility (symlinks to .opencode)
```

---

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