# Global Rules & Layer 1 Optimization

This guide explains **how to organize your CLAUDE.md for maximum effectiveness** — covering modular organization with @sections, the Two-Question Framework for auto-load vs on-demand decisions, strategic context loading to avoid token bloat, and building Layer 1 with AI — going deeper than the guide at `reference/layer1-guide.md`.

---

## 1. What This Guide Covers

### The Journey from Practice to Construction

The System Foundations guide established the **why** — the system gap, architecture, and baseline assessment. The PIV Loop Practice guide taught the **how** — the PIV Loop in practice, Layer 1 vs Layer 2 planning, the 4 Pillars of Context Engineering, and validation methodology. This guide teaches you **how to build and optimize** your global rules.

This is the construction step. You're not learning concepts or practicing workflows — you're learning how to create the foundation that everything else builds on: your CLAUDE.md file.

### What You'll Learn

- **What global rules are** and where to put them
- **Two organization strategies** — single file vs modular @sections
- **The context bloat problem** and why it matters
- **The Two-Question Framework** for deciding what to auto-load vs load on-demand
- **Loading strategies** — always-loaded vs on-demand, with two loading methods
- **10 recommended sections** for a comprehensive CLAUDE.md
- **Building Layer 1 with AI** — two copy-paste prompts for generating rules
- **Practical exercise** — auditing a real 600-line CLAUDE.md to cut bloat by 60%

### Why This Matters

Without this guide, you might create a CLAUDE.md that's too long (wasting context), too short (missing critical rules), or poorly organized (hard to maintain). The average bloated CLAUDE.md wastes 60-65% of its auto-loaded tokens on content that's only needed occasionally.

This guide teaches you to solve this systematically — not by guessing, but by applying a framework that tells you exactly where each piece of context belongs.

---

## 2. Global Rules: Concept & Placement

### What Global Rules Are

Global rules are the **core of Layer 1 planning** — the stable foundation auto-loaded into every AI session. Think of them as **day one onboarding for your AI coding assistant**. Everything the AI needs to know on its first day to work effectively on your codebase.

If you're familiar with building AI agents, global rules function like a **system prompt** — persistent context that shapes every interaction.

### Universal Concept, Different Names

The concept is the same across all AI coding tools — only the filename differs:

| Tool | Global Rules File |
|------|-------------------|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| Cursor | `AGENTS.md` or `.cursorrules` |
| Windsurf | `AGENTS.md` or `.windsurf` |
| Gemini CLI | `AGENTS.md` |

`AGENTS.md` is emerging as the universal standard — like `README.md` for humans, `AGENTS.md` for AI agents. Most repositories will eventually have both side-by-side.

### Where to Put Global Rules

**Root of repository** (recommended):
- Applies to all work in the project
- Most common and simplest setup
- Place alongside README.md

**Parent directories** (advanced):
- Claude Code looks upward and loads parent CLAUDE.md files
- Useful for monorepos with shared conventions across packages

**Child directories** (advanced):
- Nested CLAUDE.md files for subsection-specific rules
- Only loaded when working in that directory
- Useful when different parts of codebase have different conventions

**Home folder** (`~/.claude/`):
- Personal rules that apply across ALL projects
- Loaded in every session regardless of project

**Recommendation**: Start with a single file at repository root. Add complexity only when clearly needed.

---

## 3. Organization Strategies

Two approaches to organizing your global rules file:

### Version 1: Single File

All rules in one consolidated CLAUDE.md file.

```
CLAUDE.md    # Everything in one place
```

**Pros**: Simple to navigate, easy to search (Ctrl+F), no file fragmentation.

**Cons**: Can become large and unwieldy (600+ lines), harder to maintain independently, all content loads at once.

**Best for**: Small to medium projects, stable conventions, teams wanting simplicity.

### Version 2: Modular Files (Recommended for Growth)

Main CLAUDE.md with `@` references to separate section files.

```
CLAUDE.md                      # Slim file with @references
sections/
├── 01_core_principles.md
├── 02_tech_stack.md
├── 03_architecture.md
└── ...
```

