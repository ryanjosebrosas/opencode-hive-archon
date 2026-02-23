# Command Design Framework: INPUT-PROCESS-OUTPUT

This guide explains **how to design, build, and evolve** slash commands — reusable prompts that automate workflows — using the INPUT→PROCESS→OUTPUT framework — the comprehensive guide to command design.

---

## 1. What This Guide Covers

### The Journey from Construction to Automation

The System Foundations guide established the **why** — the system gap and learning architecture. The PIV Loop Practice guide taught the **how** — the PIV Loop in practice. The Global Rules Optimization guide taught **how to build** — modular CLAUDE.md, the Two-Question Framework, and strategic context loading. This guide teaches you **how to automate** — turning manual prompts into reusable, chainable commands.

This is the automation layer. You're not learning concepts or building rules — you're learning how to create the reusable prompts that drive your entire workflow.

### What You'll Learn

- **The INPUT→PROCESS→OUTPUT framework** for designing effective commands
- **Three output patterns** and when to use each (Context Loading, Document Creation, Action Automation)
- **Command features** — arguments, bash execution, file references, frontmatter
- **The Core 4 command patterns** — how `/prime`, `/planning`, `/execute`, `/commit` are designed internally
- **The bug fix workflow** — an alternative command chain for investigating and fixing GitHub issues
- **Consumer optimization** — how to design output for humans vs agents vs systems
- **Trust progression** — the three stages from manual prompts to autonomous workflows
- **How to build your own commands** — practical exercises applying the framework

### Why This Guide Matters

Commands are the bridge between manual prompting and systematic workflows. Without them, every task requires typing the same instructions from scratch. With them, you codify proven patterns into reusable, improvable artifacts.

Commands also implement the Global Rules Optimization guide's recommended Method 2 for on-demand loading. The `@` file reference syntax in commands **guarantees** reference guides are loaded — more reliable than hoping the AI remembers to load them (Method 1).

**Mental model**: Commands are "saved macros" for AI coding assistants. They encode your best instructions into repeatable workflows that improve over time.

---

## 2. The INPUT→PROCESS→OUTPUT Framework

Every command answers three questions. This section explores each with examples and practical guidance.

### The Three Questions (From the Agent's Perspective)

1. **INPUT — What does the agent NEED to see?** Context, domain knowledge, references, constraints. Without input, the agent guesses.
2. **PROCESS — What should the agent DO?** Steps to follow, criteria to evaluate, tools to use, order of operations. Without process, the agent improvises.
3. **OUTPUT — What do you WANT back?** Format, structure, detail level, and — critically — who will consume it. Without output specification, the agent decides.

### INPUT: Setting the Stage

The INPUT section provides everything the agent needs — not generic advice, but project-specific context.

**What to include**: Tech stack and constraints, domain knowledge (conventions, patterns), file references (`@`) to load guides, bash execution (`!`) to capture current state.

**Example:**
```markdown
## Context
You are reviewing code for a FastAPI application using:
- Python 3.12 with strict type hints
- Pydantic for validation
Read the project rules: @CLAUDE.md
Current state: !`git status`
```

### PROCESS: Defining the Work

Clear, step-by-step instructions the agent follows in order without inventing extra steps.

**What to include**: Numbered steps in execution order, specific evaluation criteria, tools/methods per step, conditions ("if X, then Y").

**Example:**
```markdown
## Process
1. Read the plan file completely
2. For each task: read target file → implement → run validation
3. After all tasks, run full validation suite
4. Fix any failures before reporting completion
```

### OUTPUT: Specifying the Result

The most overlooked section, and the most impactful. Defines format, structure, detail level, and — critically — **who consumes it**.

**What to include**: Required sections/headers, level of detail, format constraints, consumer identification.

**Example:**
```markdown
## Output Format
Report back with:
### Project Overview — Purpose (1 sentence), tech stack (list)
### Architecture — Directory structure (tree), key patterns
### Current State — Active branch, recent changes
Keep it scannable — 30-second verification target.
```

### Why Structure Matters

