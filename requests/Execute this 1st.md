# Feature: SwarmTools Integration

## Feature Description

Integrate SwarmTools.ai multi-agent coordination system alongside existing PIV Loop and Archon MCP. This creates a hybrid system where PIV handles planning/execution workflow, Archon manages task tracking + RAG, and SwarmTools provides parallel execution coordination, file conflict prevention, and automatic learning.

## User Story

As a developer using this coding system, I want to use SwarmTools for complex parallel tasks while keeping my PIV Loop workflow intact, so that I can scale to larger features without file conflicts or lost context.

## Problem Statement

Current system handles parallel agents well (`/prime`, `/planning`, `/code-review`) but lacks:
- Git-backed work item tracking that survives sessions
- File reservation system to prevent edit conflicts
- Automatic learning from task outcomes
- Checkpoint/recovery for context compaction

## Solution Statement

Install SwarmTools plugin side-by-side with existing system. Create bridge commands and worker agents. Keep PIV Loop as primary workflow, add `/swarm-execute` for complex features requiring coordination.

- Decision: Side-by-side architecture — because replacing PIV would lose methodology benefits
- Decision: Create 4 specialized workers initially — because YAGNI, can add more as needed
- Decision: Keep Archon for tasks + RAG — because Swarm learning is complementary, not replacement

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `.opencode/commands/`, `.opencode/agents/`, `opencode.json`
- **Dependencies**: SwarmTools plugin (npm), CASS (optional), UBS (optional), Ollama (optional)

---

## CONTEXT REFERENCES

### Relevant Codebase Files

- `.opencode/commands/prime.md:8-250` — Why: Pattern for parallel agent dispatch (5-6 agents simultaneously)
- `.opencode/commands/planning.md:76-131` — Why: Dynamic agent prompts, Task tool usage
- `.opencode/commands/code-review.md:19-31` — Why: Pattern for 4 parallel specialized agents
- `.opencode/agents/research-codebase.md:1-80` — Why: Agent definition structure template
- `templates/AGENT-TEMPLATE.md:46-58` — Why: Frontmatter options, MCP server configuration
- `opencode.json:1-60` — Why: MCP configuration location, agent mode settings

### New Files to Create

- `.opencode/commands/swarm-execute.md` — Swarm coordination command for complex features
- `.opencode/agents/swarm-worker-backend.md` — Backend implementation worker
- `.opencode/agents/swarm-worker-frontend.md` — Frontend implementation worker
- `.opencode/agents/swarm-worker-database.md` — Database/migrations worker
- `.opencode/agents/swarm-worker-testing.md` — Testing specialist worker
- `reference/swarmtools-integration.md` — Deep integration guide
- `reference/SWARMTOOLS-QUICKSTART.md` — Quick start reference
- `requests/execution-reports/` — Directory for execution reports (create if missing)

### Related Memories (from memory.md)

- No relevant memories found in memory.md (first-time integration)

### Relevant Documentation

