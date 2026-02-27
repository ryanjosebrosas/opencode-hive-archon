---
description: Run a generalist code review on recent changes or specified files
agent: build
---

# Code Review: Find Bugs, Security Issues, and Quality Problems

Run a comprehensive code review using the code-review agent. Reports findings only — does NOT implement fixes.

## Usage

```
/code-review [target]
```

`$ARGUMENTS` — What to review:
- Empty (default): review all uncommitted changes (`git diff` + `git diff --cached`)
- File path: review a specific file
- `last-commit`: review changes in the most recent commit

---

## Pipeline Position

Used manually, or inside the `/code-loop` automated review-fix cycle:

```
/code-review → /execute (fix) → /code-review → /commit
```

---

## Step 1: Determine Scope

**If no arguments:**
```bash
git diff --name-only
git diff --cached --name-only
```
Review all changed files.

**If file path provided:**
Review that specific file.

**If `last-commit`:**
```bash
git diff HEAD~1 --name-only
```
Review files changed in the last commit.

If no changes found, report: "No changes to review." and stop.

---

## Step 2: Gather Context

Before reviewing, gather supporting context:

1. **Read `memory.md`** — check for relevant gotchas, patterns, past decisions about affected files
2. **Read affected files** — full content, not just diffs
3. **Check patterns** — how do similar files in the project handle the same concerns?

### Archon RAG (Optional)

If Archon MCP is available, search for relevant documentation:
- `rag_search_knowledge_base(query="2-5 keywords")` for library best practices
- `rag_search_code_examples(query="2-5 keywords")` for reference implementations

Keep queries SHORT (2-5 keywords). If Archon unavailable, proceed with local context.

---

## Step 3: Review

Check for issues at three severity levels:

### Critical (blocks commit)
- Security vulnerabilities (SQL injection, XSS, hardcoded secrets)
- Logic errors (null dereference, off-by-one, race conditions)
- Type safety issues (unsafe casts, missing null checks)

### Major (fix soon)
- Performance issues (N+1 queries, O(n^2), memory leaks)
- Architecture violations (layer breaches, tight coupling)
- Error handling gaps (uncaught exceptions, silent failures)
- Documentation mismatches with Archon RAG sources

### Minor (consider fixing)
- Code quality (DRY violations, unclear naming)
- Missing tests for new functionality
- Documentation gaps

---

## Step 4: Dispatch for Second Opinions (Optional)

For security-sensitive or architecturally complex changes, use the dispatch tool to get a second opinion from another model:

| Concern | taskType | Model (FREE) |
|---------|----------|--------------|
| Security review | `security-review` | zai-coding-plan/glm-5 |
| Architecture | `research` | bailian-coding-plan-test/qwen3.5-plus |
| Logic verification | `logic-verification` | bailian-coding-plan-test/qwen3-coder-plus |

If `opencode serve` is not running, skip dispatch and proceed with your own review.

---

## Step 5: Report Findings

Present findings in this format:

```
CODE REVIEW: {scope description}
================================

Critical (blocks commit):
- `file:line` — {issue}
  Why: {explanation}
  Fix: {suggestion}

Major (fix soon):
- `file:line` — {issue}
  Why: {explanation}
  Fix: {suggestion}

Minor (consider):
- `file:line` — {issue}

RAG-Informed:
- {findings backed by documentation, or "No RAG sources applicable"}

Dispatch Second Opinions:
- {findings from other models, or "No dispatch used"}

Summary: {X} critical, {Y} major, {Z} minor
Recommendation: {PASS / FIX CRITICAL / FIX MAJOR}
```

---

## Step 6: Next Steps

Based on severity:

- **All clear**: "No issues found. Ready to commit with `/commit`."
- **Minor only**: "Minor issues found. Commit at your discretion, or fix first."
- **Major/Critical**: "Found issues that should be fixed. Run `/execute` with the findings above, then re-review."

---

## Notes

- This command is **read-only** — it does NOT modify any files
- The code-review agent (`.opencode/agents/code-review.md`) provides the detailed review logic
- For automated review-fix loops, use `/code-loop` instead
- Single sequential review — no parallel agents
