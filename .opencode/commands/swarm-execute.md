---
description: Execute complex tasks with SwarmTools coordination for parallel multi-agent execution
mode: command
---

# Swarm Execute Command

## Purpose
Use SwarmTools primitives for parallel task execution on complex features requiring coordination, file conflict prevention, and progress tracking across multiple workers.

## When to Use

**Use /swarm-execute when:**
- Plan has 15+ tasks across multiple systems
- Multiple agents need to work in parallel
- Risk of file conflicts between workers
- Long-running work that should survive context compaction
- Need automatic checkpointing and learning

**Use /execute when:**
- Plan has <15 tasks
- Single system or component
- No parallel execution needed
- Simple linear implementation

## Workflow

### 1. Check Hive Status

First, check if there are existing work items:

```
hive_ready()
```

- Returns next unblocked cell from `.hive/issues.jsonl`
- If no cells exist, you need to create an epic with subtasks

### 2. Decompose Task (if starting new swarm)

If no existing work items, decompose the task:

```
swarm_decompose({
  task: "{task from plan}",
  max_subtasks: 5,
  query_cass: true
})
```

- Queries CASS for similar past decompositions (if available)
- Returns strategy-specific breakdown (file-based, feature-based, or risk-based)
- Generates 3-5 subtasks optimal for parallel execution

### 3. Create Epic + Subtasks

Create work items atomically:

```
hive_create_epic({
  epic_title: "{feature name}",
  subtasks: [
    {title: "Subtask 1", description: "...", priority: 0},
    {title: "Subtask 2", description: "...", priority: 1},
    ...
  ]
})
```

- Creates epic and subtasks in `.hive/issues.jsonl`
- All subtasks are git-tracked
- Priority determines execution order

### 4. Spawn Workers (Parallel)

For each subtask, launch a specialized worker agent:

```
Launch Task agent:
- **subagent_type**: `general` or use specific @swarm-worker-* agent
- **description**: "{subtask title}"
- **Dynamic prompt**: Include subtask details from hive, plan context, file patterns
```

Each worker will:
1. Call `swarmmail_reserve()` before editing files (PREVENTS CONFLICTS)
2. Implement their subtask following plan specifications
3. Report progress via `swarm_progress()` at 25%, 50%, 75%
4. Call `swarm_complete()` when done (auto-releases reservations)

**Max 10 concurrent agents** — batch if you have more subtasks.

### 5. Monitor Progress

Watch for issues and coordinate:

```
swarmmail_inbox({
  agent_name: "coordinator",
  limit: 10
})
```

- Check for blocker messages from workers
- Resolve file conflicts if they arise
- Unblock dependencies between subtasks
- Workers send high-priority messages for blockers

### 6. Complete & Sync (MANDATORY)

When all workers complete:

1. **Verify completion**:
   ```
   hive_query({
     status: "done",
     epic_id: "{epic_id}"
   })
   ```

2. **Sync to git** (CRITICAL):
   ```
   hive_sync()
   git push
   ```
   
   This persists all work items to git. Without this, work is lost.

3. **Store learnings**:
   ```
   semantic-memory_store({
     information: "{what worked, what didn't}",
     tags: "swarm,parallel,{feature-type}"
   })
   ```

## Integration with /execute

Both commands save execution reports to `requests/execution-reports/`:

```markdown
# Report structure
- Meta Information (plan file, files added/modified)
- Completed Tasks
- Divergences from Plan
- Validation Results
- Tests Added
- Issues & Notes
- Ready for Commit
```

**Key difference:**
- `/execute` — Sequential, single agent, simple plans
- `/swarm-execute` — Parallel, multiple workers, complex coordination

## Troubleshooting

### File Reservation Conflicts

If workers report conflicts:
```
swarmmail_reserve() returned contention
```

**Solution:** Check which agent holds the lock:
```
swarmmail_inbox({agent_name: "coordinator"})
```
Wait for holder to complete or release.

### Worker Blocked

If worker sends BLOCKED message:
```
swarmmail_send({
  to: ["coordinator"],
  subject: "BLOCKED: {reason}",
  importance: "high"
})
```

**Solution:** Unblock dependency or reassign task.

### Context Compaction

If context compacts mid-swarm:
```
swarm_recover({
  project_key: "{project}",
  epic_id: "{epic_id}"
})
```

**Solution:** Automatic checkpoints at 25%, 50%, 75% restore state.

### MCP Server Unavailable

If SwarmTools MCP not responding:

**Fallback:** Use `/execute` with manual parallel agent dispatch:
```
Launch 4 Task agents in parallel with different file assignments
Coordinate manually via Task tool
```

## Examples

### Simple Swarm (3 workers)

```
/swarm-execute "Add user authentication"
→ Decomposes into: schema, service, routes
→ Spawns: @swarm-worker-database, @swarm-worker-backend, @swarm-worker-testing
→ All run in parallel, no file conflicts
→ Sync to git, store learnings
```

### Complex Swarm (8 workers)

```
/swarm-execute "Build dashboard with auth, API, database"
→ Decomposes into: auth, dashboard components, API endpoints, database migrations, tests
→ Spawns: 8 specialized workers
→ Coordinates via file reservations
→ Checkpoints at 25%, 50%, 75%
→ All complete, sync, push
```

## Rules

1. **ALWAYS** reserve files before editing — prevents conflicts
2. **NEVER** edit files reserved by other agents — check `swarmmail_inbox()`
3. **ALWAYS** call `swarm_complete()` — releases reservations, records learnings
4. **ALWAYS** call `hive_sync()` + `git push` — persists work
5. **REPORT** progress at 25%, 50%, 75% — creates checkpoints
6. **SEND** blocker messages immediately — unblock fast
7. **CHECK** semantic memory before starting — learn from past
