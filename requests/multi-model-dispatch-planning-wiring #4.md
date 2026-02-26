# Feature: Multi-Model Dispatch Planning Wiring

## Feature Description

Wire the `dispatch` tool into the `/planning` command as a research acceleration mechanism. During Phases 2-3 (Codebase Intelligence and Documentation Research), the planning model can dispatch specific research queries to other models — documentation lookups, library comparisons, API surface summaries, pattern analysis — while retaining full control of reasoning and synthesis. This is the fourth slice of the multi-model dispatch feature, extending coverage to the last major workflow command without dispatch integration.

## User Story

As a developer planning a new feature, I want the planning model to dispatch targeted research queries to other AI models during codebase and documentation analysis phases, so that planning is faster and more thorough without requiring me to manually look up information or switch contexts.

## Problem Statement

`/planning` is the most reasoning-intensive command in the workflow. It runs 6 phases of deep analysis (MVP discovery, technology exploration, feature understanding, codebase intelligence, documentation research, strategic synthesis). During Phases 2-3, the model performs extensive research — exploring codebase patterns, reading documentation, checking library compatibility. Currently:

1. **All research is sequential**: The model reads one file at a time, fetches one URL at a time. There's no way to delegate a research query to another model while continuing local analysis.
2. **No second opinion on research findings**: The model's understanding of a library or pattern is limited to its own training data plus whatever Archon/WebFetch returns. No way to cross-check against another model's knowledge.
3. **The "No subagents" rule blocks creativity**: The preamble says "No subagents. No delegated research." — but dispatch is not a subagent. It's a tool call that returns inline results to the same conversation. The distinction is not clarified, so the model won't consider using dispatch even if it's available.

The three execution-path commands (`/execute`, `/code-review`, `/code-loop`) already have dispatch wiring from Slice 2. `/planning` is the only major workflow command without it.

## Solution Statement

- Decision 1: **Clarify dispatch ≠ subagent** — add a one-line clarification after the "No subagents" rule that dispatch tool calls are allowed because they return inline and the planner retains full reasoning control.
- Decision 2: **Integrate dispatch into Phase 2 and Phase 3** — rather than a separate phase, add dispatch guidance directly into the existing Phase 2 (Codebase Intelligence) and Phase 3 (Documentation Research) sections. This keeps the flow natural: the model does local research first, then considers dispatching to fill gaps.
- Decision 3: **Research dispatch only, not generation** — during planning, dispatch is for research queries (documentation, comparisons, API summaries, pattern explanations). NOT for generating plan content — the planning model writes the plan.
- Decision 4: **Same optional pattern as Slice 2** — dispatch is guidance, not a gate. If `opencode serve` isn't running, planning works exactly as before.
- Decision 5: **Single file change** — only `.opencode/commands/planning.md` is modified.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Low
- **Primary Systems Affected**: `.opencode/commands/planning.md`
- **Dependencies**: `dispatch` tool from Slice 1 (`.opencode/tools/dispatch.ts`)

### Slice Guardrails (Required)

