---
description: Create a new subagent definition file
agent: build
---

# Create Subagent

## Input

Agent purpose: $ARGUMENTS

If no purpose is provided, ask the user: "What should this agent do? Describe the task it will handle (e.g., 'review code for accessibility issues', 'research API documentation for a framework')."

## Step 1: Determine Agent Type

Based on the purpose description, classify the agent:

| Type | When to Use | Default Model | Default Tools |
|------|-------------|---------------|---------------|
| **Research** | Finding information, exploring codebases, reading docs | haiku | read, glob, grep |
| **Review** | Analyzing code quality, security, patterns, compliance | haiku | read, glob, grep |
| **Analysis** | Synthesizing findings, comparing options, deep reasoning | sonnet | read, glob, grep, bash |
| **Custom** | Doesn't fit above — ask user for clarification | sonnet | Ask user |

**Model guidance**:
- **Haiku** — read-only, pattern-matching, high-volume tasks (cost-optimized)
- **Sonnet** — analysis, synthesis, balanced reasoning (default)

## Step 2: Choose a Name

Generate a kebab-case name from the purpose:
- `code-review-accessibility` for "review code for accessibility"
- `research-api-docs` for "research API documentation"
- Keep it short (2-4 words), descriptive, unique

## Step 3: Design the 5 Components

Walk through each component of the agent design framework (from `templates/AGENT-TEMPLATE.md`):

### a. Role Definition — What IS this agent?
- Write a clear identity statement with specialized expertise
- Be specific about domain and what makes it different from a general agent

### b. Core Mission — WHY does this agent exist?
- One sentence, singular focus
- An agent that tries to do everything does nothing well

### c. Context Gathering — What does it NEED?
- List specific files the agent should read (not "read everything")
- Start with `AGENTS.md` for project conventions
- Add domain-specific files (e.g., config files, schema files, test patterns)

### d. Analysis Approach — What STEPS does it follow?
- Write numbered, specific instructions (5-8 steps)
- Order of operations matters
- Include evaluation criteria and classification rules

### e. Output Format — What do you WANT back?
- **This is the most critical section** — it controls what the main agent sees
- Must be structured and parsable
- Include metadata header (query, files reviewed, match counts)
- Include findings with severity, location (file:line), description, and suggested fix

## Step 4: Generate the Agent File

Create the agent file with this structure:

```markdown
---
description: Use this agent when {triggering scenario with examples}. {What it does in one sentence}.
mode: subagent
model: anthropic/claude-{haiku|sonnet}-4-20250514
tools:
  read: true|false
  glob: true|false
  grep: true|false
  bash: true|false
  write: false
  edit: false
---

# Role: {Agent Name}

{Role definition — identity, expertise, domain}

{Core mission — singular purpose statement}

You are a RESEARCHER/REVIEWER, not an implementer — you discover/evaluate and report, never modify.

## Context Gathering

Read these files to understand project conventions:
- `AGENTS.md` — project rules and standards
- {additional context files specific to this agent's domain}

## Approach

1. {First step}
2. {Second step}
...

## Output Format

### Metadata
- **Query/Task**: [what was requested]
- **Files reviewed**: [count]
- **Key findings**: [count by severity]

### Findings

For each finding:
- **Severity**: Critical / Major / Minor
- **Location**: `file:line`
- **Issue**: [description]
- **Suggested Fix**: [how to resolve]

### Summary
- Total findings: X (Critical: Y, Major: Z, Minor: W)
- Overall assessment: [brief judgment]

---

Present findings to the main agent. Do NOT start fixing issues or making changes without user approval.
```

## Step 5: Save the File

Save to: `.opencode/agents/{agent-name}.md`

**Important**: If `.opencode/agents/` doesn't exist, create it.

## Step 6: Verify

After creating the file, verify:
1. Frontmatter has all required fields (`description`, `mode`) and relevant optional fields (`model`, `tools`)
2. Body contains all 5 components (Role, Mission, Context, Approach, Output)
3. Output format includes the "do NOT start fixing" instruction
4. Tools are restricted to minimum needed (reviewers don't need write access)

Report to the user:
- Agent file path: `.opencode/agents/{agent-name}.md`
- Agent type and model
- How to use: "The agent will be auto-delegated based on its description, or you can reference it in commands with `@{agent-name}`"

## Important Rules

- **Minimal tools** — don't give write access to read-only agents
- **Specific context** — list exact files, not "read the whole project"
- **Structured output** — always include severity, file:line, and metadata
- **Guard against auto-fix** — always include the "don't fix without approval" instruction
- **One job per agent** — if the purpose is broad, suggest creating multiple specialized agents instead