# Implementation Discipline: Execute, Meta-Reasoning & Save States

This guide explains **how to implement from plans reliably, evolve your system through meta-reasoning, and build trust for faster iteration** — covering the `/execute` command design, the Navigate→Implement→Verify pattern, research validation, save states, and speed progression — going deeper than the always-loaded overview in `sections/02_piv_loop.md`.

---

## 1. What This Guide Covers

### The Journey from Methodology to Discipline

The System Foundations guide established the **why** — the system gap and learning architecture. The PIV Loop Practice guide taught the **how** — the PIV Loop in practice. The Global Rules Optimization guide taught **how to build** — modular CLAUDE.md and strategic context loading. The Command Design Framework guide taught **how to automate** — slash commands and the INPUT→PROCESS→OUTPUT framework. The Planning Methodology guide taught **how to plan** — the 6-phase planning methodology that produces implementation-ready plans. This guide teaches **execution discipline** — how to implement from plans reliably and evolve the system when things go wrong.

This is deliberately the **shortest guide** in the series. The brevity is the point — it proves the PIV Loop thesis: when planning is thorough, implementation becomes simple.

### What You'll Learn

- **The execute command design** — two critical components that prevent lazy AI behavior
- **Navigate → Implement → Verify** — the per-task pattern for reliable execution
- **Custom workflow injection** — extending the execute command with project-specific integrations
- **PIV loops in action** — two complete loops demonstrating deliberate vs fast execution
- **Meta-reasoning** — the 5-step system evolution technique for permanent fixes
- **The WHERE-to-fix framework** — deciding which part of the system needs the fix
- **Research validation** — verifying research completeness before building plans on it
- **Save states & git workflow** — commit strategy with three rollback scenarios
- **Generic vs customized commands** — how commands evolve per-project through meta-reasoning
- **Speed & trust progression** — when and how to accelerate your PIV loops

### The Core Insight

> **"If you invest heavily in planning, implementation becomes simple."**

This guide's length directly reflects this. All the intelligence lives in the structured plan — the execute command just orchestrates how tasks are handled.

### The Sandwich Metaphor

```
PLANNING    (thick layer — research, patterns, context)
    ↓
IMPLEMENTATION  (thin layer — execute command)
    ↓
VALIDATION  (thick layer — testing, review, system evolution)
```

When you get planning right, implementation becomes almost automatic. The execute command is simple because the structured plan contains all context the AI needs.

---

## 2. The Execute Command Deep Dive

### Purpose

The execute command is the bridge between planning and code. The structured plan defines **what** tasks to execute; the execute command specifies **how** to handle each task. See `.claude/commands/execute.md` for the full implementation.

### Two Critical Components

| Component | Purpose | Without It |
|-----------|---------|------------|
| Thoroughness Instructions | Force AI to read the entire plan, run all validation | AI reads part of plan, skips validation, asks permission at each step |
| Task Handling Process | Define Navigate→Implement→Verify per-task pattern | AI implements haphazardly, misses patterns, doesn't verify |

### Thoroughness Instructions

AI coding assistants have quirks where they try to be lazy. Without explicit instructions, they may:
- Only read part of the plan
- Set up a "phased approach" asking permission at each step
- Execute some validation commands and ask you to do the rest

The execute command addresses this with explicit directives:
- "Read the ENTIRE plan carefully"
- "Execute ALL validation commands from the plan in order"
- "Don't skip validation steps"

This makes a considerable difference for feature implementations.

### Task Handling Process: Navigate → Implement → Verify

For each task in the plan:

1. **Navigate** — Identify the file and action required, read existing related files if modifying
2. **Implement** — Follow the detailed specifications exactly, maintain consistency with existing patterns
3. **Verify** — After each file change, check syntax, ensure imports are correct, verify types

This per-task cycle prevents the AI from implementing everything in a rush and then discovering issues at the end.

### Current Execute Command Structure

