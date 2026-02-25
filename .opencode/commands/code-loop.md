---
description: Automated review → fix → review loop until clean, then commit
agent: build
---

# Code Loop: Automated Fix Loop

## Purpose

Automates the fix loop workflow:
```
/code-review → /execute (fix) → /code-review → /commit
```

Runs until all issues are fixed or unfixable error detected.

## Usage

```
/code-loop [feature-name]
```

- `feature-name` (optional): Used for commit message and report file

---

## Pre-Loop UBS Scan

```bash
ubs --staged --fail-on-warning
```

**If UBS finds critical issues:**
- Report: "UBS found critical bugs. Fixing first..."
- Run `/execute` with UBS findings
- Re-run UBS until clean

**If UBS clean:**
- Proceed to review loop

---

## Fix Loop

### Checkpoint System (Context Compaction)

At the start of EACH iteration, save progress checkpoint:
```markdown
**Checkpoint {N}** - {timestamp}
- Issues remaining: X (Critical: Y, Major: Z)
- Last fix: {what was fixed}
- Validation: {lint/test results}
```

**Why:** If context compacts or session interrupts, work can be recovered from last checkpoint.

### Iteration 1-N

1. **Run `/code-review`**
   - Save to: `requests/code-reviews/{feature}-review-{N}.md`

2. **Check findings:**
   - **If 0 issues:** → Exit loop, go to commit
   - **If only Minor issues:** → Ask user: "Fix minor issues or skip to commit?"
   - **If Critical/Major issues:** → Continue to fix step

3. **Run `/execute` (fix mode)**
   - Input: `requests/code-reviews/{feature}-review-{N}.md`
   - Fixes issues in priority order

4. **Run validation:**
   ```bash
   # Linting
   npm run lint 2>/dev/null || echo "No lint configured"
   
   # Type check
   npm run typecheck 2>/dev/null || echo "No typecheck configured"
   
   # Tests
   npm test 2>/dev/null || echo "No tests configured"
   ```

5. **Check for unfixable errors:**
   - Command not found → Stop, report missing tool
   - Dependency errors → Stop, report "run npm install"
   - Syntax errors blocking analysis → Stop, report file:line
   - If no unfixable errors → Continue to next iteration

### Loop Exit Conditions

| Condition | Action |
|-----------|--------|
| 0 issues + validation passes | → Commit ✓ |
| Only Minor issues | → Ask user: "Fix or skip?" |
| Unfixable error detected | → Stop, report what's blocking |

### User Interruption Handling

**If user presses Ctrl+C during iteration:**
1. Save current checkpoint to `requests/code-loops/{feature}-interrupted.md`
2. Report:
   ```
   ⚠️  Loop interrupted at iteration {N}

   Progress:
   - Issues fixed: X (Critical: Y, Major: Z)
   - Issues remaining: A (Critical: B, Major: C)
   - Last checkpoint: requests/code-loops/{feature}-checkpoint-{N}.md

   Resume: Run `/code-loop {feature}` again — will continue from checkpoint
   ```
3. Clean exit (no partial commits)

**If context compacts (session memory limit):**
1. Last checkpoint is already saved (from checkpoint system)
2. Next iteration reads checkpoint and continues
3. Report: "Resumed from checkpoint {N}"

---

## Commit (When Loop Exits Clean)

1. **Run `/commit`**
   - Message: `fix({feature}): address code review feedback`

2. **Report completion:**
   ```
   ✅ Code loop complete
   
   Iterations: N
   Issues fixed: X (Critical: Y, Major: Z, Minor: W)
   Commit: {hash}
   ```

---

## Output Report

Save to: `requests/code-loops/{feature}-loop-report.md`

### Loop Summary

- **Feature**: {feature-name}
- **Iterations**: N
- **Final Status**: Clean / Stopped (unfixable error) / Stopped (user interrupt) / Stopped (user choice)

### Issues Fixed by Iteration

| Iteration | Critical | Major | Minor | Total |
|-----------|----------|-------|-------|-------|
| 1 | X | Y | Z | T |
| 2 | X | Y | Z | T |
| ... | ... | ... | ... | ... |
| N (final) | X | Y | Z | T |

### Checkpoints Saved

- `requests/code-loops/{feature}-checkpoint-1.md` — Iteration 1 progress
- `requests/code-loops/{feature}-checkpoint-2.md` — Iteration 2 progress
- ...
- **If interrupted:** `requests/code-loops/{feature}-interrupted.md` — Resume point

### Validation Results

```bash
# Output from lint/typecheck/tests
```

### Commit Info

- **Hash**: {commit-hash}
- **Message**: {full message}
- **Files**: X changed, Y insertions, Z deletions

---

## Error Handling

**Distinguish Fixable vs Unfixable Errors:**

**Fixable (continue loop):**
- Code review finds issues → `/execute` fixes them
- Lint errors → `/execute` fixes formatting
- Type errors (simple) → `/execute` adds type annotations
- Test failures → `/execute` fixes logic

**Unfixable (stop loop, report to user):**
- Command not found (`npm`, `node`, lint tool not installed)
- Missing dependencies (`npm install` needed)
- Syntax errors preventing parsing
- Circular dependencies requiring refactor
- Missing files or broken imports
- Architecture-level changes needed

**If `/code-review` fails:**
- Retry once
- If still fails: Stop, report error

**If `/execute` (fix) fails:**
- Report which issues couldn't be fixed
- Check if unfixable (missing tools) or temporary (agent timeout)
- If unfixable: Stop loop, report blocking issue
- If temporary: Continue to next iteration

**If `/commit` fails:**
- Report: "Commit failed (pre-commit hook?)"
- Show error from git
- Don't retry automatically

**If UBS fails:**
- Report: "UBS scan failed"
- Continue without UBS (agent review will catch issues)

**If user interrupts (Ctrl+C):**
- Save checkpoint immediately
- Report progress and remaining issues
- Allow resume from checkpoint
