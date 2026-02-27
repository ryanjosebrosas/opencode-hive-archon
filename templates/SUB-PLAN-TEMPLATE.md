# Sub-Plan Template

> Use this for each phase of a complex feature.
> Save to `requests/{feature}-phase-{N}.md` and fill in every section.
>
> **When to use**: One sub-plan per phase of a complex feature.
> The master plan (`MASTER-PLAN-TEMPLATE.md`) defines the overall structure.
>
> **Target Length**: This sub-plan should be **700-1000 lines** when filled.
> Each sub-plan is self-contained enough for a T1 model to execute WITHOUT
> reading prior sub-plans (the Prior Phase Summary provides continuity).
>
> **Target**: 5-10 tasks per sub-plan. If a phase has more, split it.

---

# Feature: {Feature Name} — Phase {N} of {M}

> **Master Plan**: `requests/{feature}-master-plan.md`
> **This Phase**: Phase {N} — {Phase Name}
> **Sub-Plan Path**: `requests/{feature}-phase-{N}.md`

---

## PRIOR PHASE SUMMARY

> What was done in the previous phase(s). Provides continuity without requiring
> the execution agent to read prior sub-plans.

### For Phase 1

This is the first phase — no prior work. Start fresh.

### For Phase 2+

**Files Changed in Prior Phase(s):**
- `path/to/file1` — {what was changed}
- `path/to/file2` — {what was changed}

**Key Outcomes from Prior Phase(s):**
- {Outcome 1 — what was delivered}
- {Outcome 2 — what was delivered}

**State Carried Forward:**
- {What this phase inherits from prior phases}
- {Any patterns, structures, or state to build on}

**Known Issues or Deferred Items:**
- {Any issues from prior phases this phase should be aware of}
- {Items intentionally deferred to this phase}

---

## PHASE SCOPE

**What This Phase Delivers:**