- **Single Outcome**: `/planning` command contains dispatch guidance for research acceleration during Phases 2-3
- **Expected Files Touched**: 1 file (`.opencode/commands/planning.md`)
- **Scope Boundary**: Does NOT modify dispatch.ts, does NOT create new commands or agents. Does NOT change the 6-phase structure. Does NOT make dispatch mandatory.
- **Split Trigger**: If the dispatch section exceeds 80 lines within any single phase, extract to a reference file

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/commands/planning.md` (lines 1-584) — Why: the file being modified. Must understand current structure: preamble rules (lines 36-39), Phase 2 Codebase Intelligence (lines 193-237), Phase 3 Documentation Research (lines 239-257), Phase 4 Strategic Design (lines 259-279)
- `.opencode/commands/execute.md` (section 1.7) — Why: existing dispatch guidance pattern to mirror. Shows "When to dispatch / When NOT to dispatch / Model routing / Prompt templates" structure
- `.opencode/agents/code-review.md` (dispatch section) — Why: existing dispatch guidance pattern for review context. Shows model routing table format
- `.opencode/commands/code-loop.md` (dispatch section) — Why: existing dispatch guidance pattern for loop context
- `.opencode/tools/dispatch.ts` (lines 1-280) — Why: current tool with 9 args (provider, model, prompt, sessionId, port, cleanup, timeout, systemPrompt, jsonSchema). Must understand available capabilities for prompt templates
- `opencode.json` (lines 11-87) — Why: available models in `bailian-coding-plan` provider for routing table

### New Files to Create

- None — single file modification

### Related Memories (from memory.md)

- Memory: "`/execute` Archon RAG policy: plan is source of truth, RAG is recovery path only" — Relevance: in planning, dispatch follows a different pattern — it's proactive research acceleration, not recovery. But still optional.
- Memory: "Planning quality floor: Require concrete code samples before writing step-by-step tasks" — Relevance: dispatch can help gather additional context to meet this quality floor
- Memory: "Avoid mixed-scope loops: Combining workflow/docs changes with backend behavior in one slice increases review noise" — Relevance: this slice is docs-only (markdown changes). No code changes.
- Memory: "Context mode detection: Single glob call is more efficient than sequential file probing for mode detection" — Relevance: dispatch can parallelize research the same way — ask another model while continuing local analysis

### Relevant Documentation

- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools/)
  - Specific section: Tool execution context
  - Why: confirms tools are called by the model inline and return results to the same conversation — key distinction from subagents
- [OpenCode Agents](https://opencode.ai/docs/agents/)
  - Specific section: Agent markdown format
  - Why: `/planning` uses a command markdown file, not an agent. Dispatch tool availability depends on the agent running the command (likely `build` or `plan` agent)

### Patterns to Follow

**Existing dispatch guidance in execute.md** (section 1.7):
```markdown
### 1.7. Multi-Model Dispatch (optional acceleration)

The `dispatch` tool sends prompts to other connected AI models via the OpenCode server.
Use it to accelerate execution by delegating appropriate subtasks or gathering pre-implementation research.

**Default behavior**: Execute tasks yourself. Dispatch is an optional optimization, not a requirement.

**When to consider dispatching:**
...

**When NOT to dispatch:**
...

**Model routing for execution tasks:**
| Task Type | Recommended Provider/Model | Why |
...

**How to dispatch a subtask:**
...

