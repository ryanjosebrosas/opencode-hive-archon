# SwarmTools Integration Guide

> Comprehensive guide for integrating SwarmTools multi-agent coordination with PIV Loop and Archon MCP.

---

## Architecture Overview

### Three-Layer System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYBRID SYSTEM ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   LAYER 1: PLANNING (PIV Loop)                                              │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  /planning → /execute → /code-review → /commit                      │   │
│   │  - Creates structured plans in requests/*.md                       │   │
│   │  - Uses 6-phase planning methodology                                │   │
│   │  - memory.md for cross-session learning                            │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│   LAYER 2: TASK TRACKING (Archon MCP)                                       │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  Archon MCP                                                         │   │
│   │  - Project/task management (manage_task)                           │   │
│   │  - RAG search over docs/code (rag_search_*)                        │   │
│   │  - Version tracking                                                │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│   LAYER 3: EXECUTION (SwarmTools)                                           │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  SwarmTools Plugin                                                  │   │
│   │  - /swarm command for parallel decomposition                       │   │
│   │  - hive_* tools for git-backed work tracking                       │   │
│   │  - swarmmail_* for file reservations + messaging                   │   │
│   │  - semantic-memory_* for automatic learning                        │   │
│   │  - skills_* for knowledge injection                                │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### System Boundaries

| System | Owns | Shares |
|--------|------|--------|
| **PIV Loop** | Plans, methodology, memory.md | Tasks → Archon, Complex tasks → Swarm |
| **Archon MCP** | Task tracking, RAG search | Tasks from PIV, Context for Swarm |
| **SwarmTools** | Parallel execution, file reservations, learning | Execution results → PIV, Patterns → memory.md |

---

## Installation Deep Dive

### Prerequisites

- Node.js 18+ or Bun
- OpenCode CLI ([opencode.ai](https://opencode.ai))
- Git repository

### Step-by-Step Installation

#### 1. Install Plugin

```bash
npm install -g opencode-swarm-plugin@latest
```

#### 2. Run Setup

```bash
swarm setup
```

This configures:
- OpenCode plugin
- Hive initialization at `.hive/`
- libSQL storage (embedded SQLite)

#### 3. Optional Dependencies

**CASS (Cross-Agent Session Search):**
```bash
git clone https://github.com/Dicklesworthstone/coding_agent_session_search
cd coding_agent_session_search
pip install -e .
cass index  # Build index
```

**UBS (Ultimate Bug Scanner):**
```bash
git clone https://github.com/Dicklesworthstone/ultimate_bug_scanner
cd ultimate_bug_scanner
pip install -e .
```

**Ollama (Semantic Memory):**
```bash
brew install ollama
ollama serve &
ollama pull mxbai-embed-large
```

#### 4. Configure MCP Server

Add to `opencode.json`:
```json
{
  "mcpServers": {
    "swarm": {
      "type": "stdio",
      "command": "swarm",
      "args": ["mcp-server"],
      "env": {
        "HIVE_PATH": ".hive/",
        "OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

**Note:** OpenCode must be restarted after config change.

#### 5. Verify Health

```bash
swarm doctor
```

Expected output:
```
✓ Bun/Node.js detected
✓ Hive initialized
✓ MCP server configured
✓ CASS available (optional)
✓ UBS available (optional)
```

---

## Integration Points

### PIV Loop → Swarm Handoff

When `/planning` creates a structured plan, add execution method metadata:

```markdown
## Execution Method

- **Recommended**: /swarm-execute
- **Reason**: 20 tasks across 4 systems, parallel work on auth + database + API
- **Workers needed**: backend, database, testing
```

**Decision Tree:**
```
Plan has <15 tasks? → /execute (normal)
Plan has 15+ tasks? → /swarm-execute
Plan needs parallel work? → /swarm-execute
Plan touches same files? → /swarm-execute (file reservations prevent conflicts)
```

### Archon Tasks ↔ Hive Epics

Map Archon tasks to Hive epics for dual tracking:

```typescript
// Create Archon task for project management
manage_task("create", {
  project_id: "{project}",
  title: "{feature}",
  description: "Tracked via Swarm hive"
})

// Create Hive epic for execution
hive_create_epic({
  epic_title: "{feature}",
  subtasks: [...]
})

// Link them in memory.md
```

### Learning Integration

Combine three learning systems:

| System | Purpose | Storage |
|--------|---------|---------|
| **memory.md** | Cross-session decisions | Git-tracked file |
| **Archon RAG** | Curated documentation | Vector database |
| **Swarm semantic-memory** | Task outcomes, patterns | libSQL embedded |

**Flow:**
```
1. After swarm_complete, Swarm stores outcome in semantic-memory
2. Periodically review and promote patterns to memory.md
3. Archon RAG provides context during planning
```

---

## Worker Agents

### Four Specialized Workers

Created in `.opencode/agents/`:

1. **swarm-worker-backend.md** — Backend services, APIs, business logic
2. **swarm-worker-frontend.md** — React components, UI, styling
3. **swarm-worker-database.md** — Schema design, migrations, queries
4. **swarm-worker-testing.md** — Unit tests, integration tests, fixtures

### File Reservation Protocol

**All workers MUST follow this protocol:**

```typescript
// 1. BEFORE any edits
swarmmail_reserve({
  paths: ["src/auth/**"],
  reason: "bd-123.2: Auth implementation",
  exclusive: true,
  ttl_seconds: 3600
})

// 2. Do work...

// 3. Report progress (creates checkpoint)
swarm_progress({
  project_key: "{project}",
  agent_name: "WorkerA",
  cell_id: "bd-123.2",
  progress_percent: 50,
  message: "Service layer complete"
})

// 4. Complete (auto-releases reservations)
swarm_complete({
  project_key: "{project}",
  agent_name: "WorkerA",
  cell_id: "bd-123.2",
  summary: "OAuth flow implemented",
  files_touched: ["src/auth.ts"]
})
```

### Progress Reporting

Workers report at **25%, 50%, 75%** completion:

- Creates automatic checkpoints
- Survives context compaction
- Enables recovery via `swarm_recover()`

---

## Troubleshooting

### Common Issues

#### 1. Cold Start (No CASS Patterns)

**Problem:** No historical patterns for decomposition initially.

**Solution:** Seed semantic memory manually:
```typescript
semantic-memory_store({
  information: "Auth features work best with feature-based decomposition: schema → service → routes → tests",
  tags: "auth,decomposition,pattern"
})
```

#### 2. File Reservation Conflicts

**Problem:** Multiple agents try to edit same files.

**Solution:** Check reservations before work:
```typescript
swarmmail_inbox({agent_name: "my_agent"})
```

Wait for lock holder to complete or release.

#### 3. TTL Locks Expire

**Problem:** File reservations expire after 1 hour (default TTL).

**Solution:** For long-running tasks, extend TTL:
```typescript
swarmmail_reserve({
  paths: ["src/auth/**"],
  ttl_seconds: 7200  // 2 hours
})
```

#### 4. Learning Isolation

**Problem:** Learnings are local, not shared across team.

**Solution:** Commit `.hive/issues.jsonl` to git:
```bash
git add .hive/issues.jsonl
git commit -m "hive: work items and learnings"
```

#### 5. MCP Server Not Responding

**Problem:** SwarmTools MCP server unavailable.

**Solution:**
1. Check `opencode.json` has mcpServers config
2. Verify installation: `swarm doctor`
3. Restart OpenCode
4. Check Node.js/npm installed

#### 6. Context Compaction Mid-Swarm

**Problem:** Context compacts, losing progress.

**Solution:** Automatic checkpoints at 25%, 50%, 75% enable recovery:
```typescript
swarm_recover({
  project_key: "{project}",
  epic_id: "bd-123"
})
```

Returns last checkpoint with files modified, strategy, progress.

### Debugging File Conflicts

**Check current reservations:**
```typescript
const reservations = await swarmmail_inbox({agent_name: "coordinator"})
console.log(reservations)
```

**Force release (use carefully):**
```typescript
swarmmail_release({
  agent_name: "problematic_agent",
  paths: ["src/auth/**"]
})
```

### Recovery from Failed Swarms

**Step 1:** Check epic status:
```typescript
hive_query({
  epic_id: "bd-123",
  status: "in_progress"
})
```

**Step 2:** Recover from checkpoint:
```typescript
swarm_recover({
  project_key: "{project}",
  epic_id: "bd-123"
})
```

**Step 3:** Reassign incomplete subtasks:
```typescript
hive_update({
  cell_id: "bd-123.2",
  status: "open"
})
```

---

## Best Practices

### 1. When to Use Swarm

**Use /swarm-execute when:**
- 15+ tasks across multiple systems
- Parallel execution needed
- File conflict risk
- Long-running work (survives compaction)
- Need automatic learning

**Use /execute when:**
- <15 tasks
- Single system
- Linear implementation
- Quick feature

### 2. Worker Agent Design

**Keep agents specialized:**
- Backend worker: APIs, services, business logic
- Frontend worker: Components, UI, state
- Database worker: Schema, migrations, queries
- Testing worker: Tests, fixtures, coverage

**Don't:** Create general-purpose "do everything" workers.

### 3. File Reservations

**Always:**
- Reserve before editing
- Use specific paths: `src/auth/**/*.ts`
- Set reasonable TTL (default 1 hour)
- Include reason with cell_id

**Never:**
- Edit without reservation
- Hold reservations while waiting
- Forget to call `swarm_complete()`

### 4. Progress Reporting

**Always:**
- Report at 25%, 50%, 75%
- Include files_touched
- Include clear status message

**Never:**
- Skip reporting (misses checkpoints)
- Report 100% without calling `swarm_complete()`

### 5. Learning

**Always:**
- Store outcomes in semantic-memory
- Review patterns periodically
- Promote successful patterns to memory.md

**Never:**
- Ignore failed patterns
- Store duplicates
- Forget to tag for retrieval

---

## Architecture Decisions

### Why Side-by-Side?

**Decision:** Keep PIV Loop, add SwarmTools alongside.

**Alternatives considered:**
1. Replace PIV with Swarm — rejected: loses methodology benefits
2. Full integration (PIV commands use Swarm internally) — rejected: adds complexity
3. Side-by-side — chosen: best of both worlds

**Rationale:**
- PIV Loop provides planning discipline
- SwarmTools provides execution coordination
- Each system does what it's best at

### Why 4 Workers Initially?

**Decision:** Start with backend, frontend, database, testing.

**Alternatives considered:**
1. 10 specialized workers — rejected: YAGNI, can add more as needed
2. 2 general workers — rejected: loses specialization benefits
3. 4 focused workers — chosen: covers common tech stack

**Rationale:**
- Covers full-stack development
- Easy to add more (DevOps, security, docs)
- Matches common team structure

### Why Git-Backed Hive?

**Decision:** Store `.hive/issues.jsonl` in git.

**Alternatives considered:**
1. External database — rejected: adds infrastructure
2. Local-only files — rejected: no team sharing
3. Git-tracked JSONL — chosen: simple, versioned, shareable

**Rationale:**
- Survives context death
- Shares learnings across team
- No external infrastructure needed
- Version history for audit

---

## Metrics & Monitoring

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Parallel workers | 4-10 concurrent | Count Task agent launches |
| File conflicts | 0 | Check `swarmmail_reserve()` warnings |
| Context compaction survival | 100% recovery | Verify checkpoints restore state |
| Learning accuracy | 80%+ pattern match | Check `semantic-memory_find()` relevance |
| Task completion rate | 95%+ success | Track `swarm_complete()` outcomes |

### Monitoring Commands

```bash
# Check Hive status
hive_query({status: "in_progress"})

# Check reservations
swarmmail_inbox({agent_name: "coordinator"})

# Check semantic memory
semantic-memory_find({query: "patterns", limit: 10})

# Health check
swarm doctor
```

---

## Future Enhancements

### Phase 2 (After Initial Success)

- Add CASS integration for historical patterns
- Set up Ollama for semantic memory embeddings
- Create additional worker agents (DevOps, security, docs)
- Integrate UBS for automatic bug scanning

### Phase 3 (Advanced)

- Cross-project pattern sharing
- Automated pattern promotion to memory.md
- Custom skills for domain expertise
- Dashboard for swarm visualization

---

## Resources

- **SwarmTools Docs:** https://www.swarmtools.ai/docs
- **GitHub:** https://github.com/joelhooks/swarm-tools
- **npm:** https://www.npmjs.com/package/opencode-swarm-plugin
- **Quick Start:** `reference/SWARMTOOLS-QUICKSTART.md`
