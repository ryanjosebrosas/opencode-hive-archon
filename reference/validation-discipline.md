# Validation Discipline: Testing, Code Review & System Evolution

This guide explains **how to validate AI-generated code systematically, use code review and system review commands effectively, and evolve your system through validation feedback** — covering the 5-Level Validation Pyramid, the four validation commands, parallel code review with agents, and the critical distinction between fixing code bugs vs fixing process bugs.

---

## 1. Why Validation Is a Discipline

### The Validation Problem

AI coding agents are remarkably productive — but they also produce subtle bugs, skip edge cases, and drift from requirements. Without systematic validation, you're rolling the dice on code quality with every implementation.

The PIV Loop places validation as the THIRD pillar for a reason: it's not an afterthought, it's a gate. Implementation without validation is just hope.

### The Core Insight

> **"Don't just fix the bug. Fix the system that allowed the bug."**

When validation catches an issue, you have two choices:
1. **Fix the code** — solve the immediate problem
2. **Fix the system** — update commands, templates, or rules to prevent the category of problem

Choice #1 is necessary. Choice #2 is what compounds. The validation discipline is about making choice #2 a habit.

### What This Guide Covers

- The 5-Level Validation Pyramid — a gated progression from syntax to human review
- Four validation commands — `/code-review`, `/code-review-fix`, `/execution-report`, `/system-review`
- Parallel code review — using 4 specialized agents for 40-50% faster reviews
- Validation as feedback — the meta-reasoning loop that evolves your system
- The selectivity principle — why you shouldn't blindly follow all AI recommendations
- Practical workflows — when to use which command and in what order

---

## 2. The 5-Level Validation Pyramid

Each level gates the next. Don't proceed to the next level if the current one fails. This prevents wasting time running expensive integration tests when a linting error would catch the issue in seconds.

```
        Level 5: Human Review
              (Alignment with intent)
                    |
        Level 4: Integration Tests
              (System behavior)
                    |
        Level 3: Unit Tests
              (Isolated logic)
                    |
        Level 2: Type Safety
              (Type checking)
                    |
        Level 1: Syntax & Style
              (Linting, formatting)
```

### Level 1 — Syntax & Style

**What it catches**: Syntax errors, formatting inconsistencies, import issues, style violations.

**Tools**: Linters (`ruff`, `eslint`, `biome`), formatters (`black`, `prettier`), auto-fix on save.

**When to run**: After every file write. Most editors and AI tools can do this automatically.

**Why it matters**: The fastest, cheapest check. If your code doesn't parse, nothing else matters. Running linting first prevents false positives at higher levels (a type checker may report errors that are actually just syntax issues).

**Common commands**:
```bash
# Python
ruff check . --fix
ruff format .

# TypeScript/JavaScript
npx eslint . --fix
npx prettier --write .

# Go
go fmt ./...
golangci-lint run
```

### Level 2 — Type Safety

**What it catches**: Type mismatches, missing return types, incorrect function signatures, null/undefined handling.

**Tools**: Type checkers (`mypy`, `pyright`, `tsc --noEmit`).

**When to run**: After implementation, before tests. Type errors can cause tests to fail for the wrong reason.

**Why it matters**: Catches an entire category of bugs that tests might miss — especially in dynamically typed languages where type hints exist but aren't enforced.

**Common commands**:
```bash
# Python
mypy app/ --strict
pyright

# TypeScript
npx tsc --noEmit

# Go (built into compiler)
go build ./...
```

**AI-specific pitfall**: AI agents frequently generate code that *looks* correct but has subtle type issues — wrong generic parameters, missing optional markers, incorrect union types. Type checking catches these before runtime.

### Level 3 — Unit Tests

**What it catches**: Logic errors, edge cases, incorrect calculations, broken algorithms.

**Tools**: Test frameworks (`pytest`, `jest`, `vitest`, `go test`).

**When to run**: After type checking passes. Run focused tests first (just the feature), then the full suite.

**Why it matters**: Verifies that individual functions and classes work correctly in isolation.

