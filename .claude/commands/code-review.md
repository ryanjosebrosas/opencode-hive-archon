---
description: Technical code review for quality and bugs
---

Perform technical code review on recently changed files.

## Review Mode Selection

**If custom review agents exist** in `.claude/agents/`: Use **Parallel Review** (4 agents, 40-50% faster)
**If not**: Use **Standard Review** (single-agent sequential)

```bash
ls .claude/agents/code-review-*.md 2>/dev/null | wc -l
```

---

## PARALLEL REVIEW MODE (Preferred)

Launch four Task agents simultaneously:

1. **@code-review-type-safety** — Type annotations, type checking, proper typing
2. **@code-review-security** — Vulnerabilities, exposed secrets, injection, auth issues
3. **@code-review-architecture** — Pattern compliance, layering, DRY/YAGNI, conventions
4. **@code-review-performance** — N+1 queries, algorithm efficiency, memory issues

All agents review ALL changed files from their specialized perspective. After completion: combine results, deduplicate, sort by severity (Critical → Major → Minor). Save to `requests/code-reviews/[feature-name]-review.md`.

**Archon** (if available): `manage_task("update", task_id="...", status="done")` for code review task.

---

## STANDARD REVIEW MODE (Fallback)

### Step 1: Gather Context

Read @CLAUDE.md and project README for standards.

### Step 2: Examine Changes

```bash
git status
git diff HEAD
git diff --stat HEAD
git ls-files --others --exclude-standard
```

Read each changed file in its entirety for full context.

### Step 3: Analyze Each File

Check for: logic errors, security issues, performance problems, code quality (DRY, naming, types), standards compliance (CLAUDE.md conventions, linting, testing patterns).

### Step 4: Verify Issues

Run specific tests for issues found. Confirm type errors are legitimate. Validate security concerns with context.

---

## Output Format (Both Modes)

Save to: `requests/code-reviews/[feature-name]-review.md`

### Review Summary

- **Mode**: Parallel / Standard
- **Files Modified/Added/Deleted**: counts
- **Total Findings**: X (Critical: Y, Major: Z, Minor: W)

### Findings by Severity

```yaml
severity: critical|major|minor
category: Type Safety|Security|Architecture|Performance|Logic|Quality
file: path/to/file:line
issue: [one-line description]
detail: [why this is a problem]
suggestion: [how to fix]
```

### Security Alerts

If CRITICAL security issues found, list separately with attack vector, impact, and remediation.

### Summary Assessment

- Overall: Pass / Needs minor fixes / Needs revision / BLOCKED - critical issues
- Recommended action: Commit as-is / Fix minor issues / Major rework needed

---

## Important

- Be specific (line numbers, not vague complaints)
- Focus on real bugs, not style preferences
- Suggest fixes, don't just complain
- Flag security issues as CRITICAL
- In parallel mode, deduplicate across agents
