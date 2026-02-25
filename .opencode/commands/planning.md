---
description: Create comprehensive feature plan with MVP discovery and PRD planning
---

# Plan a new task

## Feature: $ARGUMENTS

Transform a feature request into a comprehensive implementation plan through systematic codebase analysis and strategic planning.

Core principle: We do not write code in this phase.

Key philosophy: Context is king. The plan must contain all information needed for one-pass implementation success.

Important execution rule for this command:
- No subagents.
- No delegated research.
- No external web research.
- Do all discovery and planning directly in the main conversation.

Two-part execution model:
1. MVP discovery and confirmation
2. PRD-style implementation planning aligned to MVP foundation bricks

Interaction protocol (required):
- Keep planning conversational and interactive.
- Confirm each major insight with the user before locking it in.
- Ask short checkpoint confirmations after: problem framing, user story, MVP draft, and PRD direction.
- If the user says "I already provided the answer," stop re-asking and synthesize from their provided inputs.
- When information is sufficient, proceed decisively to synthesis instead of extending discovery.
- Use concise confirmation prompts such as: "Got it - does this capture your intent?"

## Planning Process

### Phase 0: MVP Discovery and Alignment

Check for `mvp.md` at repository root.

If `mvp.md` exists:
1. Read `mvp.md` fully and summarize the current big idea.
2. Proactively ask the user if they are satisfied with the MVP as written.
3. Align the requested feature as a foundation brick for that MVP.
4. If misaligned, ask what changed and update `mvp.md` only with explicit user confirmation.
5. If user is satisfied, skip discovery and continue to PRD planning (Phase 1).
6. If user is not satisfied, revise `mvp.md` collaboratively before any PRD planning.
7. After revision, ask for explicit confirmation: "MVP looks right now - proceed to PRD planning?"

If `mvp.md` does not exist:
1. Run conversational discovery to establish the big idea.
2. Ask focused probing questions based on user clarity level:
   - Clear vision: challenge assumptions and define first implementation slice.
   - Vague vision: ask who/what/why and suggest options with tradeoffs.
3. Ask the user what text they already have for the big idea and incorporate it.
4. Synthesize a structured MVP draft and write `mvp.md` using:

```markdown
# {Product Name}

## Big Idea

{2-4 paragraphs describing what is being built, why it matters, and the product direction.}

## Users and Problems

- {Primary user type}
- {Top problem 1}
- {Top problem 2}

## Core Capabilities (Foundation Bricks)

- {Capability 1}
- {Capability 2}
- {Capability 3}

## Out of Scope for Now

- {Deferred item 1}
- {Deferred item 2}

## Success Signals

- {Signal 1}
- {Signal 2}
```

5. Proactively ask the user if they are satisfied with the MVP draft.
6. If not satisfied, refine iteratively before proceeding.
7. Proceed to PRD planning (Phase 1) only after MVP confirmation.
8. If user indicates prior answers already cover MVP details, synthesize immediately and request final MVP confirmation.

### Phase 1: PRD Planning - Feature Understanding

- Extract core problem, user value, and expected impact.
- Classify feature type: New Capability, Enhancement, Refactor, or Bug Fix.
- Assess complexity: Low, Medium, High.
- Map systems and components likely affected.
- Create or refine user story:

```text
As a <type of user>
I want to <action or goal>
So that <benefit or value>
```

Before moving to Phase 2, confirm the phase output with the user:
- "Does this feature framing match what you want to build?"
- If user says they already answered, synthesize and proceed.

### Phase 2: Codebase Intelligence Gathering

Use direct analysis with local project tools only (Glob, Grep, Read, Bash as needed).

1. Project structure analysis:
   - Detect language(s), framework(s), runtime versions.
   - Map architecture and integration boundaries.
   - Locate manifests and build/test tooling.

2. Pattern recognition:
   - Find similar implementations.
   - Extract naming, error handling, logging, module, typing, and testing patterns.
   - Capture anti-patterns to avoid.
   - Read `AGENTS.md` and `memory.md` for project rules and prior decisions.

3. Dependency analysis:
   - Catalog libraries relevant to this feature.
   - Note versions, integration style, and compatibility constraints.
   - Read local docs if present (`docs/`, `reference/`, `.agents/reference/`, `ai_docs/`, `ai-wiki/`).

4. Testing pattern analysis:
   - Identify test framework, folder conventions, fixtures, and assertion style.
   - Find closest comparable tests to mirror.

5. Integration points:
   - List files to update.
   - List new files to create.
   - Identify registration points (router, command maps, config, schemas, migrations).

If requirements are still ambiguous, ask targeted clarification before continuing.

### Phase 3: Local Documentation and Project Constraints

Use only project-local sources:

- Read local docs and references (`README.md`, `docs/`, `reference/`, `.agents/`, `AGENTS.md`, `memory.md`).
- Extract project-specific constraints, conventions, and gotchas.
- Do not fetch external docs in this planning command.

Output a focused "Relevant Documentation" list using local repo paths and reasons.

### Phase 4: Strategic Design and Synthesis

- Design implementation order with explicit dependencies.
- Evaluate risks: edge cases, error paths, race conditions, data integrity, backward compatibility.
- Decide between alternatives with rationale.
- Define testing approach and acceptance criteria.
- Ensure maintainability and scalability match project constraints.

If `.agents/PRD.md` exists, verify plan alignment with its architecture and interface constraints.

Before generating final output, confirm PRD direction with user:
- "This is the implementation bridge from MVP to delivery. Confirm and I will finalize the plan."
- If user says they already provided direction, finalize without extra questioning.

