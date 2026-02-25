---
description: Create comprehensive feature plan with MVP discovery and PRD planning
---

# Plan a new task

## Feature: $ARGUMENTS

Transform a feature request into a comprehensive implementation plan through systematic codebase analysis and strategic planning.

Core principle: We do not write code in this phase.

Key philosophy: Context is king. The plan must contain all information needed for one-pass implementation success.

Slice discipline rule (required):
- Plan one slice at a time.
- Do not start planning the next slice until the current slice is execution-complete and code-review clean (or explicitly accepted by user with minor skips).

Lean mode (default):
- Required artifacts per feature are only:
  1) `requests/{descriptive-name} #<n>.md` (plan)
  2) `requests/execution-reports/{feature}-report.md` (execution report, produced by `/execute`)
- Additional docs are optional and created only when they change implementation behavior.

Important execution rule for this command:
- No subagents.
- No delegated research.
- Do all discovery and planning directly in the main conversation.

External research is ALLOWED and ENCOURAGED:
- Use Archon MCP RAG search for curated knowledge base lookup (required)
- Use WebFetch for specific documentation URLs
- Use web search for finding library docs and best practices

Archon requirement (non-skippable):
- `/planning` must use Archon preflight + RAG retrieval before finalizing the plan.
- If Archon is unavailable/unhealthy, stop and report: "Blocked: Archon MCP unavailable. `/planning` requires Archon."

Two-part execution model:
1. MVP discovery and confirmation
2. PRD-style implementation planning aligned to MVP foundation bricks

Important scope rule:
- MVP is necessary but not sufficient. Planning must also lock the technical specification baseline needed to execute.
- Never assume the big idea alone is enough for implementation planning.

Interaction protocol (required):
- Keep planning conversational and interactive.
- Confirm each major insight with the user before locking it in.
- Ask short checkpoint confirmations after: problem framing, user story, MVP draft, and PRD direction.
- If the user says "I already provided the answer," stop re-asking and synthesize from their provided inputs.
- When information is sufficient, proceed decisively to synthesis instead of extending discovery.
- Use concise confirmation prompts such as: "Got it - does this capture your intent?"

Mandatory spec handshake (non-skippable):
- Before producing any final plan file, ask and confirm these 5 items explicitly:
  1. Implementation mode: docs/spec only, runnable code, or both
  2. Target repo/path for implementation (not just planning workspace)
  3. Preferred stack/framework constraints (or "follow existing stack")
  4. Acceptance depth: alpha scaffold, production-ready MVP, or full production
  5. Output artifact type: PRD, structured execution plan, or both
- If the user already provided these, restate them in one compact "spec lock" block and ask for explicit confirmation.
- Never finalize a plan file if these 5 items are not locked.

Mandatory approval gate before file write:
- Produce a 1-page planning preview first (problem, scope, architecture direction, task phases, assumptions).
- Ask for explicit approval: "Approve this direction to write the final plan file?"
- Only write the final plan file after approval.
- If approval is denied, revise preview and repeat.

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

### Phase 0.5: Technology and OSS Options Exploration (Mandatory)

Before Phase 1, run an options scan so planning is not locked to one assumed stack.

Requirements:
1. Gather user-provided references first (GitHub repos, docs, preferred tools).
2. Research at least 2 viable options when the architecture/stack is not fully locked.
3. Build a decision matrix with:
   - Option name
   - Integration effort
   - Maintenance burden
   - Performance/latency fit
   - Cost/licensing fit
   - Lock-in risk
   - Capability overlap/redundancy risk
   - Why it fits/does not fit this MVP
4. Include current/default approach as one option for fair comparison.
5. Ask user for selection or hybrid path before moving to Phase 1.

Redundancy rule (mandatory):
- Do not stack duplicate retrieval components without explicit benefit.
- Example: if provider-native reranking is enabled (e.g., Mem0 rerank), external reranker must be optional/disabled by default unless A/B evidence shows quality gain.

Checkpoint question (required):
- "Which option should we lock for this plan: A, B, C, or hybrid?"

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

Also confirm implementation specificity before proceeding:
- "Should this feature be spec-only or implemented in code in this loop?"
- "Which stack/framework should this plan target?"

### Phase 2: Codebase Intelligence Gathering

Use direct analysis with local project tools (Glob, Grep, Read, Bash as needed).

