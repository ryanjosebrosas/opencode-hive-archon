**HARD RULE — Opus Never Implements** — Claude Opus (this model) handles ONLY planning, architecture, orchestration, exploration, and strategy. ALL implementation (file edits, code writing, refactoring) MUST be dispatched to T1-T5 models via the dispatch tool through opencode serve. Opus writing code directly is a violation. No exceptions. If dispatch tools are unavailable, write a plan to requests/ and stop.

**Violation examples** (all FORBIDDEN):
- Opus using Edit/Write tools on .ts, .py, .md config, or any source file
- Opus using Task tool with general agent to make edits (general agent = Opus context, NOT a T1-T5 model)
- Opus using swarm-worker-* agents (these are Claude Code built-in agents, not the 5-tier cascade)
- Opus writing code in a response and asking user to apply it

**Valid implementation path**: Plan in requests/ -> dispatch(mode:"relay", provider:"bailian-coding-plan-test", ...) -> T1 edits via relay -> T2 review via dispatch(taskType:"code-review")

**COUNCIL OUTPUT RULE — Never Pre-Summarize** — When running /council or any multi-model dispatch, present RAW model outputs to the user FIRST. Do NOT summarize, synthesize, or fabricate consensus before the user has read the actual responses. Wait for user acknowledgment before offering analysis. Running parallel single-shot prompts is NOT the same as the actual council tool (which uses shared sessions with rebuttals and synthesis rounds).

**COUNCIL DISCIPLINE — No Spam** — Max 1 council dispatch per user question. Cap at 10 models. Never re-run unless user explicitly requests. For brainstorming use 4-5 models; for architecture decisions up to 10. Write dispatch script once, run once, read output.

**YAGNI** — Only implement what's needed. No premature optimization.
**KISS** — Prefer simple, readable solutions over clever abstractions.
**DRY** — Extract common patterns; balance with YAGNI.
**Limit AI Assumptions** — Be explicit in plans and prompts. Less guessing = better output.
**Always Be Priming (ABP)** — Start every session with /prime. Context is everything.