### Phase 5: Plan Structure Generation

Create the final PRD-style implementation plan using this exact structure:

```markdown
# Feature: <feature-name>

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

## Feature Description

<Detailed description of feature, purpose, and value>

## User Story

As a <type of user>
I want to <action or goal>
So that <benefit or value>

## Problem Statement

<Specific problem or opportunity this feature addresses>

## Solution Statement

<Proposed solution and why it solves the problem>

## Feature Metadata

**Feature Type**: [New Capability/Enhancement/Refactor/Bug Fix]
**Estimated Complexity**: [Low/Medium/High]
**Primary Systems Affected**: [Main components or services]
**Dependencies**: [External libraries or services required]

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `path/to/file.py` (lines 15-45) - Why: Contains pattern for X to mirror
- `path/to/model.py` (lines 100-120) - Why: Database model structure
- `path/to/test.py` - Why: Testing pattern example

### New Files to Create

- `path/to/new_service.py` - Service implementation for X
- `path/to/new_model.py` - Data model for Y
- `tests/path/to/test_new_service.py` - Unit tests for new service

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Documentation Link 1](https://example.com/doc1#section)
  - Specific section: Authentication setup
  - Why: Required for secure endpoint implementation
- [Documentation Link 2](https://example.com/doc2#integration)
  - Specific section: Database integration
  - Why: Async database pattern reference

### Patterns to Follow

<Project-specific patterns with real code references>

**Naming Conventions:**

**Error Handling:**

**Logging Pattern:**

**Other Relevant Patterns:**

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

<Foundational work required before main implementation>

**Tasks:**

- Set up base schemas, types, and interfaces
- Configure dependencies and foundational helpers

### Phase 2: Core Implementation

<Main feature logic>

**Tasks:**

- Implement core business logic
- Create service layer components
- Add API endpoints or interfaces
- Implement data models

### Phase 3: Integration

<Connect with existing system>

**Tasks:**

- Connect routers/handlers
- Register components
- Update configuration
- Add middleware/interceptors if needed

### Phase 4: Testing and Validation

<Feature-specific test strategy>

**Tasks:**

- Unit tests for each component
- Integration tests for main flows
- Edge case and failure-path tests

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task must be atomic and independently testable.

### Task Format Guidelines

- **CREATE**: New files or components
- **UPDATE**: Modify existing files
- **ADD**: Insert new functionality into existing code
- **REMOVE**: Delete deprecated code
- **REFACTOR**: Restructure without behavior changes
- **MIRROR**: Reuse an existing codebase pattern

### {ACTION} {target_file}

- **IMPLEMENT**: {Specific implementation detail}
- **PATTERN**: {Reference to existing pattern - file:line}
- **IMPORTS**: {Required imports and dependencies}
- **GOTCHA**: {Known issues or constraints to avoid}
- **VALIDATE**: `{executable validation command}`

---

## TESTING STRATEGY

### Unit Tests

<Scope and requirements matching project standards>

### Integration Tests

<Scope and requirements matching project standards>

### Edge Cases

<List edge cases that must be tested>

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and feature correctness.

### Level 1: Syntax and Style

```bash
# TypeScript type checking
npm run type-check

# ESLint
npm run lint

# Prettier formatting check
npm run format:check
```

### Level 2: Unit Tests

<Project-specific unit test commands>

### Level 3: Integration Tests

<Project-specific integration test commands>

### Level 4: Manual Validation

<Feature-specific manual validation steps>

### Level 5: Additional Validation (Optional)

<Additional CLI or MCP validations>

---

## ACCEPTANCE CRITERIA

- [ ] Feature implements all specified functionality
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage meets project requirements
- [ ] Integration tests verify key workflows
- [ ] Code follows project conventions and patterns
- [ ] No regressions in existing functionality
- [ ] Documentation updated if applicable
- [ ] Performance and security considerations addressed if applicable

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] Full validation command set executed successfully
- [ ] Full test suite passes
- [ ] No linting, formatting, or type-check errors
- [ ] Build succeeds
- [ ] All acceptance criteria met
- [ ] Code reviewed for maintainability

---

## NOTES

<Additional context, design decisions, and tradeoffs>
```

## Output Format

Filename: `.agents/plans/{kebab-case-descriptive-name}.md`

- Replace `{kebab-case-descriptive-name}` with short descriptive feature name.
- Examples: `add-user-authentication.md`, `implement-search-api.md`, `refactor-database-layer.md`

Directory: Create `.agents/plans/` if it does not exist.

## Quality Criteria

### Context Completeness

- All required patterns identified and documented
- External library usage documented with links
- Integration points clearly mapped
- Gotchas and anti-patterns captured
- Every task has an executable validation command

### Implementation Ready

- Another developer can execute without additional context
- Tasks are ordered by dependency and executable top-to-bottom
- Each task is atomic and independently testable
- Pattern references include concrete file:line locations

### Pattern Consistency

- Tasks follow existing conventions
- New patterns are justified
- Existing patterns and utilities are reused where appropriate
- Testing approach matches project standards

### Information Density

- No generic references; all details are specific and actionable
- URLs include section anchors where possible
- Task descriptions use codebase keywords
- Validation commands are non-interactive and executable

## Success Metrics

- One-pass implementation: execution can proceed without additional research
- Validation complete: every task includes at least one working validation command
- Context rich: plan passes the no-prior-knowledge test
- Confidence score: X/10 confidence for first-pass execution success

## Report

After creating the plan, provide:
- Summary of feature and approach
- Full path to created plan file
- Complexity assessment
- Key implementation risks or considerations
- Estimated confidence score for one-pass success
