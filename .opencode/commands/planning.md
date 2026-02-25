---
description: Create comprehensive feature plan with deep codebase analysis and research
agent: build
---

# Planning: Comprehensive Feature Plan

## Feature Request

$ARGUMENTS

## Mission

Transform this feature request into a **comprehensive implementation plan** through systematic codebase analysis, external research, and strategic planning.

**Core Principle**: The template is the control mechanism. All research fills specific template sections. Nothing is missed because the template specifies what's needed.

**Key Rules**:
- We do NOT write code in this phase. Create a context-rich plan that enables one-pass implementation.
- The completed plan should be **fit-for-purpose** — comprehensive enough for one-pass implementation, no artificial constraints.
- Every section must contain feature-specific content — not generic placeholders.

## Determine Feature Name

Create a concise kebab-case feature name (e.g., "user-authentication", "payment-processing").

**Feature Name**: [create-feature-name]
**Plan File**: `requests/[feature-name]-plan.md`

---

## THE TEMPLATE (CONTROL MECHANISM)

Read `templates/STRUCTURED-PLAN-TEMPLATE.md` now — it defines the exact structure. All 6 phases below fill those template sections.

---

## MVP.md Check

**Check for `mvp.md` at repo root:**

**If EXISTS:**
1. Read `mvp.md`
2. Reference the big idea: "This feature serves: {big idea from mvp.md}"
3. Quick confirmation: "Does this still match your vision?"
4. If YES → Skip Phase 0, proceed to Phase 1
5. If NO → "What changed?" → Update mvp.md (only if user confirms vision changed)

**If NOT EXISTS:**
1. Proceed to Phase 0 (Vibe Planning)
2. After Phase 0, CREATE `mvp.md` with the big idea (one paragraph)

---

## PHASE 0: Vibe Planning (Create mvp.md if First Feature)

**Goal:** Discover the BIG IDEA through conversation. Adapt to user's energy.

**If user wants to explore:**
- Go deep — ask about inspiration, reference projects, trade-offs
- Explore options: "What if we tried X?" "Have you seen Y done well?"
- Synthesize: "So the vision is..."
- Time: 30-60 mins

**If user has clear vision:**
- Go fast — confirm understanding, identify first brick
- "What's the simplest version that solves this?"
- Time: 10-15 mins

**End of Phase 0:**
- Ask: "What's the BIG IDEA in one paragraph?"
- User responds → Write to `mvp.md` at repo root
- Confirm: "This is our vision — we'll reference it for every feature"

**mvp.md Format:**
```
# {Product Name}

{One paragraph — what you're building and why. 5-10 lines.}
```

**Rules:**
- This is a CONVERSATION, not a checklist
- Adapt to user's energy and communication style
- If user has reference projects, study them together
- End with clarity: one paragraph that captures the vision

---

### Quick Alignment (mvp.md Exists — Subsequent Features)

**When mvp.md already exists:**

1. **Read mvp.md** — understand the big idea
2. **Align this feature:** "Based on mvp.md, {feature} is part of {capability}"
3. **Quick confirm:** "Does this still match your vision?"
    - If YES → Proceed to Phase 1 (skip Phase 0)
    - If NO → "What changed?" → Discuss → Update mvp.md if vision changed
4. **Proceed to Phase 1**

**Why skip Phase 0?**
- Vision is already documented
- No need to re-discover what's already clear
- Save time for building, not re-planning

**When to ask Phase 0 questions anyway:**
- Feature seems misaligned with mvp.md
- User indicates vision might have evolved
- Feature is complex and needs deeper exploration

---

## PHASE 1: Feature Understanding & Scoping

**Goal**: Fill → Feature Description, User Story, Problem Statement, Solution Statement, Feature Metadata

1. Check memory.md for past decisions about this feature area
2. Parse the feature request. If unclear, ask user to clarify BEFORE continuing.
3. Create User Story: `As a [user], I want [goal], so that [benefit]`
4. State Problem and Solution approach
5. Document Feature Metadata: Type (New/Enhancement/Refactor/Fix), Complexity (Low/Medium/High), Systems Affected, Dependencies

---

## PHASE 2: Codebase Intelligence (Parallel Agents)

**Goal**: Fill → Relevant Codebase Files, New Files to Create, Patterns to Follow

After Phase 1 scopes the feature, delegate to **2 parallel pre-defined research agents**. Craft focused queries using the feature description, systems affected, and keywords from Phase 1.

**Launch simultaneously with Phase 3 agents** — all research agents run in parallel.

### Agent A: @research-codebase — Similar Implementations & Integration Points
- **Delegation query must include**:
  - The feature description and systems affected from Phase 1
  - Specific file patterns to search (e.g., "find route handlers in src/routes/", "find similar service patterns")
  - Instruction: "Document all relevant file paths WITH line numbers"
  - Instruction: "Identify which existing files need changes and what new files to create"

### Agent B: @research-codebase — Project Patterns & Conventions
- **Delegation query must include**:
  - Instruction to focus on 2-3 representative files in the feature area
  - Request to extract: naming conventions, error handling, logging, type patterns, testing approach
  - Instruction: "Include actual code snippets with file:line references"