**Common commands**:
```bash
# Python
pytest tests/unit/ -v
pytest tests/ -k "test_feature_name"

# TypeScript/JavaScript
npx jest --testPathPattern="feature-name"
npx vitest run

# Go
go test ./... -v
```

**Critical pitfall — AI mocking tests to pass**: AI agents will sometimes write tests that mock so heavily they test nothing real. Watch for:
- Tests that mock the function being tested (circular)
- Tests with no real assertions (just `assert mock.called`)
- Tests where all external dependencies are mocked away
- Tests that pass trivially regardless of implementation

**Rule**: Reject mocks without justification. If you see a mock, ask: "What real behavior is this test verifying?" If the answer is "nothing," the test is fake.

### Level 4 — Integration Tests

**What it catches**: Component interaction bugs, database issues, API contract violations, race conditions.

**Tools**: Same test frameworks with integration markers, test databases, fixtures.

**When to run**: After unit tests pass. Uses more resources, takes longer, so run last.

**Why it matters**: Individual components can work perfectly in isolation but fail when combined. Integration tests verify the connections between components.

**Common commands**:
```bash
# Python (with markers)
pytest tests/integration/ -v
pytest -m integration

# TypeScript
npx jest --testPathPattern="integration"

# Docker-based
docker compose up -d test-db && pytest tests/integration/ && docker compose down
```

**Best practices**:
- Mock **external services** (Stripe, SendGrid) but not **internal components**
- Use test fixtures and factories for database setup
- Clean up after each test (use transactions or truncation)
- Run against a real test database, not mocks

### Level 5 — Human Review

**What it catches**: Architectural drift, intent misalignment, pattern violations, security oversights, over-engineering.

**How to do it**: Read the git diff. Compare implementation against the plan. Look at the big picture.

**When to do it**: After levels 1-4 pass. This is the final gate before merge/commit.

**Why it matters**: AI handles mechanical validation (levels 1-4). Humans judge strategic alignment — does this implementation actually solve the right problem the right way?

**What to look for**:
- Does the implementation match the plan? (Or did the AI drift?)
- Are the right patterns being followed? (Check against CLAUDE.md conventions)
- Is the approach sound architecturally? (Or is it a hack that will cause problems later?)
- Are there security concerns the automated checks missed?
- Is there unnecessary complexity? (YAGNI violations)

**The 80/20 of human review**: Focus on:
1. New files — these define new patterns
2. Public interfaces — API contracts, function signatures
3. Database changes — migrations, schema modifications
4. Security-sensitive code — auth, input validation, data access

---

## 3. The Four Validation Commands

The PIV Loop includes four dedicated validation commands. Each serves a different purpose and has different optimal timing.

### /code-review — Technical Code Review

**Purpose**: Find bugs, security issues, performance problems, and pattern violations in changed files.

**When to run**: After implementation, before commit. Works on uncommitted changes.

**What it does**:
1. Gets the git diff of changed files
2. Reads the full content of each changed file
3. Reviews for: correctness, security, performance, patterns
4. Produces a structured report with severity levels (Critical/Major/Minor)
5. Saves the report to `requests/code-reviews/`

**Output format**: Structured findings with severity, location (file:line), issue description, evidence (code snippet), and suggested fix.

**Key design decisions**:
- Reviews **changed files only** — not the entire codebase
- Reads the **full file**, not just the diff — because context matters
- Produces a **saved artifact** — consumed by `/code-review-fix` downstream
- Optimized for **agent consumption** — explicit file paths, exact line numbers

### /code-review-fix — Fix Issues from Review

**Purpose**: Take a code review report and fix the identified issues.

**When to run**: After `/code-review`, before commit.

**What it does**:
1. Reads the code review report
2. Processes issues by severity (Critical first, then Major, then Minor)
3. Fixes each issue with minimal changes
4. Optionally scopes fixes (all files, specific files, or specific severity)

**Key design decisions**:
- Accepts a **scope parameter** — fix everything, or just critical issues
- Fixes in **severity order** — critical issues first, don't waste time on minor issues if critical ones exist
- **Minimal changes** — fix the issue, don't refactor surrounding code

