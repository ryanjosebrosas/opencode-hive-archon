# Template Section-Filling Guide

This guide maps each section of `templates/STRUCTURED-PLAN-TEMPLATE.md` to the planning phase that fills it, with quality criteria and common mistakes.

---

## Section → Phase Mapping

| Template Section | Filled By | Key Input |
|-----------------|-----------|-----------|
| Feature Description | Phase 1 | Feature request parsing |
| User Story | Phase 1 | User type, goal, benefit |
| Problem Statement | Phase 1 | Why we're building this |
| Solution Statement | Phase 1 | Decisions from vibe planning |
| Feature Metadata | Phase 1 | Type, complexity, systems, deps |
| Relevant Codebase Files | Phase 2 | Explore agent findings |
| New Files to Create | Phase 2 | Explore agent + Phase 4 design |
| Related Memories | Phase 2c | memory.md entries |
| Relevant Documentation | Phase 3 | External research agent findings |
| Patterns to Follow | Phase 2 | Explore agent code extractions |
| Implementation Plan | Phase 4 | Synthesis of all research |
| Step-by-Step Tasks | Phase 5 | Phase 4 breakdown into atomics |
| Testing Strategy | Phase 4 | Testing plan from design |
| Validation Commands | Phase 6 | 5-level validation pyramid |
| Acceptance Criteria | Phase 4 | Measurable completion criteria |
| Completion Checklist | Phase 6 | Standard + feature-specific items |
| Notes / Confidence | Phase 6 | Risk assessment, design decisions |

---

## Quality Criteria Per Section

### Feature Description
- **Good**: One paragraph, specific, scoped. Names exact components affected.
- **Bad**: Vague ("improve the system"), too broad ("add all missing features"), or lists everything from the PRD.
- **Rule**: If it takes more than 3 sentences, the scope is too large — split into multiple PIV loops.

### User Story
- **Good**: `As a [specific user type], I want [concrete action], so that [measurable benefit]`
- **Bad**: `As a user, I want the app to work better` (too vague)
- **Rule**: Every field must be specific enough to validate completion against.

### Problem / Solution Statement
- **Good**: Problem describes pain point with evidence. Solution lists decisions with reasoning.
- **Bad**: Problem is just the inverse of the solution. No "because" in solution decisions.
- **Rule**: Each decision uses the format: `Decision: {choice} — because {reason}`

### Relevant Codebase Files
- **Good**: `path/to/file.py` (lines 45-62) — Why: Contains the service pattern we'll mirror
- **Bad**: `path/to/file.py` — relevant file (no line numbers, no reason)
- **Rule**: Every entry has line numbers AND a "Why" explanation.

### New Files to Create
- **Good**: `app/services/payment_service.py` — Payment processing service following user_service.py pattern
- **Bad**: `new_file.py` — new service (no path context, no pattern reference)
- **Rule**: Full path, clear purpose, reference to pattern if applicable.

### Patterns to Follow
- **Good**: Actual code snippets from the project with file:line reference, "why this pattern" explanation, and gotcha warnings.
- **Bad**: Generic code examples not from the project, or just naming a pattern without showing it.
- **Rule**: Every pattern has (1) actual code from THIS project, (2) source file:line, (3) why + gotcha.

### Implementation Plan (Phases)
- **Good**: 3-4 phases with clear dependency ordering. Foundation → Core → Integration → Testing.
- **Bad**: One giant phase, or phases that could run in any order (no real dependencies).
- **Rule**: Each phase builds on the previous. Phase N+1 cannot start if Phase N failed.

### Step-by-Step Tasks
- **Good**: Every task has all 7 fields (ACTION, TARGET, IMPLEMENT, PATTERN, IMPORTS, GOTCHA, VALIDATE). Tasks execute top-to-bottom.
- **Bad**: Missing fields, especially IMPORTS and GOTCHA. Tasks that require backtracking.
- **Rule**: The execution agent should succeed without additional research. Every task is independently verifiable.

### Testing Strategy
- **Good**: Specific test files to create, specific functions to test, specific edge cases.
- **Bad**: "Write tests for the feature" (no specifics).
- **Rule**: Name the test files, the test functions, and the assertions.

### Validation Commands
- **Good**: Copy-paste-ready commands at 5 levels (syntax, types, unit, integration, manual).
- **Bad**: Generic commands ("run the tests"), or missing levels.
- **Rule**: Every command must be executable as-is. Include the exact framework/tool invocation.

### Acceptance Criteria
- **Good**: Specific, measurable, testable. "API returns 200 with valid payload" not "API works".
- **Bad**: Subjective criteria ("code is clean"), or criteria that can't be verified.
- **Rule**: Each criterion maps to at least one validation command or manual test step.

### Confidence Score
- **Good**: X/10 with specific strengths (clear patterns), uncertainties (untested library), and mitigations (fallback approach).
- **Bad**: "8/10 — looks good" (no justification).
- **Rule**: Low scores (< 7) should trigger additional research or scope reduction before proceeding.

---

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Generic patterns (not from project) | Execution agent uses wrong conventions | Extract real code from codebase |
| Missing line numbers | Execution agent can't find the pattern | Always include file:line references |
| Tasks without IMPORTS | Execution agent guesses wrong imports | List exact import statements |
| Tasks without GOTCHA | Execution agent hits known pitfalls | Research and document pitfalls |
| Plan exceeds 700 lines | Too verbose, agent may lose focus | Cut non-essential details, be concise |
| Plan under 500 lines | Missing critical context | Add more patterns, imports, gotchas |
| Unverified research | Plan built on wrong assumptions | Run Phase 3b research validation |
| One-task phases | Phases aren't meaningful groupings | Combine into fewer, larger phases |
| Mocked tests in plan | Implementation agent writes fake tests | Specify real assertions and fixtures |

---

## Template File Location

The template to fill: `templates/STRUCTURED-PLAN-TEMPLATE.md`

The plan saves to: `requests/{feature-name}-plan.md`

The execution command: `/execute requests/{feature-name}-plan.md`