The command follows seven sections (see `.claude/commands/execute.md`):

| Step | Purpose |
|------|---------|
| 1. Read & Understand | Parse entire plan, note dependencies and validation commands |
| 1b. memory.md warnings (optional) | Check past gotchas before implementing |
| 1.5 Archon init (optional) | Create project and tasks for Kanban visibility |
| 2. Execute tasks | Navigate→Implement→Verify per task, with Archon status updates |
| 3. Testing strategy | Create test files, implement test cases from plan |
| 4. Run validation | Execute ALL validation commands; fix failures before continuing |
| 5. Final verification | Confirm all tasks complete, tests passing, conventions followed |
| 5.5 Archon completion (optional) | Mark all tasks done, update project status |
| 6. Update plan checkboxes | Check off acceptance criteria and completion checklist |

### Output Report

The execute command specifies a structured output: completed tasks (files created/modified), tests added (files and results), validation results (command output), and readiness for `/commit`.

### Golden Nuggets for the Execute Command

- **Check environment changes**: After implementation, ask "How can I run everything? Do I need to change anything in my environment?" — catches deployment requirements
- **Concise summary**: Include a summary request in the output format (what was implemented, files changed, next steps)
- **Don't skip validation**: Add as an explicit instruction — AI assistants will try to shortcut validation if not told otherwise

---

## 3. Custom Workflow Injection

### The WHAT vs HOW Distinction

The structured plan outlines **what** tasks to knock out. The execute command specifies **how** to handle them. Customizing the HOW is where you inject project-specific workflows.

### Integration Examples

| Workflow Integration | What It Does | Where in Execute |
|---------------------|-------------|-----------------|
| Archon MCP | Status updates per task (doing → review → done) | Steps 1.5, 2a.5, 5.5 |
| memory.md warnings | Check past gotchas before implementing | Step 1b |
| Notion/Jira | Update external task boards | After each task completion |
| Research per task | Run tool-specific research before implementing | Start of each task |
| Progress tracking | Custom logging/reporting | Throughout |

### Backward Compatibility Pattern

Use conditional checks — "If Archon available, use it" — for backward compatibility. Not everyone has MCP servers configured. The command works with or without integrations.

The execute command is the **most customized command** in your system. Every project evolves it differently based on workflows, task management tools, and validation requirements.

---

## 4. PIV Loops in Action

### The Full Workflow

A complete PIV loop runs through six prompts:

1. **`/prime`** — Load context, orient the AI to the codebase
2. **"Based on the PRD, what tool should we implement first?"** — PRD-guided feature selection; even if you know what to build, let the PRD guide ordering
3. **Vibe planning research** — "No implementation. Research only." Reference on-demand context, fetch external docs, explore codebase patterns
4. **`/planning` with final considerations** — Feed vibe planning context into the structured plan command
5. **Meta-reasoning on plan quality** — "This plan is WAY too long (1752 lines). Do some meta reasoning..." Leads to system evolution
6. **`/execute [plan-path]`** — Implement from the validated, right-sized plan

**Golden nugget**: After vibe planning, ask "Let me know what context you already have in this conversation" to verify all on-demand context was loaded.

### Anatomy of Each Prompt

**Prompt 2 — PRD-guided selection**: The AI analyzes the PRD and recommends the safest starting tool (one that validates the entire integration stack). Even when you already know what to build, letting the PRD guide ordering ensures logical feature sequencing.

**Prompt 3 — Vibe planning research**: The key directive is "No implementation. Research only." This prompt loads on-demand context (tool designs, VSA patterns), fetches external documentation (library docs with specific URLs), and explores the existing codebase. It gets both you and the AI on the same page before creating the structured plan.

**Prompt 5 — Plan quality meta-reasoning**: This is where system evolution happens. Rather than just compressing the plan, you ask WHY it happened and WHERE to fix it. The result: a permanent constraint added to the planning command that prevents the issue from recurring.