**Fallback**: If the feature is trivially simple (1-2 file changes, obvious pattern), skip agents and explore directly with Glob/Grep.

---

## PHASE 3: External Research (Parallel Agent)

**Goal**: Fill → Relevant Documentation

Delegate to **1 pre-defined research agent** simultaneously with Phase 2 agents. Skip if no external dependencies are involved (internal-only changes).

### Agent C: @research-external — Documentation & Best Practices
- **Delegation query must include**:
  - The specific libraries, frameworks, or APIs involved from Phase 1
  - Request for official documentation with specific section links
  - Instruction to check version compatibility and note breaking changes
  - Request to identify known gotchas and recommended patterns
  - If Archon MCP available: "Search Archon RAG with SHORT queries (2-5 keywords)"

**Fallback**: If purely internal changes with no external dependencies, skip this agent and note "No external research needed."

### Phase 2c: Memory Search (if memory.md exists)

Read memory.md for past decisions, gotchas, and patterns relevant to this feature.

---

## PHASE 3c: Research Validation

After all agents return, validate their findings in the main conversation:

1. **Verify file references** — spot-check that cited file:line locations exist and contain what agents described
2. **Cross-check agents** — do Agent A and B findings align? Any contradictions about patterns or conventions?
3. **Validate external research** — are Agent C's library versions current? Are doc links valid?
4. **Fill gaps** — if critical research is missing, do targeted follow-up directly with Glob/Grep/WebSearch

---

## PHASE 4: Strategic Design & Synthesis

**Goal**: Fill → Implementation Plan (phases), Testing Strategy, Acceptance Criteria

1. **Synthesize agent findings** from Phases 2, 3, & 2c:
   - Extract file paths from Agent A/B "File Map" and "Findings" sections → populate **Relevant Codebase Files**
   - Extract code snippets from Agent A/B "Patterns Identified" → populate **Patterns to Follow**
   - Extract URLs and excerpts from Agent C "Findings" and "Best Practices" → populate **Relevant Documentation**
   - Extract "Suggested files to create/modify" from Agent summaries → populate **New Files to Create**

2. **Design implementation approach**: fit with existing architecture, dependency ordering, phases (Foundation → Core → Integration → Testing)

3. **Plan testing strategy**: unit tests, integration tests, edge cases

4. **Define acceptance criteria**: specific, measurable, includes functional requirements + test coverage + pattern compliance

---

## PHASE 4.5: Plan Decomposition Decision

**Decompose if**: High complexity, 4+ phases, 15+ tasks, 3+ systems, or user requests it.

**If decomposing**: Create sub-plans manually (1 phase = 1 plan file, max 8 tasks each). Each sub-plan must be self-contained with full context.

**If NOT decomposing** (default): Proceed to Phase 5 normally (single plan, 700-1000 lines).

---

## PHASE 5: Step-by-Step Task Generation

**Goal**: Fill → STEP-BY-STEP TASKS section

**Critical Rule**: Each task MUST include ALL of these fields:

- **ACTION**: CREATE / UPDATE / ADD / REMOVE / REFACTOR / MIRROR
- **TARGET**: Specific file path
- **IMPLEMENT**: What to implement (code-level detail)
- **PATTERN**: Reference to codebase pattern (file:line)
- **IMPORTS**: Exact imports needed (copy-paste ready)
- **GOTCHA**: Known pitfalls and how to avoid them
- **VALIDATE**: Executable command to verify task completion

Break Phase 4's implementation phases into atomic tasks. Order by dependency. Ensure top-to-bottom execution without backtracking.

**If decomposed mode**: Each sub-plan gets 5-8 tasks max using same 7-field format. Include HANDOFF NOTES at end of each sub-plan. Each sub-plan must be self-contained.

---

## PHASE 6: Quality Validation & Confidence Score

**Goal**: Fill → Validation Commands, Completion Checklist, Notes (including Confidence Score)

1. **Compile validation commands** (5 levels): Syntax/Style, Unit Tests, Integration Tests, Manual Validation, Additional
2. **Create completion checklist**: all tasks done, validations pass, tests pass, acceptance criteria met
3. **Assess confidence**: Score X/10, strengths, uncertainties, mitigations, key design decisions

---

## OUTPUT

### Standard Mode (default)

Save to: `requests/[feature-name]-plan.md`

Use `templates/STRUCTURED-PLAN-TEMPLATE.md`. Every section must be filled — specific, not generic.

### Decomposed Mode (from Phase 4.5)

<!-- PLAN-SERIES -->

Save to multiple files:
- `requests/{feature}-plan-01-{phase}.md` through `-NN-` (use `templates/STRUCTURED-PLAN-TEMPLATE.md`)

Include EXECUTION ROUTING at top of first sub-plan: Recommended model, shared context summary, task dependencies.

### For Both Modes

**CRITICAL**: This plan is for ANOTHER AGENT in a fresh conversation. It must contain ALL information needed — patterns, file paths with line numbers, exact commands, documentation links.

## Confirmation

Report: feature name, plan file path, complexity, key risks, confidence score, next step (`/execute`).