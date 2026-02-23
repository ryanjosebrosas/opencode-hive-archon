# Agents

> **Note**: These are agent definitions. Agents in `.claude/agents/` are automatically available in your Claude Code sessions.

This directory contains **12 agents** across 4 categories: research, code review, utility, and specialist.

---

## Research Agents

These agents handle **parallel research** — exploring your codebase and external documentation simultaneously. They're designed to be invoked from commands like `/planning` or used directly for ad-hoc research.

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **research-codebase** | Sonnet | Read, Glob, Grep | File discovery, pattern extraction, codebase exploration |
| **research-external** | Sonnet | Read, Glob, Grep, WebSearch, WebFetch | Documentation search, best practices, version compatibility |

### When to Use

- **research-codebase** (Sonnet): Parallel codebase exploration during planning, finding files and patterns, extracting code examples with line numbers. Read-only tools keep it safe.
- **research-external** (Sonnet): Documentation search, best practices research, version compatibility checks, migration guides.

### Usage Examples

Invoke from a prompt or command:
```
Use the research-codebase agent to find all authentication-related files and patterns.
```
```
Use the research-external agent to find the React 19 migration guide and breaking changes.
```

### Model Selection

Both research agents use **Sonnet** for consistent quality across codebase and external research.

### Parallel Research in /planning

When custom research agents are activated, the `/planning` command can launch **5-10 parallel agents** instead of 2:

```text
Main Agent (Sonnet)
  |-> research-codebase #1 (Sonnet) --- "auth patterns middleware"
  |-> research-codebase #2 (Sonnet) --- "session model schema"
  |-> research-codebase #3 (Sonnet) --- "auth test fixtures"
  |-> research-external #1 (Sonnet) -- "JWT token refresh"
  |-> research-external #2 (Sonnet) -- "bcrypt password hashing"
  |-> research-external #3 (Sonnet) -- "OAuth2 PKCE flow"
       | (results return in parallel)
Main Agent combines findings into unified research report
```

**Speed improvement**: 3-5x faster than 2-agent standard mode for complex features.

**Scale guideline**:
- Simple features (Low complexity): 2-4 agents total
- Medium features: 4-6 agents total
- Complex features (High complexity): 6-10 agents total (max 10 concurrent)

### Basic Parallel Research

Launch both agents simultaneously for comprehensive research (codebase patterns + external docs):
```
Launch two Task agents in parallel:
1. research-codebase agent: "Find all payment-related files, models, and API patterns"
2. research-external agent: "Find Stripe API v2024 documentation and migration guide"
```

### Activation

Research agents are pre-installed in `.claude/agents/` and automatically available. To customize for your project, edit the agent files directly:
- Update search patterns and sources for your tech stack
- Adjust output format or focus areas

The `/planning` command automatically detects them and switches to Parallel Research Mode (5-10 agents) instead of Standard Research Mode (2 built-in agents).

---

## Code Review Agents

These agents demonstrate **parallel code review** using the Pattern A approach from `reference/subagents-deep-dive.md`.

## What These Agents Do

Instead of one agent reviewing everything sequentially, these four agents work **in parallel** — each focusing on a specific aspect:

| Agent | Focus | What It Checks |
|-------|-------|----------------|
| **code-review-type-safety** | Type annotations & type checking | Missing types, incorrect types, type errors |
| **code-review-security** | Security vulnerabilities | SQL injection, XSS, exposed secrets, auth issues |
| **code-review-architecture** | Design patterns & conventions | Layer violations, DRY, YAGNI, naming, structure |
| **code-review-performance** | Performance & scalability | N+1 queries, inefficient algorithms, memory leaks |

> **Tool access**: Type Safety and Security agents include Bash for running external tools
> (type checkers, secret scanners). Architecture and Performance agents are read-only analysis.

## Model Selection

All code review agents use **Sonnet** for higher quality analysis across all review dimensions.

## How to Use

### Customization

Code review agents are pre-installed in `.claude/agents/` and automatically available. To customize for your project, edit the agent files directly:

1. Update `Context Gathering` section to reference your project files
2. Add project-specific patterns to check
3. Adjust severity thresholds based on your standards
4. Modify output format if needed

Use with `/code-review` command (which will invoke them automatically).

The agents work out-of-the-box and adapt to your project by reading `CLAUDE.md`, but will be more targeted after customization.

## Parallel Execution

When you run `/code-review`, all four agents launch simultaneously:

```text
Main Agent
  ├─> Type Safety Agent (reviews all files for type issues)
  ├─> Security Agent (reviews all files for vulnerabilities)
  ├─> Architecture Agent (reviews all files for pattern compliance)
  └─> Performance Agent (reviews all files for efficiency)
       ↓ (results return in parallel)
Main Agent combines findings into unified report
```

**Speed improvement**: 40-50% faster than sequential review (same as `/planning` parallel research).

## When NOT to Use All Four

You don't always need all four agents. Pick based on your feature:

| Feature Type | Agents to Use |
|--------------|---------------|
| **New API endpoint** | Security + Architecture + Performance |
| **Frontend component** | Type Safety + Architecture |
| **Database migration** | Security + Architecture + Performance |
| **Bug fix** | Type Safety + Security (usually sufficient) |
| **Documentation** | Skip parallel review, use basic `/code-review` |

