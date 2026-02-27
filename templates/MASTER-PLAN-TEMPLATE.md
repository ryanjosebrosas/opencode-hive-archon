# Master Plan Template

> Use this for complex features with 10+ tasks or multiple distinct phases.
> Save to `requests/{feature}-master-plan.md` and fill in every section.
>
> **When to use**: Complex features that need multiple sub-plans (one per phase).
> **Typical**: 2-4 phases. 1 phase per 3-5 tasks.
> **Target Length**: This master plan should be **~500 lines** when filled.
> The detailed step-by-step tasks live in the sub-plans, not here.
>
> **For simpler features**: Use `STRUCTURED-PLAN-TEMPLATE.md` directly for features
> with <10 tasks that fit in one 700-1000 line plan.

---

# Feature: {Feature Name}

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
- **Estimated Complexity**: {High} (master plan is for complex features)
- **Primary Systems Affected**: {list all components/services}
- **Dependencies**: {external libraries or services required}
- **Total Phases**: {N}
- **Total Estimated Tasks**: {10+}

### Slice Guardrails (Whole Feature)

- **Single Outcome**: {one concrete outcome the entire feature delivers}
- **Expected Files Touched**: {list of all files across all phases}
- **Scope Boundary**: {what this feature intentionally does NOT include}
- **Split Trigger**: {when to stop and create a follow-up feature}

---

## PHASE BREAKDOWN

> This is the core of the master plan. Each phase gets a sub-plan with detailed tasks.

### Phase 1: {Phase Name}

- **Scope**: {What this phase delivers in 1-2 sentences}
- **Files Touched**:
  - `path/to/file1` — {what changes}
  - `path/to/file2` — {what changes}
- **Dependencies**: {None / Depends on: N/A}
- **Sub-Plan Path**: `requests/{feature}-phase-1.md`
- **Estimated Tasks**: {3-5}

### Phase 2: {Phase Name}

- **Scope**: {What this phase delivers in 1-2 sentences}
- **Files Touched**:
  - `path/to/file1` — {what changes}
  - `path/to/file2` — {what changes}
- **Dependencies**: {Phase 1 must complete first}
- **Sub-Plan Path**: `requests/{feature}-phase-2.md`
- **Estimated Tasks**: {3-5}

### Phase 3: {Phase Name}

- **Scope**: {What this phase delivers in 1-2 sentences}
- **Files Touched**:
  - `path/to/file1` — {what changes}
  - `path/to/file2` — {what changes}
- **Dependencies**: {Phase 1, Phase 2 must complete first}
- **Sub-Plan Path**: `requests/{feature}-phase-3.md`
- **Estimated Tasks**: {3-5}

{Add more phases as needed...}

---

## SHARED CONTEXT REFERENCES

> These files/resources are shared across ALL sub-plans. Each sub-plan references this section.

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing ANY phase!

- `path/to/file` (lines X-Y) — Why: {contains pattern for Z that we'll mirror}
- `path/to/file` (lines X-Y) — Why: {database model structure to follow}
- `path/to/test` — Why: {test pattern example}

### New Files to Create (Across All Phases)

- `path/to/new_file` — {purpose description}
- `path/to/new_file` — {purpose description}

### Related Memories (from memory.md)

> Past experiences and lessons relevant to this feature.

- Memory: {summary} — Relevance: {why this matters}
- Memory: {summary} — Relevance: {why this matters}
- (If no relevant memories found, write "No relevant memories found in memory.md")

### Relevant Documentation

> The execution agent SHOULD read these before implementing.

- [Documentation Title](https://example.com/docs#section)
  - Specific section: {Section Name}
  - Why: {required for implementing X}
- [Documentation Title](https://example.com/docs#section)
  - Specific section: {Section Name}
  - Why: {shows recommended approach for Y}

### Patterns to Follow

> Specific patterns extracted from the codebase — include actual code examples.

**{Pattern Name}** (from `path/to/file:lines`):
```
{actual code snippet from the project}
```
- Why this pattern: {explanation}
- Common gotchas: {warnings}

**{Pattern Name}** (from `path/to/file:lines`):
```
{actual code snippet from the project}
```
- Why this pattern: {explanation}
- Common gotchas: {warnings}

---

## HUMAN REVIEW CHECKPOINT

> After each phase completes, a human must review and approve before the next phase begins.

- [ ] **Phase 1 Review** — Approved by: {name} on {date}
  - Sub-plan: `requests/{feature}-phase-1.md`
  - Status: {pending / approved / changes requested}
  - Notes: {any feedback or concerns}

- [ ] **Phase 2 Review** — Approved by: {name} on {date}
  - Sub-plan: `requests/{feature}-phase-2.md`
  - Status: {pending / approved / changes requested}
  - Notes: {any feedback or concerns}

- [ ] **Phase 3 Review** — Approved by: {name} on {date}
  - Sub-plan: `requests/{feature}-phase-3.md`
  - Status: {pending / approved / changes requested}
  - Notes: {any feedback or concerns}

{Add more phase reviews as needed...}

---

## ACCEPTANCE CRITERIA (Whole Feature)

> These criteria apply to the ENTIRE feature, not individual phases.

### Implementation (verify during execution)

- [ ] All phases completed successfully
- [ ] Feature implements all specified functionality
- [ ] Code follows project conventions and patterns
- [ ] All validation commands pass with zero errors (each phase)
- [ ] Unit test coverage meets project requirements
- [ ] Documentation updated (if applicable)
- [ ] Security considerations addressed (if applicable)

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify end-to-end workflows
- [ ] Feature works correctly in manual testing
- [ ] Performance meets requirements (if applicable)
- [ ] No regressions in existing functionality
- [ ] All phases integrate together correctly

---

## KEY DESIGN DECISIONS

{Capture major architectural or design decisions that apply to the whole feature.}

- **Decision 1**: {choice} — because {reason}
  - Alternatives considered: {what else we could have done}
  - Trade-offs: {what we gain, what we lose}

- **Decision 2**: {choice} — because {reason}
  - Alternatives considered: {what else we could have done}
  - Trade-offs: {what we gain, what we lose}

---

## RISKS

{Identify risks that span multiple phases or affect the whole feature.}

- **Risk 1**: {description}
  - Likelihood: {Low / Medium / High}
  - Impact: {Low / Medium / High}
  - Mitigation: {how we'll handle it}

- **Risk 2**: {description}
  - Likelihood: {Low / Medium / High}
  - Impact: {Low / Medium / High}
  - Mitigation: {how we'll handle it}

---

## CONFIDENCE SCORE

**Overall Confidence**: {X}/10

- **Strengths**: {what's clear and well-defined}
- **Uncertainties**: {what might change or cause issues}
- **Mitigations**: {how we'll handle the uncertainties}

### Per-Phase Confidence

- **Phase 1**: {X}/10 — {brief reason}
- **Phase 2**: {X}/10 — {brief reason}
- **Phase 3**: {X}/10 — {brief reason}

---

## SUB-PLAN INDEX

| Phase | Sub-Plan Path | Status | Tasks | Files |
|-------|---------------|--------|-------|-------|
| 1 | `requests/{feature}-phase-1.md` | {pending/in_progress/done} | {N} | {list} |
| 2 | `requests/{feature}-phase-2.md` | {pending/in_progress/done} | {N} | {list} |
| 3 | `requests/{feature}-phase-3.md` | {pending/in_progress/done} | {N} | {list} |

{Add more rows as needed...}
