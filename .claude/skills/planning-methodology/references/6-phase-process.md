# 6-Phase Planning Process — Detailed Reference

This reference provides detailed instructions for each phase of the planning methodology. Load this when actively executing the planning process.

---

## Phase 1: Feature Understanding & Scoping

**Template sections to fill**: Feature Description, User Story, Problem Statement, Solution Statement, Feature Metadata

### Process

1. **Read memory.md** (if it exists) for past decisions:
   - Look for entries about this feature area under Key Decisions and Lessons Learned
   - Note any relevant context from past sessions
2. **Parse the feature request** — identify scope, affected systems, user-facing changes
3. **Clarify ambiguity** — if requirements are unclear, ask the user BEFORE continuing
4. **Create User Story**: `As a [user type], I want [action], so that [benefit]`
5. **Document Feature Metadata**:
   - Feature Type: New Capability / Enhancement / Refactor / Bug Fix
   - Estimated Complexity: Low / Medium / High
   - Primary Systems Affected: list all components/services
   - Dependencies: external libraries or services required

### Validation Gate

Can someone understand the feature without additional questions? If no, go back and clarify.

---

## Phase 2: Codebase Intelligence (Parallel Agent)

**Template sections to fill**: Relevant Codebase Files, New Files to Create, Patterns to Follow

### Agent Configuration

**Parallel Mode** (if custom research agents exist in `.claude/agents/`):
- **Detection**: `ls .claude/agents/research-*.md 2>/dev/null | wc -l`
- **Agent type**: research-codebase (custom)
- **Model**: Haiku (cost-optimized)
- **Count**: 3-5 agents, each with a focused research query
- **Tools**: Read, Glob, Grep

**Standard Mode** (fallback):
- **Agent type**: Explore (built-in, fast, read-only)
- **Model**: Haiku (cost-optimized)
- **Count**: 1 agent
- **Tools**: Read, Glob, Grep

Both modes run in parallel with Phase 3.

### What the Agent Should Find

1. **Similar implementations** — existing code doing comparable things. Document file paths WITH line numbers. Extract pattern examples from actual project code.
2. **Integration points** — existing files that must be modified, new files that must be created, how new components connect to existing ones.
3. **Project patterns** with code examples:
   - Naming conventions
   - Error handling approach
   - Logging patterns
   - Type/model patterns
   - Testing patterns
   - API/routing patterns (if applicable)
   - Database/model patterns (if applicable)

### Required Output Format

```markdown
### Relevant Codebase Files
- `path/to/file` (lines X-Y) — Why: Contains pattern for Z that we'll mirror

### New Files to Create
- `path/to/new_file` — Purpose description

### Patterns to Follow
**Pattern Name** (from `path/to/file:lines`):
[actual code snippet from project]
- Why this pattern: explanation
- Common gotchas: warnings
```

### Validation Gate

Every file reference has line numbers. Every pattern has a code example from the project. No generic references.

---

## Phase 3: External Research (Parallel Agent)

**Template sections to fill**: Relevant Documentation

### Agent Configuration

**Parallel Mode** (if custom research agents exist in `.claude/agents/`):
- **Detection**: `ls .claude/agents/research-*.md 2>/dev/null | wc -l`
- **Agent type**: research-external (custom)
- **Model**: Sonnet (synthesis quality)
- **Count**: 3-5 agents, each with a focused research query
- **Tools**: Read, Glob, Grep, WebSearch, WebFetch

**Standard Mode** (fallback):
- **Agent type**: general-purpose (built-in)
- **Model**: Sonnet (synthesis quality for documentation analysis)
- **Count**: 1 agent
- **Tools**: Read, Glob, Grep, WebSearch, WebFetch

Both modes run in parallel with Phase 2.

### What the Agent Should Find

1. **Library/framework documentation** — official docs with specific section anchors
2. **Best practices** — expert recommendations for this feature type
3. **Version compatibility** — current library versions, breaking changes, migration guides
4. **Gotchas and known issues** — what doesn't work as expected

### Archon RAG Integration (Phase 3b — Parallel with Phase 3)

If Archon RAG is available, search curated knowledge base FIRST:
1. `rag_get_available_sources()` — find indexed documentation
2. For each relevant technology: `rag_search_knowledge_base(query="2-5 keywords", source_id="...")`
3. `rag_search_code_examples(query="2-5 keywords")` for implementation examples
4. **Critical**: Keep queries SHORT — 2-5 keywords maximum for best vector search results