{1-2 sentences describing the scope of this specific phase. Copy from the master plan's phase breakdown.}

**Files This Phase Touches:**
- `path/to/file1` — {what changes}
- `path/to/file2` — {what changes}
- `path/to/new_file` — {new file to create}

**Dependencies:**
- {Phase N-1 must complete first / None if Phase 1}

**Out of Scope for This Phase:**
- {What this phase intentionally does NOT do}
- {What is deferred to later phases}

---

## CONTEXT REFERENCES

> Phase-specific files to read. Also reference the master plan's shared context.

### Phase-Specific Files

> Files that are particularly relevant to THIS phase (not covered in master plan's shared context).

- `path/to/file` (lines X-Y) — Why: {specific to this phase}
- `path/to/file` (lines X-Y) — Why: {specific to this phase}

### Shared Context (from Master Plan)

> The following shared context from the master plan also applies:
> - Master plan section: `SHARED CONTEXT REFERENCES`
> - Codebase patterns: {list key files}
> - Documentation: {list key docs}
> - Memories: {list relevant memories}

### Patterns to Follow (Phase-Specific)

> Patterns especially relevant to this phase — include actual code snippets.

**{Pattern Name}** (from `path/to/file:lines`):
```
{actual code snippet from the project}
```
- Why this pattern: {explanation}
- Common gotchas: {warnings}

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.
>
> **Action keywords**: CREATE (new files), UPDATE (modify existing), ADD (insert new functionality),
> REMOVE (delete deprecated code), REFACTOR (restructure without changing behavior), MIRROR (copy pattern from elsewhere)
>
> **Tip**: For text-centric changes (templates, commands, configs), include exact **Current** / **Replace with**
> content blocks in IMPLEMENT. This eliminates ambiguity and achieves higher plan-to-implementation fidelity
> than prose descriptions. See `reference/piv-loop-practice.md` Section 3 for guidance.

### {ACTION} {target_file_path}

- **IMPLEMENT**: {what to implement — code-level detail}
- **PATTERN**: {reference to codebase pattern — file:line}
- **IMPORTS**: {exact imports needed, copy-paste ready}
- **GOTCHA**: {known pitfalls and how to avoid them}
- **VALIDATE**: `{executable command to verify task completion}`

### {ACTION} {target_file_path}

- **IMPLEMENT**: {what to implement — code-level detail}
- **PATTERN**: {reference to codebase pattern — file:line}
- **IMPORTS**: {exact imports needed, copy-paste ready}
- **GOTCHA**: {known pitfalls and how to avoid them}
- **VALIDATE**: `{executable command to verify task completion}`

### {ACTION} {target_file_path}

- **IMPLEMENT**: {what to implement — code-level detail}
- **PATTERN**: {reference to codebase pattern — file:line}
- **IMPORTS**: {exact imports needed, copy-paste ready}
- **GOTCHA**: {known pitfalls and how to avoid them}
- **VALIDATE**: `{executable command to verify task completion}`

{Continue for all tasks in this phase... Target 5-10 tasks total.}

---

## TESTING STRATEGY (This Phase)

### Unit Tests

{Scope and requirements for this phase's unit tests. What specific components to test.}

### Integration Tests

{Scope and requirements. What end-to-end workflows to verify for this phase.}

### Edge Cases

- {Edge case 1 — what could break?}
- {Edge case 2 — unusual inputs or states}
- {Edge case 3 — error conditions}

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.
> Full validation depth is required for every slice; one proof signal is not enough.

### Level 1: Syntax & Style
```
{linting and formatting commands}
```

### Level 2: Type Safety
```
{type-check commands}
```

### Level 3: Unit Tests
```
{unit test commands — specific to this phase's tests}
```

### Level 4: Integration Tests
```
{integration test commands — specific to this phase}
```

### Level 5: Manual Validation

{Feature-specific manual testing steps for this phase — API calls, UI testing, CLI usage, etc.}

### Level 6: Additional Validation (Optional)

{MCP servers, additional CLI tools, or other verification methods if available.}

---

## PHASE ACCEPTANCE CRITERIA

> Check off Implementation items during execution.
> Leave Runtime items for manual testing or post-deployment verification.

### Implementation (verify during execution)

- [ ] Phase implements all specified functionality
- [ ] Code follows project conventions and patterns
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage meets project requirements
- [ ] Documentation updated (if applicable)
- [ ] Security considerations addressed (if applicable)

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify end-to-end workflows for this phase
- [ ] Phase works correctly in manual testing
- [ ] Performance meets requirements (if applicable)
- [ ] No regressions in existing functionality
- [ ] Integrates correctly with prior phases (if Phase 2+)

---

## HANDOFF NOTES

> What the NEXT phase needs to know. This feeds into the next sub-plan's
> "Prior Phase Summary" section.

### Files Created/Modified

- `path/to/file1` — {what was created/modified, key patterns used}
- `path/to/file2` — {what was created/modified, key patterns used}

### Patterns Established

- {Pattern 1 — what pattern was established, where it lives}
- {Pattern 2 — what pattern was established, where it lives}

### State to Carry Forward

- {What state the next phase inherits}
- {Any structures or interfaces the next phase should build on}

### Known Issues or Deferred Items

- {Any issues the next phase should be aware of}
- {Items intentionally deferred to the next phase}

---

## PHASE COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration for this phase)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms phase works
- [ ] Phase acceptance criteria all met
- [ ] Handoff notes completed for next phase

---

## PHASE NOTES

### Key Design Decisions (This Phase)

- {Why this approach over alternatives}
- {Trade-offs made and why}

### Risks (This Phase)

- {Risk 1 and mitigation}
- {Risk 2 and mitigation}

### Confidence Score: {X}/10

- **Strengths**: {what's clear and well-defined}
- **Uncertainties**: {what might change or cause issues}
- **Mitigations**: {how we'll handle the uncertainties}
