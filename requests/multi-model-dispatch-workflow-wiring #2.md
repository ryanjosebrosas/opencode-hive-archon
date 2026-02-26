# Feature: Multi-Model Dispatch Workflow Wiring

## Feature Description

Wire the `dispatch` custom tool (built in Slice 1) into the three core workflow commands: `/execute`, `/code-review` (agent), and `/code-loop`. This adds dispatch guidance sections to each command/agent markdown file, telling the model WHEN to use dispatch, WHICH models to pick for different task types, and HOW to format dispatch prompts. The model decides at runtime whether to dispatch — these are instructions, not hard gates.

## User Story

As a developer running the PIV Loop workflow, I want my primary model to automatically consider dispatching subtasks to other connected models during execution, review, and fix loops, so that I get faster results, cheaper token usage on boilerplate, and multi-perspective code reviews without manual intervention.

## Problem Statement

The `dispatch` tool exists (Slice 1) but no workflow command knows about it. The models running `/execute`, `/code-review`, and `/code-loop` have no instructions on when or how to delegate work to other models. Without guidance, dispatch will never be used — it's just a tool sitting in the toolbox with no playbook.

## Solution Statement

- Decision 1: **Instructions-only pattern** — add dispatch guidance as new sections in existing markdown files. No hard gates, no mandatory steps. The model evaluates dispatch opportunities at runtime.
- Decision 2: **Model routing table** — include a model recommendation table in each command so the model knows which provider/model to use for which task type (e.g., cheap model for boilerplate, strong model for security review).
- Decision 3: **Prompt templates** — provide copy-paste-ready prompt templates for common dispatch scenarios (code generation, review, research) so the model doesn't have to invent prompts from scratch.
- Decision 4: **No changes to dispatch.ts** — the tool is complete. All changes are markdown-only.
- Decision 5: **Additive, non-breaking** — new sections are appended to existing commands. Existing workflow logic is untouched. If dispatch is unavailable (no `opencode serve`), commands work exactly as before.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Low-Medium
- **Primary Systems Affected**: `.opencode/commands/execute.md`, `.opencode/agents/code-review.md`, `.opencode/commands/code-loop.md`
- **Dependencies**: `dispatch` tool from Slice 1 (`.opencode/tools/dispatch.ts`)

### Slice Guardrails (Required)

- **Single Outcome**: All three workflow commands/agents contain dispatch guidance that models can follow at runtime
- **Expected Files Touched**: 3 files (execute.md, code-review.md, code-loop.md)
- **Scope Boundary**: Does NOT modify dispatch.ts, does NOT add new commands, does NOT create new agents. Does NOT touch `/final-review`, `/commit`, `/planning`, or `/prime`.
- **Split Trigger**: If any command's dispatch section exceeds 80 lines, split into a separate dispatch-guide reference file

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `.opencode/tools/dispatch.ts` (lines 1-152) — Why: the tool being wired in. Must understand args (provider, model, prompt, sessionId, port, cleanup) and return format (`--- dispatch response from provider/model ---\n{text}`)
- `.opencode/commands/execute.md` (lines 1-251) — Why: target file for dispatch integration. Current structure: Hard Entry Gate → Plan Read → Archon Preflight → Task Execution → Validation → Report
- `.opencode/agents/code-review.md` (lines 1-107) — Why: target agent file. Current structure: Archon RAG → What to Check → Output Format
- `.opencode/commands/code-loop.md` (lines 1-260) — Why: target file. Current structure: Pre-Loop RAG → UBS Scan → Fix Loop (review → plan → execute → validate) → Handoff
- `opencode.json` (lines 1-119) — Why: available models and provider IDs for the routing table

### New Files to Create

- None — all changes are updates to existing files

### Related Memories (from memory.md)

- Memory: "`/execute` Archon RAG policy: plan is source of truth, RAG is recovery path only" — Relevance: dispatch follows same philosophy — plan is primary, dispatch is an optional acceleration. Don't make it mandatory.
- Memory: "Avoid mixed-scope loops: Combining workflow/docs changes with backend behavior in one slice increases review noise" — Relevance: this slice is docs-only (markdown changes). No code changes.
- Memory: "Incremental-by-default slices with full validation every loop" — Relevance: each command gets a self-contained dispatch section. They don't depend on each other.

