---
description: Automated review → fix → review loop until clean
agent: build
---

# Code Loop: Automated Fix Loop

## Purpose

Automates the fix loop workflow:
```
/code-review → /planning (fix-slice) → /execute (fix plan) → /code-review
```

Runs until all issues are fixed or unfixable error detected.

**Next step after clean exit:** Run `/final-review` to summarize all changes and get human approval, then `/commit`.

Slice completion rule:
- A slice is considered complete only when code review returns no Critical/Major issues (or user explicitly accepts remaining minor issues).
- Start the next slice only after this completion condition.

Incremental rule:
- Keep each loop focused on one concrete outcome.
- If fixes spread into unrelated domains, stop and split into a follow-up loop/plan.

## Usage

```
/code-loop [feature-name]
```

- `feature-name` (optional): Used for commit message and report file

---

## Pre-Loop: Archon RAG Context Load

Before starting the review loop, gather relevant documentation context from Archon RAG to inform the review:

1. **Check Archon availability**: Call `rag_get_available_sources()`. If unavailable, skip RAG steps and proceed.
2. **Search for relevant patterns**: Based on the feature/files being reviewed, run 1-3 targeted RAG searches:
   - `rag_search_knowledge_base(query="<technology or pattern keywords>")` — find docs for libraries used in changed files
   - `rag_search_code_examples(query="<pattern keywords>")` — find reference implementations
3. **Pass context to code-review agent**: Include relevant RAG findings in the review prompt so the agent can cross-reference against curated documentation.

**Keep RAG queries SHORT** (2-5 keywords). Only search for technologies/patterns that appear in the changed files.

If Archon is unavailable, proceed without RAG context — the code-review agent has its own RAG access as fallback.

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

## Multi-Model Dispatch in Loop

The `dispatch` tool sends prompts to other AI models. In the code-loop context, use it for:

1. **Multi-model review** — get additional review perspectives beyond the primary code-review agent
2. **Fix delegation** — dispatch fix implementation to fast models while you orchestrate

**This is optional.** If `opencode serve` is not running, skip all dispatch steps and run the loop normally.

### Review Dispatch (during step 1 of each iteration)

After the primary `/code-review` runs, consider dispatching the changed code to a second model for additional findings:

**When to dispatch a second review:**
- First iteration (fresh code, worth getting a second perspective)
- When review finds security-sensitive issues (get confirmation)
- When review finds 0 issues (sanity check — did we miss something?)
- When changes touch multiple interconnected files

**When to skip dispatch review:**
- Later iterations with only minor fixes remaining
- When previous dispatch review added no new findings
- When changes are trivial (typos, formatting)

**How to dispatch a review:**
```
dispatch({
  taskType: "code-review",
  prompt: "Review this code change for bugs, security issues, and quality problems:\n\n{paste git diff or relevant code snippets}\n\nContext: {what was changed and why}\n\nReport findings as:\n- Critical: {description}\n- Major: {description}\n- Minor: {description}\n\nIf no issues found, say 'No issues found.'"
})
```

**Merging dispatch findings with primary review:**
- Deduplicate — if dispatch finds the same issue as primary review, note "confirmed by {model}"
- Add new findings to the review artifact with source attribution
- Include in the fix plan so `/execute` addresses them

### Fix Dispatch (during step 4 of each iteration)

When running `/execute` to fix review findings, the execute agent may dispatch subtasks to other models.
This is governed by `/execute`'s own dispatch guidance (section 1.7).

Additionally, if you have simple, isolated fixes (e.g., "add missing null check at line 42", "rename variable X to Y"):

**How to dispatch a simple fix:**
```
dispatch({
  taskType: "simple-fix",
  prompt: "Fix this code issue:\n\nFile: {filename}\nIssue: {description from review}\nCurrent code:\n```\n{paste current code}\n```\n\nReturn the fixed code only, no explanations."
})
```

**Rules for fix dispatch:**
- Only dispatch fixes you can verify (you must review the result before applying)
- Never dispatch architectural changes or multi-file refactors
- If the dispatched fix looks wrong, implement it yourself
- Track dispatched fixes in the loop report: "Fix dispatched to {model}: {description}"

### Model Routing for Loop Tasks (5-Tier Cascade)

| Task | Tier | taskType | Provider/Model | Cost |
|------|------|----------|----------------|------|
| First code review | T2 | `code-review` | `zai-coding-plan/glm-5` | FREE |
| Second review opinion | T3 | `second-validation` | `ollama-cloud/deepseek-v3.2` | FREE |
| Simple fix generation | T1a | `simple-fix` | `bailian-coding-plan/qwen3-coder-next` | FREE |
| Complex fix generation | T1c | `complex-fix` | `bailian-coding-plan/qwen3.5-plus` | FREE |
| Security-focused review | T2 | `security-review` | `zai-coding-plan/glm-5` | FREE |
| Near-final code review | T4 | `codex-review` | `openai/gpt-5.3-codex` | PAID (cheap) |
| Final critical review | T5 | `final-review` | `anthropic/claude-sonnet-4-6` | PAID (last resort) |

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
   - Save to: `requests/code-reviews/{feature}-review #{N}.md`

