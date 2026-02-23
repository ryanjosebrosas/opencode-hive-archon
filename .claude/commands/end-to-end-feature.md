---
description: Autonomously develop a complete feature from planning to commit
argument-hint: [feature-description]
---

# End-to-End Feature Development

**Feature Description**: $ARGUMENTS

This command chains the 4 core commands for autonomous feature development.

**WARNING**: Only use this command if you trust each individual command (`/prime`, `/planning`, `/execute`, `/commit`). If you haven't run them individually 10+ times, use them separately first.

---

## Step 1: Prime - Load Codebase Context

Execute the priming workflow to understand the codebase:

Build comprehensive understanding by:
1. Analyzing project structure (files, directories)
2. Reading core documentation (CLAUDE.md, README)
3. Identifying key files (entry points, configs, schemas)
4. Understanding current state (branch, recent commits)
5. Read project memory from memory.md (if it exists)

Provide a brief summary before proceeding.

---

## Step 2: Planning - Create Implementation Plan

Create a detailed implementation plan for the feature: **$ARGUMENTS**

1. Analyze existing codebase patterns
2. Research external documentation if needed
3. Check memory.md for related past experiences (if it exists)
4. Design implementation approach
5. Break down into step-by-step tasks
6. Save plan to `requests/[feature-name]-plan.md`

**IMPORTANT**: Note the feature name and plan file path for the next step.

---

## Step 3: Execute - Implement the Feature

Implement the feature from the plan document created in Step 2.

1. Read the ENTIRE plan
2. Check memory.md for warnings about affected files (if it exists)
3. Execute every task in order
4. Create all tests specified
5. Run all validation commands
6. Fix any issues until everything passes

---

## Step 4: Commit - Save Changes

Create a git commit for all changes:

1. Review git status and diff
2. Analyze changes for commit type
3. Create conventional commit message
4. Stage and commit
5. Update memory.md with lessons learned (if it exists)

---

## Step 5: Create Pull Request

Automatically create a PR to complete the feature delivery:

1. **Check current branch**:
   ```bash
   CURRENT_BRANCH=$(git branch --show-current)
   BASE_BRANCH=$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5)
   ```

2. **Push the branch** (if not already pushed):
   ```bash
   git push -u origin $CURRENT_BRANCH
   ```

3. **Generate PR content** using the commit history and changes:
   - **Title**: Use conventional commit format from the commit message (first 72 chars)
   - **Description**:
     ```markdown
     ## Summary
     [Brief description of what was implemented - from $ARGUMENTS]

     ## Changes
     [Bullet points from the plan's implementation tasks]

     ## Test Plan
     - [x] All tests pass
     - [x] Validation commands executed successfully

     ## Related Plan
     See `requests/[feature-name]-plan.md` for full implementation details

     🤖 Generated with [Claude Code](https://claude.com/claude-code) via `/end-to-end-feature`
     ```

4. **Create the PR**:
   ```bash
   gh pr create --title "[title]" --body "[description]" --base $BASE_BRANCH
   ```

5. **Capture PR URL** and number from output

**Error Handling:**
- If `gh` CLI is not available, provide manual instructions
- If already on master/main, skip PR creation and warn user
- If PR already exists for this branch, skip and show existing PR URL

---

## Final Summary

After completing all 5 steps, provide:

### Feature Implementation Complete ✅

**Original Request**: $ARGUMENTS

**Steps Executed:**
1. ✅ Prime - Codebase context loaded
2. ✅ Planning - Plan created at `requests/[feature-name]-plan.md`
3. ✅ Execute - Feature implemented and validated
4. ✅ Commit - Changes committed to git
5. ✅ Pull Request - PR created and ready for review

**Outputs:**
- Plan document: `requests/[feature-name]-plan.md`
- Files created/modified: [list]
- Tests added: [list]
- Commit hash: [hash]
- **Pull Request**: #[PR number] - [PR URL]

**Next Steps:**
- CodeRabbit will review the PR automatically (if configured)
- Claude Code will auto-fix any issues (via claude-fix-coderabbit.yml)
- Review and merge when ready

**Note**: This command maximizes memory.md usage — every step reads or writes the memory file, creating a compounding knowledge loop across sessions.
