---
description: Create feature branch, push, and open PR with Codex review request
agent: build
---

# PR: Create Branch and Pull Request

## Arguments

`$ARGUMENTS` — Optional: feature name for the branch (e.g., `supabase-provider`), or PR title override

(If no arguments, derive branch name from the latest commit message)

## Prerequisites

- Commit must already exist (run `/commit` first)
- If working tree is dirty, report and exit

---

## Step 1: Gather Context

```bash
git status
git log -5 --oneline
git remote -v
git branch --show-current
```

**If working tree is dirty (uncommitted changes):**
- Report: "Uncommitted changes detected. Run `/commit` first."
- Exit — do NOT commit automatically.

---

## Step 2: Determine Branch Name and Scope

Each PR gets its own branch. The branch name should reflect the specific feature/fix, not a long-lived epic branch.

**Branch naming convention**: `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`

Derive the branch name:
1. If `$ARGUMENTS` contains a feature name → use it (e.g., `feat/supabase-provider`)
2. Otherwise → derive from the latest commit message:
   - `feat(memory): add Supabase provider` → `feat/supabase-provider`
   - `fix(rerank): handle empty results` → `fix/rerank-empty-results`

**Determine which commits belong to this PR:**
- Default: the latest commit only (1 commit = 1 PR, clean and focused)
- If user specifies a range or multiple related commits, include them all
- Ask if ambiguous: "Include just the latest commit, or the last N commits?"

---

## Step 3: Create Feature Branch and Push

```bash
# Create new branch from current HEAD
git checkout -b <branch-name>

# Push the new branch to remote
git push brain-ultimaum-fin <branch-name> -u
```

After push, switch back to the original branch so it's not disrupted:
```bash
git checkout <original-branch>
```

If branch name already exists on remote:
- Report: "Branch `<name>` already exists on remote."
- Ask: create with a suffix (e.g., `feat/supabase-provider-2`), or use existing?

---

## Step 4: Generate PR Title and Body via Haiku

```bash
# Gather context for Haiku
git log --oneline brain-ultimaum-fin/master..<branch-name>
git diff brain-ultimaum-fin/master...<branch-name> --stat
git diff brain-ultimaum-fin/master...<branch-name>
```

Dispatch to Haiku for PR title + body generation:

```
dispatch({
  taskType: "pr-description",
  prompt: "Write a GitHub pull request title and body for these changes.\n\nCommits:\n{git log --oneline}\n\nChanged files:\n{git diff --stat}\n\nDiff:\n{git diff}\n\nFormat:\nTITLE: type(scope): description (conventional commit format, max 72 chars)\n\nBODY:\n## What\n<What changed — 2-4 bullets, specific and concrete>\n\n## Why\n<Why this was needed — 1-2 sentences>\n\n## Changes\n<Files changed grouped by area with 1-line description each>\n\n## Testing\n<Test results, validation commands run, pass/fail>\n\n## Notes\n<Breaking changes, migration steps, known skips — or 'None'>\n\nReturn ONLY the title and body — no extra explanation."
})
```

Use Haiku's output verbatim for both `--title` and `--body`.

---

## Step 5: Create Pull Request

```bash
gh pr create \
  --repo ryanjosebrosas/brain-ultimaum-fin \
  --base master \
  --head <branch-name> \
  --title "<pr-title>" \
  --body "$(cat <<'EOF'
## Summary
<2-5 bullet points covering changes in this PR>

## Changes
<Group by area: Backend, Frontend, Tests, Config, Workflow>
<For each area, list files changed with 1-line description>

## Testing
<Test count, validation results if available>

## Notes
<Migration steps, breaking changes, or deployment notes if any>
EOF
)"
```

---

## Step 6: Request Codex Review

After PR is created, add a review comment:

```bash
gh pr comment <pr-number> \
  --repo ryanjosebrosas/brain-ultimaum-fin \
  --body "@codex Please review this PR. Focus on:
- Code correctness and logic errors
- Security issues (hardcoded secrets, injection risks)
- Architecture alignment with existing patterns
- Test coverage for new functionality
- Type safety and error handling"
```

---

## Step 7: Report Completion

```
PR Created
==========

Branch:  <branch-name> (new, from <original-branch>)
PR:      <pr-url>
Title:   <pr-title>
Base:    master
Commits: <N> commits
Review:  @codex review requested
Current: Back on <original-branch>

Next: Wait for Codex review, then merge or address feedback.
```

---

## Notes

- **One PR per feature/slice** — each `/pr` creates a fresh branch, not extending a prior PR
- Always target `master` on `brain-ultimaum-fin` remote
- After PR creation, return to the original branch so work can continue
- If `gh` CLI is not authenticated, report and suggest `gh auth login`
- Do NOT force-push unless explicitly asked
- The @codex comment is posted separately (not in PR body) so it triggers properly
- If the current branch IS already a clean feature branch with only relevant commits, skip branch creation and push + PR directly
