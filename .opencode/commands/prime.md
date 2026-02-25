---
description: Prime agent with project context
agent: build
---

# Prime: Load Project Context

Quick context load — no agents, no bloat. Direct commands and file reads.

## Step 1: Detect Context Mode

Check for code directories using a **single** Glob call with brace expansion:

```
{src,app,frontend,backend,lib,api,server,client}/**
```

**If ANY files found** → **Codebase Mode** (go to Step 2B)
**If no files found** → **System Mode** (go to Step 2A)

---

## Step 2A: System Mode — Load Context

Run these commands directly:

```bash
git log -10 --oneline
git status
```

Read these files if they exist:
- `memory.md`
- `opencode.json`

---

## Step 2B: Codebase Mode — Load Context

Run these commands directly:

```bash
git log -10 --oneline
git status
git ls-files
```

Read these files if they exist:
- `memory.md`
- `README.md`
- `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` (package manifest)
- `src/index.*` / `main.*` / `app.*` (entry point)

---

## Step 3: Assemble Report

**System Mode** — Present:

## Current State
- **Branch**: {current branch name}
- **Status**: {clean/dirty, summary of changes if any}
- **Recent Work**: {list each of the last 10 commits as "- `hash` message"}

## Memory Context
{If memory.md exists:
- **Last Session**: {most recent date from Session Notes}
- **Key Decisions**: {bullet list from Key Decisions section}
- **Active Patterns**: {from Architecture Patterns section}
- **Gotchas**: {from Gotchas section}
- **Memory Health**: {if last session date is >7 days ago, warn "Stale — last updated {date}". Otherwise "Fresh"}
Otherwise: "No memory.md found"}

---

**Codebase Mode** — Present:

## Current State
- **Branch**: {current branch name}
- **Status**: {clean/dirty, summary of changes if any}
- **Recent Work**: {list each of the last 10 commits as "- `hash` message"}

## Project Overview
{If README.md exists:
- **Purpose**: {what this project does — 1 sentence}
- **Key Capabilities**: {main features — comma-separated list}
Otherwise: "No README.md found"}

## Tech Stack
{From package manifest:
- **Language**: {language and version}
- **Framework**: {framework and version}
- **Key Dependencies**: {top 5 with versions}
Otherwise: "No package manifest found"}

## Memory Context
{If memory.md exists:
- **Last Session**: {most recent date from Session Notes}
- **Key Decisions**: {bullet list from Key Decisions section}
- **Active Patterns**: {from Architecture Patterns section}
- **Gotchas**: {from Gotchas section}
- **Memory Health**: {if last session date is >7 days ago, warn "Stale — last updated {date}". Otherwise "Fresh"}
Otherwise: "No memory.md found"}