### First Loop vs Second Loop

| Aspect | First Loop (Deliberate) | Second Loop (Fast) |
|--------|------------------------|-------------------|
| Vibe planning | Extensive research, multiple prompts | Skipped entirely |
| Reason | First-ever tool implementation | Similar to previous tool |
| System evolution | Plan length constraint added | System already evolved |
| AI reference | No prior work to reference | Read previous implementation |
| Speed | Multiple hours, many prompts | Minutes, 3 prompts |

### The AI References Its Own Work

A powerful pattern emerges in the second loop: when implementing similar features, the AI will:
- Read through the PRD to understand the next tool
- Find the previous tool implementation in the codebase
- Use it as a reference pattern for the new feature

This is why Layer 1 planning (PRD, on-demand context) is so powerful — it creates a compounding knowledge base that the AI leverages automatically.

### Key Takeaway

The second loop was faster because the system had evolved (hard constraint in place), the AI could reference previous work, and trust was earned through the first loop. Speed is a consequence of system maturity, not a shortcut.

---

## 5. Meta-Reasoning: System Evolution Technique

### What Meta-Reasoning Is

Asking the AI to analyze **why** something went wrong and **where** in the system the fix belongs — rather than just fixing the immediate problem. It's the difference between patching a symptom and curing the disease.

### The 5-Step Process

