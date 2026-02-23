# PIV Loop in Practice: Planning, Implementation & Validation

This guide explains **how to apply the PIV Loop methodology in practice** — covering Layer 1 vs Layer 2 planning, the 4 Pillars of Context Engineering, implementation with fresh context, systematic validation, and practical iteration patterns — going deeper than the always-loaded overview in `sections/02_piv_loop.md`.

---

## 1. From Concept to Practice: What This Guide Covers

### The Journey from Theory to Action

The System Foundations guide established the foundation — the **why** behind the PIV Loop, the system gap between average and exceptional AI coding, and the overall architecture. This guide takes that foundation and makes it **actionable**. You'll see the complete Plan -> Implement -> Validate cycle in practice, demonstrated through a real project: the **Obsidian Second Brain AI Assistant**.

This isn't a toy example. The Obsidian project is a production-ready FastAPI + Pydantic AI backend with:
- OpenAI-compatible API
- Tool-based agent design
- Vertical slice architecture
- Full test coverage
- Structured logging

This project becomes the running example for the rest of the system, providing concrete patterns you can adapt to your own work.

### What You'll Learn in This Guide

**Layer 1 Planning — Global Rules** (done once):
- How to create CLAUDE.md with 6 essential sections
- Why global rules matter (the with/without comparison)
- What belongs in Layer 1 vs what doesn't
- How to maintain your "AI layer" over time

**Layer 2 Planning — Task Planning** (done every feature):
- Vibe planning: exploratory, unstructured conversation with AI
- Structured planning: turning conversations into detailed execution plans
- The handoff between vibe and structured (when to transition)
- When to invest in structured plans vs quick prompts

**The 4 Pillars of Context Engineering**:
- Memory (short-term conversation + long-term memory.md)
- RAG (external docs, library references, task specifications)
- Prompt Engineering (be explicit, reduce AI assumptions)
- Task Management (clear step-by-step execution)

**Implementation with Fresh Context**:
- Why starting a new conversation matters
- How to feed only the structured plan (not vibe planning)
- Trust but verify principle in practice
- When to pause and update the plan

**Systematic Validation**:
- The 5-level validation pyramid (order matters!)
- What AI validates vs what humans validate
- Validation report formats
- When validation failures reveal system issues

**Git Save Points Strategy**:
- Commit plans BEFORE implementation
- Rollback strategies when things go wrong
- Why save points enable confident experimentation

### Why This Guide Matters

The System Foundations guide showed you the gap. This guide shows you the bridge.

The difference between:
- **Vibe planning** (exploratory, unstructured, discovering the approach) — perfectly fine
- **Vibe coding** (letting AI make up the approach as it goes) — chaotic, unpredictable

This guide teaches you to plan deliberately while coding systematically. This distinction is the key to reliable AI-assisted development.

---

## 2. Layer 1 Planning: Global Rules (CLAUDE.md)

### What Layer 1 Is

Layer 1 = **done once, updated rarely**. It creates your "AI layer" — the rules, constraints, and conventions that govern how AI works on your code.

Think of CLAUDE.md as the constitution for your project. It doesn't change with every feature, but it profoundly shapes every feature you build.

### The 6-Section CLAUDE.md Structure

**1. Core Principles** (non-negotiable rules):
```
- TYPE SAFETY IS NON-NEGOTIABLE
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)
- DRY (Don't Repeat Yourself)
```

These aren't suggestions—they're hard constraints that the AI must follow.