Without the framework, a prompt like "Review this code" produces vague, generic, unpredictable output. With INPUT (project context) + PROCESS (specific checks) + OUTPUT (structured format), the same command produces consistent, actionable results every time.

---

## 3. Three Output Patterns

The following table shows the three output patterns. Here's the deeper understanding of when and how to use each.

### Pattern 1: Context Loading

**Produces**: Agent state change (no file, no side effect). **Consumer**: YOU (human). **Example**: `/prime`

Agent reads project structure, docs, key files → outputs human-readable summary → you scan in 30 seconds to verify understanding. Effective because: concise summaries (not full regurgitation), headers for navigation, bullet points for scanning, confidence checks built in.

### Pattern 2: Document Creation

**Produces**: Markdown file saved to disk. **Consumer**: ANOTHER AGENT (executes in separate conversation). **Example**: `/planning`

Agent researches codebase → creates `requests/{feature}-plan.md` → output optimized for `/execute` to consume. Effective because: explicit file paths (`src/auth/jwt.py:45-62` not "the auth module"), exact commands (copy-paste ready), validation checkpoints per task, complete context (zero assumptions).

### Pattern 3: Action Automation

**Produces**: Side effect (git commit, file modification). **Consumer**: SYSTEM + YOU. **Example**: `/commit`

Agent reviews changes → creates conventional commit → executes `git add` + `git commit` → reports result. Effective because: follows system format exactly, confirms what happened, reports side effects, human-readable summary.

### Output Patterns Summary

| Pattern | Produces | Consumer | Optimization | Example |
|---------|----------|----------|-------------|---------|
| Context Loading | Understanding | Human | Scannable, 30-sec verify | `/prime` |
| Document Creation | Saved artifact | Another agent | Explicit, zero ambiguity | `/planning` |
| Action Automation | Side effect | System + Human | Format-compliant | `/commit` |

**Key insight**: Same INPUT→PROCESS→OUTPUT framework, different output optimization based on who consumes it. This is the most practical insight from this guide.

---

## 4. Command Features Reference

The command design overview mentions these features briefly. Here's the complete reference with syntax, behavior, and practical examples.

### Arguments: Dynamic Input

**Two methods for accepting user input:**

**Method 1: `$ARGUMENTS`** — All arguments as a single string.
```markdown
# planning.md
Create an implementation plan for: $ARGUMENTS
```
Usage: `/planning authentication system with JWT tokens`
Result: `$ARGUMENTS` becomes `"authentication system with JWT tokens"`

**Best for**: Feature descriptions, prompts, natural language input — anything where the full text is one concept.

**Method 2: `$1`, `$2`, `$3`** — Positional arguments.
```markdown
# fix-issue.md
Fix issue #$1 with priority $2 following our coding standards.
```
Usage: `/fix-issue 123 high`
Result: `$1` = `123`, `$2` = `high`

**Best for**: Issue numbers, file paths, specific values — structured input where each piece has a distinct purpose.

### Bash Execution: `!` Prefix

Execute shell commands immediately when the command is invoked. Output is captured and inserted into the prompt.

**Syntax**: `` !`command` ``

**Example:**
```markdown
Current git status:
!`git status`

Recent changes:
!`git diff HEAD`

Based on the above changes, create a descriptive commit message.
```

**How it works:**
1. Command invoked (e.g., `/create-commit`)
2. Bash commands run immediately
3. Output captured and inserted into the prompt text
4. Agent sees actual output and acts on it

**Use cases**: Load project state (`git status`, `git log`), check test results, get system information.

### File References: `@` Prefix

Load file contents into context automatically. This is the Global Rules Optimization guide's Method 2 (recommended) for on-demand loading.

**Syntax**: `@path/to/file.md`

**Example:**
```markdown
# create-tool.md
Reference guide: @reference/adding_tools_guide.md

Based on the guide above, create a new tool for: $ARGUMENTS
```

**How it works:**
1. `@reference/adding_tools_guide.md` loads the full file contents inline
2. `$ARGUMENTS` receives user input
3. Agent has the guide in context and knows what to build