2. **Check findings:**
   - **If 0 issues:** → Exit loop, go to commit
   - **If only Minor issues:** → Ask user: "Fix minor issues or skip to commit?"
   - **If Critical/Major issues:** → Continue to fix step

3. **Create fix plan via `/planning` (required)**
    - Input: latest review artifact `requests/code-reviews/{feature}-review #{N}.md`
    - Output: `requests/{feature}-review-fixes #<n>.md`
    - The fix plan must define a single bounded fix slice (Critical/Major first)
    - If the review includes RAG-informed findings, include the RAG source references in the fix plan so `/execute` has the documentation context

4. **Run `/execute` with the fix plan (required)**
   - Input: `requests/{feature}-review-fixes #<n>.md`
   - Never run `/execute` directly on raw review findings
   - After this fix pass succeeds, mark the source review file `.done.md`
     - Example: `requests/code-reviews/{feature}-review #{N}.md` -> `requests/code-reviews/{feature}-review #{N}.done.md`

5. **Run full validation for this slice:**
   - Run lint/style checks
   - Run type safety checks
   - Run unit tests
   - Run integration tests
   - Run manual verification steps from the active plan
   - Use project-specific commands from the current plan/repo (not JS-only defaults)

6. **Check for unfixable errors:**
   - Command not found → Stop, report missing tool
   - Dependency errors → Stop, report "run npm install"
   - Syntax errors blocking analysis → Stop, report file:line
   - If no unfixable errors → Continue to next iteration

### Loop Exit Conditions

| Condition | Action |
|-----------|--------|
| 0 issues + validation passes | → Hand off to `/final-review` |
| Only Minor issues | → Fix if quick and safe; otherwise ask user whether to defer |
| Unfixable error detected | → Stop, report what's blocking |

### User Interruption Handling

**If user presses Ctrl+C during iteration:**
1. Save current checkpoint to `requests/code-loops/{feature}-interrupted #<n>.md`
2. Report:
   ```
   ⚠️  Loop interrupted at iteration {N}

   Progress:
   - Issues fixed: X (Critical: Y, Major: Z)
   - Issues remaining: A (Critical: B, Major: C)
   - Last checkpoint: requests/code-loops/{feature}-checkpoint #{N}.md

   Resume: Run `/code-loop {feature}` again — will continue from checkpoint
   ```
3. Clean exit (no partial commits)

**If context compacts (session memory limit):**
1. Last checkpoint is already saved (from checkpoint system)
2. Next iteration reads checkpoint and continues
3. Report: "Resumed from checkpoint {N}"

---

## Handoff (When Loop Exits Clean)

1. **Report completion:**
   ```
   Code loop complete

   Iterations: N
   Issues fixed: X (Critical: Y, Major: Z, Minor: W)
   Status: Ready for /final-review
   ```

2. **Next step:** Tell the user to run `/final-review` for a summary + approval gate, then `/commit`.
   - Do NOT auto-commit. The user must approve via `/final-review` first.

---

## Output Report

Working filename: `requests/code-loops/{feature}-loop-report #<n>.md`

Write the loop report to the working filename as the loop progresses. Do NOT use `.done.md` until the completion sweep.

Done marker rule:
- Mark done status in filenames only by appending `.done` before `.md`.
- Do not modify markdown H1/title text just to indicate completion.
- On clean exit (0 issues or user accepts), perform a **completion sweep** as the final step before commit:
  1. Rename the loop report: `{feature}-loop-report #<n>.md` → `{feature}-loop-report #<n>.done.md`
  2. Rename the last review file: `{feature}-review #<n>.md` → `{feature}-review #<n>.done.md`
  3. Rename any fix plan artifacts that were fully applied: `.md` → `.done.md`
- On interrupted/stopped exit, leave filenames as `.md` (not done).

Numbering rule:
- Use hash numbering for loop outputs to match request artifact convention.
- Final report filename after sweep: `requests/code-loops/{feature}-loop-report #1.done.md` (or next available number).

### Loop Summary

- **Feature**: {feature-name}
- **Iterations**: N
- **Final Status**: Clean / Stopped (unfixable error) / Stopped (user interrupt) / Stopped (user choice)
- **Dispatch used**: {yes — N dispatches across M iterations / no}

### Issues Fixed by Iteration

| Iteration | Critical | Major | Minor | Total | Dispatches |
|-----------|----------|-------|-------|-------|------------|
| 1 | X | Y | Z | T | N |
| 2 | X | Y | Z | T |
| ... | ... | ... | ... | ... |
| N (final) | X | Y | Z | T |

### Checkpoints Saved

- `requests/code-loops/{feature}-checkpoint #1.md` — Iteration 1 progress
- `requests/code-loops/{feature}-checkpoint #2.md` — Iteration 2 progress
- ...
- **If interrupted:** `requests/code-loops/{feature}-interrupted #<n>.md` — Resume point

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
