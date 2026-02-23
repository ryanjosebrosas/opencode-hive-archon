---
description: Create git commit with conventional message format
argument-hint: [file1] [file2] ... (optional - commits all changes if not specified)
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*)
---

# Commit: Create Git Commit

## Files to Commit

Files specified: $ARGUMENTS

(If no files specified, commit all changes)

## Commit Process

### 1. Review Current State

```bash
git status
git diff HEAD
```

If staging specific files: `git diff HEAD -- $ARGUMENTS`

### 2. Analyze Changes

Determine type (feat/fix/refactor/docs/test/chore/perf/style/plan), scope, and description (imperative mood, 50 chars). Add body if significant context needed.

### 3. Stage and Commit

```bash
git add $ARGUMENTS  # or git add . if no files specified
git commit -m "type(scope): description"
```

### 4. Confirm Success

```bash
git log -1 --oneline
git show --stat
```

## Output Report

**Commit Hash**: [hash]
**Message**: [full message]
**Files**: [list with change stats]
**Summary**: X files changed, Y insertions(+), Z deletions(-)

**Next**: Push to remote (`git push`) or continue development.

### 5. Update Memory (if memory.md exists)

Append to memory.md: session note, any lessons/gotchas/decisions discovered. Keep entries 1-2 lines each. Don't repeat existing entries. Skip if memory.md doesn't exist.

### 6. Report Completion

**Archon** (if available):
1. Find the current project: `find_projects(query="{feature-name}")` or use project_id from the planning/execute session
2. Find all tasks with status "doing" or "review": `find_tasks(filter_by="project", filter_value=project_id)`
3. Mark each as "done": `manage_task("update", task_id="...", status="done")`
4. Update project: `manage_project("update", project_id="...", description="Feature complete, committed: {hash}")`

If no Archon project exists for this feature, skip task updates. Only update project if project_id is available from context.

## Notes

- If no changes to commit, report clearly
- If commit fails (pre-commit hooks), report the error
- Follow the project's commit message conventions
- Do NOT include Co-Authored-By lines in commits