**If dispatch fails:** Implement the task yourself...
```
- Why this pattern: same instructional structure for planning dispatch — "Default behavior", "When to dispatch", "When NOT to dispatch", "Model routing", "Prompt templates", "Failure handling".
- Common gotchas: keep guidance concise. Planning already has dense instructions. Don't bloat Phase 2-3 with walls of text.

**Existing "No subagents" preamble rule** (lines 36-39):
```markdown
Important execution rule for this command:
- No subagents.
- No delegated research.
- Do all discovery and planning directly in the main conversation.
```
- Why this pattern: the clarification must be minimal and non-disruptive. Add a single exception line, not a paragraph.
- Common gotchas: don't rewrite the rule. Add a clarification that dispatch is a tool call (inline results, same conversation), not a subagent (separate context window).

**Existing Archon integration in Phase 2** (lines 197-209):
```markdown
Required Archon preflight and retrieval:
- Verify connectivity with `archon_health_check` before discovery work.
- List sources with `archon_rag_get_available_sources`.
- Search codebase patterns using `archon_rag_search_code_examples` with 2-5 keyword queries.
...
```
- Why this pattern: dispatch guidance in Phase 2 follows after the Archon retrieval block — it's an additional tool for filling research gaps that Archon doesn't cover.
- Common gotchas: don't position dispatch as replacing Archon. Archon is required; dispatch is optional acceleration.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Clarify the dispatch/subagent distinction in the preamble.

**Tasks:**
- Add dispatch exception to the "No subagents" rule

### Phase 2: Core Implementation

Add dispatch research guidance to Phase 2 (Codebase Intelligence) and Phase 3 (Documentation Research).

**Tasks:**
- Add dispatch research block at end of Phase 2
- Add dispatch research block at end of Phase 3
- Add model routing table for planning research tasks

### Phase 3: Integration

No additional integration — changes are self-contained within the planning command file.

### Phase 4: Testing & Validation

Manual verification that the markdown is well-structured and doesn't disrupt existing phase flow.

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. UPDATE `.opencode/commands/planning.md` — Clarify dispatch ≠ subagent in preamble

- **IMPLEMENT**: Add a dispatch exception after the existing "No subagents" rule (lines 36-39). This clarifies that dispatch tool calls are allowed because they return inline to the same conversation.

  **Current** (lines 36-44):
  ```markdown
  Important execution rule for this command:
  - No subagents.
  - No delegated research.
  - Do all discovery and planning directly in the main conversation.

  External research is ALLOWED and ENCOURAGED:
  - Use Archon MCP RAG search for curated knowledge base lookup (required)
  - Use WebFetch for specific documentation URLs
  - Use web search for finding library docs and best practices
  ```

  **Replace with:**
  ```markdown
  Important execution rule for this command:
  - No subagents.
  - No delegated research.
  - Do all discovery and planning directly in the main conversation.
  - Exception: the `dispatch` tool is allowed. It sends a research query to another model and returns the result inline to this conversation. You retain full reasoning control. See Phase 2 and Phase 3 for when to use it.

  External research is ALLOWED and ENCOURAGED:
  - Use Archon MCP RAG search for curated knowledge base lookup (required)
  - Use WebFetch for specific documentation URLs
  - Use web search for finding library docs and best practices
  - Use `dispatch` tool for targeted research queries to other AI models (optional, see Phases 2-3)
  ```

- **PATTERN**: `.opencode/commands/planning.md:36-44` — existing preamble rules
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: The exception must be clearly scoped to "research queries" — not "generate plan sections" or "write tasks". The planning model writes the plan; dispatch only provides research inputs.
- **VALIDATE**: Read the file, confirm the dispatch exception line exists after "No delegated research" and a dispatch bullet exists in "External research" list.

### 2. UPDATE `.opencode/commands/planning.md` — Add dispatch research block to Phase 2

- **IMPLEMENT**: Add a dispatch research subsection at the end of Phase 2 (Codebase Intelligence), after line 237 ("If requirements are still ambiguous, ask targeted clarification before continuing.") and before "### Phase 3: Documentation Research". This teaches the model to consider dispatching research queries to fill gaps that local exploration and Archon didn't cover.

  **Insert after line 237 (after "If requirements are still ambiguous..."), before "### Phase 3:":**

  ```markdown

  6. Dispatch research acceleration (optional):

     If `opencode serve` is running, use the `dispatch` tool to accelerate codebase intelligence by sending targeted research queries to other models. This is optional — if dispatch is unavailable, continue with local tools and Archon.

     **When to dispatch during Phase 2:**
     - Compare two library options: "What are the tradeoffs between library A and library B for {use case}?"
     - Understand unfamiliar code patterns: "Explain the {pattern name} pattern used in {framework}. When is it appropriate?"
     - Check API surfaces: "What methods does {library} v{version} expose for {feature}? Include required imports."
     - Cross-check architecture decisions: "Is {proposed approach} a common pattern for {problem type}? What are the pitfalls?"

     **When NOT to dispatch during Phase 2:**
     - Questions answerable by reading local files (use Glob/Grep/Read instead)
     - Questions answerable by Archon RAG (use Archon first, dispatch only if Archon misses)
     - Asking another model to explore the codebase (the dispatched model has no file access)
     - Vague, open-ended questions ("What should I build?") — dispatch works best for specific, bounded queries

     **How to dispatch a research query:**
     ```
     dispatch({
       provider: "bailian-coding-plan",
       model: "qwen3.5-plus",
       prompt: "I am planning a {feature type} feature using {stack}.\nQuestion: {specific question}\nContext: {relevant context from codebase exploration}\nBe concise — 2-3 paragraphs max.",
       timeout: 30,
       systemPrompt: "You are a technical research assistant. Answer concisely with concrete details. Include code examples when relevant. Do not ask follow-up questions."
     })
     ```

     **Using dispatch results in Phase 2:**
     - Cross-reference dispatch answers with local codebase evidence before trusting them
     - If dispatch contradicts local evidence, trust local evidence (it's the actual codebase)
     - Record useful dispatch findings in the plan's "Relevant Documentation" or "Patterns to Follow" sections
     - Note the source: "Dispatch research ({model}): {finding}"
  ```

- **PATTERN**: `.opencode/commands/execute.md` section 1.7 — same "when to / when not to / how to / using results" structure
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: 
  1. The dispatch prompt template uses `timeout: 30` and `systemPrompt` — these are Slice 3 enhanced args, now available.
  2. Must emphasize "dispatched model has no file access" — can't ask it to explore the codebase.
  3. Must emphasize "Archon first, dispatch second" — don't bypass the required Archon preflight.
  4. The numbered item is "6." to continue from the existing 5 numbered items in Phase 2 (1. Project structure, 2. Pattern recognition, 3. Dependency analysis, 4. Testing patterns, 5. Integration points).
- **VALIDATE**: Read the file, confirm subsection 6 exists at end of Phase 2, before Phase 3.

### 3. UPDATE `.opencode/commands/planning.md` — Add dispatch research block to Phase 3

- **IMPLEMENT**: Add a dispatch research subsection at the end of Phase 3 (Documentation Research), after line 257 ("External documentation URLs with specific sections and why they matter") and before "### Phase 4: Strategic Design and Synthesis". This teaches the model to use dispatch for documentation research when local sources and Archon are insufficient.

  **Insert after line 257 (after the "Output a comprehensive..." paragraph), before "### Phase 4:":**

  ```markdown

  **Dispatch research acceleration (optional):**

  After local docs and Archon retrieval, if specific documentation gaps remain, use `dispatch` to query other models:

  **When to dispatch during Phase 3:**
  - Library documentation not in Archon: "What is the recommended setup for {library} v{version} with {framework}?"
  - Version compatibility: "Is {library A} v{version} compatible with {library B} v{version}? Any known issues?"
  - Best practices not found locally: "What are the best practices for {pattern} in {language/framework}? Include pitfalls."
  - API reference details: "What parameters does {function/method} accept? What does it return? Include TypeScript types."

  **When NOT to dispatch during Phase 3:**
  - Documentation already found via Archon or WebFetch (don't duplicate)
  - General knowledge questions you can answer from training data
  - Questions that require reading the user's specific codebase (dispatch model has no file access)

  **How to dispatch a documentation query:**
  ```
  dispatch({
    provider: "bailian-coding-plan",
    model: "qwen3.5-plus",
    prompt: "Documentation research for planning:\n\nTopic: {library/API/pattern}\nSpecific question: {what you need to know}\nContext: {how it will be used in the planned feature}\n\nProvide: exact API signatures, required imports, configuration, and common gotchas.",
    timeout: 30,
    systemPrompt: "You are a documentation research assistant. Provide precise, factual API documentation. Include exact function signatures, parameter types, and return types. If uncertain, say so."
  })
  ```

  **Using dispatch results in Phase 3:**
  - Verify claims against official documentation when possible (WebFetch the official docs URL)
  - Include verified dispatch findings in the plan's "Relevant Documentation" section with source attribution
  - If dispatch provides code examples, verify they compile/match current library versions before including in the plan
  - Note in plan: "Dispatch-sourced ({model}): {documentation reference}"
  ```

- **PATTERN**: Phase 2 dispatch block (Task 2 above) — same instructional structure
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: 
  1. Phase 3 dispatch focuses on documentation, not codebase patterns (that's Phase 2).
  2. Must emphasize "verify against official docs" — dispatched model's training data may be outdated.
  3. The `systemPrompt` is different from Phase 2 — focused on documentation precision rather than general research.
- **VALIDATE**: Read the file, confirm dispatch block exists at end of Phase 3, before Phase 4.

### 4. UPDATE `.opencode/commands/planning.md` — Add model routing table for planning

- **IMPLEMENT**: Add a model routing reference after the Phase 3 dispatch block (at the end of Phase 3, before Phase 4). This consolidates routing guidance for both Phase 2 and Phase 3 dispatch in one place.

  **Insert after the Phase 3 dispatch block, before "### Phase 4:":**

  ```markdown

  **Model routing for planning research dispatch:**

  | Research Type | Recommended Provider/Model | Why |
  |---------------|---------------------------|-----|
  | Library comparison / architecture questions | `bailian-coding-plan/qwen3.5-plus` | Strong reasoning, broad knowledge |
  | API surface / code pattern questions | `bailian-coding-plan/qwen3-coder-plus` | Code-specialized with thinking |
  | Documentation lookups / version compatibility | `bailian-coding-plan/kimi-k2.5` | Long context, good at factual recall |
  | Quick factual checks | `bailian-coding-plan/qwen3-coder-next` | Fast response, good enough for simple lookups |
  | Deep research / complex tradeoff analysis | `anthropic/claude-sonnet-4-20250514` | Strongest reasoning when accuracy is critical |

  These are recommendations. Use any connected model that fits the query. If unsure, default to `qwen3.5-plus`.
  ```

- **PATTERN**: `.opencode/commands/execute.md` section 1.7 — model routing table format
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: The routing table is guidance, not enforcement. Models should be the same as in other dispatch sections for consistency but recommendations differ because planning research queries are different from execution/review tasks.
- **VALIDATE**: Read the file, confirm routing table exists at end of Phase 3 section.

### 5. UPDATE `.opencode/commands/planning.md` — Add dispatch tracking to Report section

- **IMPLEMENT**: Add a dispatch usage line to the Report section at the end of the file (lines 577-584).

  **Current** (lines 577-584):
  ```markdown
  ## Report

  After creating the plan, provide:
  - Summary of feature and approach
  - Full path to created plan file
  - Complexity assessment
  - Key implementation risks or considerations
  - Archon retrieval summary (sources searched and key references)
  - Estimated confidence score for one-pass success
  ```

  **Replace with:**
  ```markdown
  ## Report

  After creating the plan, provide:
  - Summary of feature and approach
  - Full path to created plan file
  - Complexity assessment
  - Key implementation risks or considerations
  - Archon retrieval summary (sources searched and key references)
  - Dispatch research summary (queries dispatched, models used, and key findings — or "No dispatch used")
  - Estimated confidence score for one-pass success
  ```

- **PATTERN**: `.opencode/commands/execute.md` report section — "Dispatch used" tracking field
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Keep it on one line with guidance for both "used" and "not used" cases.
- **VALIDATE**: Read the file, confirm "Dispatch research summary" line exists in Report section.

---

## TESTING STRATEGY

### Unit Tests

N/A — all changes are markdown instruction files. No executable code modified.

### Integration Tests

**Test 1: Planning with dispatch available**
- Run `/planning` on a feature that requires library research
- Expected: model considers dispatching research queries during Phase 2-3
- Pass criteria: no errors, planning completes, report may include "Dispatch research summary"

**Test 2: Planning without dispatch (no server)**
- Run `/planning` without `opencode serve` running
- Expected: model proceeds normally, skips dispatch, uses Archon + local tools
- Pass criteria: no blocking errors, planning completes as if dispatch doesn't exist

**Test 3: Dispatch used for library comparison**
- During Phase 0.5 (Technology Exploration), dispatch "Compare library A vs library B"
- Expected: dispatch returns comparison, model incorporates into decision matrix
- Pass criteria: dispatch result is useful and referenced in the plan

**Test 4: Dispatch result contradicts local evidence**
- Dispatch claims a pattern that doesn't match the actual codebase
- Expected: model trusts local evidence per instructions ("trust local evidence")
- Pass criteria: model notes the discrepancy and follows local evidence

**Test 5: Excessive dispatch usage**
- Model dispatches every minor question instead of using local tools
- Expected: "When NOT to dispatch" guidance prevents over-use
- Pass criteria: dispatch is used selectively for genuine research gaps, not routine file reads

### Edge Cases

- **E1: Dispatch returns outdated library info** — instructions say "verify against official docs". The model should WebFetch to cross-check.
- **E2: Dispatch is slow (30s+ for a research query)** — timeout: 30 in the prompt template caps this. If timeout fires, model continues with local research.
- **E3: Archon and dispatch both return conflicting info** — instructions prioritize local evidence > Archon > dispatch. Clear hierarchy.
- **E4: Model dispatches during Phase 0 or Phase 1** — no dispatch guidance in those phases. Model should only dispatch during Phases 2-3 where research happens.
- **E5: Model uses dispatch to generate plan sections** — instructions explicitly say "dispatch is for research queries, not plan generation". The planning model writes the plan.
- **E6: systemPrompt arg not available** — if running an older dispatch.ts without Slice 3 args, the systemPrompt field will be ignored. The prompt template's core query still works without it.

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
N/A — markdown file only
```

### Level 2: Type Safety
```
N/A — markdown file only
```

### Level 3: Unit Tests
```
N/A — markdown file only
```

### Level 4: Integration Tests
```
N/A — manual testing (see Testing Strategy)
```

### Level 5: Manual Validation

**Validate file structure:**
1. Read `.opencode/commands/planning.md` — confirm:
   - Dispatch exception in preamble rules (after "No delegated research")
   - Dispatch bullet in "External research" list
   - Phase 2 subsection 6 "Dispatch research acceleration" at end of Phase 2
   - Phase 3 "Dispatch research acceleration" block at end of Phase 3
   - Model routing table at end of Phase 3
   - "Dispatch research summary" in Report section

**Validate no existing instructions disrupted:**
2. Confirm Phase 0, 0.5, 1 are unchanged
3. Confirm Phase 2 items 1-5 and Archon preflight are unchanged
4. Confirm Phase 3 local/external/Archon blocks are unchanged
5. Confirm Phase 4, Phase 5 are unchanged
6. Confirm all existing rules (spec handshake, approval gate, slice discipline, Archon requirement) are unchanged

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] Preamble clarifies dispatch ≠ subagent (exception line added)
- [ ] "External research" list includes dispatch bullet
- [ ] Phase 2 has dispatch research subsection (numbered item 6)
- [ ] Phase 2 dispatch includes: when to dispatch, when NOT to, prompt template, result usage
- [ ] Phase 3 has dispatch research block
- [ ] Phase 3 dispatch includes: when to dispatch, when NOT to, prompt template, result usage
- [ ] Model routing table present with 5+ model recommendations
- [ ] Prompt templates use Slice 3 args (timeout, systemPrompt)
- [ ] Report section includes "Dispatch research summary" field
- [ ] All dispatch guidance is framed as optional (not mandatory/blocking)
- [ ] Existing Phase 2-3 content (Archon preflight, code sample requirement, local docs) unchanged
- [ ] No existing rules or gates disrupted

### Runtime (verify after testing/deployment)

- [ ] Planning works normally when dispatch is unavailable
- [ ] Model dispatches selectively during Phases 2-3 when server is running
- [ ] Dispatch results are cross-referenced against local evidence
- [ ] Report includes dispatch research summary

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] No existing planning workflow behavior changed or broken