**Why this matters**: `@` references **guarantee** the guide is loaded. Unlike Method 1 (mentioning the guide in CLAUDE.md and hoping AI loads it), this is deterministic. Every time the command runs, the guide is there.

### Frontmatter: Command Configuration

YAML frontmatter at the top of command files provides metadata and tool restrictions.

**Syntax:**
```markdown
---
description: Short description of what this command does
argument-hint: [what-arguments-to-provide]
allowed-tools: Tool1, Tool2(pattern:*)
---
```

**Key fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | Shows in command list | `Research and create implementation plan` |
| `argument-hint` | Helps users know what to provide | `[feature-description]` |
| `allowed-tools` | Restricts which tools the agent can use | `Bash(git:*), Read, Write` |

**`allowed-tools` pattern syntax:**
```text
Read                    # Allow the Read tool
Write                   # Allow the Write tool
Edit                    # Allow the Edit tool
Bash(git:*)             # Bash commands starting with "git"
Bash(ruff:*)            # Bash commands starting with "ruff"
Bash(pytest:*)          # Bash commands starting with "pytest"
```

**Why restrict tools?**
- **Security**: Prevent unintended operations (e.g., commit command can't delete files)
- **Focus**: Agent doesn't waste time trying tools it shouldn't use
- **Clarity**: Explicit about what the command can and cannot do

---

## 5. The Core 4 Command Patterns

The command design overview lists the Core 4 and their purposes. Here's how each is designed internally — the decisions behind their INPUT, PROCESS, and OUTPUT sections.

### `/prime` — Context Loading Pattern

**Purpose**: Build comprehensive codebase understanding at session start.

**Consumer**: Human (to verify) + Agent (to inform future actions).

**Process outline:**
1. Analyze project structure (directory tree, key files)
2. Read core documentation (CLAUDE.md, README, PRD if exists)
3. Identify and read key implementation files (entry points, config, models)
4. Understand current state (git log, git status, active branch)

**Output format** (human-optimized for scanning):
```text
### Project Overview — Purpose, type, current state
### Architecture — Structure, patterns, key directories
### Tech Stack — Languages, frameworks, versions
### Core Principles — Code style, documentation, testing approach
### Current State — Active branch, recent changes, open work
```

**When to use**: Start of session, switching projects, before major changes, when agent seems confused about the project.

### `/planning` — Document Creation Pattern

**Purpose**: Research and create detailed implementation plans.

**Consumer**: Another agent (`/execute`) + Human (to review and approve).

**Process outline:**
1. Determine feature name (kebab-case for file naming)
2. Analyze existing codebase patterns (similar features, conventions)
3. Research external documentation (libraries, APIs, best practices)
4. Design implementation approach (architecture decisions, tradeoffs)
5. Break down into atomic tasks (with file paths, validation per task)
6. Create plan document and save to `requests/{feature}-plan.md`

**Required output sections** (agent-optimized — zero ambiguity):
1. **Overview** — Brief description, requirements, success criteria
2. **Relevant Files** — Full paths with descriptions and create/modify labels
3. **Dependencies** — New libraries, existing utilities, config changes
4. **Step-by-Step Tasks** — Exact tasks with file, action, details, validation
5. **Testing Strategy** — What to test, where test files go, key cases
6. **Validation Commands** — Exact commands to run in order
7. **Integration Notes** — How it connects, breaking changes, migrations

**When to use**: Before implementing new features, for complex multi-file changes, when you need a reviewable approach before coding. The key test: could another agent execute this plan without asking questions?

### `/execute` — Implementation Pattern

**Purpose**: Implement features from detailed plans.

**Consumer**: Human (the working feature) + Git (via commit).

**Process outline:**
1. Read entire plan, understand tasks and dependencies
2. Execute tasks in order (navigate → implement → verify each)
3. Implement testing strategy (create tests alongside code)
4. Run all validation commands (fix issues, re-run until all pass)
5. Final verification (all tasks complete, tests passing, conventions followed)

**Frontmatter example** (restricts tools to implementation-safe operations):
```markdown
---
allowed-tools: Read, Write, Edit, Bash(ruff:*), Bash(mypy:*), Bash(pytest:*)
---
```

**When to use**: After creating a plan with `/planning`. Never without a plan — the plan IS the context.

### `/commit` — Action Automation Pattern

**Purpose**: Create well-formatted git commits with conventional message format.

**Consumer**: Git (version control) + Team (via git history).

**Process outline:**
1. Review current state (`git status`, `git diff HEAD`)
2. Analyze changes — determine type, scope, description
3. Stage appropriate files (`git add` specific files)
4. Create commit with conventional message format
5. Confirm success and report details

**Conventional commit format:**
```text
type(scope): description

[optional body]

[optional footer]
```

**Commit types**: `feat` (new feature), `fix` (bug fix), `refactor` (code restructuring), `docs` (documentation), `test` (tests), `chore` (maintenance), `perf` (performance), `style` (formatting).

**Frontmatter example** (restricts to git-only operations):
```markdown
---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git commit:*)
---
```

**When to use**: After completing implementation, after any code changes you want to save.

### Command Patterns Summary

| Command | Pattern | Produces | Consumer | Frequency |
|---------|---------|----------|----------|-----------|
| `/prime` | Context Loading | Agent understanding | Human + Agent | Every session |
| `/planning` | Document Creation | Plan document | Another agent + Human | Per feature |
| `/execute` | Implementation | Code + Tests | Human + Git | Per plan |
| `/commit` | Action Automation | Git commit | Git + Team | After changes |
| `/rca` | Document Creation | RCA document | Another agent | Per bug |
| `/implement-fix` | Implementation | Bug fix | Git | Per RCA |
| `/end-to-end-feature` | Chained Workflow | Full feature | Human + Git | Per feature |

### The Complete Development Lifecycle

```text
/prime → /planning [feature] → /execute [plan] → /commit → NEXT CYCLE
  ↓            ↓                     ↓                ↓
Context    Plan artifact       Code + tests      Git commit
```

Each step produces something the next step consumes. Prime loads context for planning. Planning creates the artifact for execution. Execution produces code for commit.

---

## 6. Design Philosophy: Why the Core 4 Work

### Separation of Concerns

Planning and execution are different mental modes. Planning requires **exploration and thinking** — researching options, weighing tradeoffs, designing approaches. Execution requires **focus and precision** — following a spec, writing code, running tests.

Combining them in one command would create a prompt that tries to do everything and does nothing well. Separating them lets each command optimize for its specific task.

### Intelligence Reuse

Plans are **artifacts**, not ephemeral conversations. A plan document can be:
- **Executed multiple times** (if the first implementation attempt fails, revert and retry)
- **Reviewed before execution** (catch issues before any code is written)
- **Refined iteratively** (improve the plan, then re-execute)
- **Referenced later** (documentation of how and why a feature was built)
- **Shared with team** (anyone can execute the same plan)

### Agent-to-Agent Communication

The `/planning` command knows that `/execute` will consume its output — in a separate conversation, without the planning context. This awareness drives the planning command to produce:
- **Explicit file paths** (not "the auth module" but `src/auth/jwt.py`)
- **Exact commands** (not "run the tests" but `uv run pytest tests/ -m unit -v`)
- **Zero ambiguity** (no "use appropriate patterns" — specify which patterns)
- **Complete context** (another agent can execute without questions)

This is agent-to-agent communication through artifacts. The planning agent writes for the execution agent, not for you.

### Workflow Flexibility

Commands work independently AND chain together. Prime without planning, plan without executing, execute any existing plan, commit incremental progress, plan multiple features before executing any. You adapt the workflow to the task, not the other way around.

---

## 7. Bug Fix Workflow

The Core 4 cover feature development. Bug investigation and fixing use an alternative two-command chain that integrates with GitHub Issues.

### Prerequisites

The bug fix workflow requires GitHub CLI (`gh`). Verify it's set up:
```bash
gh auth status     # Check authentication
gh issue list      # Test access to your repository
```

### `/rca [issue-id]` — Root Cause Analysis

**Pattern**: Document Creation (for another agent).

**Purpose**: Investigate a GitHub issue, analyze the root cause, and document findings with a proposed fix strategy.

**Process:**
1. Fetch issue details via GitHub CLI (`gh issue view`)
2. Investigate the code — trace the bug through the codebase
3. Check git history for relevant recent changes
4. Document root cause, impact analysis, and affected components
5. Propose fix strategy with specific file changes
6. Save RCA document to `docs/rca/issue-{id}.md`

**When to use**: Before fixing a reported bug. Always investigate first, code second.

### `/implement-fix [issue-id]` — Fix Implementation

**Pattern**: Implementation (produces code).

**Purpose**: Read the RCA document and implement the documented fix.

**Process:**
1. Read RCA document for the issue
2. Implement the proposed fix following the documented approach
3. Add regression tests (prevent the bug from returning)
4. Run validation suite
5. Report completion

**When to use**: After completing `/rca` for the issue.

### Bug Fix Lifecycle

```text
1. /prime                          # Load project context
   ↓
2. /rca 123                        # Investigate issue #123
   ↓  Output: docs/rca/issue-123.md
   ↓
3. /implement-fix 123              # Fix based on RCA findings
   ↓  Output: Working fix + regression tests
   ↓
4. /commit                         # Commit with "Fixes #123"
```

### Why Separate Investigation from Implementation

Same separation principle as the Core 4:
- **Investigation = research + analysis** (explore, trace, understand)
- **Implementation = focused coding** (follow the fix strategy)

Additional benefits:
- RCA captures knowledge for future reference (institutional memory)
- You can review the analysis before any code is written
- Same RCA can inform multiple fix attempts if the first doesn't work
- RCA documents build a searchable knowledge base of past issues

---

## 8. Designing for Different Consumers

The most practical insight from this guide: same INPUT→PROCESS→OUTPUT framework, radically different outputs depending on who consumes them.

### Human-Optimized Output (Context Loading)

When a human will read the output (e.g., `/prime`):

- **Concise** — summaries, not full regurgitation
- **Scannable** — bullet points, headers, visual structure
- **30-second target** — human should verify understanding in under a minute
- **Highlights over details** — key principles, not every rule
- **Conversational tone** — "Here's what I found" not "SECTION 1: FINDINGS"

### Agent-Optimized Output (Document Creation)

When another agent will execute the output (e.g., `/planning`):

- **Explicit** — exact file paths, line numbers, function names
- **Complete** — every piece of context needed, no assumptions
- **Ordered** — numbered tasks with clear dependencies
- **Unambiguous** — "Create `src/auth/jwt.py`" not "Add authentication"
- **Validation-rich** — checkpoint after every task, not just at the end
- **Instructional tone** — "Execute this" not "Consider this"

### System-Optimized Output (Action Automation)

When a system (git, CI, API) will receive the output (e.g., `/commit`):

- **Format-compliant** — follows the system's expected format exactly
- **Exact syntax** — conventional commits, not creative descriptions
- **Confirmation** — reports what action was taken
- **Side effects documented** — what changed, what was affected
- **Machine-readable** — parseable by other tools

### Consumer Comparison

| Aspect | Human Output | Agent Output |
|--------|-------------|--------------|
| Length | Concise (scannable) | Detailed (explicit) |
| Structure | Bullets and headers | Step-by-step tasks |
| Specificity | Highlights and summaries | Exact paths and commands |
| Validation | Quick confirmation | Comprehensive checkpoints |
| Tone | Conversational | Instructional |
| Goal | Verify understanding | Enable execution |

> **"Same framework (Input → Process → Output), different optimization. That's the power of thinking in patterns!"**

---

## 9. Trust Progression: From Manual to Autonomous

The command design overview introduces the three-stage diagram. Here's the deeper understanding with transition criteria and practical guidance.

### Stage 1: Manual Prompts

You write custom prompts for each task, experiment with phrasings, learn what works, iterate through trial and error. **When to use**: Learning a new domain, exploring how to instruct the AI, not yet confident in a repeatable approach.

### Stage 2: Reusable Commands

You've identified repeatable patterns and codified them as command files. You run each command individually and verify output before proceeding. **When to use**: You know reliable instructions for this task type, want consistency, want to verify each step.

The workflow: `/prime` → verify → `/planning` → review plan → `/execute` → watch → `/commit` → verify. Human verification at each step.

### Stage 3: Chained Commands

You trust each individual command completely and chain them for end-to-end execution: `/end-to-end-feature "description"` runs prime → planning → execute → commit with minimal intervention. **When to use**: Every command reliable, 10+ manual workflow runs, confident in autonomous execution.

### Transition Criteria

**Before creating reusable commands** (Stage 1 → 2):
- You've manually prompted similar tasks **3+ times** successfully
- You know exactly what instructions produce good results
- You can predict the AI's output before it generates it
- The pattern is stable and repeatable

**Before chaining commands** (Stage 2 → 3):
- Each individual command works reliably on its own
- You've run the full workflow manually **10+ times** successfully
- You trust each step's output without needing to verify
- The workflow is stable across different features/tasks

### `/end-to-end-feature` — The Autonomous Workflow

**What it chains**: `/prime` → `/planning [feature]` → `/execute [plan]` → `/commit`

**What it produces**: A fully implemented, tested, and committed feature with zero manual intervention.

**When to use**: ONLY when you trust every command in the chain individually. This is the final stage of the trust progression.

### The Philosophy

> **Manual prompts teach the pattern.**
> **Reusable commands codify the pattern.**
> **Chained commands scale the pattern.**

Each stage builds on trust earned through repetition. Rushing to automation without trust leads to unpredictable results and difficult debugging. The cost of premature chaining is wasted time diagnosing which step failed and why — much harder to debug in a chain than in individual commands.

---

## 10. Getting Started & Command Evolution

### Recommended First-Use Order

1. **`/prime`** — Understand your codebase. Simplest to verify (just read the output).
2. **`/commit`** — Create your next commit. Easy to verify (check the git message and staged files).
3. **`/planning` + `/execute`** — Plan and implement your next feature. More complex, but the plan gives you a review checkpoint.
4. **Refine each command** — After using them 3-5 times, note what works and what doesn't.

### Command Evolution Path

Commands improve through use:

- **V1 (Basic)**: Commands from templates, generic patterns
- **V2 (Project-specific)**: Add your tech stack, conventions, file paths
- **V3 (Optimized)**: Refine output formats based on what you actually review
- **V4 (Integrated)**: Add tool integrations (Archon tasks, memory.md, MCP servers)

### Tips for Success

1. **Verify prime output** — Always scan the summary to confirm understanding
2. **Review plans before executing** — The plan is your checkpoint; catch issues before code is written
3. **Refine commands based on use** — When output is consistently suboptimal, update the command (system evolution)
4. **Add project specifics** — Generic commands work, but project-customized commands work better
5. **Share with team** — Project commands (`.claude/commands/`) are version-controlled and benefit everyone

---

## 11. Practical Exercises

### Exercise 1: Build a Priming Command (Context Loading)

**Task**: Create `/prime-tools` — loads tool development patterns into agent context.

**Solution structure**: Context section (what domain) → Read section (`@reference/adding_tools_guide.md`) → Process section (6 specific things to understand) → Report Back section (scannable output with key principles, critical distinctions, confirmation).

**Why it works**: Clear context setting, `@` reference guarantees guide loading, focused processing (6 items, not "read everything"), human-optimized output (scannable, 30-second verification), verification built-in.

### Exercise 2: Design Planning Command Output (Document Creation)

**Task**: Design the output template for a planning command that another agent will execute.

**Solution structure**: Feature Description → User Story → Problem/Solution Statements → Relevant Files (exact paths) → Research Documentation (links with anchors) → Implementation Plan (phased) → Step-by-Step Tasks (file, action, details, validation per task) → Testing Strategy → Acceptance Criteria → Validation Commands → Checklist.

**Why it works**: Complete context (no assumptions), explicit file references, structured research, unambiguous tasks, built-in validation per task and at end, agent-optimized (step-by-step, zero ambiguity).

### Key Takeaway

Both exercises use the same INPUT→PROCESS→OUTPUT framework. Exercise 1 optimizes for a **human** reader (concise, scannable). Exercise 2 optimizes for an **agent** executor (explicit, complete). The framework is the constant; the consumer optimization is the variable.

---

## FAQ: Common Questions

### "Should I create my own commands right away?"

**Short answer**: No. Use the built-in Core 4 first.

**Long answer**: Creating commands prematurely means encoding unproven patterns. Use the Core 4 on 3-5 features first. Only then create custom commands — you'll know exactly what instructions to include.

### "How do I know my command is well-designed?"

**Short answer**: Apply the INPUT→PROCESS→OUTPUT checklist and test it 3 times.

**Long answer**: Clear INPUT (all context), specific PROCESS (numbered steps), structured OUTPUT (format + consumer). Test on 3 different tasks — consistent output quality means well-designed. Wildly varying output means PROCESS needs specificity or INPUT is missing context.

### "When should I chain commands?"

**Short answer**: Only when each individual command is proven reliable and you've run the full workflow manually 10+ times.

**Long answer**: Chaining amplifies both good and bad patterns. If planning occasionally produces vague tasks, chaining means vague implementations. Fix individual commands first — the trust progression catches these issues before they compound.

### "What's the difference between an overview and this guide?"

**Short answer**: An overview covers what. This guide covers how.

**Long answer**: An overview would be a concise on-demand reference (command list, framework summary, patterns table). This guide is the deep dive (command anatomy, Core 4 internals, consumer optimization, exercises). Overview = "what are commands?" This guide = "how do I design effective commands?"

### "Can I use these commands with other AI tools?"

**Short answer**: The framework transfers; the syntax is tool-specific.

**Long answer**: INPUT→PROCESS→OUTPUT applies to any AI tool (Cursor, Codex, Copilot). The syntax (`$ARGUMENTS`, `!`, `@`, frontmatter) is Claude Code specific, but the patterns transfer. When switching tools, adapt syntax, keep framework.

---

## Next Steps

1. **Read this guide** (you're doing this now)
2. **Try `/prime`** to understand your codebase — simplest to verify
3. **Use `/commit`** for your next commit — easy to verify the result
4. **Run `/planning` and `/execute`** together for your next feature
5. **Build Exercise 1** (priming command) to practice the framework hands-on
6. **Move to the planning methodology skill** — learn the 6-phase planning methodology that enhances `/planning`

---

## Related Resources

- **Command template**: `templates/COMMAND-TEMPLATE.md` — design guide for creating new commands
- **Structured plan template**: `templates/STRUCTURED-PLAN-TEMPLATE.md` — the output format `/planning` produces
- **Existing commands**: `.claude/commands/` — see how the Core 4 and other commands are implemented
- **Global Rules Optimization guide** (prerequisite): `reference/global-rules-optimization.md` — global rules, Two-Question Framework, on-demand loading
- **Planning Methodology skill**: `.claude/skills/planning-methodology/` — 6-phase planning methodology

---

**That's the Command Design Framework!** You now understand:
- The INPUT→PROCESS→OUTPUT framework for command design
- Three output patterns (Context Loading, Document Creation, Action Automation)
- Command features ($ARGUMENTS, !, @, frontmatter)
- How each Core 4 command is designed internally
- The bug fix workflow (/rca → /implement-fix)
- How to optimize output for different consumers (human vs agent)
- Trust progression (Manual → Commands → Chained)
- How to build your own commands (exercises)

**Ready for the Planning Methodology guide?** Learn the 6-phase planning methodology that transforms `/planning` from a basic command into a comprehensive research and planning system. It also introduces the granularity principle, PRD templates, and the system evolution mindset.