**Usage patterns**:
```bash
# Fix all issues
/code-review-fix requests/code-reviews/feature-review.md

# Fix only critical and major issues
/code-review-fix requests/code-reviews/feature-review.md critical+major

# Fix issues in specific files only
/code-review-fix requests/code-reviews/feature-review.md src/auth/
```

### /execution-report — Implementation Report

**Purpose**: Document what actually happened during implementation for comparison against the plan.

**Critical constraint**: Must run in the **SAME conversation context** as `/execute`. If you start a new conversation, the AI loses memory of what it did and the report becomes generic guesswork.

**When to run**: Immediately after `/execute` completes, BEFORE commit or context switch.

**What it does**:
1. Recalls what was implemented (from current conversation memory)
2. Lists files created, modified, and deleted
3. Documents any deviations from the plan
4. Notes any issues encountered and how they were resolved
5. Records validation results

**Why it must be same-context**: The report is accurate because the AI remembers exactly what it did. In a fresh context, the AI would have to infer from file diffs — missing the *why* behind decisions, workarounds tried and rejected, and deviations from the plan.

**Output**: Saved to `requests/execution-reports/` for later use by `/system-review`.

### /system-review — Divergence Analysis

**Purpose**: Compare plan vs implementation to find **process bugs** — not code bugs.

**When to run**: After commit, when you want to evolve the system. Not every loop — only when something felt wrong.

**What it does**:
1. Reads the structured plan
2. Reads the execution report
3. Compares: What was planned vs what actually happened?
4. Identifies divergences and categorizes them:
   - **Plan gap** — plan was missing information → fix the planning command/template
   - **Execution drift** — AI deviated from plan → fix the execute command
   - **Validation miss** — issue not caught → fix validation commands
   - **System gap** — no command covers this scenario → create new command
5. Recommends specific system improvements

**Key insight**: `/code-review` finds bugs in **code**. `/system-review` finds bugs in **process**. Different purposes, different commands, different timing.

**When NOT to use it**: Don't run system review after every loop. Use it when:
- Implementation took significantly longer than expected
- You had to manually intervene multiple times
- The AI made the same type of mistake repeatedly
- The output quality was noticeably different from previous runs

---

## 4. The Complete Validation Workflow

### Recommended Sequence

```
/execute [plan] → /execution-report → /code-review → /code-review-fix → /commit
```

**Step-by-step**:
1. **`/execute [plan]`** — Implement the feature from the structured plan
2. **`/execution-report`** — Document what happened (SAME context, before commit)
3. **`/code-review`** — Technical review of changed files
4. **`/code-review-fix`** — Fix issues found in review
5. **`/commit`** — Create the git commit

**Optional system evolution** (after commit):
```
/system-review [plan] [report]
```

### When to Skip Steps

Not every loop needs the full workflow:

| Situation | Recommended Workflow |
|-----------|---------------------|
| Simple bug fix | `/execute` → `/commit` |
| Standard feature | `/execute` → `/code-review` → `/code-review-fix` → `/commit` |
| Complex feature | Full workflow including `/execution-report` |
| Repeated quality issues | Full workflow + `/system-review` |
| Documentation only | `/execute` → `/commit` (no code review needed) |

### Timing Matters

The order is not arbitrary:

- **Execution report before commit**: The AI remembers what it did
- **Code review before fix**: You need findings before you can fix them
- **Fix before commit**: Don't commit known issues
- **System review after commit**: You need the final artifact (committed code) to compare against the plan

---

## 5. Parallel Code Review with Agents

### The Pattern

Instead of one agent reviewing everything sequentially, four specialized agents review in parallel — each focused on a specific concern:

```
Main Agent
  ├─> Type Safety Agent      (types, annotations, type errors)
  ├─> Security Agent         (vulnerabilities, injection, secrets)
  ├─> Architecture Agent     (patterns, conventions, structure)
  └─> Performance Agent      (queries, algorithms, memory)
       ↓ (results return in parallel)
Main Agent combines findings → unified report
```

### Why Parallel

**Speed**: 40-50% faster than sequential review. Four agents working simultaneously instead of one doing four passes.