The `@` syntax tells Claude Code to load the referenced file inline:
```markdown
## Core Principles
@sections/01_core_principles.md
```

**Pros**: Easy to maintain individual sections, smaller diffs in version control, scales better for large projects.

**Cons**: More complex initial setup, requires navigating multiple files.

**Best for**: Large or growing projects, teams with multiple contributors, projects that frequently update conventions.

### When to Choose Each

| Factor | Version 1 (Single) | Version 2 (Modular) |
|--------|--------------------|--------------------|
| Project size | Small-medium | Medium-large |
| Team size | Solo or small | Multiple contributors |
| Update frequency | Rarely | Frequently |
| Convention stability | Very stable | Evolving |

**This template uses Version 2** — the modular approach with `sections/` directory and `@` references.

### Converting Between Versions

**V1 → V2**: Split your CLAUDE.md into logical sections, save each as a separate `.md` file in `sections/`, create a new CLAUDE.md with `@` references.

**V2 → V1**: Copy content from all modular files into a single CLAUDE.md, remove `@` references, add section dividers (`---`).

---

## 4. The Context Bloat Problem

### The Issue

Loading everything in global rules auto-loads hundreds of lines every session — including detailed information only relevant for specific task types.

**Problem symptoms**:
- Large token usage before writing any code
- Context window consumed by rarely-used guides
- Slower AI processing
- Reduced space for actual implementation context

### The 80/20 Insight

In a practical exercise, a real project CLAUDE.md was 601 lines. Analysis revealed:

- **One section (tool docstrings) = 400+ lines = 66% of the entire file**
- That section was only needed when creating agent tools — a rare task type
- After optimization: 601 lines → 160 lines auto-loaded (**60-65% reduction**)
- All knowledge remained accessible — just strategically loaded

Most context bloat comes from a small number of detailed sections. Finding and moving those on-demand creates massive savings.

### The Solution

The solution is **strategic loading** — splitting content between always-loaded (auto-load) and load-on-demand using the Two-Question Framework (Section 5) and Loading Strategies (Section 6).

---

## 5. The Two-Question Framework

This is the key decision framework for organizing your Layer 1 content.

### Question 1: Is this constant or task-specific?

- **Constant** (stable, reusable across many tasks) → Layer 1. Go to Question 2.
- **Task-specific** (only for one specific task) → Layer 2 (structured plan). Does NOT belong in CLAUDE.md.

### Question 2: Needed every session?

- **YES** → Auto-load in CLAUDE.md (or `sections/`)
- **NO** → Load on-demand (in `reference/` folder)

### Visual Decision Tree

```
Is this constant or task-specific?
    │
    ├─ Task-specific → Layer 2 (structured plan for that task)
    │
    └─ Constant → Layer 1
           │
           Is it needed EVERY session?
               │
               ├─ YES → Auto-load (CLAUDE.md or sections/)
               │
               └─ NO → On-demand (reference/ folder)
```

### Worked Examples

**Example 1: "Core Principles" (TYPE SAFETY, KISS, YAGNI)**
- Q1: Constant? Yes — applies to all code, all tasks.
- Q2: Every session? Yes — every line of code should follow these.
- **Result**: Auto-load in `sections/01_core_principles.md`

**Example 2: "API Endpoint Building Guide"**
- Q1: Constant? Yes — same patterns every time you build an API.
- Q2: Every session? No — only when building API endpoints.
- **Result**: On-demand in `reference/API_guide.md`

**Example 3: "Feature plan for user authentication"**
- Q1: Constant? No — specific to this one feature.
- **Result**: Layer 2 — goes in `requests/user-auth-plan.md`, not CLAUDE.md at all.

**Example 4: "Logging Rules" (structured logging, fix_suggestion)**
- Q1: Constant? Yes — every file needs logging, conventions are always the same.
- Q2: Every session? Yes — almost every task touches logging.
- **Result**: Auto-load in `sections/` (high frequency, small size)

