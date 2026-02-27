---
name: planning-methodology
description: Guide for systematic interactive planning with template-driven output and confidence scoring
license: MIT
compatibility: opencode
---

# Planning Methodology — Interactive Discovery + Structured Output

This skill provides the knowledge framework for transforming feature requests into comprehensive implementation plans. It complements the `/planning` command — the command provides the interactive discovery workflow, this skill provides the structured output methodology.

## When This Skill Applies

- User asks to "plan a feature", "create an implementation plan", or "structure development work"
- A feature request needs to be broken down before implementation
- Moving from vibe planning (unstructured) to structured planning (Layer 2)
- Inside `/build` when generating standard or heavy plans

## The Discovery-to-Plan Flow

The `/planning` command drives an interactive conversation with the user. This skill defines what the plan artifact should contain and how to produce it.

### Phase 1: Understand (Interactive)
**Goal**: Define WHAT we're building and WHY — through conversation, not automation.
- Ask questions, confirm intent, discuss tradeoffs with the user
- Check `memory.md` for past decisions about this feature area
- Check `specs/build-state.json` for context from prior specs
- Output: Clear shared understanding of scope and approach

### Phase 2: Explore (Codebase Intelligence)
**Goal**: Ground the plan in reality by exploring the codebase.
- **Local exploration**: Use Glob, Grep, Read to find patterns and integration points
- **Archon MCP** (if available): `rag_search_code_examples` for similar implementations
- **Dispatch** (optional): Send targeted research queries to free models
- Share findings with the user as you discover them
- Output: File references with line numbers, patterns to follow, gotchas identified

### Phase 3: Design (Strategic Decisions)
**Goal**: Lock in the implementation approach.
- Propose approach with alternatives and tradeoffs
- For non-trivial decisions, suggest `/council` for multi-model input
- Get explicit user confirmation before proceeding
- Output: Locked approach, key decisions documented

### Phase 4: Preview + Approval
**Goal**: Validate direction before writing the full plan.
- Show a 1-page preview: what, approach, files, key decision, risks, tests
- Get explicit approval before writing the plan file
- Output: User approval to proceed

### Phase 5: Write Plan
**Goal**: Generate the structured plan document at the appropriate depth.
- **Light (~100 lines)**: What, Files, Tasks with validation, Acceptance criteria
- **Standard (~300 lines)**: + Feature Description, Solution Statement, Patterns, Code Samples, Testing, Edge Cases
- **Heavy (~700 lines)**: + Alternatives Considered, Risk Analysis, Integration Tests, detailed Phase breakdown

## Plan Quality Requirements

1. **Template-driven**: All plans fill sections of `templates/STRUCTURED-PLAN-TEMPLATE.md`
2. **Evidence-backed**: Every file reference has line numbers; every pattern has a code example from THIS project
3. **Executable tasks**: Each task includes ACTION, TARGET, IMPLEMENT, and VALIDATE at minimum
4. **No-prior-knowledge test**: Another session can execute the plan without additional context
5. **Approval gate**: Preview shown and approved before writing the final plan file

### The 7-Field Task Format (for heavy plans)

Every task in a heavy plan MUST include ALL fields:

| Field | Purpose | Example |
|-------|---------|---------|
| **ACTION** | What operation | CREATE / UPDATE / ADD / REMOVE / REFACTOR |
| **TARGET** | Specific file path | `app/services/auth_service.py` |
| **IMPLEMENT** | Code-level detail | "Class AuthService with methods: login(), logout()" |
| **PATTERN** | Reference pattern | "Follow pattern in `app/services/user_service.py:45-62`" |
| **IMPORTS** | Exact imports | Copy-paste ready import statements |
| **GOTCHA** | Known pitfalls | "Must use async/await — the database client is async-only" |
| **VALIDATE** | Verification command | `pytest tests/services/test_auth.py -v` |

Light and standard plans use a reduced format (ACTION, TARGET, IMPLEMENT, VALIDATE minimum).

## Archon RAG Integration

If Archon MCP is available, search curated knowledge FIRST:
1. `rag_get_available_sources()` — find indexed documentation
2. `rag_search_knowledge_base(query="2-5 keywords")` — search docs
3. `rag_search_code_examples(query="2-5 keywords")` — find code patterns
4. **Critical**: Keep queries SHORT — 2-5 keywords maximum for best vector search results

If Archon unavailable, proceed with local exploration and web search.

## Key Rules

1. **Discovery first, plan second.** Do NOT auto-generate. Work WITH the user.
2. **Plan depth scales with complexity.** Light for scaffolding, heavy for core logic.
3. **No code in planning.** Plans produce documents, not implementations.
4. **Research validation.** Verify all findings before building the plan on them.
5. **Agent-to-agent optimization.** The plan is consumed by `/execute` in a fresh session — it must be self-contained.

## Output

Save to: `requests/{spec-number}-{spec-name}-plan.md`
(or `requests/{descriptive-name}-plan.md` for standalone planning)

Use template: `templates/STRUCTURED-PLAN-TEMPLATE.md` — every section filled with feature-specific content.

## Detailed References

For template section-filling guide:
@references/template-guide.md

For detailed phase-by-phase research methodology:
@references/6-phase-process.md

## Related Commands

- `/planning [feature]` — The interactive discovery workflow that uses this methodology
- `/execute [plan-path]` — Implements the plan this methodology produces
- `/build [spec]` — Wraps planning + execution in an automated loop
- `/prime` — Load context before starting planning
