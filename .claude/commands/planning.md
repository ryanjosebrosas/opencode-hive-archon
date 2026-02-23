---
description: "Create comprehensive feature plan with deep codebase analysis and research"
argument-hint: [feature-description]
---

# Planning: Comprehensive Feature Plan

## Feature Request

$ARGUMENTS

## Mission

Transform this feature request into a **comprehensive implementation plan** through systematic codebase analysis, external research, and strategic planning.

**Core Principle**: The template is the control mechanism. All research fills specific template sections. Nothing is missed because the template specifies what's needed.

**Key Rules**:
- We do NOT write code in this phase. Create a context-rich plan that enables one-pass implementation.
- The completed plan MUST be **700-1000 lines minimum**. You have failed if under 700 lines. Complex features should target 1000. Every section must have feature-specific content, not placeholders.

## Determine Feature Name

Create a concise kebab-case feature name (e.g., "user-authentication", "payment-processing").

**Feature Name**: [create-feature-name]
**Plan File**: `requests/[feature-name]-plan.md`

---

## THE TEMPLATE (CONTROL MECHANISM)

Read `templates/STRUCTURED-PLAN-TEMPLATE.md` now — it defines the exact structure. All 6 phases below fill those template sections.

---

## PHASE 0: Interactive Discovery (Vibe Planning Buddy)

**Goal**: Collaboratively discover scope, approach, and priorities before formal planning.

**Escape hatch**: If the user provides detailed requirements, references an existing plan, or wants to skip discovery — proceed to Phase 1.

**Process**:

1. **Understand the user's level**: Adapt language — technical users get architecture questions, non-technical get outcome-focused questions.
2. **Challenge constructively**: Ask probing questions to sharpen the vision — what problem does this solve? What's the simplest valuable version? Have you seen this done well?
3. **Explore inspiration**: If user has reference projects/repos, analyze their approach. If not, suggest 2-3 approaches with trade-offs.
4. **Scope negotiation**: Push back on scope creep. Suggest vertical slices. Identify hidden complexity.
5. **Confirm readiness**: Summarize agreed scope, list key decisions, get user confirmation before proceeding.

**Rules**: This is a CONVERSATION, not a checklist. Be genuinely curious. If the user has a clear vision, respect that. Spend 3-10 minutes depending on clarity.

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

After Phase 1 scopes the feature, launch **2 parallel Task agents** for codebase research. Craft each agent's prompt dynamically using the feature description, systems affected, and keywords from Phase 1.

**Launch simultaneously with Phase 3 and 3b agents** — all research agents run in parallel.

### Agent A: Similar Implementations & Integration Points (Sonnet)
- **subagent_type**: `general-purpose`
- **model**: `sonnet`
- **description**: "Find similar code and integration points"
- **Dynamic prompt must include**:
  - The feature description and systems affected from Phase 1
  - Specific Grep/Glob queries for relevant patterns (file types, function names, route patterns)
  - Instruction: "Document all relevant file paths WITH line numbers"
  - Instruction: "Identify which existing files need changes and what new files to create"
  - Instruction: "Return free-form findings with code snippets and file:line references"

### Agent B: Project Patterns & Conventions (Sonnet)
- **subagent_type**: `general-purpose`
- **model**: `sonnet`
- **description**: "Extract project patterns"
- **Dynamic prompt must include**:
  - Instruction to read 2-3 representative files in the feature area
  - Extract: naming conventions, error handling, logging, type patterns, testing approach
  - Include actual code snippets with file:line references
  - Note conventions the new feature must follow
  - Instruction: "Return free-form findings — no specific format required"

**Fallback**: If the feature is trivially simple (1-2 file changes, obvious pattern), skip agents and explore directly with Glob/Grep.

---

## PHASE 3: External Research (Parallel Agent)

**Goal**: Fill → Relevant Documentation

Launch **1 agent** simultaneously with Phase 2 agents. Skip if no external dependencies are involved (internal-only changes).

