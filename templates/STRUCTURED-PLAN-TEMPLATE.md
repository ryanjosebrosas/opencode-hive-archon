# Structured Plan Template

> Use this template when creating a feature plan (Layer 2 of the PIV Loop).
> Save to `requests/{feature}-plan.md` and fill in every section.
>
> **Target Length**: The completed plan should be **700-1000 lines**. You have failed
> if the plan is under 700 lines. Complex or comprehensive features should target 1000.
> Every section must contain feature-specific content — not generic placeholders.
> Reference guides, code snippets, and file:line citations are context, not filler.
>
> **Core Principle**: This template is the control mechanism. The `/planning` command's
> 6 phases exist to fill these sections systematically. Nothing is missed because
> the template specifies exactly what's needed.
>
> **For the execution agent**: Validate documentation and codebase patterns before
> implementing. Pay special attention to naming of existing utils, types, and models.
> Import from the right files.

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
- **Estimated Complexity**: {Low / Medium / High}
- **Primary Systems Affected**: {list all components/services}
- **Dependencies**: {external libraries or services required}

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `path/to/file` (lines X-Y) — Why: {contains pattern for Z that we'll mirror}
- `path/to/file` (lines X-Y) — Why: {database model structure to follow}
- `path/to/test` — Why: {test pattern example}

### New Files to Create

- `path/to/new_file` — {purpose description}
- `path/to/new_file` — {purpose description}

### Related Memories (from memory.md)

> Past experiences and lessons relevant to this feature. Populated by `/planning` from memory.md.

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

> Specific patterns extracted from the codebase — include actual code examples from the project.

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

## IMPLEMENTATION PLAN

### Phase 1: Foundation

{Describe foundational work needed before main implementation.}

**Tasks:**
- {Set up base structures, schemas, types, interfaces}
- {Configure necessary dependencies}
- {Create foundational utilities or helpers}

### Phase 2: Core Implementation

{Describe the main implementation work.}

**Tasks:**
- {Implement core business logic}
- {Create service layer components}
- {Add API endpoints or interfaces}

### Phase 3: Integration

{Describe how the feature integrates with existing functionality.}

**Tasks:**
- {Connect to existing routers/handlers}
- {Register new components}
- {Update configuration files}

### Phase 4: Testing & Validation

{Describe the testing approach.}

**Tasks:**
- {Implement unit tests for each component}
- {Create integration tests for the feature workflow}
- {Add edge case tests}

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

{Continue for all tasks in dependency order...}

---

## TESTING STRATEGY

### Unit Tests

{Scope and requirements based on project standards. Design tests with fixtures and assertions following existing testing approach.}

### Integration Tests

{Scope and requirements. What end-to-end workflows to verify.}

### Edge Cases

- {Edge case 1 — what could break?}
- {Edge case 2 — unusual inputs or states}
- {Edge case 3 — error conditions}

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style
```
{linting and formatting commands}
```

### Level 2: Unit Tests
```
{unit test commands}
```

### Level 3: Integration Tests
```
{integration test commands}
```

### Level 4: Manual Validation

{Feature-specific manual testing steps — API calls, UI testing, CLI usage, etc.}

### Level 5: Additional Validation (Optional)

{MCP servers, additional CLI tools, or other verification methods if available.}

---

## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable
> only after running the code). Check off Implementation items during execution.
> Leave Runtime items for manual testing or post-deployment verification.

### Implementation (verify during execution)

- [ ] Feature implements all specified functionality
- [ ] Code follows project conventions and patterns
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage meets project requirements
- [ ] Documentation updated (if applicable)
- [ ] Security considerations addressed (if applicable)

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify end-to-end workflows
- [ ] Feature works correctly in manual testing
- [ ] Performance meets requirements (if applicable)
- [ ] No regressions in existing functionality

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions
- {Why this approach over alternatives}
- {Trade-offs made and why}

### Risks
- {Risk 1 and mitigation}
- {Risk 2 and mitigation}

### Confidence Score: {X}/10
- **Strengths**: {what's clear and well-defined}
- **Uncertainties**: {what might change or cause issues}
- **Mitigations**: {how we'll handle the uncertainties}