1. **Identify the problem** — e.g., "This plan is 1700 lines, way too long"
2. **Ask for analysis** — prompt: "Do some meta reasoning. Don't make any changes yet. Help me understand WHY this happened and how I can adjust the system to avoid this in the future. Look at my commands, rules, and templates."
3. **AI examines the system** — analyzes global rules, on-demand context, commands, templates, vibe planning prompts to locate the root cause
4. **You decide** which suggestion to implement (you may override the AI's idea)
5. **Apply the system fix FIRST**, then fix the immediate output

Step 4 is critical — don't accept all AI suggestions blindly. Human judgment selects the right fix granularity.

### The WHERE-to-Fix Decision Framework

| Fix Location | When to Use | Example |
|---|---|---|
| **Global rules** (CLAUDE.md/sections) | Convention applies to ALL tasks | "Always use structured logging" |
| **On-demand context** (reference/) | Task-type-specific guidance | Streaming patterns guide |
| **Commands** (planning, execute) | Process/workflow issue | Add plan length constraint |
| **Templates** (structured plan, PRD) | Output format/structure issue | Add new section to plan template |
| **Vibe planning** (your prompts) | Research was incomplete or scope wrong | Ask better research questions |

### One-Off Fix vs System Evolution

| Approach | Scope | Outcome |
|----------|-------|---------|
| One-off fix | Fixes immediate output | Same issue recurs next time |
| System evolution | Updates command/template | Issue prevented for all future runs |

**Always prefer system evolution.** One-off fixes solve today; system updates solve forever. Every mistake is an opportunity to make the system better.

### Concrete Example: Plan Length

**Problem**: Plan was 1,752 lines (target: 700-1000).

**Meta-reasoning revealed**: No hard constraint on plan length existed in the planning command.

**AI suggestions**: (1) Add hard constraint, (2) reduce detail in task subsections, (3) compress research sections, (4) limit validation detail.

**Human decision**: Accept #1 (add constraint), reject #2 (keep detailed tasks — they're valuable). Simple fix: just add the line count constraint.

**System fix applied**:
```markdown
CRITICAL CONSTRAINT: The final structured plan must be between 700-1000 lines long.
```

**Then fix the immediate output**: "Make this plan between 500 and 700 lines long."

System fix first. Immediate fix second. Now all future plans respect the constraint automatically.

### The Streaming Bug Example (Human Override)

During the second PIV loop, streaming issues (missing first token, missing newlines) triggered meta-reasoning. The AI suggested creating extensive on-demand context for streaming patterns. The human chose a simpler, more general fix: **research validation** — validating research documents during planning before building plans on them.

**Why the human override was better**:
- More general (applies to all research, not just streaming)
- Won't clutter `reference/` with topics that may not recur
- Addresses the systemic issue (incomplete research)
- Simpler to maintain

### Common Anti-Patterns

| Anti-Pattern | Why It's Harmful |
|---|---|
| One-off fix without system evolution | Solves today but not tomorrow |
| Applying all AI suggestions blindly | Sometimes simpler is better; human judgment matters |
| Ignoring plan length issues | Plans >1000 lines indicate insufficient granularity |
| Skipping research validation | Gaps discovered during implementation are expensive |
| Jumping to fix before analyzing | Miss the root cause; fix symptoms not disease |

When implementation fails repeatedly, use meta-reasoning to identify whether the root cause is in the plan, the system rules, or the execution approach. Ask: "Do some meta reasoning. Don't make any changes yet. Help me understand WHY this happened and how I can adjust the system to avoid this in the future."

---

## 6. Research Validation

### The Problem

During the second PIV loop (note manager tool), implementation had streaming issues — missing first token, missing newlines. Meta-reasoning revealed the root cause was in **Layer 2 planning**: a research document created during vibe planning (`pydantic-ai-streaming-research.md`) was incomplete and didn't cover critical streaming patterns.

### The Solution

Validate research documents during the planning phase, before building the structured plan on top of them. This was added to the planning command as Phase 3b: Research Validation.

### What Was Added

After creating any research reports or technical documents during vibe planning:

1. Read each document thoroughly
2. Verify completeness — Are all critical patterns covered? Are code examples complete? Are edge cases addressed?
3. Flag contradictions between research sources
4. If critical research is missing, do targeted follow-up before creating the structured plan

### Why This Is Better Than On-Demand Context

| Creating on-demand context | Research validation |
|---|---|
| Specific to one topic (streaming) | General (applies to all research) |
| Clutters `reference/` with niche guides | No new files created |
| Maintenance burden | Self-maintaining (part of the planning flow) |
| Addresses symptom | Addresses systemic issue (incomplete research) |

**Philosophy**: Extend research to include research validation. Don't just create documents — verify they're complete before building the plan on top of them.

---

## 7. Save States & Git Workflow

### Commit Strategy

Every stage gets its own commit, creating save points for rollback:

```
git commit -m "plan: {feature} structured plan"    # After planning
git commit -m "feat: {feature} implementation"      # After execution
```

### Three Rollback Scenarios

| Scenario | Rollback | Then |
|----------|----------|------|
| Bad plan | `git stash` or `git checkout .` | Evolve command/template, retry planning |
| Bad implementation | `git stash` or `git checkout .` | Tweak plan, retry with `/execute` |
| After system evolution | Go to any save point | Retry to verify the fix works |

### Value of Committing "Bad" Implementations

Sometimes commit buggy code intentionally:
- Creates a save state for teaching validation (the Validation Discipline guide uses the streaming bug)
- Shows before/after comparison for system evolution
- Demonstrates the retry workflow

Not all commits need to be perfect. The commit history shows exactly what changed and when. After evolving the system (fixing a command or template), you can retry from any save point to see if the fix works.

---

## 8. Generic vs Project-Customized Commands

### The Evolution Pattern

As you evolve commands through meta-reasoning, they often become project-specific. The plan length constraint is universal; the streaming research validation example references Pydantic AI specifically.

### Classification

| Evolution Type | Scope | Example | Keep in Template? |
|---------------|-------|---------|-------------------|
| Universal fix | All projects | Plan length constraint (700-1000 lines) | Yes |
| Domain fix | Similar projects | Pydantic AI streaming validation | No (project-specific) |
| Project fix | Single project | Specific file naming convention | No (project-specific) |

### Strategy

- **Template repo**: Generic commands, widely applicable
- **Project repo**: Customized commands, evolved through meta-reasoning for that specific codebase

The more you evolve, the more customized — which is good for that project but may not transfer to others. This divergence is healthy and expected. Maintain this template as your generic baseline; create project-customized versions in each project's `.claude/commands/`.

---

## 9. Speed & Trust Progression

### First PIV Loop (Deliberate)

Prime → extensive vibe planning → plan → validate plan → execute. Multiple prompts, hours of work. Encountered issues (plan too long), applied meta-reasoning, evolved the system.

### Second PIV Loop (Fast)

Prime → plan → execute. Skipped vibe planning entirely. Similar feature, AI referenced previous implementation, system already evolved. Three prompts, minutes of work.

### When to Speed Up

| Criterion | Why It Matters |
|-----------|---------------|
| 3+ similar features implemented successfully | Patterns are proven |
| Commands produce consistent output | System is reliable |
| System evolved through meta-reasoning | Known issues are fixed |
| AI can reference previous implementations | Patterns available in codebase |

### What "Speeding Up" Actually Means

Speeding up doesn't mean cutting corners — it means earning the right to skip redundant steps:

| Step | First Loop | After Trust Built |
|------|-----------|-------------------|
| `/prime` | Always | Always |
| Vibe planning | Extensive (multiple prompts) | Skip if similar feature |
| Research validation | Full verification | Quick scan |
| `/planning` | Full 6-phase process | Full 6-phase process |
| Plan review | Detailed manual review | Quick scan |
| `/execute` | Watch closely | Trust the process |
| Validation | Run everything | Run everything (never skip) |

Note: you never skip `/planning` or validation. The time savings come from reduced vibe planning and faster plan review — not from skipping safety gates.

### Trust Progression

```
Manual Prompts → Commands → Chained Commands
     ↑ trust & verify ↑    ↑ trust & verify ↑
```

**Warning**: "Don't skip stages. Prematurely speeding up leads to unpredictable results and difficult debugging." Speed is earned through repetition and system evolution, not by skipping steps.

### The Caveat

> "I wouldn't recommend going this fast. It's a bit of an exaggeration, but you get the point I'm trying to drive home here."

The second loop's speed was partly for demonstration. In practice, even fast loops benefit from a brief vibe planning conversation to catch edge cases that "similar" features might not share.

---

## 10. Practical Exercises

### Exercise 1: Run Your First PIV Loop

**Challenge**: Take a simple feature from your PRD and complete the full loop: prime → vibe plan → structured plan → execute → commit.

**Focus**: Note what works and what doesn't. Identify one issue and apply meta-reasoning to determine where in the system the fix belongs.

**Expected outcome**: A committed feature AND at least one system improvement (command update, template change, or rule addition).

**Key takeaway**: The first loop is always slow — that's by design. You're building trust and evolving the system.

### Exercise 2: Meta-Reasoning Practice

**Challenge**: After encountering an implementation issue, write the meta-reasoning prompt. Let the AI analyze. Don't make changes yet.

**The prompt to use**:
```
Do some meta reasoning. Don't make any changes yet.
Help me understand WHY this happened and how I can adjust
the system to avoid this in the future. Look at my commands,
rules, and templates.
```

**Focus**: Which AI suggestion do you accept? Which do you override? Where in the system does the fix belong? Use the WHERE-to-fix framework from Section 5.

**Key takeaway**: Human judgment selects the right fix granularity — simpler is often better.

### Exercise 3: System Evolution Audit

**Challenge**: Review your last 3 implementations. For each, ask: what went wrong? Was it fixed one-off or systemically?

**Audit template**:

| Implementation | Issue Found | Fix Type | System Location | Action Needed |
|---|---|---|---|---|
| Feature 1 | (describe) | One-off / System | (which part) | (what to update) |
| Feature 2 | (describe) | One-off / System | (which part) | (what to update) |
| Feature 3 | (describe) | One-off / System | (which part) | (what to update) |

**Focus**: If any were one-off fixes, apply the system fix now. Update the relevant command, template, or rule.

**Key takeaway**: One-off fixes solve today; system updates solve forever. Every missed system fix is compounding debt.

---

## FAQ: Common Questions

### "Is this really the shortest guide?"

**Short answer**: Yes, by design. **Long answer**: The brevity proves the PIV Loop thesis — thorough planning makes implementation simple. The execute command is straightforward because all the intelligence is in the structured plan. Implementation is the thin layer in the sandwich metaphor (thick planning → thin execution → thick validation).

### "When should I use meta-reasoning vs just fixing the issue?"

**Short answer**: Always for recurring or systemic issues. **Long answer**: One-off fixes are acceptable for truly unique, unrepeatable problems. But if you've seen the issue before, or it feels like a category of problem (e.g., "plans are always too long"), that's a system bug. Meta-reasoning finds the root cause and fixes it permanently.

### "Should I commit buggy implementations?"

**Short answer**: Sometimes, intentionally. **Long answer**: Committing a known-buggy implementation creates a save state for comparison, validation practice (the Validation Discipline guide uses the streaming bug for this), and teaching. But don't commit security issues or broken interfaces others depend on. Label intentional bug commits clearly.

### "How do I know when to speed up (skip vibe planning)?"

**Short answer**: When you've done 3+ similar features with reliable results. **Long answer**: Speed is earned through repetition. Your commands must produce consistent output, the AI must be able to reference previous implementations, and your system must be evolved through meta-reasoning. If in doubt, do the vibe planning — thoroughness is always safer than speed.

### "What if my execute command produces poor results?"

**Short answer**: Apply meta-reasoning to find the root cause. **Long answer**: The issue is rarely the execute command itself. Check: Is the plan quality sufficient? (Go back to `/planning`.) Are patterns documented with code examples? (Go back to research.) Are validation commands specified? (Update the plan template.) The execute command is only as good as the plan it consumes.

---

## Next Steps

1. Read `sections/02_piv_loop.md` for the always-loaded PIV Loop overview
2. Read `.claude/commands/execute.md` to see the current execute command implementation
3. Try Exercise 1 — run a complete PIV loop on a small feature
4. Apply meta-reasoning to one issue you encounter (Exercise 2)
5. Review the planning-methodology skill for the planning phase that feeds into execution
6. Move to the Validation Discipline guide — validation strategies, the 5-level validation pyramid, `/code-review` and `/execution-report` commands, divergence analysis with `/system-review`, and how validation feeds back into system evolution

---

## Related Resources

- **PIV Loop overview**: `sections/02_piv_loop.md` — always-loaded overview of Plan → Implement → Validate
- **Command design**: `reference/command-design-framework.md` — on-demand command design with meta-reasoning overview
- **Execute command**: `.claude/commands/execute.md` — the actual execute command implementation
- **Structured Plan Template**: `templates/STRUCTURED-PLAN-TEMPLATE.md` — the plan format that `/execute` consumes
- **Planning Methodology skill** (prerequisite): `.claude/skills/planning-methodology/` — planning phase that feeds into execution
- **Validation Discipline guide** (next): `reference/validation-discipline.md` — validation phase that follows execution

---

**That's the Implementation Discipline guide!** You now understand:
- The execute command's two critical components (thoroughness + task handling)
- Navigate → Implement → Verify per-task pattern
- Custom workflow injection (Archon, memory.md, task management)
- Meta-reasoning: the 5-step system evolution technique
- The WHERE-to-fix decision framework (5 locations)
- Research validation — verify before building the plan
- Save states and three rollback scenarios
- Generic vs project-customized command evolution
- Speed and trust progression — when to accelerate

**Ready for the Validation Discipline guide?** Learn validation discipline — the 5-level validation pyramid, `/code-review` and `/execution-report` commands, divergence analysis with `/system-review`, and how validation feeds back into system evolution.
