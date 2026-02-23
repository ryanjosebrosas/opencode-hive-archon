# Agent Design Template

> Use this guide when creating new subagents for `.claude/agents/`.
> Every agent should follow the Role → Mission → Context → Approach → Output framework.

---

## The Framework: Role → Mission → Context → Approach → Output

Every effective subagent answers five questions:

### 1. Role Definition: What IS this agent?

- Clear identity and specialized expertise
- What domain does it operate in?
- What makes it different from a general-purpose agent?

### 2. Core Mission: WHY does this agent exist?

- Singular purpose — one focused job
- An agent that tries to do everything does nothing well
- State the mission in one sentence

### 3. Context Gathering: What does it NEED?

- What files or info must it read?
- What does the main agent provide vs what must the agent fetch?
- How do you keep context focused without missing critical info?

### 4. Analysis Approach: What STEPS does it follow?

- Numbered, specific instructions
- Order of operations matters
- Include evaluation criteria and depth of analysis

### 5. Output Format: What do you WANT back?

- The most critical section — controls what the main agent sees
- Structured, parsable, includes metadata
- Explicit about what happens next
- Who consumes this output? (human, main agent, another command)

---

## Frontmatter Reference

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | `lowercase-with-hyphens` | Unique identifier |
| `description` | Yes | text | When to use — guides autonomous delegation |
| `model` | No | `haiku` / `sonnet` / `opus` | Default: inherits from parent |
| `tools` | No | list or `["*"]` | Default: inherits all tools |
| `color` | No | color name | Visual indicator in terminal |
| `maxTurns` | No | number | Limit agentic turns |
| `skills` | No | list | Skills to preload |
| `mcpServers` | No | list | MCP servers available |

See `reference/subagents-deep-dive.md` for complete field documentation with all options.

---

## Two Invocation Modes

### Autonomous Delegation

The main agent auto-delegates based on the `description` field. Write descriptions with "Use this agent when..." and include examples of triggering scenarios.

Best for: recurring tasks where you want hands-free delegation.

### Manual Invocation

User or command explicitly requests the agent. Write descriptions more generally.

Best for: specialized tasks where you want control over when the agent runs.

Tip: Start manual, move to autonomous once you trust the agent's output consistently.

---

## Output Format Patterns

### Report Pattern
Agent saves findings to a file. Consumer: another command or human review.
- Include: file path for report, structured findings, severity levels, file/line references
- Example: code reviewer saves report to `.agents/code-reviews/review.md`

### Summary Pattern
Agent returns concise summary to main agent. Consumer: main agent decision-making.
- Include: key findings, action items, metrics
- Example: research agent returns bullet-point summary of 5 API options

### Action Pattern
Agent performs side effects and reports. Consumer: system + human.
- Include: what was done, what changed, what needs manual verification
- Example: migration agent applies changes and lists affected files

Critical: always include metadata (files analyzed, line numbers) and instructions for what main agent should do next.

---

## Controlling Main Agent Behavior

After the subagent completes, the main agent decides what to do. Control this via:

**In agent output format** (agent-side): Add at end of system prompt:
> "When done, instruct the main agent to NOT start fixing any issues without the user's approval."

**In calling command** (command-side): Add in the slash command:
> "After the agent completes, only address critical issues, then report to user."

Without this, the main agent may automatically act on all findings when you just wanted a report. Use both for safety.

---

## Starter Template

Copy and adapt this for new agents:

```markdown
---
name: {agent-name}
description: Use this agent when {triggering scenario}. {What it does and why}.
model: sonnet
tools: ["Read", "Glob", "Grep"]
---

# Role: {Agent Name}

You are a {role description} specializing in {domain}. Your singular purpose is {mission statement}.

## Context Gathering

Read the following to understand the task:
- {file or info the agent needs}
- {file or info the agent needs}

## Approach

1. {First step — what to analyze}
2. {Second step — how to evaluate}
3. {Third step — how to classify findings}

## Output Format

Return analysis in this structure:

### Mission Understanding
[Explain your understanding of your mission]

### Context Analyzed
- Files reviewed: [list with line counts]

### Findings
For each finding:
- **Severity**: Critical / Major / Minor
- **Category**: {category}
- **Location**: {file:line}
- **Description**: {what's wrong}
- **Suggested Fix**: {how to fix}

### Summary
- Total findings: X (Critical: Y, Major: Z, Minor: W)
- Overall assessment: [brief judgment]

### Recommendations
1. [Specific actionable recommendation]
2. [Specific actionable recommendation]

---
When done, instruct the main agent to {what should happen next — e.g., "present findings to user without making changes"}.
```

---

## When to Create an Agent

Create an agent when:
- Context-heavy task you've done 3+ times manually
- You need parallelization (multiple aspects researched simultaneously)
- Specialized review against documented standards
- You want controlled output format that doesn't change

Don't create agents for:
- One-off tasks (just prompt directly)
- Simple operations that don't need isolation
- Tasks needing full main conversation context

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Vague role definition | Be specific about singular purpose |
| No output format | Define explicit structure for findings |
| No main agent instructions | Tell it what to do (or not do) with results |
| Too much context | Specify exact files needed, not "read everything" |
| Tool overreach | Reviewers don't need write access — restrict tools |
| Missing metadata | Include files reviewed, line numbers, severity |