### Relevant Documentation

- [OpenCode Custom Tools](https://opencode.ai/docs/custom-tools/)
  - Specific section: Tool execution context
  - Why: confirms tools are called by the model based on description + args. Dispatch guidance makes the model more likely to use it effectively.
- [OpenCode Agents](https://opencode.ai/docs/agents/)
  - Specific section: Agent markdown format, tools config
  - Why: code-review agent must have `dispatch` tool enabled in frontmatter

### Patterns to Follow

**Existing Archon RAG guidance in code-review.md** (lines 22-40):
```markdown
## Archon RAG Integration

Before reviewing code, search Archon's knowledge base for relevant documentation...

**When to search Archon:**
- When reviewing code that uses external libraries...
- When checking architecture patterns...

**How to search:**
1. `rag_get_available_sources()` — see what curated docs are indexed
2. `rag_search_knowledge_base(query="2-5 keywords")` — find relevant documentation
```
- Why this pattern: same structure for dispatch guidance — "When to dispatch", "How to dispatch", with concrete examples. Consistent with existing agent instructions.
- Common gotchas: keep guidance concise. The agent's context window is limited. Don't write an essay — write actionable rules.

**Existing recovery-path pattern in execute.md** (lines 85-105):
```markdown
### 1.6. Archon Knowledge Retrieval (recovery path only)

The plan produced by `/planning` is the source of truth...

**Default behavior**: Trust the plan. Do NOT run upfront RAG searches before implementation.

**Recovery trigger**: If during task execution you encounter any of these:
- A plan reference that is ambiguous...
```
- Why this pattern: dispatch in `/execute` follows the same "optional acceleration, not mandatory" pattern. Trust the plan; dispatch only when it makes sense.
- Common gotchas: don't frame dispatch as a required step. It's guidance for the model to consider.

**Existing tool enablement in agent frontmatter** (code-review.md lines 1-15):
```yaml
---
tools:
  read: true
  glob: true
  grep: true
  bash: true
  archon_rag_search_knowledge_base: true
  write: false
  edit: false
---
```
- Why this pattern: the code-review agent must have `dispatch: true` in its tools frontmatter, or the tool won't be available to it.
- Common gotchas: tool name in frontmatter is the filename without extension: `dispatch: true`.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Enable the dispatch tool in the code-review agent's tool permissions.

**Tasks:**
- Add `dispatch: true` to code-review agent frontmatter

### Phase 2: Core Implementation

Add dispatch guidance sections to all three target files. Each section includes: when to dispatch, model routing table, prompt templates, and integration with existing workflow.

**Tasks:**
- Add "Multi-Model Dispatch" section to `/execute` command
- Add "Multi-Model Dispatch" section to `code-review` agent
- Add "Multi-Model Dispatch" section to `/code-loop` command

### Phase 3: Integration

No additional integration needed — the sections are self-contained within each file.

### Phase 4: Testing & Validation

Manual verification that the markdown is well-structured and doesn't break existing command behavior.

**Tasks:**
- Verify each file renders correctly
- Verify no existing instructions were disrupted
- Test dispatch invocation in a live session

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. UPDATE `.opencode/agents/code-review.md` — Enable dispatch tool

- **IMPLEMENT**: Add `dispatch: true` to the frontmatter tools section. This allows the code-review agent to call the dispatch tool.

  **Current** (lines 4-14):
  ```yaml
  tools:
    read: true
    glob: true
    grep: true
    bash: true
    archon_rag_search_knowledge_base: true
    archon_rag_search_code_examples: true
    archon_rag_read_full_page: true
    archon_rag_get_available_sources: true
    write: false
    edit: false
  ```

  **Replace with:**
  ```yaml
  tools:
    read: true
    glob: true
    grep: true
    bash: true
    dispatch: true
    archon_rag_search_knowledge_base: true
    archon_rag_search_code_examples: true
    archon_rag_read_full_page: true
    archon_rag_get_available_sources: true
    write: false
    edit: false
  ```

- **PATTERN**: `.opencode/agents/code-review.md:4-14` — existing tools frontmatter
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Tool name in frontmatter is the filename without `.ts` extension: `dispatch`, not `dispatch.ts` or `dispatch_tool`.
- **VALIDATE**: Read the file, confirm `dispatch: true` is present in tools section.

### 2. UPDATE `.opencode/agents/code-review.md` — Add dispatch guidance section

- **IMPLEMENT**: Add a new section after the existing "Archon RAG Integration" section (after line 40) and before "What to Check" (line 42). The section teaches the agent when and how to use dispatch for multi-model review.

  **Insert after line 40 (after "If Archon is unavailable, proceed with review using local context only."):**

  ```markdown

  ## Multi-Model Dispatch (Second Opinions)

  You have access to the `dispatch` tool which sends prompts to other AI models via the OpenCode server.
  Use it to get second opinions on complex or security-sensitive code.

  **When to dispatch for a second opinion:**
  - Security-sensitive changes (auth, crypto, input validation, SQL) — dispatch to a second model for security review
  - Architecture changes (new patterns, major refactors) — dispatch for architecture review
  - Complex algorithms or business logic — dispatch for logic verification
  - When you are uncertain about a finding — dispatch to confirm or refute

  **When NOT to dispatch:**
  - Simple formatting, naming, or style issues
  - Obvious bugs you are confident about
  - When `opencode serve` is not running (dispatch will return a connection error — that's fine, skip it)

  **Model routing for review tasks:**
  | Task Type | Recommended Provider/Model | Why |
  |-----------|---------------------------|-----|
  | Security review | `anthropic/claude-sonnet-4-20250514` | Strong at security analysis |
  | Architecture review | `bailian-coding-plan/qwen3.5-plus` | Good architectural reasoning |
  | Logic verification | `bailian-coding-plan/qwen3-coder-plus` | Code-specialized |
  | General second opinion | `bailian-coding-plan/qwen3-coder-next` | Fast, capable coder |

  **How to dispatch a review:**
  ```
  dispatch({
    provider: "bailian-coding-plan",
    model: "qwen3-coder-plus",
    prompt: "Review this code for [security/architecture/logic] issues:\n\n```python\n{paste the relevant code}\n```\n\nFocus on: {specific concern}\nContext: {what the code does, what changed}"
  })
  ```

  **Merging dispatch findings:**
  - If the dispatched model finds issues you missed, add them to your findings with a note: "Confirmed by {provider}/{model}"
  - If the dispatched model disagrees with your finding, note the disagreement and let the user decide
  - If the dispatched model finds nothing new, note: "Second opinion from {model}: no additional issues found"
  - Include dispatch findings in the "RAG-Informed Observations" section (or add a "Dispatch-Informed Observations" subsection)

  **If dispatch fails (server not running, model unavailable):** Proceed with your own review. Dispatch is optional enrichment, not a gate.
  ```

- **PATTERN**: `.opencode/agents/code-review.md:22-40` — existing Archon RAG Integration section (same instructional pattern)
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: The code-review agent is a subagent with limited tools. Ensure `dispatch: true` was added in Task 1 before this section is meaningful. Also, the dispatch prompt must include the actual code — the agent should paste the relevant snippet, not just a file reference (the dispatched model has no file access).
- **VALIDATE**: Read the file, confirm the new section exists between "Archon RAG Integration" and "What to Check".

### 3. UPDATE `.opencode/agents/code-review.md` — Update output format for dispatch findings

- **IMPLEMENT**: Add a "Dispatch-Informed Observations" subsection to the Output Format section (after "RAG-Informed Observations" around line 78-83).

  **Insert after line 83 ("If no RAG sources were consulted or relevant, write: 'No RAG sources applicable to this review.'"):**

  ```markdown

  ### Dispatch-Informed Observations

  List any findings where a second model opinion informed the review:
  - `file:line` — {what dispatch revealed} — Model: {provider/model}

  If no dispatch was used or relevant, write: "No dispatch second opinions requested."
  ```

  Also update the Summary section (around line 85-90) to include dispatch count:

  **Current:**
  ```markdown
  ### Summary

  - Critical: X
  - Major: Y
  - Minor: Z
  - RAG sources consulted: N
  ```

  **Replace with:**
  ```markdown
  ### Summary

  - Critical: X
  - Major: Y
  - Minor: Z
  - RAG sources consulted: N
  - Dispatch second opinions: M
  ```

- **PATTERN**: `.opencode/agents/code-review.md:78-90` — existing RAG observations + summary
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Keep the summary line simple — just a count. Don't bloat the output format.
- **VALIDATE**: Read the file, confirm "Dispatch-Informed Observations" subsection and updated summary exist.

### 4. UPDATE `.opencode/commands/execute.md` — Add dispatch guidance section

- **IMPLEMENT**: Add a new section "### 1.7. Multi-Model Dispatch (optional acceleration)" after section 1.6 (Archon Knowledge Retrieval) and before section 2 (Execute Tasks in Order). This teaches the execute agent when to dispatch during task execution.

  **Insert after line 105 (end of section 1.6, before "### 2. Execute Tasks in Order"):**

  ```markdown

  ### 1.7. Multi-Model Dispatch (optional acceleration)

  The `dispatch` tool sends prompts to other connected AI models via the OpenCode server.
  Use it to accelerate execution by delegating appropriate subtasks or gathering pre-implementation research.

  **Default behavior**: Execute tasks yourself. Dispatch is an optional optimization, not a requirement.

  **When to consider dispatching:**

  1. **Subtask delegation** — delegate simple/repetitive tasks to faster, cheaper models:
     - Boilerplate code generation (CRUD, schemas, type definitions)
     - Test file scaffolding (fixtures, basic test cases)
     - Configuration file generation
     - Documentation generation
     - Repetitive pattern application across multiple files

  2. **Pre-implementation research** — ask another model for context before implementing:
     - "How does library X handle Y?" — when the plan doesn't cover a specific API
     - "What's the recommended pattern for Z?" — when facing an unfamiliar integration
     - "Review this approach before I implement it" — sanity check on complex logic

  **When NOT to dispatch:**
  - Core business logic that requires understanding the full plan context
  - Tasks that require reading many project files (the dispatched model has no file access)
  - Quick, simple changes (dispatch overhead > doing it yourself)
  - When the plan explicitly specifies how to implement something (trust the plan)
  - When `opencode serve` is not running (dispatch will error — that's fine, do it yourself)

  **Model routing for execution tasks:**
  | Task Type | Recommended Provider/Model | Why |
  |-----------|---------------------------|-----|
  | Boilerplate generation | `bailian-coding-plan/qwen3-coder-next` | Fast, good at patterns |
  | Test scaffolding | `bailian-coding-plan/qwen3-coder-plus` | Code-specialized |
  | Research / API lookup | `bailian-coding-plan/qwen3.5-plus` | Strong reasoning |
  | Documentation | `bailian-coding-plan/minimax-m2.5` | Good prose generation |
  | Complex code generation | `anthropic/claude-sonnet-4-20250514` | Strongest reasoning |

  **How to dispatch a subtask:**
  ```
  dispatch({
    provider: "bailian-coding-plan",
    model: "qwen3-coder-next",
    prompt: "Generate a Python {type} that:\n- {requirement 1}\n- {requirement 2}\n\nFollow this pattern:\n```python\n{paste example from plan}\n```\n\nReturn only the code, no explanations."
  })
  ```

  **How to dispatch research:**
  ```
  dispatch({
    provider: "bailian-coding-plan",
    model: "qwen3.5-plus",
    prompt: "I need to implement {task description}.\nQuestion: {specific question about API/pattern/approach}\nContext: {relevant context from the plan}"
  })
  ```

  **Using dispatch results:**
  - Review dispatched code before using it — never blindly paste
  - Adapt generated code to match project patterns (imports, naming, style)
  - If dispatch fails or returns unhelpful results, implement the task yourself
  - Note in the execution report if dispatch was used: "Task N: delegated boilerplate to {model}, reviewed and integrated"

  **If dispatch fails:** Implement the task yourself. Dispatch is optional. Never block execution because dispatch is unavailable.
  ```

- **PATTERN**: `.opencode/commands/execute.md:85-105` — existing section 1.6 (Archon Knowledge Retrieval) uses the same "optional, with guidance on when/how" pattern
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Section numbering — must be 1.7 to fit between 1.6 (Archon retrieval) and 2 (Execute Tasks). Don't renumber existing sections. Also: the dispatched model has NO file access — prompts must include all relevant code/context inline.
- **VALIDATE**: Read the file, confirm section 1.7 exists between 1.6 and 2.

### 5. UPDATE `.opencode/commands/execute.md` — Update report template for dispatch usage

- **IMPLEMENT**: Add a dispatch usage line to the Output Report Meta Information section (around line 204).

  **Current** (lines 203-205):
  ```markdown
  - **Archon RAG recovery used**: {yes — describe gap that triggered it / no — plan was self-contained}
  - **RAG references**: {list of page_ids/URLs used during recovery, or "None"}
  ```

  **Replace with:**
  ```markdown
  - **Archon RAG recovery used**: {yes — describe gap that triggered it / no — plan was self-contained}
  - **RAG references**: {list of page_ids/URLs used during recovery, or "None"}
  - **Dispatch used**: {yes — list tasks delegated and models used / no — all tasks self-executed}
  ```

- **PATTERN**: `.opencode/commands/execute.md:199-205` — existing Meta Information section
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Keep it on one line. The report template is consumed by `/system-review`.
- **VALIDATE**: Read the file, confirm "Dispatch used" line exists in Meta Information.

### 6. UPDATE `.opencode/commands/code-loop.md` — Add dispatch guidance section

- **IMPLEMENT**: Add a new section "## Multi-Model Dispatch in Loop" after the "Pre-Loop UBS Scan" section (after line 64) and before "## Fix Loop" (line 68). This teaches the code-loop orchestrator when to dispatch for review and fix execution.

  **Insert after line 64 (end of "If UBS clean:" / "Proceed to review loop"), before "## Fix Loop":**

  ```markdown

  ## Multi-Model Dispatch in Loop

  The `dispatch` tool sends prompts to other AI models. In the code-loop context, use it for:

  1. **Multi-model review** — get additional review perspectives beyond the primary code-review agent
  2. **Fix delegation** — dispatch fix implementation to fast models while you orchestrate

  **This is optional.** If `opencode serve` is not running, skip all dispatch steps and run the loop normally.

  ### Review Dispatch (during step 1 of each iteration)

  After the primary `/code-review` runs, consider dispatching the changed code to a second model for additional findings:

  **When to dispatch a second review:**
  - First iteration (fresh code, worth getting a second perspective)
  - When review finds security-sensitive issues (get confirmation)
  - When review finds 0 issues (sanity check — did we miss something?)
  - When changes touch multiple interconnected files

  **When to skip dispatch review:**
  - Later iterations with only minor fixes remaining
  - When previous dispatch review added no new findings
  - When changes are trivial (typos, formatting)

  **How to dispatch a review:**
  ```
  dispatch({
    provider: "bailian-coding-plan",
    model: "qwen3-coder-plus",
    prompt: "Review this code change for bugs, security issues, and quality problems:\n\n{paste git diff or relevant code snippets}\n\nContext: {what was changed and why}\n\nReport findings as:\n- Critical: {description}\n- Major: {description}\n- Minor: {description}\n\nIf no issues found, say 'No issues found.'"
  })
  ```

  **Merging dispatch findings with primary review:**
  - Deduplicate — if dispatch finds the same issue as primary review, note "confirmed by {model}" 
  - Add new findings to the review artifact with source attribution
  - Include in the fix plan so `/execute` addresses them

  ### Fix Dispatch (during step 4 of each iteration)

  When running `/execute` to fix review findings, the execute agent may dispatch subtasks to other models.
  This is governed by `/execute`'s own dispatch guidance (section 1.7).

  Additionally, if you have simple, isolated fixes (e.g., "add missing null check at line 42", "rename variable X to Y"):

  **How to dispatch a simple fix:**
  ```
  dispatch({
    provider: "bailian-coding-plan",
    model: "qwen3-coder-next",
    prompt: "Fix this code issue:\n\nFile: {filename}\nIssue: {description from review}\nCurrent code:\n```\n{paste current code}\n```\n\nReturn the fixed code only, no explanations."
  })
  ```

  **Rules for fix dispatch:**
  - Only dispatch fixes you can verify (you must review the result before applying)
  - Never dispatch architectural changes or multi-file refactors
  - If the dispatched fix looks wrong, implement it yourself
  - Track dispatched fixes in the loop report: "Fix dispatched to {model}: {description}"

  ### Model Routing for Loop Tasks

  | Task | Recommended Provider/Model | Why |
  |------|---------------------------|-----|
  | Second review opinion | `bailian-coding-plan/qwen3-coder-plus` | Code-specialized review |
  | Security-focused review | `anthropic/claude-sonnet-4-20250514` | Strong security analysis |
  | Simple fix generation | `bailian-coding-plan/qwen3-coder-next` | Fast, accurate for small fixes |
  | Complex fix generation | `anthropic/claude-sonnet-4-20250514` | Best reasoning for complex logic |
  ```

- **PATTERN**: `.opencode/commands/code-loop.md:37-49` — existing "Pre-Loop: Archon RAG Context Load" section (same instructional pattern: when to do it, how to do it, what to do with results)
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: The code-loop command orchestrates — it calls `/code-review` and `/execute` as subcommands. Dispatch guidance here is for the orchestrator's decisions, not duplicating the guidance already in those sub-files. Keep it focused on WHEN to dispatch, not detailed HOW (the sub-commands handle that).
- **VALIDATE**: Read the file, confirm new section exists between "Pre-Loop UBS Scan" and "Fix Loop".

### 7. UPDATE `.opencode/commands/code-loop.md` — Update loop report for dispatch tracking

- **IMPLEMENT**: Add dispatch tracking to the Loop Summary report template (around line 186-189).

  **Current** (lines 186-189):
  ```markdown
  - **Feature**: {feature-name}
  - **Iterations**: N
  - **Final Status**: Clean / Stopped (unfixable error) / Stopped (user interrupt) / Stopped (user choice)
  ```

  **Replace with:**
  ```markdown
  - **Feature**: {feature-name}
  - **Iterations**: N
  - **Final Status**: Clean / Stopped (unfixable error) / Stopped (user interrupt) / Stopped (user choice)
  - **Dispatch used**: {yes — N dispatches across M iterations / no}
  ```

  Also add a dispatch column to the iteration table (around lines 192-197):

  **Current:**
  ```markdown
  | Iteration | Critical | Major | Minor | Total |
  |-----------|----------|-------|-------|-------|
  | 1 | X | Y | Z | T |
  ```

  **Replace with:**
  ```markdown
  | Iteration | Critical | Major | Minor | Total | Dispatches |
  |-----------|----------|-------|-------|-------|------------|
  | 1 | X | Y | Z | T | N |
  ```

- **PATTERN**: `.opencode/commands/code-loop.md:184-197` — existing Loop Summary template
- **IMPORTS**: N/A (markdown)
- **GOTCHA**: Keep the table simple. "Dispatches" is a count of how many times dispatch was used in that iteration (review + fix combined).
- **VALIDATE**: Read the file, confirm "Dispatch used" in summary and "Dispatches" column in table.

---

## TESTING STRATEGY

### Unit Tests

N/A — all changes are markdown instruction files. No executable code modified.

### Integration Tests

Manual integration testing by running the workflow commands and observing dispatch behavior:

**Test 1: Code review with dispatch**
- Run `/code-review` on a file with security-sensitive code
- Expected: agent considers dispatching for a second opinion (may or may not dispatch depending on complexity)
- Pass criteria: no errors, review output may include "Dispatch-Informed Observations" section

**Test 2: Execute with dispatch**
- Run `/execute` on a plan with simple boilerplate tasks
- Expected: agent considers dispatching boilerplate generation
- Pass criteria: no errors, report may include "Dispatch used: yes" in meta

**Test 3: Code loop with dispatch**
- Run `/code-loop` on a feature with known issues
- Expected: loop considers dispatching second review and simple fixes
- Pass criteria: no errors, loop report may include "Dispatches" column

**Test 4: Dispatch unavailable (no server)**
- Run any command WITHOUT `opencode serve` running
- Expected: dispatch tool returns connection error, command proceeds normally without dispatch
- Pass criteria: no blocking errors, command completes as if dispatch doesn't exist

### Edge Cases

- **E1: Dispatch returns empty response** — instructions say "implement it yourself". The dispatch tool wraps empty responses with `[dispatch warning]` prefix so the model knows to fall back.
- **E2: Dispatch returns incorrect code** — instructions say "review before using, never blindly paste". This is emphasized in all three files.
- **E3: Multiple dispatches in one iteration** — each creates its own session, no interference. The dispatch tool handles session lifecycle independently per call.
- **E4: Code-review agent doesn't have dispatch enabled** — Task 1 adds `dispatch: true` to frontmatter. Without this, the agent can't call the tool even if the guidance section exists.
- **E5: Dispatched model hallucinates file paths** — the dispatched model has no file access. It may reference non-existent files. Instructions say to include all relevant code inline in the prompt.
- **E6: Dispatch adds significant latency** — for models behind slow APIs (large Qwen, Gemini thinking), dispatch may take 30-90 seconds. The "When NOT to dispatch" guidance prevents unnecessary delays on simple tasks.
- **E7: Model routing table becomes stale** — new models get connected, old ones deprecated. The table is guidance, not enforcement. Models can pick any connected provider/model.
- **E8: Dispatch used excessively** — the model dispatches everything instead of doing work itself. "When NOT to dispatch" rules and "Default behavior: do it yourself" framing prevent this.

### Model Routing Rationale

The model routing tables across all three files recommend specific models for specific task types. Here's the reasoning:

| Model | Strengths | Best For |
|-------|-----------|----------|
| `bailian-coding-plan/qwen3-coder-next` | Fast response, good code generation | Boilerplate, simple fixes, test scaffolding |
| `bailian-coding-plan/qwen3-coder-plus` | Code-specialized with thinking | Code review, complex code generation |
| `bailian-coding-plan/qwen3.5-plus` | Strong reasoning, image understanding | Research, architecture review, analysis |
| `bailian-coding-plan/glm-4.7` | Balanced capabilities | General tasks, documentation |
| `bailian-coding-plan/kimi-k2.5` | Long context, reasoning | Large code review, multi-file analysis |
| `bailian-coding-plan/minimax-m2.5` | Good prose generation | Documentation, commit messages |
| `anthropic/claude-sonnet-4-20250514` | Strongest overall reasoning | Security review, complex logic, architecture |
| `openai/gpt-4.1` | Strong coding, tool use | Alternative for any task |

These are recommendations, not requirements. The executing model should pick based on the task at hand.

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style
```bash
# Markdown lint (if available)
# These are markdown files — no code syntax to check
echo "Markdown files — syntax check is visual"
```

### Level 2: Type Safety
```
N/A — markdown files only
```

### Level 3: Unit Tests
```
N/A — markdown files only
```

### Level 4: Integration Tests
```
N/A — manual testing (see Testing Strategy above)
```

### Level 5: Manual Validation

**Validate file structure:**
1. Read `.opencode/agents/code-review.md` — confirm:
   - `dispatch: true` in frontmatter tools
   - "Multi-Model Dispatch" section between "Archon RAG" and "What to Check"
   - "Dispatch-Informed Observations" subsection in Output Format
   - "Dispatch second opinions: M" in Summary

2. Read `.opencode/commands/execute.md` — confirm:
   - Section 1.7 between 1.6 and 2
   - Model routing table present
   - Prompt templates present
   - "Dispatch used" in report Meta Information

3. Read `.opencode/commands/code-loop.md` — confirm:
   - "Multi-Model Dispatch in Loop" section between UBS scan and Fix Loop
   - Review dispatch and fix dispatch subsections
   - Model routing table present
   - "Dispatch used" in Loop Summary
   - "Dispatches" column in iteration table

**Validate no existing instructions disrupted:**
4. Confirm `/execute` still has Hard Entry Gate, Archon Preflight, Task Execution, Validation steps intact
5. Confirm `/code-review` agent still has Archon RAG Integration, What to Check, Output Format intact
6. Confirm `/code-loop` still has Pre-Loop RAG, UBS Scan, Fix Loop, Handoff intact

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `dispatch: true` added to code-review agent frontmatter
- [ ] Code-review agent has Multi-Model Dispatch section with when/how guidance
- [ ] Code-review agent output format includes Dispatch-Informed Observations
- [ ] Code-review agent summary includes dispatch count
- [ ] Execute command has section 1.7 Multi-Model Dispatch
- [ ] Execute command report template includes "Dispatch used" field
- [ ] Code-loop command has Multi-Model Dispatch in Loop section
- [ ] Code-loop report includes dispatch tracking
- [ ] All three files have model routing tables
- [ ] All three files have prompt templates
- [ ] No existing command instructions were disrupted or removed
- [ ] Dispatch is presented as optional in all three files (not mandatory/blocking)

### Runtime (verify after testing/deployment)

- [ ] Code-review agent can successfully call dispatch tool
- [ ] Commands work normally when dispatch is unavailable (no server)
- [ ] Dispatch findings integrate into review output format
- [ ] Execute report includes dispatch usage when applicable

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] No existing workflow behavior changed or broken

---

## NOTES

### Key Design Decisions

- **Instructions-only, not code**: All changes are markdown. The dispatch tool is already built — we're teaching the workflow commands how to use it effectively.
- **Optional, not mandatory**: Every dispatch section explicitly states "if dispatch fails, proceed normally." This prevents dispatch from becoming a gate that blocks workflow execution.
- **Model routing tables**: Concrete recommendations prevent the model from guessing or always picking the same model. Based on actual strengths of connected models.
- **Prompt templates**: Reduces the model's work — copy-paste-ready templates with clear placeholders. This is the key to actually getting dispatch used in practice.
- **Dispatched model has no file access**: A critical constraint. All prompts must include the relevant code inline. This is called out in every dispatch section.

### Risks

- **Models may ignore dispatch guidance**: LLMs may not follow optional instructions consistently. Mitigation: clear trigger conditions ("when to dispatch"), concrete examples, model routing table.
- **Prompt template drift**: As the codebase evolves, the recommended models in routing tables may become outdated. Mitigation: routing tables are guidance, not hard-coded — the model can choose other connected models.
- **Context window pressure**: Adding dispatch sections to commands increases the instruction length. Mitigation: sections are self-contained and concise (~40-60 lines each). Total addition is ~150 lines across 3 files.
- **Dispatch latency**: Dispatch adds round-trip time (create session → prompt → wait → extract). For simple tasks, this may be slower than doing it directly. Mitigation: "When NOT to dispatch" guidance is explicit.

### Follow-up Slices

- **Slice 3**: Add `timeout` arg, `systemPrompt` arg, structured output support to dispatch.ts
- **Slice 4**: Dispatch dashboard — list active dispatch sessions, costs, model usage stats
- **Slice 5**: Batch dispatch — send same prompt to N models, compare responses side-by-side
- **Slice 6**: Auto-routing — let the orchestrating model auto-select the best model based on task type without manual provider/model args

### Confidence Score: 8/10

- **Strengths**: All target files read and understood. Clear integration points identified. Pattern consistency with existing Archon RAG sections. No code changes — markdown only. Dispatch tool already validated in Slice 1.
- **Uncertainties**: Whether models will actually follow the dispatch guidance (depends on model capability and context). Whether the recommended model routing is optimal (can be tuned later). Whether prompt templates cover the most common dispatch scenarios.
- **Mitigations**: All dispatch guidance is additive and optional — worst case, it's ignored and everything works as before. Model routing can be updated in future slices. Prompt templates can be refined based on real-world usage.