If Archon RAG unavailable or returns no results, fall back to Phase 3 web search.

### Memory Search (Phase 2c)

Read memory.md (if it exists) for past experiences:
- Check Key Decisions for choices about this feature area
- Check Gotchas & Pitfalls for warnings about affected systems
- Check Architecture Patterns for relevant conventions

### Required Output Format

```markdown
### Relevant Documentation
- [Documentation Title](https://example.com/docs#section)
  - Specific section: Section Name
  - Why: Required for implementing X

### Related Memories (from memory.md)
- Memory: {summary} — Relevance: {why this matters}
```

### Validation Gate

Every documentation link includes a specific section anchor. Every reference explains WHY it's needed.

---

## Phase 3b: Research Validation

**Goal**: Ensure all research is accurate before building the plan on it.

### Process

1. Read research reports from Phases 2 and 3
2. Cross-check key findings:
   - Do referenced code patterns still exist at those line numbers?
   - Are library versions current?
   - Are file references accurate?
3. Flag contradictions between research sources
4. If critical research is missing or outdated, do targeted follow-up research

### Validation Gate

No plan section should be built on unverified research. Better to spend 2 minutes validating than to build a plan on wrong assumptions.

---

## Phase 4: Strategic Design & Synthesis

**Template sections to fill**: Implementation Plan (phases), Testing Strategy, Acceptance Criteria

### Process

1. **Synthesize validated research** from all prior phases
2. **Design implementation approach**:
   - How do new components fit with existing architecture?
   - What needs to be built first? (dependency ordering)
   - Break into phases: Foundation → Core → Integration → Testing
3. **Plan testing strategy**:
   - Unit tests: what to test, which patterns to follow
   - Integration tests: what to verify end-to-end
   - Edge cases: what could break
4. **Define acceptance criteria**: Specific, measurable criteria including functional requirements, test coverage, and pattern compliance

### Validation Gate

Clear phase breakdown. Each phase has a clear purpose. No ambiguity about implementation order.

---

## Phase 5: Step-by-Step Task Generation

**Template sections to fill**: STEP-BY-STEP TASKS

### The 7-Field Format (Required for Every Task)

Every task MUST include ALL of these fields — no exceptions:

| Field | Purpose | Example |
|-------|---------|---------|
| **ACTION** | What operation | CREATE / UPDATE / ADD / REMOVE / REFACTOR / MIRROR |
| **TARGET** | Specific file path | `app/services/auth_service.py` |
| **IMPLEMENT** | Code-level detail | "Class AuthService with methods: login(), logout(), refresh_token()" |
| **PATTERN** | Reference pattern | "Follow pattern in `app/services/user_service.py:45-62`" |
| **IMPORTS** | Exact imports | Copy-paste ready import statements |
| **GOTCHA** | Known pitfalls | "Must use async/await — the database client is async-only" |
| **VALIDATE** | Verification command | `pytest tests/services/test_auth.py -v` |

### Process

1. Break Phase 4's implementation phases into atomic tasks
2. Order by dependency (what must happen first)
3. Fill all 7 fields for every task
4. Ensure tasks can be executed top-to-bottom without backtracking

### Validation Gate

Every task is atomic. Every task has a validation command. No task leaves uncertainty about what to implement.

---

## Phase 6: Quality Validation & Confidence Score

**Template sections to fill**: Validation Commands, Completion Checklist, Notes (including Confidence Score)

### Validation Commands (5 Levels)

1. **Level 1 — Syntax & Style**: Linting and formatting commands
2. **Level 2 — Type Safety**: Static type checking commands
3. **Level 3 — Unit Tests**: Unit test commands
4. **Level 4 — Integration Tests**: Integration test commands
5. **Level 5 — Manual Validation**: Feature-specific manual testing steps

### Completion Checklist

- All tasks completed in order
- Each task validation passed
- Full test suite passes
- No linting/type checking errors
- Manual testing confirms feature works
- Acceptance criteria all met

### Confidence Score

Rate X/10 with justification:
- **Strengths**: What's clear and well-defined
- **Uncertainties**: What might change or cause issues
- **Mitigations**: How to handle the uncertainties
- **Key Design Decisions**: Why this approach over alternatives

### Validation Gate

Every command is copy-paste ready. Acceptance criteria are measurable. Confidence score is justified with reasoning.