**2. Tech Stack** (what you're using):
```
- Language: Python 3.12
- Package Manager: UV
- Framework: FastAPI + Pydantic AI
- Linting: Ruff + mypy (strict mode)
- Logging: Structlog (AI-optimized)
- Testing: Pytest with markers
```

Clear tech stack definition prevents AI from hallucinating alternatives.

**3. Architecture** (how code is organized):
```
src/
├── agent/    # Core orchestration
├── openai/   # OpenAI compatibility layer
├── tools/    # Independent slices (web_search, image_analysis, etc.)
└── shared/   # Cross-cutting (config, logging, middleware)

Each tool = vertical slice with tool.py, schemas.py, service.py
```

Explicit directory structure prevents AI from creating random organizational patterns.

**4. Documentation Standards** (how to document):

For the Obsidian project, there's a special tool documentation format:
- One-line summary
- "Use this when" (affirmative guidance)
- "Do NOT use this for" (negative guidance)
- Parameter guidance (WHY to choose different values)
- Performance notes (token usage, execution time)
- Realistic examples

Standard code uses Google-style docstrings.

**5. Logging Rules** (how to log):

Philosophy: Logs optimized for AI agent consumption.

**MUST**:
- Import shared logger: `from src.shared.logging import get_logger`
- Use structured logging (keyword arguments only)
- Descriptive event names (snake_case, answers "what happened?")
- `logger.exception()` in except blocks
- Include debugging context (IDs, input values, metrics)

**DO NOT**:
- Log sensitive data (passwords, API keys, tokens)
- Use string formatting (f-strings in logs)
- Spam logs in loops
- Silently catch exceptions

**6. Testing Patterns** (how to test):

Structure:
- Tests mirror source directory
- `src/shared/logging.py` -> `tests/shared/test_logging.py`

Markers:
- `@pytest.mark.unit` for unit tests
- `@pytest.mark.integration` for integration tests

Commands:
- `uv run pytest tests/ -m unit`
- `uv run pytest tests/ -m integration`

### Why CLAUDE.md Matters

**Without it**: AI has no context about your conventions, makes random decisions, produces inconsistent code.

**With it**: AI follows your rules automatically, produces code that looks like you wrote it, maintains patterns across features.

Layer 1 is the foundation of the PIV Loop. Everything else builds on these stable global rules.

---

## 3. Layer 2 Planning: Task Planning (Every Feature)

### The Two-Phase Approach

Layer 2 planning happens **every feature**. It has two distinct phases:

### Phase 1: Vibe Planning (Unstructured)

**Goal**: Get on the same page with AI about what to build.

**Characteristics**:
- **Unstructured** — no template, just conversation
- **Exploratory** — research options, discuss tradeoffs
- **Collaborative** — ask questions back and forth
- **Context building** — AI learns codebase patterns
- **Duration**: 10-30+ minutes (whatever it takes)

**Example Prompts**:

```
Prompt 1:
Please explore the src/agent/agent.py and core file in src/shared
and deeply understand how the src/tools/obsidian_note_manager tool is built.

---

Prompt 2:
I want to build a tool similar to the note manager tool where
the agent can also operate on folders, rename, move create, delete etc.
Explore our options for how we can build this, do any necessary research online.

Report back to me the options in this format:
Option:
Description of option:
Tradeoffs:
Effort:

---

Prompt 3:
What libraries and technologies would we need and would this solution
support win/lin/mac? What else do we need to think about during implementation?

I'm leaning heavily on option #X, so a combination of that and also
adding batch support in the batch tool for folder operations.

---

Prompt 4:
We want to ensure that the agent can only operate on folders in our vault
that is specified in the env, you can see from the .env.example file how
we load this variable so the agent should only be able to operate on
folders in the vault.
```

See `templates/VIBE-PLANNING-GUIDE.md` for more examples.

### Phase 2: Structured Plan

**Goal**: Turn conversation into a detailed plan of attack.

Once you've explored the approach through vibe planning, create a structured plan that captures:
- Feature description and user story
- Solution approach (with decisions from vibe planning)
- Relevant files to read (for AI to learn patterns)
- Research documentation (external sources discovered)
- Implementation plan (Foundation -> Core -> Integration)
- Step by step task list (atomic, ordered by dependency)
- Testing strategy (unit, integration, edge cases)
- Acceptance criteria (specific, measurable)
- Validation commands (how to verify 100% correctness)

Use `templates/STRUCTURED-PLAN-TEMPLATE.md` as your guide.

**Target length**: 700-1000 lines. Comprehensive with feature-specific content. You've failed if under 700 lines. Complex features target 1000. Sub-plans (decomposed mode) target 500-700 lines.

**Save location**: `requests/{feature}-plan.md`

### The Handoff: When to Transition

Move from vibe planning to structured planning when:
- You understand the problem fully
- You've explored options and chosen an approach
- You know which files need to change
- You've researched necessary libraries/patterns
- You have a clear picture of the implementation

Don't rush this transition. Vibe planning builds essential context. Structured planning channels that context into execution.

### When to Create Structured Plans

**Always create structured plans** for:
- Non-trivial features (more than 2-3 file changes)
- Features touching unfamiliar code
- Features requiring new libraries or patterns
- Features with multiple valid approaches
- Features you want to review before implementing

**Skip structured plans** for:
- Single-line bug fixes
- Obvious typo corrections
- Simple refactorings with clear scope

### Planning Pattern: Exact Before/After Blocks

For **text-centric changes** — templates, commands, configs, documentation — include exact content blocks in each task instead of prose descriptions:

```
**Current** (lines X-Y):
{exact content being replaced}

**Replace with**:
{exact replacement content}
```

**Why this works**: The executor copies the replacement verbatim instead of interpreting prose. This eliminates ambiguity — the most common source of plan-to-implementation divergence.

**When to use**:
- Modifying markdown templates or command files
- Updating configuration files (YAML, JSON, TOML)
- Changing documentation sections with specific formatting
- Any change where the exact output matters more than the logic

**When NOT to use**:
- Writing new code with complex logic (prose + pattern references are better)
- Creating new files from scratch (no "current" to show)
- Changes that depend on runtime values or dynamic context

**Evidence**: The prime-codebase-redesign plan (`requests/prime-codebase-redesign-plan.md`) used this format for all 4 tasks and achieved 100% plan-to-implementation fidelity — zero divergences. See `requests/system-reviews/prime-codebase-redesign-review.md` for the full analysis.

---

## 4. The 4 Pillars of Context Engineering

These pillars ensure your structured plan has ALL the context AI needs for successful implementation.

### Pillar 1: Memory

**Short-term**: The vibe planning conversation (same session).

Use the ENTIRE vibe planning conversation as context for structured planning. Reference decisions made during exploration, cite specific options discussed and why you chose one.

**Long-term**: `memory.md` for cross-session recall.

The `/planning` command reads `memory.md`:
- Checks for past decisions about this feature area
- Reviews gotchas in affected systems
- Looks for relevant patterns from past features

The `/commit` command appends to `memory.md`:
- Records lessons learned
- Documents gotchas discovered
- Captures key decisions made

This creates a natural accumulation loop: lessons from past sessions inform future planning.

**How to apply**:
- Always do vibe planning in the same session before structured planning
- Read `memory.md` for relevant past experiences
- Reference specific decisions in your structured plan

### Pillar 2: RAG (Retrieval Augmented Generation)

**What**: External documentation, library references, past projects, task specifications.

**How to apply**:
- Include links to official docs you researched (with specific sections)
- Reference similar code from other projects
- Link to relevant Stack Overflow answers, GitHub issues
- Attach task specifications from PM tools (Linear, Jira, Asana)

**Example**:

If your project has task specifications (e.g., `tasks/backend-filtering.md`, `tasks/frontend-ui.md`) or API contracts, attach them as RAG context loaded into your plan. Similarly, link to relevant PM tool exports (Linear, Jira, Asana) or design documents.

**Best practice**: Don't just link—cite specific sections with anchors. "See Django QuerySet docs, section 'Complex lookups with Q objects'" is better than "See Django docs."

### Pillar 3: Prompt Engineering

**Principle**: Be explicit, reduce AI assumptions.

**How to apply**:
- Specify exact file paths, not general areas
- Include examples from your codebase to emulate
- State what NOT to do (negative guidance)
- Define success criteria unambiguously

**Bad**: "Add authentication to the API"
**Good**: "Add JWT authentication following the pattern in `src/auth/jwt.py:45-62`. Store tokens in HttpOnly cookies with 24-hour expiration. Implement refresh token rotation using the middleware in `src/shared/middleware.py`."

### Pillar 4: Task Management

**What**: Clear step-by-step task list.

**How to apply**:
- Break feature into atomic tasks (30 min - 4 hours each)
- Order tasks by dependency
- Include validation steps per task
- Make each task actionable (not vague)

**Example task format**:

```markdown
For tool implementations:
- Define Pydantic schemas in `schemas.py`
- Implement tool with structured logging and type hints
- Register tool with Pydantic AI agent
- Create unit tests in `tests/tools/<name>/test_<module>.py`
- Add integration test in `tests/integration/` if needed
```

### The Compound Effect

When you apply all 4 pillars together:
- **Memory** + **RAG** + **Prompt Engineering** + **Task Management**
- = AI has EVERYTHING it needs to build exactly what you want

Each pillar alone helps. All 4 together are transformative.

---

## 5. Implementation with Fresh Context

### Why Fresh Context Matters

After vibe planning and structured planning, you often start a **NEW conversation** for implementation.

**Why?**

- Vibe planning creates exploration context (options, tradeoffs, research)
- Structured plan distills that into execution context (decisions, approach, tasks)
- Implementation needs execution context, not exploration context
- Fresh context = clean slate focused on the approach, not the discovery process

### The Basic Implementation Prompt

```markdown
Read coding-prompt.md and implement the complete feature following all steps.

Follow the patterns in CLAUDE.md.

Execute every step in order:
1. Implement all components (models, services, APIs, tools)
2. Write or update tests
3. Run all validation commands
4. Ensure all tests pass
5. IMPORTANT: Do not stop until the entire plan is fulfilled

Report back when complete.
```

Or use the `/execute` command with your plan path.

### Key Principles

**1. Feed ONLY the Structured Plan**

Don't feed the vibe planning conversation. The plan already contains the decisions—implementation just needs to execute.

**2. Trust but Verify**

- Let AI work through the plan autonomously
- Watch loosely—don't micromanage every line
- Check at key milestones (after each major section)
- If AI deviates from the plan, redirect it back

**3. Reference the Plan Throughout**

- Keep plan open in another window
- AI should consult plan at each step
- Major deviations -> pause and update plan first

**4. Stay in Driver's Seat**

- You defined the approach in planning
- Implementation is execution, not decision-making
- If new decisions emerge, update the plan before proceeding

### When to Pause and Adjust the Plan

Pause implementation and update the plan when:
- You discover the approach won't work (technical limitation)
- Requirements change mid-implementation
- You find a significantly better pattern
- The plan is ambiguous about a critical decision

Don't power through with a flawed plan. Fix the plan, commit it, then resume implementation.

---

## 6. Systematic Validation

### The 5-Level Validation Pyramid

Validation happens in strict order. Each level gates the next. **Don't run unit tests if linting fails.**

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

**Level 1 — Syntax & Style**:
```bash
# Ruff Linting Check
uv run ruff check src/

# Ruff Formatting Check
uv run ruff format --check src/
```

Catch obvious errors fast. Fix immediately.

**Level 2 — Type Safety**:
```bash
# Mypy Type Checking (Strict Mode)
uv run mypy src/
```

Catch type errors before runtime. Strict mode recommended.

**Level 3 — Unit Tests**:
```bash
# Unit Tests
uv run pytest tests/ -m unit -v
```

Test isolated functions and classes. Verify logic correctness.

**Level 4 — Integration Tests**:
```bash
# Start server first
uv run uvicorn src.main:app --host 0.0.0.0 --port 8030 --reload

# Then run integration tests
uv run pytest tests/ -m integration -v
```

Test system interactions. Verify components work together.

**Level 5 — Human Review**:
- Code review (git diffs)
- Manual testing (UI, workflows)
- Alignment with intent (does it solve the right problem?)
- Edge cases not covered by tests

### Validation Report Format

**On success**:
```
Validation Results
-------------------------------------------------------------------
PASSED Ruff Linting: PASSED (0 issues)
PASSED Ruff Formatting: PASSED
PASSED Mypy Type Checking: PASSED
PASSED Unit Tests: PASSED (42 tests, 2.5s)
PASSED Integration Tests: PASSED

-------------------------------------------------------------------
Status: ALL CHECKS PASSED
```

**On failure**:
```
Validation Results
-------------------------------------------------------------------
FAILED Ruff Linting: FAILED (12 issues)
PASSED Ruff Formatting: PASSED
FAILED Mypy Type Checking: FAILED (3 errors)
PASSED Unit Tests: PASSED
FAILED Integration Tests: FAILED

-------------------------------------------------------------------

Issues Found: 15 total

Linting Issues (12):
- [file:line] Issue description

Type Errors (3):
- [file:line] Issue description

-------------------------------------------------------------------
Status: VALIDATION FAILED
```

### What AI Validates vs What Humans Validate

**AI Validates**:
- Linting (syntax, style)
- Type checking (type safety)
- Unit tests (isolated logic)
- Integration tests (system behavior)

**Humans Validate**:
- Code review (patterns, design)
- Manual testing (real usage)
- Alignment with intent (right solution?)
- Edge cases not covered by tests

See `reference/validation-discipline.md` for the complete 5-level pyramid explanation.

---

## 7. Git Save Points Strategy

### The Core Pattern

**ALWAYS commit the plan BEFORE implementation**:

```bash
git add requests/{feature}-plan.md
git commit -m "plan: {feature} structured plan"
```

This creates a save point. If implementation goes wrong, you can return to this exact state.

### If Implementation Fails

```bash
git stash  # or git checkout .
# Tweak the plan based on what you learned
# Retry implementation with updated plan
```

### Why Save Points Work

- Every plan = checkpoint you can return to
- Implementation failures don't destroy planning work
- Easy to retry with refined approach
- Git history shows decision trail

This enables **confident experimentation**. You can try bold approaches knowing you can always revert to the last working state.

### The Full Workflow

1. **Vibe plan** (explore, discuss, research)
2. **Create structured plan** -> `requests/{feature}-plan.md`
3. **Commit the plan** -> `git commit -m "plan: {feature}"`
4. **Implement** (new conversation, feed plan)
5. **Validate** (5-level pyramid)
6. **If fails** -> `git stash`, update plan, retry
7. **If passes** -> `git commit -m "feat: {feature}"`

See `sections/04_git_save_points.md` for more details.

---

## 8. Common Questions (FAQ)

### Should I create a structured plan for every feature?

**Short answer**: Yes, if the feature is non-trivial.

**Long answer**: Create structured plans when:
- Feature touches more than 2-3 files
- Feature requires unfamiliar libraries or patterns
- Multiple valid approaches exist
- You want to review the approach before implementing
- The feature is complex enough that "winging it" feels risky

Skip structured plans for:
- Single-line bug fixes
- Obvious typo corrections
- Simple refactorings with crystal-clear scope

When in doubt, create the plan. Planning is not extra work—it saves time during implementation and debugging.

### What if planning takes too long?

Planning FEELS like extra work upfront, but the math tells a different story:

**Without planning**:
- 0 minutes planning
- 60 minutes coding + debugging
- 40 minutes rework (AI went wrong direction)
- **Total: 100 minutes**

**With planning**:
- 15 minutes vibe planning
- 10 minutes structured planning
- 60 minutes coding (less debugging because approach is clear)
- 10 minutes validation (catches issues early)
- **Total: 95 minutes**

Planning saves time overall. Plus, the plan becomes documentation for future you and your team.

### How is this different from the System Foundations guide?

**The System Foundations guide** established the **why** and **what**:
- Why the PIV Loop exists (the system gap)
- What mastery looks like (88% vs 30% acceptance)
- Trust progression and the overall architecture
- Baseline self-assessment framework
- Understanding AI strengths and limitations

**This guide** teaches the **how**:
- How to create Layer 1 rules (CLAUDE.md)
- How to do Layer 2 planning (vibe -> structured)
- How to apply the 4 Pillars in practice
- How to implement with fresh context
- How to validate systematically
- How to use git save points for confident iteration

The System Foundations guide is foundational concepts. This guide is practical execution.

### Can I skip vibe planning and go straight to structured planning?

No. Vibe planning builds essential context.

Vibe planning is where you:
- Explore the codebase to understand existing patterns
- Research libraries and discover best practices
- Discuss tradeoffs between different approaches
- Ask questions and clarify requirements
- Build shared understanding with the AI

If you skip this and jump to a structured plan, you're guessing. The structured plan will be shallow, miss important patterns, and require rework during implementation.

Vibe planning is exploratory. Structured planning is synthesis. You need exploration before synthesis.

### What's the difference between "vibe planning" and "vibe coding"?

This distinction is critical:

**Vibe planning** (exploratory, unstructured) = **GOOD**
- Discovering the right approach through conversation
- Researching options and discussing tradeoffs
- Learning codebase patterns
- No template needed—just explore

**Vibe coding** (letting AI make up approach as it goes) = **BAD**
- AI guesses at patterns instead of following explicit plan
- Inconsistent results
- High debugging cost
- No documentation trail

**The rule**: Plan casually (vibe planning is fine). Code systematically (always follow a structured plan).

---

## 9. Key Principles

### Vibe Planning is Okay, Vibe Coding is Not

Planning can be casual and exploratory—that's vibe planning, and it's valuable.

Coding must be systematic and planned—never let AI "vibe code" (make up the approach as it goes).

### Layer 1 vs Layer 2: Different Purposes

**Layer 1** (CLAUDE.md):
- **Done once** (updated rarely)
- **Stable foundation** (tech stack, core principles, architecture)
- **Applies to all features** (global rules)

**Layer 2** (feature plans):
- **Done every feature** (task-specific)
- **Detailed approach** (specific decisions for this feature)
- **Applies to one feature** (local context)

Don't confuse them. Global rules stabilize the system. Feature plans adapt to specific requirements.

### Context Engineering Compound Effect

Each of the 4 Pillars helps individually:
- Memory alone improves continuity
- RAG alone improves research
- Prompt Engineering alone improves clarity
- Task Management alone improves organization

But when you apply **all 4 together**, the effect compounds:
- Memory + RAG = AI knows past + present
- + Prompt Engineering = AI understands exactly what you want
- + Task Management = AI has a clear execution path

This compound effect is what makes the PIV Loop transformative.

### Planning is NOT Extra Work

Planning feels like overhead, but it:
- **Saves time** in implementation (fewer mistakes, less debugging)
- **Saves time** in maintenance (plan becomes documentation)
- **Increases confidence** (predictable outcomes)
- **Builds institutional knowledge** (plans are searchable artifacts)

The upfront investment pays dividends throughout the feature lifecycle.

---

## Next Steps

1. **Read this guide** (you're doing this now)
2. **Review vibe planning examples** — see `templates/VIBE-PLANNING-GUIDE.md` for example prompts showing the exploratory conversation style
3. **Study the structured plan template** — read `templates/STRUCTURED-PLAN-TEMPLATE.md` to understand the target output format
4. **Run `/planning` command on your first feature** — use the command to generate a comprehensive plan following the 6-phase methodology
5. **Compare to ad-hoc approach** — reflect on the difference between planning first vs "winging it" (reference your baseline self-assessment)
6. **Move to the Global Rules Optimization guide** — learn how to create CLAUDE.md from scratch with the `/init-c` command and modular @sections structure

---

## Related Resources

- **PIV Loop Overview**: See `sections/02_piv_loop.md` for the core Plan -> Implement -> Validate methodology and granularity principle
- **4 Pillars of Context Engineering**: See `sections/03_context_engineering.md` for Memory, RAG, Prompt Engineering, and Task Management definitions
- **Layer 1 Guide**: See `reference/layer1-guide.md` for the complete guide to creating CLAUDE.md for real projects
- **Validation Discipline**: See `reference/validation-discipline.md` for the complete 5-level validation pyramid
- **Structured Plan Template**: `templates/STRUCTURED-PLAN-TEMPLATE.md` — the template used by `/planning` command for Layer 2 plans
- **Vibe Planning Examples**: `templates/VIBE-PLANNING-GUIDE.md` — example prompts showing the exploratory planning phase

---

**That's the PIV Loop in Practice!** You now understand:
- Layer 1 planning (CLAUDE.md with 6 sections)
- Layer 2 planning (vibe -> structured)
- The 4 Pillars of Context Engineering
- Implementation with fresh context
- Systematic validation (5-level pyramid)
- Git save points strategy
- The difference between vibe planning (good) and vibe coding (bad)
- How this guide bridges theory (System Foundations) to practice

**Ready for the next step?** See `reference/global-rules-optimization.md` to learn how to create modular CLAUDE.md files with @sections, generate global rules automatically with `/init-c`, and build on-demand reference guides.
