When applying this template to a real project, Layer 1 has three components:

### Layer 1 Components

1. **PRD** — defines **what** to build (MVP scope, features, success criteria). Use `templates/PRD-TEMPLATE.md`
2. **CLAUDE.md** — defines **how** to build (global rules, tech stack, architecture). Use `/init-c`
3. **On-demand context** — reference guides, external docs, tool designs (in `reference/`)

### Creation Order

**New (greenfield) projects:**
1. Create PRD first (research phase — vibe plan to define scope)
2. Use PRD to create global rules (CLAUDE.md)
3. Create on-demand context from PRD + external sources
4. Validate no contradictions between PRD, rules, and context

**Existing projects:**
1. Analyze codebase
2. Create global rules (from codebase analysis)
3. Create on-demand context
4. Validate no contradictions

### CLAUDE.md Sections

Your CLAUDE.md should cover these sections. Use `/init-c` to generate them automatically, or fill in manually.

**Always-loaded (in CLAUDE.md via @sections/):**
1. **Core Principles** — non-negotiable rules (type safety, KISS, YAGNI)
2. **Tech Stack** — language, framework, package manager, linting, database
3. **Architecture** — directory layout, design patterns, file naming
4. **Documentation Standards** — docstring format
5. **Logging Rules** — structured logging, context fields, exception patterns
6. **Testing Patterns** — test structure, markers, commands, coverage
7. **Dev Commands** — install, run, lint, test commands
8. **Common Patterns** — 2-3 code examples of patterns used throughout

**On-demand (in `reference/` folder, loaded when needed):**
- PRD stored in `reference/PRD.md` (loaded when choosing next feature to build)
- Task-specific step-by-step guides (e.g., `reference/api_guide.md`)
- Detailed patterns only relevant for specific task types

**How to load on-demand guides:**

- **Method 1: Reference in CLAUDE.md** — mention the guide and when to read it. Flexible but AI must remember to load it.
- **Method 2: Include in slash commands (recommended)** — reference the guide in slash command prompts using `@reference/guide.md`. Guarantees the guide is loaded for the task. More reliable, better for consistency.
- See `templates/COMMAND-TEMPLATE.md` for how to design commands with the INPUT → PROCESS → OUTPUT framework.

**Two-question framework for deciding:**
1. Is this constant or task-specific? (constant → Layer 1, task-specific → Layer 2)
2. Needed every session? (yes → auto-load in sections/, no → on-demand in reference/)

### Layer 1 Reconciliation

When using a project template, you must reconcile template rules with your project-specific rules. Use the AI to inspect your PRD, global rules, and on-demand context for contradictions. All Layer 1 artifacts must work together — any inconsistency leads to problems during implementation.

**For comprehensive Layer 1 guidance**, see `reference/global-rules-optimization.md` for:
- Modular organization (Version 1 vs Version 2 with @sections)
- The Two-Question Framework for auto-load vs on-demand decisions
- Two methods for loading on-demand reference guides
- 10 recommended CLAUDE.md sections with examples
- Building Layer 1 with AI (two prompts, `/init-c` command)
- Practical exercise: auditing and optimizing a bloated CLAUDE.md
