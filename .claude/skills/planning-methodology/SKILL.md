---
name: planning-methodology
description: "Guide for systematic 6-phase feature planning. Use when creating implementation plans, planning features, or structuring development work. Provides the PIV Loop Layer 2 planning methodology with template-driven output and confidence scoring."
allowed-tools: ["Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"]
---

# Planning Methodology — 6-Phase Feature Planning

This skill provides the methodology for transforming feature requests into comprehensive implementation plans. It complements the `/planning` command — the command provides the execution workflow, this skill provides the knowledge framework.

## When This Skill Applies

- User asks to "plan a feature", "create an implementation plan", or "structure development work"
- A feature request needs to be broken down before implementation
- Moving from vibe planning (unstructured) to structured planning (Layer 2)

## The 6 Phases (Overview)

### Phase 1: Feature Understanding & Scoping
**Goal**: Define WHAT we're building and WHY.
- Parse requirements, create user story, define problem/solution
- Fill: Feature Description, User Story, Problem Statement, Solution Statement, Feature Metadata
- Check memory.md (if it exists) for past decisions about this feature area

### Phase 2: Codebase Intelligence (Direct Exploration)
**Goal**: Understand the existing codebase patterns.
- Use Glob and Grep tools directly to explore the codebase
- Find similar implementations, map integration points, extract project patterns
- Fill: Relevant Codebase Files (with line numbers), New Files to Create, Patterns to Follow

### Phase 3: External Research (Direct Lookup)
**Goal**: Gather external documentation and best practices.
- Use WebSearch and WebFetch to find documentation directly
- Find library docs, best practices, version compatibility, gotchas
- If Archon RAG available: search curated knowledge base FIRST (2-5 keyword queries)
- Fill: Relevant Documentation, Related Memories

### Phase 3b: Research Validation
**Goal**: Verify all research before building the plan on it.
- Cross-check code patterns still exist, library versions are current, file references are accurate
- Flag contradictions between research sources
- No plan section should be built on unverified research

### Phase 4: Strategic Design & Synthesis
**Goal**: Design the implementation approach.
- Synthesize validated research from Phases 2, 3, and 3b
- Design implementation phases: Foundation → Core → Integration → Testing
- Plan testing strategy (unit, integration, edge cases)
- Define measurable acceptance criteria
- Fill: Implementation Plan, Testing Strategy, Acceptance Criteria

### Phase 5: Step-by-Step Task Generation
**Goal**: Create atomic, executable tasks.
- Break Phase 4 design into atomic tasks ordered by dependency
- Every task MUST include all 7 fields:
  - **ACTION**: CREATE / UPDATE / ADD / REMOVE / REFACTOR / MIRROR
  - **TARGET**: Specific file path
  - **IMPLEMENT**: Code-level detail
  - **PATTERN**: Reference to codebase pattern (file:line)
  - **IMPORTS**: Exact imports needed
  - **GOTCHA**: Known pitfalls
  - **VALIDATE**: Executable verification command
- Fill: STEP-BY-STEP TASKS section

### Phase 6: Quality Validation & Confidence Score
**Goal**: Compile validation commands and assess confidence.
- 5-level validation commands (syntax, types, unit tests, integration tests, manual)
- Completion checklist
- Confidence score (X/10) with strengths, uncertainties, mitigations
- Fill: Validation Commands, Completion Checklist, Notes

## Key Rules

1. **Template is the control mechanism**: All research fills specific sections of `templates/STRUCTURED-PLAN-TEMPLATE.md`. Nothing is missed because the template specifies exactly what's needed.
2. **700-1000 lines**: The completed plan must be 700-1000 lines. Comprehensive with feature-specific content in every section. Sub-plans in decomposed mode must be 500-700 lines.
3. **Sequential research**: Explore codebase and external docs directly using Glob, Grep, WebSearch. No parallel agent spawning.
4. **No code in planning**: We do NOT write code in this phase. Goal is a context-rich plan for one-pass implementation.
5. **Agent-to-agent optimization**: The plan is consumed by `/execute` in a fresh conversation. It must contain ALL information needed — patterns, file paths with line numbers, exact commands.
6. **Research validation**: Validate vibe planning research before building the structured plan on it.
7. **Archon RAG first**: If available, search Archon curated knowledge before generic web search. Keep queries SHORT (2-5 keywords).
8. **Recommended model**: Start planning sessions with `claude --model opus`. Opus's deeper reasoning produces higher-quality plans — better scoping, more thorough codebase analysis, higher confidence scores. Sonnet works for simple features.

## Output

Save to: `requests/{feature-name}-plan.md`

Use template: `templates/STRUCTURED-PLAN-TEMPLATE.md` — every section must be filled with feature-specific content, not generic placeholders.

## Detailed References (Tier 3 — Load When Actively Planning)

For detailed phase-by-phase instructions:
@references/6-phase-process.md

For template section-filling guide:
@references/template-guide.md

## Related Commands

- `/planning [feature]` — The execution workflow that uses this methodology
- `/execute [plan-path]` — Implements the plan this methodology produces
- `/prime` — Load context before starting planning
