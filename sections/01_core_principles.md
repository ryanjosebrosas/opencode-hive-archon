**HARD RULE — Opus Never Implements** — Claude Opus (this model) handles ONLY planning, architecture, orchestration, exploration, and strategy. ALL implementation (file edits, code writing, refactoring) MUST be dispatched to T1-T5 models via the dispatch tool through opencode serve. Opus writing code directly is a violation. No exceptions. If dispatch tools are unavailable, write a plan to requests/ and stop.

**Violation examples** (all FORBIDDEN):
- Opus using Edit/Write tools on .ts, .py, .md config, or any source file
- Opus using Task tool with general agent to make edits (general agent = Opus context, NOT a T1-T5 model)
- Opus using swarm-worker-* agents (these are Claude Code built-in agents, not the 5-tier cascade)
- Opus writing code in a response and asking user to apply it

**Valid implementation path**: Plan in requests/ -> dispatch(mode:"relay", provider:"bailian-coding-plan-test", ...) -> T1 edits via relay -> T2 review via dispatch(taskType:"code-review")

**YAGNI** — Only implement what's needed. No premature optimization.
**KISS** — Prefer simple, readable solutions over clever abstractions.
**DRY** — Extract common patterns; balance with YAGNI.
**Limit AI Assumptions** — Be explicit in plans and prompts. Less guessing = better output.
**Always Be Priming (ABP)** — Start every session with /prime. Context is everything.
