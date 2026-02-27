---
description: Interactive discovery session — explore ideas WITH the user, then produce a structured plan
agent: build
---

# Planning: Interactive Discovery + Structured Plan

Work WITH the user to explore, question, and discover the right approach for a spec, then produce a structured implementation plan. This is a conversation, not an auto-generator.

## Feature: $ARGUMENTS

---

## Pipeline Position

```
/mvp → /prd → /decompose → /planning (this) → /build → /ship
```

Used per-spec inside the `/build` loop, or standalone for manual planning.

---

## Core Rules

1. **Discovery first, plan second.** Do NOT auto-generate a plan. Ask questions, discuss approaches, explore the codebase together.
2. **Work WITH the user.** This is a conversation. Ask short questions, confirm insights, discuss tradeoffs.
3. **No code in this phase.** Planning produces a plan document, not code.
4. **No subagents.** Do all discovery directly in the conversation. Dispatch tool is allowed for targeted research.
5. **Plan-before-execute.** `/execute` only runs from a `/planning`-generated artifact in `requests/`.

---

## Phase 1: Understand (Discovery Conversation)

Start by understanding what the user wants to build. This is interactive:

### If called from `/build` with a spec:
- Read the spec from `specs/BUILD_ORDER.md`
- Read `specs/build-state.json` for context from prior specs
- Summarize: "This spec is about {purpose}. It depends on {deps} which are done. Here's what I think we need to build..."
- Ask: "Does this match your thinking? Anything to add or change?"

### If called standalone:
- Ask: "What are we building? Give me the short version."
- Listen, then ask 2-3 targeted follow-up questions:
  - "What's the most important thing this needs to do?"
  - "What existing code should this integrate with?"
  - "Any constraints or preferences on how to build it?"

### Discovery Tools
Use these to explore the codebase during conversation:
- **Glob/Grep/Read** — find and read relevant files
- **Dispatch** — send targeted research queries to free models when needed:
  ```
  dispatch({ taskType: "research", prompt: "...", timeout: 30 })
  ```
- **Council** — for architectural decisions with multiple valid approaches (suggest to user)

### Checkpoints
After each major discovery, confirm:
- "Here's what I'm seeing — does this match your intent?"
- "I think we should approach it like X because Y. Sound right?"
- Keep confirmations SHORT — one sentence, not paragraphs.

---

## Phase 2: Explore (Codebase Intelligence)

Once the direction is clear, explore the codebase to ground the plan in reality:

1. **Find relevant files** — patterns to follow, code to integrate with
2. **Check existing patterns** — naming, error handling, testing conventions
3. **Map integration points** — what files need to change, what's new
4. **Identify gotchas** — from `memory.md`, prior specs, or codebase inspection

Share findings with the user as you go:
- "Found this pattern in `file.py:42` — we should follow it."
- "There's a gotcha here — `deps.py` uses lazy init, we need to match that."

**Dispatch for research** (optional, when local exploration isn't enough):

| Need | taskType | Model |
|------|----------|-------|
| Quick factual check | `quick-check` | qwen3-coder-next (FREE) |
| API/pattern question | `api-analysis` | qwen3-coder-plus (FREE) |
| Library comparison | `research` | qwen3.5-plus (FREE) |
| Documentation lookup | `docs-lookup` | kimi-k2.5 (FREE) |

---

## Phase 3: Design (Strategic Decisions)

Discuss the implementation approach with the user:

1. **Propose the approach** — "Here's how I'd build this: {approach}. The key decision is {X}."
2. **Present alternatives** — if multiple valid approaches exist, show 2-3 options with tradeoffs
3. **Confirm the direction** — "Lock in approach A? Or should we explore B more?"

For non-trivial architecture decisions, suggest council:
- "This has multiple valid approaches. Want to run `/council` to get input from 13 models?"

---

## Phase 4: Preview (Approval Gate)

Before writing the full plan, show a **1-page preview**:

```
PLAN PREVIEW: {spec-name}
=============================

What:      {1-line description}
Approach:  {the locked-in approach}
Files:     {create: X, modify: Y}
Key decision: {the main architectural choice and why}
Risks:     {top 1-2 risks}
Tests:     {testing approach}
Estimated tasks: {N tasks}

Approve this direction to write the full plan? [y/n/adjust]
```

Only write the plan file after explicit approval.

---

## Phase 5: Write Plan

Generate the structured plan. Depth scales with the spec's complexity tag:

### Light Plan (~100 lines)

```markdown
# Spec: {name}

## What
{purpose}

## Approach
{locked-in approach from discussion}

## Files
- Create: {list}
- Modify: {list}

## Tasks
1. **{ACTION}** `{target_file}`
   - IMPLEMENT: {detail}
   - VALIDATE: `{command}`

2. **{ACTION}** `{target_file}`
   - IMPLEMENT: {detail}
   - VALIDATE: `{command}`

## Acceptance
- {criteria from BUILD_ORDER.md}
- {additional criteria from discovery}

## Validate
{validation commands}
```

### Standard Plan (~300 lines)

Adds: Feature Description, Solution Statement, Patterns to Follow, Code Samples, Testing Strategy, Edge Cases

### Heavy Plan (~700 lines)

Full treatment: all standard fields plus Alternatives Considered, Risk Analysis, Integration Test Strategy, detailed Phase breakdown

---

## Output

Save to: `requests/{spec-number}-{spec-name}-plan.md`
(or `requests/{descriptive-name}-plan.md` for standalone planning)

Numbering: increment `#<n>` if same name exists.

---

## After Writing

Report:
```
Plan written: requests/{filename}
Tasks: {N} tasks across {phases} phases
Confidence: {X}/10 for one-pass success
Key risk: {top risk}

Next: /build to implement, or review the plan first.
```

---

## Interaction Protocol

- **Be concise.** Short questions, short confirmations. Don't lecture.
- **Listen more than talk.** The user knows what they want — help them articulate it.
- **Share discoveries.** When you find something in the codebase, share it immediately.
- **Confirm, don't assume.** If unsure about intent, ask. Don't guess.
- **Know when to stop discovering.** When direction is clear, move to the plan. Don't over-explore.
- **If user says "I already told you"** — synthesize from their inputs immediately. Don't re-ask.

---

## Notes

- This command replaces the old 6-phase automated planning with interactive discovery
- Archon RAG is optional (use if available, don't block if not)
- The plan must pass the "no-prior-knowledge test" — another session can execute it without context
- Keep the conversation moving — a planning session should take 10-30 minutes depending on complexity
