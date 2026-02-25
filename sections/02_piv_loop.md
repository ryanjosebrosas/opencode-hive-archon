```
PLAN → IMPLEMENT → VALIDATE → (iterate)
```

### Granularity Principle

Multiple small PIV loops — one feature slice per loop, built completely before moving on.
Complex features (15+ tasks, 4+ phases): `/planning` auto-decomposes into sub-plans.

### Planning (Layer 1 + Layer 2)

**Layer 1 — Project Planning** (done once):
- PRD (what to build), CLAUDE.md (how to build), reference guides (on-demand)

**Layer 2 — Task Planning** (done for every feature):
1. **Vibe Planning** — casual conversation to explore ideas, ask questions, research codebase. See: `templates/VIBE-PLANNING-GUIDE.md`
2. **Structured Plan** — turn conversation into a markdown document
   - Use template: `templates/STRUCTURED-PLAN-TEMPLATE.md`
   - Save to: `requests/{feature}-plan.md`
   - Apply the 4 pillars of Context Engineering (see `sections/03_context_engineering.md` for pillar → plan mapping)

**Do NOT** take your PRD and use it as a structured plan. Break it into granular Layer 2 plans — one per PIV loop.

### Implementation
- Fresh conversation → `/execute requests/{feature}-plan.md`
- Trust but verify
- Never execute implementation work without a `/planning` artifact in `requests/`

### Validation
- AI: tests + linting. Human: code review + manual testing.
- 5-level pyramid: Syntax → Types → Unit → Integration → Human. See `reference/validation-discipline.md`.
- Small issues → fix prompts. Major issues → revert to save point, tweak plan, retry.
