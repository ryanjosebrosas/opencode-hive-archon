# Plan Overview: {Feature Name}

<!-- PLAN-SERIES -->

> **This is a decomposed plan overview.** It coordinates multiple sub-plans that together
> implement a complex feature. Each sub-plan is self-contained and executable in a fresh
> conversation. Do NOT implement from this file — use `/execute` on each sub-plan in order.
>
> **Total Sub-Plans**: {N}
> **Total Estimated Tasks**: {total across all sub-plans}

---

## Feature Description

{What are we building? One paragraph overview.}

## User Story

As a {user type}, I want to {action}, so that {benefit}.

## Problem Statement

{Why are we building this? What specific problem or opportunity does it address?}

## Solution Statement

{What approach did we choose and why? Capture decisions from vibe planning.}
- Decision 1: {choice} — because {reason}
- Decision 2: {choice} — because {reason}

## Feature Metadata

- **Feature Type**: {New Capability / Enhancement / Refactor / Bug Fix}
- **Estimated Complexity**: High
- **Plan Mode**: Decomposed ({N} sub-plans)
- **Primary Systems Affected**: {list all components/services}
- **Dependencies**: {external libraries or services required}

---

## CONTEXT REFERENCES

> Shared context that ALL sub-plans need. Each sub-plan also has its own
> per-phase context section. The execution agent reads BOTH this section
> and the sub-plan's context before implementing.

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing any sub-plan!

- `path/to/file` (lines X-Y) — Why: {contains pattern for Z that we'll mirror}
- `path/to/file` (lines X-Y) — Why: {database model structure to follow}

### New Files to Create (All Sub-Plans)

- `path/to/new_file` — {purpose} — Sub-plan: {NN}
- `path/to/new_file` — {purpose} — Sub-plan: {NN}

### Related Memories (from memory.md)

- Memory: {summary} — Relevance: {why this matters}
- (If no relevant memories found, write "No relevant memories found in memory.md")

### Relevant Documentation

- [Documentation Title](https://example.com/docs#section)
  - Specific section: {Section Name}
  - Why: {required for implementing X}

### Patterns to Follow

**{Pattern Name}** (from `path/to/file:lines`):
```
{actual code snippet from the project}
```
- Why this pattern: {explanation}
- Common gotchas: {warnings}

---

## PLAN INDEX

| # | Phase | Sub-Plan File | Tasks | Context Load |
|---|-------|---------------|-------|--------------|
| 01 | {phase-name} | `requests/{feature}-plan-01-{phase}.md` | {N} | {Low/Medium} |
| 02 | {phase-name} | `requests/{feature}-plan-02-{phase}.md` | {N} | {Low/Medium} |
| 03 | {phase-name} | `requests/{feature}-plan-03-{phase}.md` | {N} | {Low/Medium} |

> Each sub-plan targets 5-8 tasks and **500-700 lines**. Sub-plans must be self-contained —
> the execution agent has no memory of previous sub-plans. Include full context references,
> pattern examples, and detailed task specifications. Context load estimates help decide
> instance assignment (Low = minimal codebase reads, Medium = several files).

---

## EXECUTION ROUTING

Each sub-plan runs in a fresh `/execute` session.
Recommended: Use Sonnet for execution, Opus for planning.

### Execution Instructions

**Manual execution** (recommended for complex features):
```bash
# Execute each sub-plan in a fresh session
claude
> /execute requests/{feature}-plan-01-{phase}.md

claude
> /execute requests/{feature}-plan-02-{phase}.md

claude
> /execute requests/{feature}-plan-03-{phase}.md
```

**Automated execution** (via `claude -p`):
```bash
for plan in requests/{feature}-plan-*.md; do
  claude -p "/execute $plan" --model sonnet
done
```

**Between sub-plans**:
- Each sub-plan runs in a fresh conversation (context reset)
- Read HANDOFF NOTES from completed sub-plan before starting the next
- If a sub-plan fails, fix and re-run it before proceeding

---

## ACCEPTANCE CRITERIA

- [ ] {Feature-wide criterion 1}
- [ ] {Feature-wide criterion 2}
- [ ] All sub-plans executed successfully
- [ ] All sub-plan validation commands pass
- [ ] No broken cross-references between sub-plan outputs
- [ ] Backwards compatibility maintained
- [ ] Documentation updated

---

## COMPLETION CHECKLIST

- [ ] Sub-plan 01 ({phase}) — complete
- [ ] Sub-plan 02 ({phase}) — complete
- [ ] Sub-plan 03 ({phase}) — complete
- [ ] All acceptance criteria met
- [ ] Feature-wide manual validation passed
- [ ] Ready for `/commit`

---

## NOTES

### Key Design Decisions
- {Why decomposition over single plan}
- {Why this phase breakdown}

### Risks
- {Risk 1 and mitigation}
- {Risk 2 and mitigation}

### Confidence Score: {X}/10
- **Strengths**: {what's clear and well-defined}
- **Uncertainties**: {what might change or cause issues}
- **Mitigations**: {how we'll handle the uncertainties}