**Depth**: Each agent is specialized — its entire system prompt focuses on one concern. A security-focused agent catches vulnerabilities that a general reviewer might miss.

**Consistency**: Each agent follows a fixed analysis approach. No concern gets short-changed because the reviewer got tired or distracted.

### The Four Review Agents

| Agent | Focus | What It Checks |
|-------|-------|----------------|
| **code-review-type-safety** | Type annotations & checking | Missing types, incorrect types, type errors, generic issues |
| **code-review-security** | Security vulnerabilities | SQL injection, XSS, exposed secrets, auth bypass, OWASP top 10 |
| **code-review-architecture** | Design patterns & conventions | Layer violations, DRY, YAGNI, naming, file structure compliance |
| **code-review-performance** | Performance & scalability | N+1 queries, inefficient algorithms, memory leaks, unnecessary computations |

### Agent Output Format

Each agent returns structured findings that the main agent can parse and combine:

```markdown
## [AGENT-NAME] Review

### Critical
- **[file:line]**: Issue description
  - Evidence: `code snippet`
  - Fix: What to do

### Major
- ...

### Minor
- ...

### Summary
- Files reviewed: N
- Issues found: X critical, Y major, Z minor
```

**Key design element**: The output format includes an instruction to the main agent: "Do NOT start fixing issues without user approval." This prevents the main agent from automatically acting on all findings when the user just wanted a report.

### How to Activate

The 4 code review agents are pre-installed in `.claude/agents/`. The `/code-review` command automatically detects these agents and switches to parallel mode. If no agents are found, it falls back to single-agent sequential review.

### Customization

The pre-installed agents are generic. Customize for your project:

1. **Update context gathering** — reference your project's specific files and patterns
2. **Add project-specific checks** — e.g., check for `pytest` coverage in architecture agent
3. **Adjust severity thresholds** — what's "critical" varies by project
4. **Tune output format** — add fields relevant to your workflow

### When NOT to Use All Four

Pick agents based on the feature type:

| Feature Type | Agents to Use |
|--------------|---------------|
| New API endpoint | Security + Architecture + Performance |
| Frontend component | Type Safety + Architecture |
| Database migration | Security + Architecture + Performance |
| Bug fix | Type Safety + Security |
| Documentation | Skip parallel review entirely |

---

## 6. Validation as Feedback

### The Meta-Reasoning Loop

When validation catches an issue, don't just fix the code. Ask:

1. **What went wrong?** — Describe the specific issue
2. **Why did it happen?** — Was the plan unclear? Did the AI drift? Was the pattern undocumented?
3. **Where in the system should I fix it?** — Is this a plan issue, a command issue, a template issue, or a rules issue?
4. **How do I prevent this category of problem?** — What system change prevents recurrence?

### Where to Fix: Decision Framework

| Fix Location | When to Use | Example |
|---|---|---|
| **Global rules** (CLAUDE.md/sections) | Convention that applies to ALL tasks | "Always use structured logging" |
| **On-demand context** (reference/) | Task-type-specific guidance | "When building APIs, follow this contract pattern" |
| **Commands** (planning, execute, etc.) | Process/workflow issue | "Planning produces plans that are too long" |
| **Templates** (structured plan, PRD) | Output format/structure issue | "Plans are missing validation commands section" |
| **Vibe planning** (your prompts) | Research was incomplete or scope was wrong | "I didn't specify the auth method clearly enough" |

### The System Evolution Principle

> When a command produces suboptimal output, **update the command itself** — don't just one-off fix it.

This is the highest-leverage activity in the entire PIV Loop. Every system fix compounds:
- Fix the planning command once → every future plan is better
- Fix the execute command once → every future implementation is better
- Fix a template once → every future output matches the right format

**Two types of improvements**:
- **Plan updates** — fix the command/template for all future runs
- **One-off fixes** — fix the immediate output without changing the system

Always prefer plan updates. One-off fixes solve today; system updates solve forever.

### Practical Example

**Problem**: AI keeps writing 1500-line plans when you want 700-1000.

