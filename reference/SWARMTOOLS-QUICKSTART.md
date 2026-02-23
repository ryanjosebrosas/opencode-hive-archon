# SwarmTools Quick Start

> Get up and running with SwarmTools multi-agent coordination in 15 minutes.

---

## Installation (5 min)

### Step 1: Install Plugin

```bash
# Using npm
npm install -g opencode-swarm-plugin@latest

# Or using Bun
bun add -g opencode-swarm-plugin@latest
```

### Step 2: Run Setup

```bash
swarm setup
```

Expected output:
```
✓ Bun/Node.js detected
✓ OpenCode plugin configured
✓ Hive initialized at .hive/
✓ All systems ready
```

### Step 3: Verify Health

```bash
swarm doctor
```

Check output for:
- ✓ Bun/Node.js version
- ✓ Hive initialized
- ✓ MCP server configured
- ✓ Dependencies available

---

## First Swarm (10 min)

### Step 1: Start OpenCode

```bash
opencode
```

### Step 2: Try Your First Swarm

```
/swarm "Create a simple TypeScript utility function"
```

Watch the coordinator:
1. Decompose task into subtasks
2. Create epic in `.hive/issues.jsonl`
3. Spawn worker agents
4. Track progress in real-time

### Step 3: Verify Results

Check that work was created:
```bash
# Check .hive/ directory
dir .hive\

# View work items
type .hive\issues.jsonl
```

---

## Common Commands

### Hive (Work Item Tracking)

```typescript
// Get next unblocked task
hive_ready()

// Create epic with subtasks
hive_create_epic({
  epic_title: "My Feature",
  subtasks: [...]
})

// Query work items
hive_query({status: "open"})

// Sync to git (MANDATORY at end)
hive_sync()
```

### Swarm Mail (Coordination)

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
  subject: "Progress update",
  body: "50% complete"
})

// Check inbox for messages
swarmmail_inbox({agent_name: "my_agent"})

// Release reservations (auto-done by swarm_complete)
swarmmail_release()
```

### Swarm (Orchestration)

```typescript
// Report progress (creates checkpoint)
swarm_progress({
  project_key: "/path/to/project",
  agent_name: "WorkerA",
  cell_id: "bd-123.2",
  progress_percent: 50,
  message: "Schema defined"
})

// Complete subtask (releases reservations)
swarm_complete({
  project_key: "/path/to/project",
  agent_name: "WorkerA",
  cell_id: "bd-123.2",
  summary: "OAuth flow implemented",
  files_touched: ["src/auth.ts"]
})

// Decompose task into subtasks
swarm_decompose({
  task: "Add authentication",
  max_subtasks: 5,
  query_cass: true
})
```

### Skills (Knowledge)

```typescript
// List available skills
skills_list()

// Load skill for task
skills_use({
  name: "testing-patterns",
  context: "Writing unit tests for AuthService"
})
```

### Semantic Memory (Learning)

```typescript
// Store learning
semantic-memory_store({
  information: "OAuth refresh tokens need 5min buffer",
  tags: "auth,tokens"
})

// Find similar patterns
semantic-memory_find({
  query: "token refresh",
  limit: 3
})
```

---

## Troubleshooting

### Issue: "swarm: command not found"

**Solution:** Verify installation:
```bash
npm list -g opencode-swarm-plugin
```

Reinstall if needed:
```bash
npm install -g opencode-swarm-plugin@latest
```

### Issue: "MCP server not responding"

**Solution:** Check `opencode.json` has mcpServers config:
```json
{
  "mcpServers": {
    "swarm": {
      "type": "stdio",
      "command": "swarm",
      "args": ["mcp-server"]
    }
  }
}
```

Restart OpenCode after config change.

### Issue: File conflicts between workers

**Solution:** Workers MUST call `swarmmail_reserve()` before editing:
```typescript
swarmmail_reserve({
  paths: ["src/auth/**"],
  exclusive: true
})
```

Check inbox for lock holders:
```typescript
swarmmail_inbox({agent_name: "my_agent"})
```

### Issue: Lost progress after context compaction

**Solution:** Use checkpoints. Progress at 25%, 50%, 75% auto-creates checkpoints.

Recover:
```typescript
swarm_recover({
  project_key: "/path/to/project",
  epic_id: "bd-123"
})
```

### Issue: No learnings from past tasks

**Solution:** Install CASS for historical context:
```bash
git clone https://github.com/Dicklesworthstone/coding_agent_session_search
cd coding_agent_session_search
pip install -e .
cass index
```

### Issue: `.hive/` not git-tracked

**Solution:** Check `.gitignore` doesn't exclude it. Should have:
```
# NOT this - .hive/ should be tracked
.hive/
```

Remove any `.hive/` entry from `.gitignore`.

---

## Next Steps

- Read `reference/swarmtools-integration.md` for deep integration guide
- Create custom worker agents for your tech stack
- Set up CASS for historical pattern learning
- Install Ollama for semantic memory embeddings

---

## Resources

- **Full Documentation:** https://www.swarmtools.ai/docs
- **GitHub:** https://github.com/joelhooks/swarm-tools
- **npm:** https://www.npmjs.com/package/opencode-swarm-plugin