### Agent C: Documentation & Best Practices (Sonnet)
- **subagent_type**: `general-purpose`
- **model**: `sonnet`
- **description**: "Research external docs and best practices"
- **Dynamic prompt must include**:
  - The specific libraries, frameworks, or APIs involved from Phase 1
  - Instruction: "Find official documentation with specific section links"
  - Instruction: "Check version compatibility and note any breaking changes"
  - Instruction: "Identify known gotchas and recommended patterns"
  - Instruction: "Return free-form findings with doc URLs and relevant excerpts"

**Fallback**: If purely internal changes with no external dependencies, skip this agent and note "No external research needed."

## PHASE 3b: Archon RAG Research (Parallel Agent)

**Goal**: Fill → Relevant Documentation (from knowledge base)

Launch **1 agent** simultaneously with Phase 2 and Phase 3 agents. Skip if Archon MCP tools are not available.

### Agent D: Archon Knowledge Base (Sonnet)
- **subagent_type**: `general-purpose`
- **model**: `sonnet`
- **description**: "Search Archon RAG knowledge base"
- **Dynamic prompt must include**:
  - The feature description and key technologies from Phase 1
  - Instruction: "Use `rag_get_available_sources()` to discover available knowledge bases"
  - Instruction: "Search with SHORT queries (2-5 keywords) using `rag_search_knowledge_base(query='...', source_id='...', match_count=5)`"
  - Instruction: "Search for code examples using `rag_search_code_examples(query='...', match_count=3)`"
  - Instruction: "Return free-form findings with source references and relevant excerpts"

**Fallback**: If Archon MCP tools are not available, skip this agent. The main agent falls back to web search if needed.

### Phase 2c: Memory Search (if memory.md exists)

Read memory.md for past decisions, gotchas, and patterns relevant to this feature.

---

## PHASE 3c: Research Validation

After all agents return, validate their findings in the main conversation:

1. **Verify file references** — spot-check that cited file:line locations exist and contain what agents described
2. **Cross-check agents** — do Agent A and B findings align? Any contradictions about patterns or conventions?
3. **Validate external research** — are Agent C's library versions current? Are doc links valid?
4. **Validate RAG results** — are Agent D's knowledge base findings relevant and current? Cross-reference with Agent A/B codebase findings.
5. **Fill gaps** — if critical research is missing, do targeted follow-up directly with Glob/Grep/WebSearch

---

## PHASE 4: Strategic Design & Synthesis

**Goal**: Fill → Implementation Plan (phases), Testing Strategy, Acceptance Criteria

1. **Synthesize agent findings and validated research** from Phases 2, 3, 3b, & 2c — aggregate free-form agent output (Agents A-D) into the template's Context References sections (Relevant Codebase Files, Patterns to Follow, Relevant Documentation)
2. **Design implementation approach**: fit with existing architecture, dependency ordering, phases (Foundation → Core → Integration → Testing)
3. **Plan testing strategy**: unit tests, integration tests, edge cases
4. **Define acceptance criteria**: specific, measurable, includes functional requirements + test coverage + pattern compliance

---

## PHASE 4.5: Plan Decomposition Decision

**Decompose if**: High complexity, 4+ phases, 15+ tasks, 3+ systems, or user requests it.

**If decomposing**:
1. Read `templates/PLAN-OVERVIEW-TEMPLATE.md` and `templates/SUB-PLAN-TEMPLATE.md`
2. Split into sub-plans (1 phase = 1 sub-plan, max 8 tasks each)
3. Assign shared context to overview, per-phase context to sub-plans
4. Proceed to Phase 5 in "decomposed mode"

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
- `requests/{feature}-plan-overview.md` (use `templates/PLAN-OVERVIEW-TEMPLATE.md`)
- `requests/{feature}-plan-01-{phase}.md` through `-NN-` (use `templates/SUB-PLAN-TEMPLATE.md`)

Include EXECUTION ROUTING in overview: Recommended model per sub-plan (e.g., Sonnet for execution, Opus for planning).

### For Both Modes

**CRITICAL**: This plan is for ANOTHER AGENT in a fresh conversation. It must contain ALL information needed — patterns, file paths with line numbers, exact commands, documentation links.

## Confirmation

Report: feature name, plan file path, complexity, key risks, confidence score, next step (`/execute`).
