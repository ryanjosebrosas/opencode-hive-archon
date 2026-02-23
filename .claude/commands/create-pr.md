---
description: Create a GitHub PR from the current branch with AI-generated title and description
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Create Pull Request

You are creating a GitHub Pull Request for the current branch.

## INPUT

**Required Context:**
1. Current branch name and git status
2. Commit history since diverging from base branch
3. Changed files (git diff summary)
4. Project context from CLAUDE.md (if available)

**Gather this information:**

```bash
# Get current branch and status
git branch --show-current
git status --short

# Get base branch (usually master/main)
git remote show origin | grep 'HEAD branch' | cut -d' ' -f5

# Get commit history for this branch
git log <base-branch>..HEAD --oneline

# Get changed files summary
git diff <base-branch>...HEAD --stat
```

## PROCESS

### Step 1: Analyze Changes

Review all commits and changed files to understand:
- What feature/fix was implemented?
- What problem does it solve?
- What files were modified and why?
- Are there any breaking changes?
- Is this a feature, fix, docs, refactor, etc.?

### Step 2: Draft PR Content

Create a PR following this structure:

**Title Format** (max 72 characters):
- `feat: <concise description>` - New feature
- `fix: <concise description>` - Bug fix
- `docs: <concise description>` - Documentation
- `refactor: <concise description>` - Code refactoring
- `chore: <concise description>` - Maintenance tasks

**Description Format:**
```markdown
## Summary
<1-3 sentences describing what and why>

## Changes
- <bullet point of key changes>
- <another change>

## Test Plan
- [ ] <how to test/verify this works>
- [ ] <another test step>

## Related Issues
Closes #<issue-number> (if applicable)
Fixes #<issue-number> (if applicable)

Generated with [Claude Code](https://claude.com/claude-code)
```

### Step 3: Push Branch (if needed)

Check if the current branch is pushed:
```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

If not pushed or behind remote:
```bash
git push -u origin <current-branch>
```

### Step 4: Ask for Confirmation

Before creating the PR, show the user:
- **Title**: <proposed title>
- **Base branch**: <base> ← <current-branch>
- **Commits included**: <count> commits
- **Files changed**: <count> files

Ask: "Create PR with this content?"

### Step 5: Create PR

Use GitHub CLI to create the PR:
```bash
gh pr create --title "<title>" --body "<description>" --base <base-branch>
```

Capture the PR URL from the output.

### Step 6: Post-Creation Actions

After PR is created:
1. Print the PR URL
2. Check if CodeRabbit is configured (`.coderabbit.yaml` exists)
3. If yes, inform user that CodeRabbit will review automatically
4. Optionally offer to open the PR in browser

## OUTPUT

**Success Response:**
```
✅ Pull Request Created!

📋 PR #<number>: <title>
🔗 <PR URL>

Next steps:
- CodeRabbit will review automatically (if configured)
- Claude Code will auto-fix issues (via claude-fix-coderabbit.yml)
- Review the PR and merge when ready

Open in browser? (y/n)
```

**Error Handling:**
- If not on a feature branch (on master/main), warn and ask for confirmation
- If no commits to push, inform user and exit
- If gh CLI not available, provide manual instructions
- If push fails, show error and suggest checking permissions

## VALIDATION

Before completing:
- ✅ PR was created successfully (check gh CLI output)
- ✅ PR URL is accessible
- ✅ Base branch is correct (not creating PR from master to master)
- ✅ Branch has commits to include

## NOTES

- This command assumes you've already committed your changes
- For the full workflow, use `/end-to-end-feature` instead
- PR creation triggers CodeRabbit review if configured
- The PR description can be edited on GitHub after creation
