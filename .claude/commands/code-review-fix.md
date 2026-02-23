---
description: "I ran a code review and found these issues:"
argument-hint: [review-path-or-description] [scope]
---

# Fix Issues from Code Review

## Input

- **Review source** ($1): File path to code review report, OR inline description of issues
- **Scope** ($2, optional): Severity filter (`critical`, `major`, `minor`, `critical+major`) or file path pattern

Review input: $ARGUMENTS

## Step 1: Load the Review

**File path**: Read and parse by standard format (severity/category/file/issue/detail/suggestion).
**Inline description**: Treat as issue(s), default severity: major.
**No input**: Check `requests/code-reviews/` for most recent review. If none, ask user.

## Step 2: Categorize and Prioritize

Group findings by severity: Critical → Major → Minor.

**Apply scope filter** (if provided): `critical` / `critical+major` / `major` / file path pattern. Default: fix all, starting with critical.

Report triage: "Found X issues: Y critical, Z major, W minor. Fixing in order: critical → major → minor."

## Step 3: Selectivity Principle

Before fixing each issue, evaluate whether it SHOULD be fixed. May choose NOT to fix issues that are: documented as acceptable, out of scope, would require architectural changes, style preferences not bugs, or false positives. **Explain every skip.** Default bias: fix it. Only skip with genuine reason.

## Step 4: Fix Issues (One at a Time)

For each issue:

**a.** Read the **entire affected file** — understand context, function purpose, call sites. Check if issue is part of a larger pattern.

**b.** State what's wrong, why it's a problem. Reference the finding (severity, file:line).

**c.** Apply **minimal change** to resolve. Don't refactor surrounding code or add features. Fix all affected files if change propagates. Preserve existing style.

**d.** Verify: run task's VALIDATE command if available, check for new issues (type errors, imports), run affected tests.

## Step 5: Post-Fix Validation

After ALL fixes, run project validation in pyramid order: linting → type checking → tests. Fix regressions, re-run until all pass. Note if validation tools aren't configured.

## Step 6: Output Summary

| Severity | Found | Fixed | Skipped |
|----------|-------|-------|---------|
| Critical | X | X | X |
| Major | X | X | X |
| Minor | X | X | X |
| **Total** | **X** | **X** | **X** |

### Issues Fixed
- **[severity]** `file:line` — issue → fix applied

### Issues Skipped
- **[severity]** `file:line` — issue → reason for skipping

### Validation Results
- Linting / Type checking / Tests: pass/fail/not configured

### Next Steps
- All critical+major fixed and validation passes → `/commit`
- Issues remain → `/code-review-fix` again with narrower scope
- Architectural issues skipped → create follow-up task

**Archon** (if available): `manage_task("update", task_id="...", status="done")` for code review fix task.

## Important Rules

- **Severity order mandatory** — critical before major before minor
- **Selectivity over completeness** — a thoughtful skip is better than a harmful fix
- **Minimal changes** — fix the issue, nothing more. Surgery, not renovation.
- **Explain everything** — every fix and every skip gets a clear explanation
- **Never auto-fix all** — evaluate each issue individually