To use only specific agents, modify the `/code-review` command to launch fewer agents.

## Output Format

Each agent returns structured findings:
- **Severity**: Critical / Major / Minor
- **Location**: file:line
- **Issue**: What's wrong
- **Evidence**: Code snippet
- **Fix**: How to resolve

The main agent combines all findings into a single report saved to `requests/code-reviews/{feature}-review.md`.

## Customization Ideas

### For Python Projects
- Add `mypy` or `pyright` integration to type-safety agent
- Add `bandit` security scanner integration to security agent
- Check for `pytest` coverage in architecture agent

### For TypeScript Projects
- Add `tsc --noEmit` to type-safety agent
- Check for `React` hook rules in architecture agent
- Add bundle size analysis to performance agent

### For API Projects
- Add OpenAPI/Swagger spec validation to architecture agent
- Add rate-limiting checks to security agent
- Add query plan analysis to performance agent

## Trust Progression

**Before using parallel agents**:
1. Use the basic `/code-review` command manually 3+ times
2. Verify it catches the issues you care about
3. Understand what good output looks like

**Before customizing agents**:
1. Run the example agents as-is on a few features
2. Note what they miss vs what's noise
3. Adjust based on your project's actual needs

**Before full automation**:
1. Use `/code-review` → `/code-review-fix` manually 5+ times
2. Verify fixes are correct and safe
3. Only then integrate into automated workflows (GitHub Actions, etc.)

Don't skip stages. Parallel agents are powerful but can generate a lot of noise if not tuned to your project.

## Integration with Commands

The updated `/code-review` command automatically uses these agents when they exist in `.claude/agents/`.

You can also invoke them from other commands:
```markdown
Use the @code-review-security agent to check for vulnerabilities in the authentication module.
```

See `reference/command-design-framework.md` for command + agent integration patterns.

## Reference

- **Pattern source**: `reference/subagents-deep-dive.md` (Pattern A: Parallel Review)
- **Agent design guide**: `templates/AGENT-TEMPLATE.md`
- **Full subagent docs**: `reference/subagents-deep-dive.md`

---

## Utility Agents

These agents provide **workflow optimization** — validating plans before execution
and suggesting test cases for changed code.

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **plan-validator** | Sonnet | Read, Glob, Grep | Validates plan structure before /execute |
| **test-generator** | Sonnet | Read, Glob, Grep | Suggests test cases from changed code |

### When to Use

- **plan-validator**: Before running `/execute` on a new plan. Catches missing sections,
  incomplete tasks, broken file references. Integrated as optional Step 1.25 in `/execute`.
- **test-generator**: After implementation, before or during `/code-review`. Identifies
  untested code paths and suggests structured test cases following project patterns.

### Usage Examples
```
Use the plan-validator agent to validate requests/my-feature-plan.md
```
```
Use the test-generator agent to suggest tests for the files changed in the last commit
```

### Model Selection

Both utility agents use **Sonnet** for consistent quality.

### Activation

Utility agents are pre-installed in `.claude/agents/` and automatically available. To customize for your project, edit the agent files directly:
- Adjust validation rules or test patterns for your tech stack
- Modify output format or severity thresholds

---

## Specialist Agents

These agents combine **deep domain expertise** with **methodology awareness**. Unlike single-purpose agents (research-only or review-only), specialist agents operate in 3 modes: research, plan+implement, and review. They understand the PIV Loop, context engineering pillars, and validation pyramid, applying them through the lens of their domain.

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **specialist-devops** | Sonnet | All | CI/CD, Docker, IaC, monitoring, deployments |
| **specialist-data** | Sonnet | All | DB design, migrations, queries, data pipelines |
| **specialist-copywriter** | Sonnet | All | UI copy, microcopy, error messages, UX writing |
| **specialist-tech-writer** | Sonnet | All | API docs, READMEs, changelogs, architecture docs |

### Operating Modes

Each specialist agent detects its mode from the invocation context:

- **Research mode**: Read-only analysis, search docs/codebase, report findings without changes
- **Plan mode**: Design implementation approach following PIV Loop, generate structured tasks, implement if approved
- **Review mode**: Analyze code/docs for domain issues AND methodology compliance, report findings with severity

Default to research mode when intent is ambiguous (safest).

### When to Use

| Feature Type | Recommended Specialist |
|--------------|----------------------|
| CI/CD pipeline, Docker, deployment | specialist-devops |
| Database schema, migrations, queries | specialist-data |
| UI text, error messages, onboarding copy | specialist-copywriter |
| API docs, README, changelog, developer guides | specialist-tech-writer |

### Model Selection

All specialist agents use **Sonnet**. Multi-modal operation requires synthesis and judgment — these agents must understand methodology context AND apply domain expertise simultaneously.

### Usage Examples

```
Use the specialist-devops agent to review this PR for CI/CD and deployment concerns.
Use the specialist-data agent to plan a database migration for adding user roles.
Use the specialist-copywriter agent to research error message patterns in the codebase.
Use the specialist-tech-writer agent to review the README for completeness.
```

---

## Model Summary

All 12 agents use **Sonnet** for consistent, high-quality output across all categories.

> **Typical usage**: Running all 12 agents simultaneously is rare. Most sessions use
> 2-4 agents per command.
