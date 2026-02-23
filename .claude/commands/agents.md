---
description: Create a new subagent definition file
argument-hint: [agent-purpose-description]
---

# Create Subagent

## Input

Agent purpose: $ARGUMENTS

If no purpose is provided, ask the user: "What should this agent do? Describe the task it will handle (e.g., 'review code for accessibility issues', 'research API documentation for a framework')."

## Step 1: Determine Agent Type

Based on the purpose description, classify the agent:

| Type | When to Use | Default Model | Default Tools |
|------|-------------|---------------|---------------|
| **Research** | Finding information, exploring codebases, reading docs | haiku | `["Read", "Glob", "Grep"]` |
| **Review** | Analyzing code quality, security, patterns, compliance | haiku | `["Read", "Glob", "Grep"]` |
| **Analysis** | Synthesizing findings, comparing options, deep reasoning | sonnet | `["Read", "Glob", "Grep", "Bash"]` |
| **Custom** | Doesn't fit above — ask user for clarification | sonnet | Ask user |

**Model guidance**:
- **Haiku** — read-only, pattern-matching, high-volume tasks (cost-optimized)
- **Sonnet** — analysis, synthesis, balanced reasoning (default)
- **Opus** — complex multi-step reasoning (premium, rarely needed for agents)

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
- Example: "You are an accessibility compliance specialist who evaluates UI code against WCAG 2.1 standards."

### b. Core Mission — WHY does this agent exist?
- One sentence, singular focus
- An agent that tries to do everything does nothing well
- Example: "Your singular purpose is to identify accessibility barriers in frontend code."

### c. Context Gathering — What does it NEED?
- List specific files the agent should read (not "read everything")
- Start with `CLAUDE.md` for project conventions
- Add domain-specific files (e.g., config files, schema files, test patterns)
- Specify: what the main agent provides vs what the agent must fetch itself

### d. Analysis Approach — What STEPS does it follow?
- Write numbered, specific instructions (5-8 steps)
- Order of operations matters
- Include evaluation criteria and classification rules
- Be explicit about depth of analysis

### e. Output Format — What do you WANT back?
- **This is the most critical section** — it controls what the main agent sees
- Must be structured and parsable
- Include metadata header (query, files reviewed, match counts)
- Include findings with severity, location (file:line), description, and suggested fix
- Include summary with totals and overall assessment
- **CRITICAL**: End with this instruction:

> "Present findings to the main agent. Do NOT start fixing issues or making changes without user approval."

This prevents the main agent from automatically acting on all findings.

## Step 4: Generate the Agent File

Read `.claude/agents/research-codebase.md` as a structural reference.

Create the agent file with this structure:

```markdown
---
name: {agent-name}
description: Use this agent when {triggering scenario with examples}. {What it does in one sentence}.
model: {haiku|sonnet|opus}
tools: {tool list}
---

# Role: {Agent Name}

{Role definition — identity, expertise, domain}

{Core mission — singular purpose statement}

You are a RESEARCHER/REVIEWER, not an implementer — you discover/evaluate and report, never modify.

## Context Gathering

Read these files to understand project conventions:
- `CLAUDE.md` — project rules and standards
- {additional context files specific to this agent's domain}

Then {what to do with the provided input}.

## Approach

1. {First step}
2. {Second step}
3. {Third step}
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

Save to: `.claude/agents/{agent-name}.md`

**Important**: If `.claude/agents/` doesn't exist, create it.

## Step 6: Verify

After creating the file, verify:
1. Frontmatter has all required fields (`name`, `description`) and relevant optional fields (`model`, `tools`)
2. Body contains all 5 components (Role, Mission, Context, Approach, Output)
3. Output format includes the "do NOT start fixing" instruction
4. Tools are restricted to minimum needed (reviewers don't need write access)

Report to the user:
- Agent file path: `.claude/agents/{agent-name}.md`
- Agent type and model
- How to use: "The agent will be auto-delegated based on its description, or you can reference it in commands with `@{agent-name}`"
- Reminder: "Restart your Claude Code session or start a new conversation to load the new agent"

## Important Rules

- **Minimal tools** — don't give write access to read-only agents
- **Specific context** — list exact files, not "read the whole project"
- **Structured output** — always include severity, file:line, and metadata
- **Guard against auto-fix** — always include the "don't fix without approval" instruction
- **One job per agent** — if the purpose is broad, suggest creating multiple specialized agents instead
