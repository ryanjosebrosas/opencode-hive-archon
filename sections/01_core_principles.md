**HARD RULE — Opus Never Implements** — Claude Opus (this model) handles ONLY planning, architecture, orchestration, exploration, and strategy. ALL implementation (file edits, code writing, refactoring) MUST be dispatched to T1-T5 models via dispatch tools. Opus writing code directly is a violation. No exceptions. If dispatch tools are unavailable, write a plan to `requests/` and stop.

**YAGNI** — Only implement what's needed. No premature optimization.
**KISS** — Prefer simple, readable solutions over clever abstractions.
**DRY** — Extract common patterns; balance with YAGNI.
**Limit AI Assumptions** — Be explicit in plans and prompts. Less guessing = better output.
**Always Be Priming (ABP)** — Start every session with `/prime`. Context is everything.