**Bad response**: "Make this plan shorter" (one-off fix)

**Good response**:
1. Ask the AI to analyze WHY the plan is long (meta-reasoning)
2. AI identifies: "The planning command has no line constraint, and the template encourages detailed task descriptions"
3. Add a `CRITICAL: Plan must be 700-1000 lines` constraint to the planning command
4. Add a conciseness guideline to the structured plan template
5. Now every future plan respects the constraint

### The Selectivity Principle

> **LLMs over-engineer recommendations. Be selective about which suggestions to implement.**

When `/system-review` or `/code-review` produces recommendations, evaluate each one critically:

- **Does this solve a real problem I've experienced?** (Not a hypothetical one)
- **Will this simplify or complicate the system?** (Prefer simplification)
- **Is this a pattern I'll use repeatedly?** (Not a one-time scenario)
- **Does the cost of the fix justify the benefit?** (Adding complexity to prevent a rare issue isn't worth it)

AI has a bias toward adding safety nets, abstractions, and edge case handling. Often the right answer is "this is fine as-is" or "fix it when it actually becomes a problem."

**Rule of thumb**: If `/system-review` suggests 10 improvements, implement 2-3 that address problems you've actually experienced. Ignore the rest until they become real.

---

## 7. Embedded Validation in Plans

### Task-Level Validation

Every task in a structured plan should include its own validation step. The `VALIDATE` field in the task format ensures validation isn't an afterthought:

```markdown
### UPDATE src/auth/middleware.py

- **IMPLEMENT**: Add JWT token validation middleware
- **PATTERN**: Follow existing middleware pattern in `src/middleware/base.py`
- **IMPORTS**: `from jose import jwt`, `from app.core.config import settings`
- **GOTCHA**: Token expiry check must use UTC, not local time
- **VALIDATE**: `pytest tests/auth/test_middleware.py -v` — all tests pass
```

The `VALIDATE` field tells the execution agent exactly what command to run after implementing. This creates a tight feedback loop: implement → validate → fix → validate → move on.

### Plan-Level Validation

At the bottom of every structured plan, there should be a `VALIDATION COMMANDS` section that lists all commands to run after all tasks are complete:

```markdown
## VALIDATION COMMANDS

### Level 1: Syntax & Style
ruff check . --fix
ruff format .

### Level 2: Type Safety
mypy app/ --strict

### Level 3: Unit Tests
pytest tests/unit/ -v

### Level 4: Integration Tests
pytest tests/integration/ -v
```

The execution agent runs these in order, fixing issues at each level before proceeding to the next. This matches the pyramid — levels gate each other.

---

## 8. Common Validation Anti-Patterns

### Anti-Pattern 1: Testing Theater

**Symptom**: Tests pass but don't verify real behavior. Heavy mocking, trivial assertions.

**Fix**: Review test files during human review (Level 5). Ask: "If I changed the implementation, would this test fail?" If not, the test is theater.

### Anti-Pattern 2: Skipping Levels

**Symptom**: Running integration tests directly after implementation, skipping linting and type checking.

**Fix**: Each level is a gate. Failing Level 1 (syntax) can cause cascading failures at Level 3 (tests). Fix cheap issues first.

### Anti-Pattern 3: Validating Once, Never Again

**Symptom**: Running validation at the end of implementation, never during.

**Fix**: Embed `VALIDATE` in every task. Run focused tests after each task, full suite only at the end.

### Anti-Pattern 4: Applying All Recommendations

**Symptom**: Every suggestion from `/code-review` or `/system-review` gets implemented, even speculative ones.

**Fix**: Apply the selectivity principle. Implement only recommendations that address real, observed problems. Ignore hypothetical improvements.

### Anti-Pattern 5: Human Review as Rubber Stamp

**Symptom**: Glancing at the diff and approving without reading. Trusting "tests pass" as sufficient.

**Fix**: Focus human review on new files, public interfaces, database changes, and security-sensitive code. These are where architectural drift hides.

---

## 9. Integrating Validation with the PIV Loop

### During Planning (Layer 2)

Include validation strategy in every structured plan:
- What tests should exist for this feature?
- What type safety requirements apply?
- What integration points need testing?
- What should human review focus on?

The planning command should produce plans that include validation commands. If your plans don't have a `VALIDATION COMMANDS` section, update the planning command and/or template.

### During Implementation

The execute command should validate as it goes:
1. After each task: run the task's `VALIDATE` command
2. After all tasks: run the plan's validation commands in pyramid order
3. Fix issues before moving to the next task or level

### During Post-Implementation

Choose the appropriate validation workflow:
- **Minimal**: `/execute` → `/commit`
- **Standard**: `/execute` → `/code-review` → `/code-review-fix` → `/commit`
- **Thorough**: `/execute` → `/execution-report` → `/code-review` → `/code-review-fix` → `/commit`
- **With system evolution**: Add `/system-review` after commit

### Trust Progression for Validation

```
Manual validation → Embedded validation → Command validation → Parallel agents → Automated CI
     ↑ trust & verify ↑       ↑ trust & verify ↑       ↑ trust & verify ↑
```

1. **Manual**: You run tests and read diffs yourself
2. **Embedded**: Plans include `VALIDATE` fields, AI runs them during execution
3. **Command**: `/code-review` and `/code-review-fix` automate the review cycle
4. **Parallel agents**: 4 specialized agents review simultaneously
5. **Automated CI**: GitHub Actions + CodeRabbit handle review-fix loops

Don't skip stages. Each tier builds trust for the next.

---

## 10. FAQ

### Q: Should I run /code-review on every feature?

A: For code changes, yes. It's fast and catches real issues. Skip it for documentation-only changes.

### Q: How do I know when to use /system-review?

A: When something felt wrong during the loop — the AI made repeated mistakes, the plan was missing information, or you had to intervene more than expected. Don't use it routinely; use it when you sense a process problem.

### Q: Can I use /code-review without the parallel agents?

A: Yes. The command works in single-agent mode by default. Parallel agents are an optional enhancement that improves speed and depth but aren't required.

### Q: What if /code-review finds issues I disagree with?

A: Use the selectivity principle. The AI over-reports. Review each finding and only fix what's actually a problem. You can scope `/code-review-fix` to specific severities or files.

### Q: Should tests be written during planning or implementation?

A: Test *strategy* during planning (what to test, test structure). Test *code* during implementation (the AI writes tests alongside the feature code). The plan should specify what tests to write; the execute command should actually write them.

### Q: How do I handle validation failures that reveal plan gaps?

A: This is the feedback loop working. When a test fails because the plan missed something:
1. Fix the immediate issue (code fix)
2. Note what the plan should have included
3. After the loop, update the planning command or template to capture this in future plans

### Q: What's the difference between /execution-report and git log?

A: Git log shows *what changed*. The execution report shows *why things changed* — including deviations from the plan, issues encountered, workarounds attempted, and decisions made. This context is only available in the same conversation where implementation happened.

### Q: How many issues should /code-review typically find?

A: Varies by feature size. For a well-planned feature: 0-2 critical, 2-5 major, 5-10 minor. If you're consistently seeing 5+ critical issues, your planning phase needs improvement — the issues should be prevented at planning time, not caught at review time.

---

## 11. Reference Files

**Commands**:
- `.claude/commands/code-review.md` — Technical code review command
- `.claude/commands/code-review-fix.md` — Fix issues from code review
- `.claude/commands/execution-report.md` — Implementation report command
- `.claude/commands/system-review.md` — Divergence analysis command

**Agents**:
- `.claude/agents/code-review-type-safety.md` — Type safety reviewer
- `.claude/agents/code-review-security.md` — Security reviewer
- `.claude/agents/code-review-architecture.md` — Architecture reviewer
- `.claude/agents/code-review-performance.md` — Performance reviewer

**Related guides**:
- `reference/implementation-discipline.md` — The execute phase that validation follows
- `reference/command-design-framework.md` — How the validation commands are designed (INPUT→PROCESS→OUTPUT)
- `reference/subagents-deep-dive.md` — How parallel review agents work under the hood
