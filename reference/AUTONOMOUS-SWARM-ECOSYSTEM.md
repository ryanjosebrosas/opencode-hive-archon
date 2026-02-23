# Autonomous Swarm Ecosystem Documentation

> **Maximum Autonomy**: Self-learning, self-reviewing development engine with CASS + UBS + SwarmTools

**Version**: 1.0  
**Last Updated**: 2026-02-23  
**Status**: Documentation Complete, Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Component Deep Dives](#component-deep-dives)
   - [CASS: Cross-Agent Session Search](#cass-cross-agent-session-search)
   - [UBS: Ultimate Bug Scanner](#ubs-ultimate-bug-scanner)
   - [SwarmTools: Multi-Agent Coordination](#swarmtools-multi-agent-coordination)
4. [Integration Architecture](#integration-architecture)
5. [Installation Guide](#installation-guide)
6. [Configuration Reference](#configuration-reference)
7. [Autonomy Features](#autonomy-features)
8. [Workflows & Pipelines](#workflows--pipelines)
9. [Testing Strategy](#testing-strategy)
10. [Troubleshooting](#troubleshooting)
11. [Appendix](#appendix)

---

## Executive Summary

### What This System Does

Transforms your PIV Loop + SwarmTools system into a **self-learning, self-reviewing autonomous development engine** that:

✅ **Learns from ALL your AI sessions** — Queries 11+ AI agents' past conversations before starting work  
✅ **Catches 1000+ bug patterns** — Scans code before completing tasks, blocks critical issues  
✅ **Self-heals** — AI automatically fixes bugs found by UBS before marking tasks complete  
✅ **Prevents regressions** — Git hooks block commits with bugs, CI/CD prevents bad merges  
✅ **Gets smarter over time** — Every completed task enriches historical knowledge base

### Current vs. Target State

**Current Architecture:**
```
PIV Loop → SwarmTools → .hive/
(Planning)  (Execution)  (Tracking)
```

**Target Architecture (Maximum Autonomy):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS SWARM ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PLANNING LAYER (PIV + CASS)                                                │
│  /planning → queries CASS → /swarm with historical context                 │
│                                                                             │
│  EXECUTION LAYER (Swarm + UBS)                                              │
│  Workers implement → UBS scans → AI fixes → Re-scan → Complete             │
│                                                                             │
│  LEARNING LAYER (Hivemind + CASS + Memory)                                  │
│  swarm_complete → stores learnings → cass indexes → memory.md updated      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Benefits

| Benefit | Before | After |
|---------|--------|-------|
| **Historical Knowledge** | Manual search through sessions | CASS queries 11+ agents instantly |
| **Bug Detection** | Post-commit or manual scanning | Pre-commit, pre-push, real-time |
| **AI Self-Review** | Hope AI gets it right | Mandatory UBS scan before complete |
| **Learning** | Scattered session files | Centralized, searchable knowledge |
| **Quality Gates** | Manual code review | Automated blocking at multiple stages |

---

## Architecture Overview

### Three-Layer System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS SWARM ECOSYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 1: PLANNING (PIV Loop + CASS)                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  /planning → creates structured plan                                  │  │
│  │  /swarm → queries CASS for historical patterns                        │  │
│  │  CASS indexes: Claude, Codex, Cursor, Gemini, 7+ more agents         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                          │                                                   │
│                          ▼                                                   │
│  LAYER 2: EXECUTION (SwarmTools + UBS)                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Workers implement with file reservations                             │  │
│  │  UBS scans before swarm_complete                                      │  │
│  │  AI fixes bugs → Re-scan → Complete                                   │  │
│  │  File watchers scan on save                                           │  │
│  │  Git hooks block commits with bugs                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                          │                                                   │
│                          ▼                                                   │
│  LAYER 3: LEARNING (Hivemind + CASS + Memory)                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  swarm_complete → stores learnings in semantic memory                │  │
│  │  cass index → indexes new sessions hourly                            │  │
│  │  memory.md ← promoted patterns from successful swarms                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Interactions

```
User Request: "Add OAuth authentication"
         │
         ▼
┌─────────────────────────────────────┐
│ 1. PLANNING PHASE                   │
│    /planning creates plan           │
│    CASS queried for past patterns   │
│    → Returns: 3 similar sessions    │
│    → Recommends: JWT + refresh      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 2. DECOMPOSITION                    │
│    /swarm decomposes task           │
│    Based on CASS findings           │
│    → Creates: schema, service,      │
│       routes, tests (proven pattern)│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 3. EXECUTION                        │
│    Workers implement in parallel    │
│    File reservations prevent locks  │
│    Progress checkpoints at 25/50/75%│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 4. QUALITY GATE                     │
│    Before complete: UBS scans       │
│    → Finds: 3 critical bugs         │
│    → Worker fixes automatically     │
│    → Re-scan: ✅ 0 issues           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 5. LEARNING                         │
│    swarm_complete stores outcome    │
│    CASS indexes new session         │
│    Patterns promoted if successful  │
│    memory.md updated                │
└─────────────────────────────────────┘
         │
         ▼
    Task Complete
```

---

## Component Deep Dives

### CASS: Cross-Agent Session Search

**Repository**: https://github.com/Dicklesworthstone/coding_agent_session_search

#### What CASS Does

CASS (Coding Agent Session Search) is a **unified knowledge base** for all your AI coding agent conversations. It:

1. **Normalizes** disparate formats from 11+ agents into common schema
2. **Indexes** everything with full-text + optional semantic search
3. **Surfaces** relevant past conversations in milliseconds
4. **Respects privacy** — everything stays local, nothing phones home

#### Supported Agents

| Agent | Storage Format | Location |
|-------|---------------|----------|
| **Claude Code** | JSONL | `~/.claude/projects/` |
| **Codex CLI** | JSONL | `~/.codex/sessions/` |
| **Gemini CLI** | JSON | `~/.gemini/tmp/` |
| **Cursor** | SQLite | Global + workspace storage |
| **OpenCode** | SQLite | `.opencode/` directories |
| **Aider** | Markdown | `~/.aider.chat.history.md` |
| **Cline** | JSON | VS Code global storage |
| **ChatGPT** | JSON | `~/Library/Application Support/` |
| **Pi-Agent** | JSONL | `~/.pi/agent/sessions/` |
| **Factory (Droid)** | JSONL | `~/.factory/sessions/` |
| **Vibe (Mistral)** | JSONL | `~/.vibe/logs/` |

#### Search Capabilities

**Lexical Search** (BM25, sub-60ms):
```bash
cass search "authentication error" --robot --limit 5
```

**Semantic Search** (vector similarity, optional):
```bash
cass search "how to handle user login" --mode semantic --robot
```

**Hybrid Search** (best of both):
```bash
cass search "auth error handling" --mode hybrid --robot
```

#### Architecture

```
┌──────────────────────────────────────────────────────────┐
│  CASS Architecture                                        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Connectors (11+) → Normalizer → Indexer → Search        │
│     │                  │           │          │           │
│     ▼                  ▼           ▼          ▼           │
│  Claude Code      Common      Tantivy    Lexical         │
│  Codex           Schema        (FTS)      Semantic        │
│  Cursor                                    Hybrid         │
│  ...more                                                        │
│                                                           │
│  Storage: ~/.local/share/cass/                            │
│  - messages.jsonl (normalized)                           │
│  - index/ (Tantivy FTS)                                  │
│  - vector_index/ (optional embeddings)                   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

#### Installation

```bash
# Easy mode (auto-installs everything)
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_session_search/main/install.sh" | bash -s -- --easy-mode

# Or via package managers
brew install dicklesworthstone/tap/cass        # macOS/Linux
scoop install dicklesworthstone/cass          # Windows

# Manual install
git clone https://github.com/Dicklesworthstone/coding_agent_session_search
cd coding_agent_session_search
pip install -e .

# Initial index (5-30 min depending on session count)
cass index
```

#### Integration with Swarm

**How Swarm uses CASS:**

```typescript
// In swarm_decompose tool
const prompt = swarm_decompose({
  task: "Add OAuth authentication",
  max_subtasks: 5,
  query_cass: true,      // ← Queries CASS
  cass_limit: 3,         // ← Number of results
  context: "Use JWT with refresh tokens"
})

// CASS returns:
{
  similar_sessions: [
    {
      session_id: "session-42",
      agent: "claude-code",
      date: "2026-02-15",
      summary: "Implemented JWT auth with refresh tokens",
      outcome: "success",
      files_changed: ["src/auth/jwt.ts", "src/middleware/auth.ts"],
      gotchas: ["Refresh tokens need 5min buffer"]
    },
    // ...2 more
  ],
  patterns: [
    "Feature-based decomposition works best for auth",
    "4-5 subtasks optimal",
    "Reserve src/auth/** early"
  ]
}
```

---

### UBS: Ultimate Bug Scanner

**Repository**: https://github.com/Dicklesworthstone/ultimate_bug_scanner

#### What UBS Does

UBS (Ultimate Bug Scanner) is a **static analysis meta-runner** that catches **1000+ bug patterns** across 8 languages. It's designed specifically for AI coding workflows.

#### Supported Languages

| Language | Patterns | Engine |
|----------|----------|--------|
| **JavaScript/TypeScript** | 200+ | AST-grep + tsserver |
| **Python** | 180+ | AST + regex |
| **Go** | 150+ | AST walker |
| **Rust** | 120+ | AST + regex |
| **Java** | 140+ | AST |
| **C/C++** | 160+ | AST-grep |
| **Ruby** | 100+ | Regex + AST |
| **Swift** | 80+ | AST |

#### Bug Categories

**Critical (🔥)** — Would crash in production:
1. Null pointer dereferences
2. Missing await (unhandled promises)
3. XSS vulnerabilities
4. SQL injection
5. Buffer overflows
6. Race conditions
7. Resource leaks

**Warnings (⚠️)** — Should fix:
8. Type coercion issues
9. Unused variables
10. Debug statements
11. TODO markers
12. Code quality issues

#### Performance

```
Small project (5K lines):     0.8 seconds  ⚡
Medium project (50K lines):   3.2 seconds  🚀
Large project (200K lines):  12 seconds    💨
Huge project (1M lines):     58 seconds    🏃
```

#### Installation

```bash
# Easy mode (auto-wires into AI agents)
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash -s -- --easy-mode

# Or via package managers
brew install dicklesworthstone/tap/ubs      # macOS/Linux
scoop install dicklesworthstone/ubs         # Windows

# Verify installation
ubs --version
ubs doctor
```

#### What --easy-mode Does

The `--easy-mode` flag automatically:

1. ✅ Installs UBS globally
2. ✅ Detects AI agents (Claude, Cursor, Codex, etc.)
3. ✅ Wires guardrails into each agent's config
4. ✅ Sets up git hooks (pre-commit, pre-push)
5. ✅ Configures file watchers (scan on save)
6. ✅ Installs dependencies (ast-grep, ripgrep, jq, typos)
7. ✅ Adds documentation to AGENTS.md

#### Integration Modes

**Mode 1: Manual Command**
```bash
ubs .                    # Scan entire project
ubs src/auth/**/*.ts     # Scan specific files
ubs --staged             # Scan git staged changes
```

**Mode 2: Git Hooks**
```bash
# Pre-commit hook (.git/hooks/pre-commit)
#!/bin/bash
changed_files=$(git diff --cached --name-only)
ubs $changed_files --fail-on-warning || exit 1
```

**Mode 3: File Watchers**
```bash
# Claude Code: .claude/hooks/on-file-write.sh
#!/bin/bash
if [[ "$FILE_PATH" =~ \.(js|ts|py|go|rs)$ ]]; then
  ubs "$FILE_PATH" --quiet
fi
```

**Mode 4: Agent Guardrails**
```markdown
# .claude/agents/rules.md
## Quality Standards

Before marking task complete:
1. Run: `ubs <changed-files>`
2. Fix ALL critical issues (🔥)
3. Review warnings (⚠️)
4. Only then mark complete
```

**Mode 5: CI/CD**
```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate
on: [push, pull_request]
jobs:
  bug-scan:
    runs-on: ubuntu-latest
    steps:
      - run: ubs . --fail-on-warning --format=sarif
```

---

### SwarmTools: Multi-Agent Coordination

**Repository**: https://github.com/joelhooks/swarm-tools

#### What SwarmTools Does

SwarmTools enables **parallel multi-agent coordination** with:
- Task decomposition into parallel subtasks
- File reservations (prevent edit conflicts)
- Git-backed work tracking (`.hive/`)
- Automatic learning from outcomes
- Checkpoint/recovery (survives context death)

#### Core Concepts

**The Hive** — Git-backed work items:
```bash
.hive/
└── issues.jsonl  # Event-sourced work items
```

**Cells** — Units of work:
```json
{
  "id": "bd-abc123.1",
  "title": "Implement JWT service",
  "status": "open",
  "priority": 0,
  "dependencies": [],
  "issue_type": "task"
}
```

**Swarm Mail** — Agent coordination:
```typescript
// Reserve files before editing
swarmmail_reserve({
  paths: ["src/auth/**"],
  reason: "bd-123.2: Auth implementation",
  exclusive: true
})

// Send message to coordinator
swarmmail_send({
  to: ["coordinator"],
  subject: "BLOCKED: Need database schema",
  importance: "high"
})

// Complete task (auto-releases reservations)
swarm_complete({
  summary: "OAuth flow implemented",
  files_touched: ["src/auth.ts"]
})
```

#### Workflow

```
User: "/swarm Add OAuth authentication"
  │
  ▼
Coordinator:
1. Query CASS for past patterns
2. Pick decomposition strategy
3. Create epic + subtasks
  │
  ▼
Spawn Workers (parallel):
- Worker A: src/auth/schema.ts
- Worker B: src/auth/service.ts
- Worker C: src/auth/routes.ts
- Worker D: src/auth/test.ts
  │
  ▼
Each Worker:
1. swarmmail_reserve(files)
2. Implement
3. swarm_progress(25/50/75%)
4. UBS scans
5. Fix bugs if found
6. swarm_complete()
  │
  ▼
Coordinator:
- Verify all complete
- hive_sync() + git push
- Store learnings
```

---

## Integration Architecture

### How Components Work Together

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER REQUEST                                                            │
│     "Add OAuth authentication"                                              │
│                                                                             │
│  2. PLANNING                                                                │
│     /planning → creates plan                                                │
│     CASS query → "How did we implement auth before?"                        │
│     Returns: 3 past sessions with outcomes                                  │
│                                                                             │
│  3. DECOMPOSITION                                                           │
│     /swarm → decompose with CASS context                                    │
│     Strategy: Feature-based (proven by CASS)                                │
│     Creates: schema, service, routes, tests                                 │
│                                                                             │
│  4. EXECUTION                                                               │
│     Workers spawn in parallel                                               │
│     File reservations prevent conflicts                                     │
│     Progress checkpoints at 25/50/75%                                       │
│                                                                             │
│  5. QUALITY GATE                                                            │
│     Before swarm_complete: UBS scans                                        │
│     Finds: 3 critical bugs                                                  │
│     Worker fixes → Re-scan → 0 issues                                       │
│                                                                             │
│  6. LEARNING                                                                │
│     swarm_complete stores outcome                                           │
│     CASS indexes new session (hourly cron)                                  │
│     Semantic memory: "JWT + refresh tokens works"                           │
│     memory.md updated with patterns                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CASS       │     │   Swarm      │     │    UBS       │
│              │     │              │     │              │
│  Sessions    │────▶│  Decompose   │────▶│  Pre-scan    │
│  Indexed     │     │  with context│     │              │
│              │     │              │     │              │
│  ◀───────────┤     │              │     │              │
│  New session │     │  Complete    │     │  Post-scan   │
│  indexed     │     │  outcome     │     │  results     │
│              │     │              │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   memory.md  │
                     │              │
                     │  Promoted    │
                     │  patterns    │
                     └──────────────┘
```

---

## Installation Guide

### Prerequisites

| Component | Required | Purpose |
|-----------|----------|---------|
| **Node.js 18+** | ✅ Yes | SwarmTools runtime |
| **Bun** | ⚠️ Recommended | Faster SwarmTools execution |
| **Git** | ✅ Yes | Hive tracking |
| **Python 3.8+** | ✅ Yes | CASS + UBS |
| **pip** | ✅ Yes | Python package install |

### Step 1: Install SwarmTools

```bash
# Already installed ✅
npm install -g opencode-swarm-plugin@latest
swarm setup
swarm doctor
```

### Step 2: Install CASS

```bash
# Easy mode
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_session_search/main/install.sh" | bash -s -- --easy-mode

# Or manual
git clone https://github.com/Dicklesworthstone/coding_agent_session_search
cd coding_agent_session_search
pip install -e .

# Initial index (first time: 5-30 min)
cass index

# Verify
cass search "test" --robot --limit 1
```

### Step 3: Install UBS

```bash
# Easy mode (auto-wires everything)
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash -s -- --easy-mode

# Or manual
brew install dicklesworthstone/tap/ubs  # macOS/Linux

# Verify
ubs --version
ubs .
```

### Step 4: Configure Auto-Indexing

**Linux (systemd):**
```ini
# /etc/systemd/system/cass-watch.service
[Unit]
Description=Auto-index AI coding agent sessions
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cass index --incremental
Restart=always
User=youruser

[Install]
WantedBy=default.target
```

```bash
systemctl enable cass-watch
systemctl start cass-watch
```

**macOS (LaunchAgent):**
```xml
<!-- ~/Library/LaunchAgents/com.cass.index.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.cass.index</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/cass</string>
    <string>index</string>
    <string>--incremental</string>
  </array>
  <key>StartInterval</key>
  <integer>3600</integer>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.cass.index.plist
```

**Cron (all platforms):**
```bash
# Edit crontab
crontab -e

# Add: Index every hour
0 * * * * cass index --incremental
```

---

## Configuration Reference

### CASS Configuration

**Config file**: `~/.config/cass/sources.toml`

```toml
# Local sources
[[sources]]
name = "local"
type = "local"
paths = ["~/.claude/projects", "~/.codex/sessions"]

# Remote sources (multi-machine)
[[sources]]
name = "laptop"
type = "ssh"
host = "user@laptop.local"
paths = ["~/.claude/projects", "~/.codex/sessions"]
sync_schedule = "manual"

# Search configuration
[search]
default_mode = "hybrid"  # lexical, semantic, hybrid
limit = 10
highlight = true

# Semantic search (optional)
[semantic]
enabled = true
model = "MiniLM"  # or "hash" for fallback
```

### UBS Configuration

**Config file**: `~/.config/ubs/config.toml`

```toml
# Default settings
[scan]
fail_on_warning = false  # CI mode: true
format = "text"          # text, json, jsonl, sarif, toon
quiet = false

# Languages to scan
[languages]
javascript = true
typescript = true
python = true
go = true
rust = true
java = true
cpp = true
ruby = true

# Ignore patterns
[ignore]
paths = ["node_modules", "vendor", "dist", "build"]
extensions = [".min.js", ".bundle.js"]

# Auto-fix settings
[auto_fix]
enabled = false  # Experimental
patterns = ["unused_imports", "debugger_statements"]
```

### SwarmTools Configuration

**Config file**: `~/.config/swarm-tools/config.toml`

```toml
# Hive settings
[hive]
path = ".hive/"
auto_sync = true
git_push = true

# Decomposition settings
[decompose]
max_subtasks = 5
query_cass = true        # ← Enable CASS integration
cass_limit = 3
strategy = "auto"        # auto, file-based, feature-based, risk-based

# Quality gates
[quality]
ubs_scan = true          # ← Enable UBS before complete
fail_on_critical = true
fail_on_warning = false

# Checkpoint settings
[checkpoint]
auto_save = true
percentages = [25, 50, 75]
```

---

## Autonomy Features

### 1. Historical Learning (CASS)

**What it does**: Before decomposing a task, queries all past AI sessions for similar implementations.

**Example flow**:
```
User: "Add user authentication"
  │
  ▼
/swarm invoked
  │
  ▼
Coordinator queries CASS: "authentication implementation"
  │
  ▼
CASS returns:
- Session #42: JWT with refresh tokens (success)
- Session #87: OAuth2 with PKCE (success)
- Session #15: Session-based (abandoned)
  │
  ▼
Coordinator picks JWT strategy (proven by CASS)
  │
  ▼
Decomposes: schema → service → routes → tests
```

**Configuration**:
```typescript
swarm_decompose({
  task: "Add authentication",
  query_cass: true,      // Enable
  cass_limit: 3,
  context: "Prefer stateless auth"
})
```

### 2. Self-Review (UBS)

**What it does**: Before `swarm_complete`, automatically scans for bugs. AI fixes findings before task marked complete.

**Example flow**:
```
Worker implements feature
  │
  ▼
Before swarm_complete: UBS scans
  │
  ▼
UBS output:
🔥 CRITICAL: 3 bugs
  - Null pointer at auth.ts:42
  - Missing await at service.ts:18
  - XSS at handler.ts:67
  │
  ▼
Coordinator: "3 critical bugs detected"
  │
  ▼
Worker fixes bugs automatically
  │
  ▼
Re-scan: ✅ 0 issues
  │
  ▼
swarm_complete succeeds
```

**Configuration**:
```typescript
swarm_complete({
  summary: "Auth implemented",
  ubs_scan: true,        // Enable
  fail_on_critical: true,
  auto_fix: true         // AI fixes before complete
})
```

### 3. Quality Gates (Git Hooks)

**What it does**: Blocks commits/pushes with critical bugs.

**Pre-commit hook** (` .git/hooks/pre-commit`):
```bash
#!/bin/bash
changed_files=$(git diff --cached --name-only)
echo "🔬 Scanning changed files..."

if ubs $changed_files --fail-on-warning; then
  echo "✅ Quality check passed"
  exit 0
else
  echo "❌ Critical bugs found. Fix before commit."
  exit 1
fi
```

**Pre-push hook** (` .git/hooks/pre-push`):
```bash
#!/bin/bash
echo "🔬 Full repository scan..."

if ubs . --fail-on-warning --ci; then
  echo "✅ Repository clean"
  exit 0
else
  echo "❌ Bugs found. Run 'ubs .' to see details"
  exit 1
fi
```

### 4. Real-Time Scanning (File Watchers)

**What it does**: Scans files on save, immediate feedback.

**Claude Code** (`.claude/hooks/on-file-write.sh`):
```bash
#!/bin/bash
if [[ "$FILE_PATH" =~ \.(js|ts|py|go|rs|java|c|cpp|rb)$ ]]; then
  ubs "$FILE_PATH" --quiet
  if [ $? -ne 0 ]; then
    echo "⚠️  Bugs detected in $FILE_PATH"
  fi
fi
```

### 5. Agent Guardrails

**What it does**: AI agents mandated to run UBS before completing tasks.

**Claude Code** (`.claude/agents/rules.md`):
```markdown
## Quality Standards

Before marking ANY task complete:

1. Run bug scanner: `ubs .` or `ubs <changed-files>`
2. Fix ALL critical issues (🔥)
3. Review warnings (⚠️) - fix if trivial
4. Only then mark complete

If scanner finds critical issues, task is NOT done.
```

### 6. CI/CD Integration

**What it does**: Blocks PR merges with bugs, uploads SARIF for GitHub code scanning.

**GitHub Actions** (`.github/workflows/quality-gate.yml`):
```yaml
name: Quality Gate

on: [push, pull_request]

jobs:
  bug-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install UBS
        run: |
          curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh" | bash -s -- --non-interactive
      
      - name: Scan for bugs
        run: ubs . --fail-on-warning --format=sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

---

## Workflows & Pipelines

### Workflow 1: Feature Development

```
User: "Add user registration endpoint"
  │
  ▼
/planning user-registration
  │
  ▼
Plan created with CASS context
  │
  ▼
/swarm "Implement user registration"
  │
  ▼
Coordinator:
1. Queries CASS → "user registration implementation"
2. Returns: 2 past sessions with patterns
3. Decomposes: schema → service → endpoint → tests
  │
  ▼
Workers implement in parallel
  │
  ▼
Each worker:
1. Reserve files
2. Implement
3. UBS scans
4. Fix bugs
5. Complete
  │
  ▼
hive_sync() + git push
  │
  ▼
CASS indexes new session (hourly)
  │
  ▼
memory.md updated with patterns
```

### Workflow 2: Bug Fix

```
User: "Fix null pointer in auth service"
  │
  ▼
/swarm "Fix auth null pointer"
  │
  ▼
Coordinator:
1. Queries CASS → "null pointer auth fix"
2. Returns: Similar fixes from past
3. Decomposes: diagnose → fix → test
  │
  ▼
Worker:
1. Diagnose root cause
2. Implement fix
3. UBS scans
4. Verify fix
5. Complete
  │
  ▼
hive_sync()
```

### Workflow 3: Refactoring

```
User: "Refactor auth to use JWT"
  │
  ▼
/swarm "Migrate to JWT"
  │
  ▼
Coordinator:
1. Queries CASS → "JWT migration"
2. Returns: Migration patterns
3. Decomposes: schema update → service → routes → tests
  │
  ▼
Workers:
1. Update schema
2. Migrate service
3. Update routes
4. Update tests
  │
  ▼
UBS scans each change
  │
  ▼
Complete
```

---

## Testing Strategy

### Test Scenarios

**1. CASS Integration**:
```bash
# Test 1: Basic search
cass search "authentication" --robot --limit 5
# Expected: Returns 5 sessions

# Test 2: Swarm with CASS
/swarm "Add user login"
# Expected: Coordinator mentions past similar sessions

# Test 3: Cross-agent search
cass search "API error handling" --agents claude,codex,cursor
# Expected: Returns sessions from specified agents
```

**2. UBS Quality Gates**:
```bash
# Test 1: Basic scan
ubs . --format=json
# Expected: JSON output with findings

# Test 2: Git hook
echo "const x = undefined; x.foo();" > test.ts
git add test.ts
git commit -m "test"
# Expected: Commit blocked

# Test 3: Agent guardrail
# Ask Claude: "Implement feature"
# Expected: Claude runs ubs before complete
```

**3. Full Workflow**:
```bash
/swarm "Add /api/health endpoint"

# Expected sequence:
# 1. CASS queried for past API implementations
# 2. Decomposition based on patterns
# 3. Workers implement
# 4. UBS scans before complete
# 5. Bugs fixed automatically
# 6. Learnings stored
# 7. CASS indexes new session
```

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **CASS Index Coverage** | 100% of sessions | `cass stats` |
| **UBS False Positives** | < 5% | Manual review |
| **Bugs Caught Pre-Commit** | 95%+ | Git hook logs |
| **Swarm Success Rate** | 90%+ (first try) | Hive analytics |
| **Auto-Fix Rate** | 80%+ | Session logs |
| **Index Freshness** | < 1 hour | CASS timestamp |

---

## Troubleshooting

### CASS Issues

**Problem**: "No sessions found"
```bash
# Check if agents are detected
cass sources list

# Force re-index
cass index --full

# Check storage location
cass config show
```

**Problem**: "Slow indexing"
```bash
# Incremental index (faster)
cass index --incremental

# Check what's being indexed
cass index --dry-run

# Exclude large directories
cass index --exclude "node_modules,vendor"
```

### UBS Issues

**Problem**: "False positives"
```bash
# Add to .ubs-ignore
echo "path/to/file.ts" >> .ubs-ignore

# Or inline suppression
eval("safe code") # ubs:ignore
```

**Problem**: "Git hook blocking workflow"
```bash
# Emergency bypass
git commit --no-verify

# Or disable temporarily
git hooks/pre-commit.bak
```

### SwarmTools Issues

**Problem**: "File conflicts"
```bash
# Check reservations
swarmmail_inbox

# Force release (careful!)
swarmmail_release --force
```

**Problem**: "Workers not completing"
```bash
# Check status
hive_query --status in_progress

# Check for blockers
swarmmail_inbox --agent coordinator
```

---

## Appendix

### A. Command Reference

**CASS**:
```bash
cass search "<query>" --robot --limit 5
cass index [--full|--incremental]
cass sources list
cass sources sync
cass health --json
```

**UBS**:
```bash
ubs . [--format=text|json|jsonl|sarif|toon]
ubs --staged
ubs --diff
ubs --fail-on-warning
ubs doctor
```

**SwarmTools**:
```bash
/swarm "<task>"
hive_ready()
hive_create({...})
hive_sync()
swarmmail_reserve({...})
swarm_complete({...})
semantic-memory_store({...})
```

### B. File Locations

| Component | Config | Data | Logs |
|-----------|--------|------|------|
| **CASS** | `~/.config/cass/` | `~/.local/share/cass/` | `~/.cache/cass/` |
| **UBS** | `~/.config/ubs/` | `~/.local/share/ubs/` | `~/.cache/ubs/` |
| **Swarm** | `~/.config/swarm-tools/` | `~/.local/share/swarm-tools/` | `~/.cache/swarm-tools/` |
| **Hive** | N/A | `.hive/` (project) | N/A |

### C. Environment Variables

```bash
# CASS
export CASS_DATA_DIR=~/.local/share/cass
export CASS_SEMANTIC_EMBEDDER=MiniLM  # or "hash"

# UBS
export UBS_CONFIG=~/.config/ubs/config.toml
export UBS_NO_AUTO_UPDATE=1

# SwarmTools
export SWARM_HIVE_PATH=.hive/
export SWARM_UBS_ENABLED=1
export SWARM_CASS_ENABLED=1
```

### D. Resources

- **SwarmTools**: https://swarmtools.ai/docs
- **CASS**: https://github.com/Dicklesworthstone/coding_agent_session_search
- **UBS**: https://github.com/Dicklesworthstone/ultimate_bug_scanner
- **This System**: `reference/` directory

---

## Quick Start Checklist

- [ ] **Step 1**: Verify SwarmTools installed (`swarm doctor`)
- [ ] **Step 2**: Install CASS (`curl ... | bash -s -- --easy-mode`)
- [ ] **Step 3**: Install UBS (`curl ... | bash -s -- --easy-mode`)
- [ ] **Step 4**: Run initial CASS index (`cass index`)
- [ ] **Step 5**: Test UBS scan (`ubs .`)
- [ ] **Step 6**: Configure auto-indexing (cron/systemd)
- [ ] **Step 7**: Set up git hooks (`ubs` installer does this)
- [ ] **Step 8**: Add agent guardrails (`.claude/agents/rules.md`)
- [ ] **Step 9**: Test first swarm with CASS + UBS (`/swarm "test"`)
- [ ] **Step 10**: Verify learnings stored (`semantic-memory_list`)

---

**Documentation Version**: 1.0  
**Ready for Implementation**: Yes  
**Estimated Setup Time**: 2-3 hours (one-time)  
**Maintenance**: Minimal (auto-indexing handles most)