**Example 5: "Adding Features Process" (step-by-step feature workflow)**
- Q1: Constant? Yes — same workflow every time you add a feature.
- Q2: Every session? Debatable — common but not universal (bugs, docs, refactors don't need it).
- **Result**: Gray area. Could go either way based on your project. If small (~10 lines), auto-load. If detailed (~50+ lines), on-demand.

### Quick-Reference Table

| Content Type | Q1: Constant? | Q2: Every Session? | Result |
|-------------|--------------|-------------------|--------|
| Core Principles | Yes | Yes | Auto-load |
| Tech Stack | Yes | Yes | Auto-load |
| Architecture | Yes | Yes | Auto-load |
| Dev Commands | Yes | Yes | Auto-load |
| Tool Docstrings | Yes | No (rare) | On-demand |
| API Guide | Yes | No (specific tasks) | On-demand |
| Feature Plan | No (one task) | — | Layer 2 |
| Bug Report | No (one task) | — | Layer 2 |

### Real-World Application

In this template, the MCP Servers & Cloud Skills content was split using this framework:
- **On-demand guide** (`reference/mcp-skills-overview.md`): 104 lines — core concepts needed whenever using MCP
- **On-demand guide** (`reference/mcp-skills-archon.md`): 190 lines — detailed setup only needed when configuring MCP

The split was guided directly by the Two-Question Framework: MCP concepts are needed when working with MCP (not every session), but setup details are only needed during initial configuration.

---

## 6. Loading Strategies

### Strategy 1: Always-Loaded Context (Auto-Load)

**Purpose**: Core principles and architecture that apply to ALL development tasks.

**Location**: `CLAUDE.md` (or modular `sections/`)

**Content types**:
- Core development principles (naming, logging, types)
- Tech stack decisions with version numbers
- Overall architecture patterns
- Code style standards
- Development commands (install, run, test, lint)

**Characteristics**:
- Used across all file types
- Applies to all coding tasks
- Would break conventions if AI didn't know

### Strategy 2: On-Demand Context (Reference Guides)

**Purpose**: Detailed patterns for specific task types.

**Location**: `reference/` folder

**Content types**:
- Step-by-step implementation guides
- Detailed code examples for specific task types
- Task-specific checklists and patterns
- Common patterns and anti-patterns

**Characteristics**:
- Only relevant when doing specific type of work
- Stable pattern, but not always applicable
- Task-type specific (e.g., only when creating API endpoints)

### Two Methods to Load On-Demand Guides

**Method 1: Reference in CLAUDE.md** — Mention the guide and when to read it.
```markdown
## Task-Specific Reference Guides

### Building API Endpoints
**When to use:** Creating new REST API endpoints
Read: `reference/API_guide.md`
```
- Flexible — AI decides when to read
- Less reliable — AI must remember to load the guide

**Method 2: Include in Commands (Recommended)** — Reference the guide in slash command prompts.
```markdown
# .claude/commands/build-api-endpoint.md
Read @reference/API_guide.md before proceeding.
Now create a new API endpoint for {feature}...
```
- **Guarantees** guide is loaded for the task
- More explicit and reliable
- Better for team consistency
- Requires command infrastructure (see the Command Design Framework guide)

**Recommendation**: Use Method 2 when possible. Method 1 as flexible fallback.

### The Frequency vs. Size Tradeoff

| Frequency | Size | Strategy |
|-----------|------|----------|
| High | Small | Auto-load (e.g., dev commands: ~10 lines, used every session) |
| High | Large | Auto-load but condense (summarize, reference details) |
| Low | Small | Borderline — auto-load is fine, minimal cost |
| Low | Large | **On-demand** (e.g., tool docstrings: 400+ lines, used rarely) |

The biggest wins come from moving **low frequency + large size** sections to on-demand.

---

## 7. Recommended CLAUDE.md Sections

Here are the 10 recommended sections for a comprehensive CLAUDE.md:

| # | Section | Purpose | Typical Size |
|---|---------|---------|-------------|
| 1 | Core Principles | Non-negotiable rules for every line of code | 10-20 lines |
| 2 | Tech Stack | Languages, frameworks, tools with versions | 15-30 lines |
| 3 | Architecture | Directory layout, design patterns, file naming | 20-40 lines |
| 4 | Code Style | Naming conventions, function/class patterns | 15-30 lines |
| 5 | Logging | Structured format, AI-optimized, fix_suggestion | 15-25 lines |
| 6 | Testing | Structure mirrors source, markers, commands | 15-25 lines |
| 7 | API Contracts | Backend models match frontend types exactly | 10-20 lines |
| 8 | Common Patterns | 2-3 code examples used throughout codebase | 30-50 lines |
| 9 | Dev Commands | Install, run, test, lint commands | 10-15 lines |
| 10 | AI Instructions | 10 bullet points guiding AI behavior | 10-15 lines |

**Total auto-loaded**: ~150-270 lines (well within the recommended 100-500 line range).

### Key Highlights Per Section

**1. Core Principles** — Non-negotiable constraints the AI must follow:
```
- TYPE SAFETY IS NON-NEGOTIABLE (all functions have type annotations)
- KISS (simple, readable solutions over clever abstractions)
- YAGNI (don't build features until needed)
- VERBOSE NAMING (intention-revealing: product_id, not id)
```

**2. Tech Stack** — Include version numbers to prevent AI hallucinating alternatives:
```
- Python 3.12, UV package manager, FastAPI 0.118+
- React 19, TypeScript strict mode, Tailwind CSS 4.0
```

**3. Architecture** — Explicit directory structure prevents random organizational patterns:
```
src/
├── agent/    # Core orchestration
├── tools/    # Independent slices (vertical architecture)
└── shared/   # Cross-cutting (config, logging)
```

**4. Code Style** — Show, don't just tell. Include brief code examples:
```python
def filter_products(category: str, min_price: Decimal) -> list[Product]:
    """Filter products by category and minimum price."""
```

**5. Logging** — Philosophy: logs optimized for AI agent consumption. Include `fix_suggestion` in error logs:
```python
logger.error("validation_failed", error_type="invalid_price",
             fix_suggestion="Ensure min_price <= max_price")
```

**6. Testing** — Tests mirror source directory structure. Every file has a corresponding test file:
```
src/shared/logging.py  →  tests/shared/test_logging.py
```

**7. API Contracts** — Backend Pydantic models must match frontend TypeScript interfaces exactly.

**8. Common Patterns** — 2-3 real code examples from your project that AI can copy and adapt.

**9. Dev Commands** — Quick reference for frequently used commands:
```bash
uv sync && uv run pytest && uv run ruff check .
```

**10. AI Instructions** — 10 concise bullet points: read existing code first, match naming conventions, use structured logging, add docstrings, include type hints, write tests, run linters, include fix_suggestion, never sacrifice clarity, consult reference guides.

---

## 8. Building Layer 1 with AI

Two copy-paste prompts for building Layer 1 using AI assistance.

### Prompt 1: Create Global Rules (CLAUDE.md)

**Purpose**: Generate your project's global rules automatically.

**For existing projects**:
1. AI analyzes your codebase (package.json, pyproject.toml, config files)
2. Examines folder structure and 3-5 representative files
3. Extracts patterns, conventions, architectural decisions
4. Generates CLAUDE.md documenting what already exists

**For new projects**:
1. AI asks clarifying questions (project type, domain, tech preferences, scale)
2. Researches current best practices
3. Looks up recommended project structures
4. Creates global rules based on research

**Critical requirements**:
- **Length**: 100-500 lines MAXIMUM
- Be specific, not generic (use actual code examples)
- Focus on what matters (not obvious statements)
- Keep it actionable (clear enough to follow immediately)

**In this template**: The `/init-c` command implements this prompt. Run `/init-c` when setting up a new project.

### Prompt 2: Create Reference Guide (On-Demand)

**Purpose**: Generate task-specific reference guides for on-demand loading.

**Process**:
1. Specify the task type (e.g., "building API endpoints")
2. Provide a research link (documentation, blog post, best practices guide)
3. AI researches the link and analyzes your codebase
4. AI generates a focused, actionable reference guide

**Required output sections**:
1. Title and Purpose — when to use this guide
2. Overall Pattern/Structure — high-level overview
3. Step-by-Step Instructions — 3-6 clear steps with code examples
4. Quick Checklist — bulleted markdown checklist

**Critical requirements**:
- **Length**: 50-200 lines MAXIMUM
- Code-heavy, explanation-light
- No generic advice — specific to this task type and codebase
- Actionable — developer can follow step-by-step

**In this template**: Use the reference guide prompt structure from layer1-guide.md.

### When to Use Each Prompt

| Situation | Which Prompt | Output |
|-----------|-------------|--------|
| New project, no CLAUDE.md yet | Prompt 1 (Create Global Rules) | `CLAUDE.md` (100-500 lines) |
| Existing project, undocumented | Prompt 1 (Create Global Rules) | `CLAUDE.md` from codebase analysis |
| Need guide for specific task type | Prompt 2 (Create Reference Guide) | `reference/{task}_guide.md` (50-200 lines) |
| Starting from this template | `/init-c` command | Project-customized CLAUDE.md |

**Pro tip**: Run Prompt 1 first to establish global rules, then Prompt 2 for each common task type in your project. This builds out your full Layer 1 context — both auto-loaded rules and on-demand guides.

---

## 9. Practical Application: Optimization Exercise

The following exercise demonstrates the Two-Question Framework applied to a real project.

### The Challenge

Given a **601-line CLAUDE.md** from a real agent project, categorize each section using three labels:

- **Auto-Load** — Needed in every session
- **On-Demand** — Constants for specific task types
- **Redundant** — Duplicate, obvious, or better documented elsewhere

### Solution

**Auto-Load (~160 lines)**:
1. Project Overview — architecture context needed for all work
2. Core Principles — TYPE SAFETY, KISS, YAGNI apply everywhere
3. Architecture — vertical slice pattern must be followed in all features
4. Documentation Style — all code needs consistent documentation
5. Logging Rules — every file needs logging, conventions are universal
6. Dev Commands — run frequently (uvicorn, ruff, mypy, pytest)
7. Testing Structure — all code needs tests, mirroring structure is critical

**On-Demand (~430 lines)**:
1. **Tool Docstrings (400+ lines!)** — Only needed when creating agent tools. Moved to `reference/adding_tools_guide.md`. This ONE section was **66% of the entire file**.
2. Adding Features Process — Only needed when adding new features (not bugs, docs, refactors). Moved to `reference/adding_features_guide.md`.

**Redundant (~10 lines)**:
1. AI Agent Notes — duplicated information already in Logging Rules section

### Key Insights

**1. The 80/20 Rule**: One section (tool docstrings) caused 66% of the bloat. Most context waste comes from a small number of large sections.

**2. Frequency vs. Size Tradeoff**: High frequency + small size = auto-load. Low frequency + large size = on-demand. The biggest wins come from the low-frequency, large-size sections.

**3. Redundancy is Subtle**: The "AI Agent Notes" section seemed useful until comparison revealed it repeated the Logging section. Always check for duplication.

**4. Gray Areas Exist**: Some sections are genuinely debatable. Dev commands (used often, only 10 lines), documentation style (applies broadly, only 20 lines), adding features (common but not universal) — these don't have clear-cut answers. Use your judgment based on your project's specifics.

---

## 10. Key Insights & Best Practices

### Golden Nuggets

1. **"Global rules is your day one onboarding for your coding assistant."** — Everything it needs to know on the first day.

2. **"README for humans, AGENTS.md for AI agents."** — Most repositories will eventually have both side-by-side.

3. **"One section = 66% of the bloat."** — The 80/20 rule applies to context optimization. Find your biggest offenders first.

4. **"Prefer Method 2 (commands) for on-demand loading."** — Guarantees the guide is loaded. More reliable than hoping AI remembers.

5. **"100-500 lines for global rules, 50-200 lines for reference guides."** — Concrete targets prevent both over-engineering and under-specification.

6. **"Use AI to build your Layer 1 context."** — Don't write it manually. Use the prompts from this guide or the `/init-c` command.

### Best Practices

1. **Keep it updated** — Stale rules are worse than no rules
2. **Be specific** — Vague rules lead to inconsistent code
3. **Include examples** — Show, don't just tell (code snippets > descriptions)
4. **Review regularly** — Update as your project evolves
5. **Start small** — Expand as you discover what matters
6. **Use AI to build it** — Don't write from scratch manually
7. **Test the rules** — Does AI follow them? If not, refine the wording
8. **Optimize for scannability** — Headers, code blocks, bullet points
9. **Focus on non-obvious** — Don't state things AI already knows
10. **Customize for your project** — Generic rules are less effective than project-specific ones

### Anti-Pattern Warning

**Don't stuff one-off fixes into global rules.** When a system review or code review reveals an issue, ask whether the fix belongs in global rules (applies to all tasks) or in a specific plan/command (applies to one task type). Adding every lesson to CLAUDE.md recreates the bloat problem you're trying to solve.

### Relationship to Other Guides

This guide builds the foundation that later guides depend on:

- **Command Design Framework guide**: Commands are the recommended Method 2 for loading on-demand guides. You need the on-demand strategy from this guide before commands can deliver it.
- **Planning Methodology & Implementation Discipline guides**: Structured plans (Layer 2) assume Layer 1 is solid. Poor global rules lead to plans that over-specify obvious conventions.
- **Validation Discipline guide**: System review (`/system-review`) identifies where fixes belong in the system — global rules, commands, or plans. The framework in this guide decides which.
- **MCP Skills & Archon guide**: MCP servers introduce additional context cost. The Two-Question Framework helps balance MCP tokens with global rules tokens.

---

## FAQ: Common Questions

### "Should I use Version 1 or Version 2?"

**Short answer**: Version 1 for small projects with stable conventions. Version 2 for growing projects or teams.

**Long answer**: Version 1 (single file) is simpler to set up and navigate — everything in one place, easy to search. It works well when your CLAUDE.md is under ~200 lines and rarely changes.

Version 2 (modular @sections) adds initial complexity but pays off as your project grows. Individual sections can be updated independently, diffs are smaller and more reviewable, and different team members can own different sections. If you're starting small but expect growth, starting with Version 2 saves you from a later migration.

Most projects that use this template should use Version 2, since the template already provides the modular structure.

### "How many sections should my CLAUDE.md have?"

**Short answer**: 6-10 auto-loaded sections, plus on-demand reference guides as needed.

**Long answer**: The 10 recommended sections (Section 7 of this guide) are a comprehensive target, but not all projects need all 10. A backend-only project might skip "API Contracts" (section 7). A solo project might skip "AI Instructions" (section 10) if the other sections are clear enough.

Start with the sections that matter most for your project (Core Principles, Tech Stack, Architecture are almost always needed), then add others as you discover gaps. The Two-Question Framework helps you decide what stays auto-loaded vs what goes on-demand.

### "What if I'm not sure whether something should be auto-loaded or on-demand?"

**Short answer**: Apply the Two-Question Framework. If still unsure, consider the frequency vs. size tradeoff.

**Long answer**: The Two-Question Framework (Section 5) handles most cases clearly. For the genuinely gray areas — sections that are borderline — consider:

- **If it's small (10-20 lines)**: Auto-load it. The token cost is minimal, and having it always available prevents gaps.
- **If it's large (100+ lines)**: Put it on-demand. Large sections consume significant context even when irrelevant.
- **If it's used in >50% of sessions**: Auto-load it.
- **If it's used in <20% of sessions**: On-demand.

When truly uncertain, err toward auto-loading small sections and on-demand for large ones. You can always move things later — this is not a permanent decision.

### "Can I just use /init-c to generate everything?"

**Short answer**: `/init-c` creates the initial CLAUDE.md, but you should review and customize it.

**Long answer**: The `/init-c` command (built from the "Create Global Rules" prompt) generates a solid starting point by analyzing your codebase or asking clarifying questions. But AI-generated rules are a first draft, not a final product.

After running `/init-c`, review the output for: accuracy (does it match your actual conventions?), completeness (is anything important missing?), specificity (are examples from YOUR code, not generic?), and length (100-500 lines target). Customize as needed, then commit. Your CLAUDE.md will evolve over time as you discover what matters — see the System Evolution principle in `reference/command-design-framework.md`.

### "How do I know if my global rules are too long?"

**Short answer**: If auto-loaded content exceeds ~300-500 lines, audit with the Two-Question Framework.

**Long answer**: There's no hard limit, but practical guidelines exist:

- **Under 200 lines**: Probably fine. Minimal context cost.
- **200-500 lines**: Normal range for mature projects. Monitor but don't worry.
- **500+ lines**: Audit time. Apply the Two-Question Framework to every section. Likely some content should move to on-demand.
- **800+ lines**: Definitely bloated. You're probably auto-loading task-specific guides that belong in `reference/`.

The exercise walkthrough (Section 9) shows a real example of a 601-line file being reduced to 160 lines. The Two-Question Framework and frequency vs. size tradeoff guide the audit.

### "How often should I update my global rules?"

**Short answer**: Whenever conventions change or you discover a pattern the AI keeps getting wrong.

**Long answer**: Global rules should be a living document, not a one-time artifact. Update them when:

- **You add a new technology** (e.g., switch from npm to bun) — update Tech Stack
- **AI keeps making the same mistake** (e.g., wrong naming convention) — add/clarify the rule
- **You discover a better pattern** — update Common Patterns with the improved approach
- **System review reveals a process gap** — but only if it applies to ALL tasks (not one-off fixes)

Don't update for every small issue. The system evolution principle applies: fix the system when a problem is recurring, not when it happens once. And always ask whether the fix belongs in global rules (all tasks) vs a specific command or reference guide (specific task types).

---

## Next Steps

1. **Read this guide** (you're doing this now)
2. **Review your current CLAUDE.md** — Is it Version 1 or Version 2? Is anything bloated? Apply the Two-Question Framework to each section
3. **Apply the Two-Question Framework** — Categorize each section as auto-load, on-demand, or redundant
4. **Use `/init-c` if starting a new project** — Generates CLAUDE.md automatically by analyzing your codebase or asking clarifying questions
5. **Create reference guides for on-demand content** — Use the two-question framework to identify what belongs in reference/
6. **Continue to the Command Design Framework guide** — Learn slash commands, the recommended Method 2 for loading on-demand guides, and the INPUT → PROCESS → OUTPUT framework

---

## Related Resources

- **Layer 1 Guide**: See `reference/layer1-guide.md` for the on-demand guide to Layer 1 components, creation order, and the Two-Question Framework summary
- **PIV Loop**: See `sections/02_piv_loop.md` for the core Plan → Implement → Validate methodology and how Layer 1 fits into the bigger picture
- **Context Engineering**: See `sections/03_context_engineering.md` for the 4 Pillars (Memory, RAG, Prompt Engineering, Task Management)
- **Generate Global Rules**: Use the `/init-c` command to build Layer 1 with AI assistance
- **Structured Plan Template**: `templates/STRUCTURED-PLAN-TEMPLATE.md` — For Layer 2 task-specific plans (what does NOT go in CLAUDE.md)
- **Slash Commands**: See `reference/command-design-framework.md` for Method 2 on-demand loading via commands and the trust progression

---

**That's the Global Rules & Layer 1 Optimization guide!** You now understand:
- What global rules are and where to put them
- Version 1 (single file) vs Version 2 (modular @sections)
- The context bloat problem and the 80/20 insight
- The Two-Question Framework for deciding auto-load vs on-demand
- Two loading strategies and two loading methods
- 10 recommended CLAUDE.md sections with examples
- Building Layer 1 with AI (two prompts, `/init-c`)
- Practical exercise for auditing and optimizing global rules

**Ready for the next step?** Learn slash commands — reusable prompts that automate workflows and provide the recommended Method 2 for loading reference guides on-demand. See `reference/command-design-framework.md` for the deep dive.