- [SwarmTools Documentation](https://www.swarmtools.ai/docs)
  - Installation: Quick Start section
  - Tools: Hive, Swarm Mail, Swarm, Skills
  - Checkpoint & Recovery mechanism
- [SwarmTools GitHub](https://github.com/joelhooks/swarm-tools)
  - opencode-swarm-plugin repository
  - Installation and setup instructions

### Patterns to Follow

**Parallel Agent Dispatch** (from `.opencode/commands/prime.md:28-224`):
```markdown
Launch ALL of the following Task agents **simultaneously**:
### Agent 1: Commands Inventory (Sonnet)
- **subagent_type**: `general`
- **description**: "Inventory slash commands"
```
- Why this pattern: Swarm workers will follow same parallel dispatch
- Common gotchas: Max 10 concurrent agents, manage with batches if needed

**Agent Definition Structure** (from `.opencode/agents/research-codebase.md:1-11`):
```markdown
---
description: Use this agent for parallel codebase exploration...
mode: subagent
tools:
  read: true
  write: true
  ...
---
```
- Why this pattern: Standard format for all agent definitions
- Common gotchas: `mode: subagent` required, tools control capabilities

**MCP Configuration** (from `templates/AGENT-TEMPLATE.md:58`):
```json
"mcpServers": ["swarm"]
```
- Why this pattern: How agents access SwarmTools MCP server
- Common gotchas: MCP server must be defined in `opencode.json` first

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Install SwarmTools plugin, configure MCP server, verify installation.

**Tasks:**
- Install npm package globally
- Run `swarm setup`
- Add MCP config to `opencode.json`
- Verify with `swarm doctor`

### Phase 2: Core Implementation

Create swarm-execute command and 4 worker agents.

**Tasks:**
- Create `swarm-execute.md` command following existing command patterns
- Create 4 specialized worker agents following agent template
- Each worker gets `mcpServers: ["swarm"]` access

### Phase 3: Integration

Create reference documentation, update system files.

**Tasks:**
- Create integration guide in `reference/`
- Create quick start guide
- Create execution reports directory
- Update AGENTS.md if needed

### Phase 4: Testing & Validation

Test installation, verify commands work, test worker agents.

**Tasks:**
- Run `swarm doctor` — verify all systems operational
- Test `/swarm` command with simple task
- Validate agent definitions with markdown linting
- Verify file structure created correctly

---

## STEP-BY-STEP TASKS

### ADD mcpServers to opencode.json

- **TARGET**: `opencode.json` (lines 58-60, before closing brace)
- **IMPLEMENT**: Add mcpServers section at root level (same level as "agent"):
  ```json
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
  ```
  Add comma after line 58 (`}`), then add the mcpServers block.
- **PATTERN**: Root-level config like "agent" section at `opencode.json:46-59`
- **IMPORTS**: None
- **GOTCHA**: 
  - Add comma after existing last property in "agent" section
  - Preserve indentation (2 spaces)
  - OpenCode must be restarted after config change
- **VALIDATE**: `node -e "console.log(JSON.stringify(JSON.parse(require('fs').readFileSync('opencode.json')), null, 2))"`

### CREATE .opencode/commands/swarm-execute.md

- **TARGET**: `.opencode/commands/swarm-execute.md`
- **IMPLEMENT**: Create command file with this structure:
  ```markdown
  ---
  description: Execute complex tasks with SwarmTools coordination
  mode: command
  ---
  
  # Swarm Execute Command
  
  ## Purpose
  Use SwarmTools primitives for parallel task execution on complex features (15+ tasks, multiple systems, file conflict risk).
  
  ## Workflow
  
  1. **Check Hive Status**
     - Call `hive_ready()` to get next unblocked cell
     - If no cells exist, use `hive_create_epic()` to create work items
  
  2. **Spawn Workers** (parallel, up to 10)
     - For each subtask, launch Task agent with appropriate @swarm-worker-* agent
     - Workers call `swarmmail_reserve()` before editing files
     - Workers report progress via `swarm_progress()`
  
  3. **Monitor Progress**
     - Check `swarmmail_inbox()` for blocker messages
     - Resolve conflicts, unblock dependencies
  
  4. **Complete & Sync** (MANDATORY)
     - Each worker calls `swarm_complete()` (auto-releases reservations)
     - Call `hive_sync()` to persist to git
     - Run `git push` to backup
  
  ## Integration with /execute
  - Use `/execute` for simple plans (<15 tasks, single system)
  - Use `/swarm-execute` for complex plans needing coordination
  - Both save reports to `requests/execution-reports/`
  ```
- **PATTERN**: Command structure from `.opencode/commands/prime.md:1-30` (frontmatter + purpose + workflow)
- **IMPORTS**: None
- **GOTCHA**: 
  - Command must check if SwarmTools is available before using hive_* tools
  - If MCP unavailable, fall back to normal `/execute` workflow
  - Always end with `hive_sync()` + `git push`
- **VALIDATE**: `if exist .opencode\commands\swarm-execute.md (echo Command created) else (echo FAILED)`

### CREATE .opencode/agents/swarm-worker-backend.md

- **TARGET**: `.opencode/agents/swarm-worker-backend.md`
- **IMPLEMENT**: Create agent file with this exact frontmatter and role:
  ```markdown
  ---
  description: Backend implementation specialist for SwarmTools coordination. Reserves files before editing, reports progress, prevents conflicts.
  mode: subagent
  model: sonnet
  tools:
    read: true
    write: true
    edit: true
    bash: true
    glob: true
    grep: true
  mcpServers:
    - swarm
  ---
  
  # Role: Backend Implementation Worker
  
  You are a specialized worker in a SwarmTools coordination system. You receive specific subtasks from a coordinator and implement backend services, APIs, and business logic.
  
  ## Mandatory Workflow
  
  1. **Reserve Files** (BEFORE ANY EDITS)
     ```
     swarmmail_reserve({
       paths: ["{files you'll edit}"],
       reason: "{cell_id}: {brief description}",
       exclusive: true,
       ttl_seconds: 3600
     })
     ```
  
  2. **Implement**
     - Follow plan specifications exactly
     - Check semantic memory: `semantic-memory_find({query: "{task type}", limit: 3})`
     - Load skills if needed: `skills_use({name: "testing-patterns"})`
  
  3. **Report Progress** (at 25%, 50%, 75%)
     ```
     swarm_progress({
       project_key: "{project}",
       agent_name: "BackendWorker",
       cell_id: "{your_cell}",
       progress_percent: 50,
       message: "Current status",
       files_touched: ["{list}"]
     })
     ```
  
  4. **Complete** (MANDATORY - releases reservations)
     ```
     swarm_complete({
       project_key: "{project}",
       agent_name: "BackendWorker",
       cell_id: "{your_cell}",
       summary: "{what you implemented}",
       files_touched: ["{list}"],
       evaluation: "{success/issues}"
     })
     ```
  
  ## Rules
  - ALWAYS reserve files before editing
  - NEVER edit files reserved by other agents (check `swarmmail_inbox()`)
  - Call `swarm_complete()` even if you fail (coordinator needs to know)
  - Report progress at 25%, 50%, 75% completion
  ```
- **PATTERN**: Agent definition from `.opencode/agents/research-codebase.md:1-11` (frontmatter) + `research-codebase.md:14-80` (role/workflow)
- **IMPORTS**: None
- **GOTCHA**: 
  - Frontmatter MUST have `mode: subagent` or agent won't work
  - `mcpServers: ["swarm"]` grants access to SwarmTools MCP server
  - Model defaults to parent, but explicit `sonnet` ensures quality
- **VALIDATE**: `if exist .opencode\agents\swarm-worker-backend.md (echo Backend worker created) else (echo FAILED)`

### CREATE .opencode/agents/swarm-worker-frontend.md

- **TARGET**: `.opencode/agents/swarm-worker-frontend.md`
- **IMPLEMENT**: Create agent file with frontmatter (same as backend) but frontend-focused role:
  - Change role to "Frontend Implementation Worker"
  - Description: "Frontend specialist for React/TypeScript components, UI implementation, styling"
  - Workflow same as backend worker
  - Focus areas: Components, hooks, styling, state management, accessibility
- **PATTERN**: Same as `swarm-worker-backend.md` being created
- **IMPORTS**: None
- **GOTCHA**: 
  - Change agent_name in workflow to "FrontendWorker"
  - Focus on component patterns from existing codebase
- **VALIDATE**: `if exist .opencode\agents\swarm-worker-frontend.md (echo Frontend worker created) else (echo FAILED)`

### CREATE .opencode/agents/swarm-worker-database.md

- **TARGET**: `.opencode/agents/swarm-worker-database.md`
- **IMPLEMENT**: Create agent file with database specialist role:
  - Role: "Database Implementation Worker"
  - Description: "Database specialist for schema design, migrations, queries, data modeling"
  - Skills: Include `skills_use({name: "system-design"})` for database patterns
  - Focus areas: Schema design, migrations, indexes, query optimization
- **PATTERN**: Same as `swarm-worker-backend.md`
- **IMPORTS**: None
- **GOTCHA**: 
  - Change agent_name to "DatabaseWorker"
  - Always check existing schema patterns before creating new tables
- **VALIDATE**: `if exist .opencode\agents\swarm-worker-database.md (echo Database worker created) else (echo FAILED)`

### CREATE .opencode/agents/swarm-worker-testing.md

- **TARGET**: `.opencode/agents/swarm-worker-testing.md`
- **IMPLEMENT**: Create agent file with testing specialist role:
  - Role: "Testing Implementation Worker"
  - Description: "Testing specialist for unit tests, integration tests, test fixtures, mocks"
  - Skills: Include `skills_use({name: "testing-patterns"})` for test patterns
  - Focus areas: Test structure, fixtures, mocks, assertions, coverage
- **PATTERN**: Same as `swarm-worker-backend.md`
- **IMPORTS**: None
- **GOTCHA**: 
  - Change agent_name to "TestingWorker"
  - Follow existing test file naming: `*.test.ts` or `*.spec.ts`
  - Match test framework used in codebase (Jest, Vitest, etc.)
- **VALIDATE**: `if exist .opencode\agents\swarm-worker-testing.md (echo Testing worker created) else (echo FAILED)`

### CREATE reference/SWARMTOOLS-QUICKSTART.md

- **TARGET**: `reference/SWARMTOOLS-QUICKSTART.md`
- **IMPLEMENT**: Create quick start guide with these sections:
  ```markdown
  # SwarmTools Quick Start
  
  ## Installation (5 min)
  1. `npm install -g opencode-swarm-plugin@latest`
  2. `swarm setup`
  3. `swarm doctor` — verify installation
  
  ## First Swarm (10 min)
  1. In OpenCode: `/swarm "Create a simple feature"`
  2. Watch workers coordinate in real-time
  3. Verify `.hive/` directory created
  
  ## Common Commands
  - `hive_ready()` — get next task
  - `swarmmail_reserve()` — reserve files
  - `swarm_complete()` — complete task
  - `hive_sync()` — sync to git
  
  ## Troubleshooting
  - `swarm doctor` — check health
  - Restart OpenCode after config changes
  - Check `.hive/issues.jsonl` for work items
  ```
- **PATTERN**: Follow structure from `reference/archon-workflow.md:1-50` (quick start section)
- **IMPORTS**: None
- **GOTCHA**: Keep concise — 1 page max, installation + first use + troubleshooting only
- **VALIDATE**: `if exist reference\SWARMTOOLS-QUICKSTART.md (echo Quick start created) else (echo FAILED)`

### CREATE reference/swarmtools-integration.md

- **TARGET**: `reference/swarmtools-integration.md`
- **IMPLEMENT**: Create comprehensive integration guide with these sections:
  ```markdown
  # SwarmTools Integration Guide
  
  ## Architecture
  - Diagram showing PIV + Archon + Swarm layers
  - System boundaries and responsibilities
  
  ## Installation Deep Dive
  - Plugin installation
  - Optional dependencies (CASS, UBS, Ollama)
  - Configuration files
  
  ## Integration Points
  - How /planning hands off to /swarm-execute
  - Archon tasks ↔ Hive epics mapping
  - Learning: memory.md + semantic-memory
  
  ## Worker Agents
  - 4 specialized workers (backend, frontend, database, testing)
  - File reservation protocol
  - Progress reporting
  
  ## Troubleshooting
  - Common issues and solutions
  - Debugging file conflicts
  - Recovery from failed swarms
  ```
  Include architecture diagram using mermaid syntax.
- **PATTERN**: Follow structure from `reference/subagents-deep-dive.md` (comprehensive guide)
- **IMPORTS**: None
- **GOTCHA**: Include full architecture diagram, all integration points, troubleshooting section
- **VALIDATE**: `if exist reference\swarmtools-integration.md (echo Integration guide created) else (echo FAILED)`

### CREATE requests/execution-reports/

- **TARGET**: `requests/execution-reports/`
- **IMPLEMENT**: Create directory for execution reports. Check `.gitignore` and add entry if missing:
  ```
  requests/execution-reports/
  ```
- **PATTERN**: Follow existing `requests/` directory pattern
- **IMPORTS**: None
- **GOTCHA**: 
  - Check if `.gitignore` exists in root
  - Add `requests/execution-reports/` to prevent commiting reports
  - Reports are ephemeral, consumed by `/system-review`
- **VALIDATE**: `if exist requests\execution-reports (echo Directory created) else (echo FAILED)`

### UPDATE AGENTS.md

- **TARGET**: `AGENTS.md` (after line 172, before Specialist Agents section)
- **IMPLEMENT**: Add new "Swarm Workers" subsection with this table:
  ```markdown
  ### Swarm Workers (SwarmTools)
  | Agent | Purpose |
  |-------|---------|
  | `swarm-worker-backend` | Backend services, APIs, business logic with file reservations |
  | `swarm-worker-frontend` | React components, UI, styling, state management |
  | `swarm-worker-database` | Schema design, migrations, queries, data modeling |
  | `swarm-worker-testing` | Unit tests, integration tests, fixtures, mocks |
  ```
- **PATTERN**: Table format from `AGENTS.md:146-157` (Research Agents section)
- **IMPORTS**: None
- **GOTCHA**: 
  - Add section header "### Swarm Workers (SwarmTools)"
  - Insert between Utility Agents and Specialist Agents
  - Keep table format consistent with existing tables
- **VALIDATE**: `findstr /C:"swarm-worker" AGENTS.md >nul && echo AGENTS.md updated || echo FAILED`

---

## TESTING STRATEGY

### Unit Tests

Each component tested independently:
- Installation: `swarm doctor` passes
- Command file exists and is valid markdown
- Agent files exist with correct frontmatter
- MCP config is valid JSON

### Integration Tests

Full workflow test:
- `/swarm` command works in OpenCode
- Worker agents can be invoked via Task tool
- File reservations function correctly

### Edge Cases

- MCP server unavailable — commands should degrade gracefully
- Agent invoked without swarm tools — should fail with clear error
- File reservation conflicts — should warn and wait

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```powershell
# Check JSON syntax (PowerShell)
node -e "console.log(JSON.stringify(JSON.parse(require('fs').readFileSync('opencode.json')), null, 2))"

# Check files exist (PowerShell/CMD)
if exist .opencode\commands\swarm-execute.md (echo Command created) else (echo FAILED)
if exist .opencode\agents\swarm-worker-backend.md (echo Backend worker) else (echo FAILED)
if exist .opencode\agents\swarm-worker-frontend.md (echo Frontend worker) else (echo FAILED)
if exist .opencode\agents\swarm-worker-database.md (echo Database worker) else (echo FAILED)
if exist .opencode\agents\swarm-worker-testing.md (echo Testing worker) else (echo FAILED)
if exist reference\SWARMTOOLS-QUICKSTART.md (echo Quick start) else (echo FAILED)
if exist reference\swarmtools-integration.md (echo Integration guide) else (echo FAILED)
```

### Level 2: Installation Check
```powershell
swarm doctor
# Expected output: All checks passing
# - Bun/Node.js detected
# - Hive initialized
# - MCP server configured
```

### Level 3: Directory Structure
```powershell
# Verify .hive/ created
if exist .hive\issues.jsonl (echo Hive initialized) else (echo HIVE NOT FOUND)

# Verify execution reports directory
if exist requests\execution-reports (echo Reports directory) else (echo NOT FOUND)

# List all new files
dir .opencode\commands\swarm-execute.md
dir .opencode\agents\swarm-worker-*.md
dir reference\SWARMTOOLS-*.md
```

### Level 4: Manual Validation

- Open OpenCode, run `/prime` — verify new commands/agents appear in inventory
- Try `/swarm-execute` command — should load without errors
- Check worker agents can be invoked via Task tool:
  ```
  Launch Task with @swarm-worker-backend
  ```
- Verify file reservation works (test with small file edit)

### Level 5: Additional Validation

```powershell
# Check MCP config in opencode.json
node -e "const c = JSON.parse(require('fs').readFileSync('opencode.json')); console.log('MCP Servers:', Object.keys(c.mcpServers || {}))"

# Verify .gitignore has execution-reports
findstr /C:"execution-reports" .gitignore >nul && echo "Gitignore OK" || echo "Add to .gitignore"
```

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] SwarmTools plugin installed and configured
- [x] MCP server added to `opencode.json`
- [x] `swarm-execute.md` command created
- [x] 4 worker agents created with correct frontmatter
- [x] Reference documentation created
- [x] Execution reports directory created
- [x] AGENTS.md updated with new workers

### Runtime (verify after testing/deployment)

- [ ] `swarm doctor` passes with all checks
- [ ] `/swarm` command works in OpenCode
- [ ] Worker agents can be invoked successfully
- [ ] File reservations prevent conflicts
- [ ] No regressions in existing commands

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions
- Side-by-side architecture chosen over replacement to preserve PIV Loop methodology
- 4 workers initially (backend, frontend, database, testing) following YAGNI
- Swarm learning complements Archon RAG, doesn't replace it

### Risks
- Cold start: No CASS patterns initially — mitigate by seeding from memory.md later
- TTL locks expire after 1 hour — monitor long-running tasks
- Learning isolation (local only) — commit .hive/ to git for team sharing

### Confidence Score: 8/10
- **Strengths**: Clear architecture, follows existing patterns, well-documented
- **Uncertainties**: SwarmTools behavior in production, interaction with existing MCP servers
- **Mitigations**: Start with simple tests, scale up complexity gradually