Required Archon preflight and retrieval:
- Verify connectivity with `archon_health_check` before discovery work.
- List sources with `archon_rag_get_available_sources`.
- Search codebase patterns using `archon_rag_search_code_examples` with 2-5 keyword queries.
- Search curated docs using `archon_rag_search_knowledge_base(query=..., return_mode="pages")`.
- Read top results using `archon_rag_read_full_page(page_id=...)`.
- If no relevant hits are found, continue with local repo evidence and record "No relevant Archon RAG hits" in the plan notes.

Code sample requirement (non-skippable):
- Collect concrete implementation samples before writing tasks:
  - At least 3 local code samples (file path + line reference + why it matches).
  - At least 2 Archon code samples via `archon_rag_search_code_examples` when relevant results exist.
- If Archon code samples are not relevant/available, document the miss explicitly and rely on local samples.

1. Project structure analysis:
   - Detect language(s), framework(s), runtime versions.
   - Map architecture and integration boundaries.
   - Locate manifests and build/test tooling.
   - Record concrete evidence for stack choice (file paths + line refs where possible).

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

### Phase 3: Documentation Research (Local + External + Archon)

**Local sources:**
- Read local docs (`README.md`, `docs/`, `reference/`, `.agents/`, `AGENTS.md`, `memory.md`).
- Extract project-specific constraints, conventions, and gotchas.

**External research (when needed):**
- Use WebFetch to retrieve specific documentation URLs (e.g., library docs, API references)
- Search for official documentation when library versions or integration details are unclear
- Use web search to find best practices, common patterns, and version compatibility notes

**Archon MCP integration (required):**
- Prioritize RAG search over generic web search for curated sources
- Use `archon_rag_read_full_page` to get complete documentation after RAG search
- Include at least one Archon-sourced code example or page reference in the final plan when relevant matches exist

Output a comprehensive "Relevant Documentation" list with:
- Local repo paths with reasons
- External documentation URLs with specific sections and why they matter

### Phase 4: Strategic Design and Synthesis

- Design implementation order with explicit dependencies.
- Evaluate risks: edge cases, error paths, race conditions, data integrity, backward compatibility.
- Decide between alternatives with rationale.
- Define testing approach and acceptance criteria.
- Ensure maintainability and scalability match project constraints.
- Include an "Alternatives considered" summary and why final choice won.

Lean-mode doc gate (required):
- Before adding any extra documentation file, verify at least one is true:
  - It defines a new shared contract/interface required by multiple modules/agents.
  - It is required for safe handoff across sessions/LLMs.
  - It is required for validation/audit of non-obvious behavior.
- If none are true, do not create extra docs.

If `.agents/PRD.md` exists, verify plan alignment with its architecture and interface constraints.

Before generating final output, confirm PRD direction with user:
- "This is the implementation bridge from MVP to delivery. Confirm and I will finalize the plan."
- If user says they already provided direction, finalize without extra questioning.

### Phase 5: Plan Structure Generation

Create the final PRD-style implementation plan using this exact structure:

Do not write the final file until the user approves the preview and the 5-item spec handshake is locked.

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

### Code Samples to Mirror (required)

- `path/to/sample_1.py:line` - Why this sample should be mirrored
- `path/to/sample_2.py:line` - Why this sample should be mirrored
- `path/to/sample_3.py:line` - Why this sample should be mirrored
- Archon sample: `{source/page_id or URL}` - Why this external sample matters

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

Filename (required): `requests/{descriptive-name} #<n>.md`

- Use `requests/` as the output directory.
- Keep the file body unchanged from the template structure; only apply numbering in the filename.
- Preserve existing numbering style used by prior plans (example: `ultima-second-brain-hybrid-retrieval-plan #1.md`).
- If same `descriptive-name` already exists, increment `<n>` to the next available number.
- If no prior file exists for that name, start with `#1`.

Examples:
- `requests/implement-search-api #1.md`
- `requests/implement-search-api #2.md`

Directory: Create `requests/` if it does not exist.

## Quality Criteria

### Context Completeness

- All required patterns identified and documented
- External library usage documented with links
- Archon RAG retrieval evidence documented (queries + references)
- Concrete code samples are included (local + Archon where relevant)
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

### Anti-Bloat Check (required)

- No documentation file is added unless it directly supports implementation, validation, or handoff.
- Avoid duplicating the same decisions across multiple markdown files.

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
- Archon retrieval summary (sources searched and key references)
- Estimated confidence score for one-pass success