---

## NOTES

### Key Design Decisions

- **Integrated into existing phases, not a new phase**: Adding dispatch guidance directly into Phase 2 and Phase 3 is more natural than creating a "Phase 3.5". The model should consider dispatch as part of its research toolkit, not as a separate step.
- **Research only, not generation**: During planning, dispatch is explicitly scoped to research queries. The planning model writes the plan. This prevents the anti-pattern of dispatching "write the implementation plan" to another model.
- **Archon first, dispatch second**: The Archon requirement is non-skippable. Dispatch supplements Archon, it doesn't replace it. This maintains the existing RAG-first policy.
- **Trust hierarchy: local > Archon > dispatch**: When sources conflict, local codebase evidence wins. Then Archon (curated docs). Then dispatch (model knowledge). This prevents dispatch hallucinations from corrupting the plan.
- **Prompt templates use Slice 3 enhanced args**: Templates include `timeout: 30` and `systemPrompt` to demonstrate the new capabilities. These degrade gracefully if Slice 3 isn't deployed (the args are just ignored by older dispatch.ts versions, which would cause a validation error — but Slice 3 is already deployed).

### Risks

- **Models may still not use dispatch**: Even with guidance, the model may prefer local tools. Mitigation: the guidance is clear and prompt templates are copy-paste ready. Low risk because local tools are fine — dispatch is bonus acceleration.
- **Dispatch research may slow down planning**: Each dispatch adds 10-30s of latency. Mitigation: timeout: 30 caps wait time. "When NOT to dispatch" rules prevent unnecessary dispatches. The model should only dispatch 2-3 times per planning session at most.
- **Dispatched research may be inaccurate**: Models hallucinate. Mitigation: "verify against official docs" and "trust local evidence" instructions. The plan should never be built solely on dispatch results.
- **Preamble exception could be misinterpreted**: The "dispatch exception" to "No subagents" might encourage the model to also spawn Task subagents. Mitigation: the exception is explicitly scoped: "the `dispatch` tool is allowed" — not "subagents are allowed for research".

### Follow-up Slices

- **Slice 5**: `/dispatch-status` command — check `opencode serve` health, list connected models, recent dispatch history
- **Slice 6**: Batch dispatch — send same prompt to N models, compare responses side-by-side
- **Slice 7**: Auto-routing — auto-select best model based on task type without manual provider/model args
- **Slice 8**: `/final-review` and `/system-review` dispatch wiring — secondary workflow commands

### Confidence Score: 9/10

- **Strengths**: Single file change, markdown only, follows established Slice 2 pattern exactly. All insertion points clearly identified with line numbers. Dispatch tool fully built (Slices 1+3). Prompt templates use real args. Trust hierarchy and scoping rules are explicit.
- **Uncertainties**: Whether models will actually use dispatch during planning (depends on model capability). Whether 30s timeout is sufficient for research queries (may need tuning).
- **Mitigations**: Dispatch is optional — worst case it's ignored. Timeout can be adjusted in prompt templates without code changes.
