---
description: Create git commit with conventional message format
agent: build
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

### 2. Generate Commit Message via Haiku

Dispatch to Haiku to write the commit message — fast, accurate prose generation:

```
dispatch({
  taskType: "commit-message",
  prompt: "Write a conventional commit message for these changes.\n\nGit diff:\n{git diff HEAD}\n\nGit status:\n{git status}\n\nFormat: type(scope): short description (imperative mood, max 50 chars)\n\nOptional body (if changes are significant): what changed and why, not how. Max 3 bullet points.\n\nTypes: feat, fix, refactor, docs, test, chore, perf, style, plan\n\nReturn ONLY the commit message — no explanation, no markdown fences."
})
```

Use Haiku's output as the commit message verbatim.

### 3. Stage and Commit

Before staging, run artifact completion sweep (required):
- For completed request artifacts in `requests/`, `requests/archive/code-reviews/`, and `requests/archive/code-loops/`, rename `.md` -> `.done.md`.
- Keep filenames as the source of completion status; do not rely on title edits.

```bash
git add $ARGUMENTS  # or git add . if no files specified
git commit --no-verify -m "{haiku-generated message}"
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
