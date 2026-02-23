Help me create the global rules for my project. Analyze the project first to see if it is a brand new project or if it is an existing one, because if it's a brand new project, then we need to do research online to establish the tech stack and architecture and everything that goes into the global rules. If it's an existing code base, then we need to analyze the existing code base.

## Output Architecture: Modular Sections

You will generate a **modular** structure — NOT a flat CLAUDE.md file. The output is:

1. **A slim `CLAUDE.md`** (30-60 lines) containing ONLY `@sections/` references
2. **Individual `sections/*.md` files** (one per topic, 15-50 lines each)
3. **A `reference/` directory suggestion** for task-specific guides

This follows the Two-Question Framework:
- **Is this constant or task-specific?** Constant → `sections/`, Task-specific → `reference/`
- **Needed every session?** Yes → `sections/` (auto-loaded), No → `reference/` (on-demand)

## CLAUDE.md Structure (What You Generate)

The generated CLAUDE.md must look like this:

```markdown
# {Project Name}

{One-line description of the project.}

---

## Core Principles
@sections/01_core_principles.md

---

## Tech Stack
@sections/02_tech_stack.md

---

## Architecture
@sections/03_architecture.md

---

## Code Style
@sections/04_code_style.md

---

## Testing
@sections/05_testing.md

---

## Common Patterns
@sections/06_common_patterns.md

---

## Development Commands
@sections/07_dev_commands.md
```

**CRITICAL**: CLAUDE.md contains ONLY `@sections/` references, NEVER inline content. Each `---` separator is required between sections.

**Line Count Constraints**:
- CLAUDE.md: 30-60 lines (only @references)
- Each section: 15-50 lines
- Total: 100-400 lines combined

## Section Definitions (What Goes in Each File)

### `sections/01_core_principles.md`
Non-negotiable development principles: naming conventions, type safety, documentation standards, and AI coding assistant instructions. Keep these clear and actionable. 5-15 bullet points. Include any project-specific AI gotchas at the end.

### `sections/02_tech_stack.md`
Technologies with version numbers: language, framework, package manager, testing tools, linting/formatting, database, deployment.

### `sections/03_architecture.md`
Folder organization, layer patterns, design patterns used. Include ASCII directory tree of the key directories.

### `sections/04_code_style.md`
Naming conventions (functions, classes, variables, model fields). Include 1-2 code examples showing the expected style. Docstring/comment format. Logging conventions (what to log, structured format examples).

### `sections/05_testing.md`
Testing framework and tools. Test file structure and naming conventions. Test patterns and 1-2 examples. Commands to run tests.

### `sections/06_common_patterns.md`
2-3 code examples of common patterns used throughout the codebase. These should be general templates, not task-specific.

### `sections/07_dev_commands.md`
Install, dev server, test, lint/format commands. Any other essential workflow commands. Use code blocks.

## Process

### For Existing Projects

1. **Analyze the codebase thoroughly**:
   - Read config files (`pyproject.toml`, `package.json`, `tsconfig.json`, `Cargo.toml`, etc.)
   - Examine folder structure (`ls` key directories)
   - Review 3-5 representative files for patterns and style
   - Check for existing documentation (README, docs/, etc.)
2. **Apply the Two-Question Framework** for each convention discovered:
   - Constant and needed every session → `sections/` file
   - Task-specific or rarely needed → suggest for `reference/` guide
3. **Generate sections/ files** with actual code examples from the codebase — not placeholders
4. **Generate slim CLAUDE.md** with only `@sections/` references
5. **Suggest reference/ guides** for task-specific patterns (e.g., "Consider creating `reference/api_guide.md` for your REST endpoint patterns")

### For New Projects

1. **Ask clarifying questions**: project type, purpose, tech preferences, scale, team size
2. After answers, **research current best practices** for the chosen tech stack
3. **Generate sections/ files** based on research and best practices
4. **Generate slim CLAUDE.md** with only `@sections/` references
5. **Suggest reference/ guides** that will be useful as the project grows

## Critical Requirements

- **Total length**: 100-400 lines across ALL generated files combined
- **Each section file**: 15-50 lines (focused and actionable)
- **CLAUDE.md**: 30-60 lines (only @references)
- **Be specific, not generic** — use actual code examples, not placeholders
- **Focus on what matters** — include conventions that truly guide development
- **Keep it actionable** — every rule should be immediately followable
- **For existing projects**: Every section must cite actual code from the codebase
- **For new projects**: Research first, then generate — don't output placeholder sections

## Output Format

1. Create the `sections/` directory if it doesn't exist
2. Write each section file: `sections/01_core_principles.md`, `sections/02_tech_stack.md`, etc.
3. Write the slim `CLAUDE.md` with `@sections/` references
4. Print a summary of what was generated and suggest reference/ guides to create later

### Post-Generation Note

After generating, include this note at the bottom of CLAUDE.md:

```markdown
---

> **Template System**: This project uses the modular @sections architecture.
> For deeper context on this system, see the reference guides in `reference/` (e.g., `system-foundations.md`, `piv-loop-practice.md`).
```

Start by analyzing the project structure now. If this is a new project and you need more information, ask your clarifying questions first.
