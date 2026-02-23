# SwarmTools Installation Guide

> **IMPORTANT**: The installation process requires interactive terminal input. Follow these steps carefully.

---

## Current Status

✅ **Completed:**
- SwarmTools plugin installed globally (`npm install -g opencode-swarm-plugin@latest`)
- Plugin installed locally in `.opencode/node_modules/opencode-swarm-plugin/`
- Git repository initialized
- `.hive/` directory created for work item tracking

⏳ **Requires Your Action:**
- Complete interactive `swarm init` setup
- Install plugin in OpenCode via `/plugin` command
- Test first swarm

---

## Step-by-Step Installation

### Step 1: Complete Swarm Init (Interactive)

**In your terminal, run:**
```bash
swarm init
```

You'll see a prompt:
```
◆ Create your first cell?
│ ● Yes / ○ No
```

**Select:** `No` (we'll create cells via `/swarm` command in OpenCode)

### Step 2: Install Plugin in OpenCode

**In OpenCode, run:**
```
/plugin
```

Then navigate the menu:
1. Select **Marketplace** (or **Install from directory**)
2. Find and select **opencode-swarm-plugin**
3. Confirm installation

**Alternative (if marketplace not available):**

The plugin is already installed in `.opencode/node_modules/`. OpenCode should auto-detect it. If not, check OpenCode documentation for loading local plugins.

### Step 3: Verify Installation

**In OpenCode:**
```
/prime
```

Check that these appear in the inventory:
- `/swarm` command (or `/swarm-execute` from our custom command)
- `@swarm-worker-backend` agent
- `@swarm-worker-frontend` agent
- `@swarm-worker-database` agent
- `@swarm-worker-testing` agent

### Step 4: Test First Swarm

**In OpenCode:**
```
/swarm "Create a simple test file with Hello World"
```

Watch the coordinator:
1. Decompose the task
2. Create work items in `.hive/`
3. Spawn worker agents
4. Complete the task
5. Store learnings

### Step 5: Verify .hive/

**In terminal:**
```bash
ls -la .hive/
cat .hive/issues.jsonl
```

You should see work items tracked in the JSONL file.

---

## Troubleshooting

### Issue: "Not in a git repository"

**Solution:**
```bash
git init
git config user.email "you@example.com"
git config user.name "Your Name"
swarm init
```

### Issue: Plugin not appearing in OpenCode

**Possible causes:**
1. Plugin not in correct location
2. OpenCode needs restart
3. Plugin needs to be loaded via `/plugin` command

**Solutions:**
- Restart OpenCode
- Run `/plugin` and check marketplace
- Verify plugin is in `.opencode/node_modules/opencode-swarm-plugin/`

### Issue: Commands not available

The plugin provides these commands automatically after installation:
- `/swarm` - Main swarm coordination command
- `/swarm:status` - Check worker progress
- `/swarm:inbox` - Review agent messages
- `/swarm:hive` - Query work items

If not available:
1. Check plugin loaded: `/plugin` → Show installed
2. Restart OpenCode
3. Reinstall plugin

---

## What We Created

This integration added:

### Custom Commands (`.opencode/commands/`)
- `swarm-execute.md` - Complex task coordination using SwarmTools primitives

### Worker Agents (`.opencode/agents/`)
- `swarm-worker-backend.md` - Backend specialist
- `swarm-worker-frontend.md` - Frontend specialist
- `swarm-worker-database.md` - Database specialist
- `swarm-worker-testing.md` - Testing specialist

### Documentation (`reference/`)
- `SWARMTOOLS-QUICKSTART.md` - Quick start guide
- `swarmtools-integration.md` - Comprehensive integration guide

### Configuration
- `.hive/` directory - Git-backed work item tracking
- Plugin in `.opencode/node_modules/` - SwarmTools integration

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your System                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PIV Loop (Your methodology)                           │
│  /planning → /execute → /code-review → /commit         │
│                                                         │
│  ⬇ Uses for complex tasks                              │
│                                                         │
│  SwarmTools (Multi-agent coordination)                 │
│  - /swarm command                                       │
│  - File reservations (prevents conflicts)              │
│  - Automatic checkpoints (survives compaction)         │
│  - Learning system (semantic memory)                   │
│                                                         │
│  ⬇ Stores work items in                                │
│                                                         │
│  .hive/ (Git-backed tracking)                          │
│  - issues.jsonl (event-sourced work items)            │
│  - Tracked in git (survives sessions)                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Complete `swarm init`** in your terminal
2. **Install plugin in OpenCode** via `/plugin` command
3. **Test with simple task** to verify everything works
4. **Commit this implementation** with `/commit`
5. **Optional**: Install CASS and UBS for enhanced features
   ```bash
   # CASS for historical patterns
   git clone https://github.com/Dicklesworthstone/coding_agent_session_search
   cd coding_agent_session_search && pip install -e .
   cass index
   
   # UBS for bug scanning
   git clone https://github.com/Dicklesworthstone/ultimate_bug_scanner
   cd ultimate_bug_scanner && pip install -e .
   ```

---

## Resources

- **SwarmTools Docs**: https://www.swarmtools.ai/docs
- **GitHub**: https://github.com/joelhooks/swarm-tools
- **Plugin README**: `.opencode/node_modules/opencode-swarm-plugin/README.md`
- **Quick Start**: `reference/SWARMTOOLS-QUICKSTART.md`
- **Integration Guide**: `reference/swarmtools-integration.md`

---

**Questions?** Run `swarm doctor` to check installation health.
