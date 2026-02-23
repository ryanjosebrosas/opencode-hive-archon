# Command Design Template

> Use this guide when creating new slash commands for `.claude/commands/`.
> Every command should follow the INPUT → PROCESS → OUTPUT framework.

---

## The Framework: INPUT → PROCESS → OUTPUT

Every effective command answers three questions from the agent's perspective:

### 1. INPUT: What does the agent NEED to see?
- Context for the task (tech stack, patterns, standards)
- Domain knowledge required
- References to documentation or files (`@` file references)
- Any constraints or requirements

### 2. PROCESS: What should the agent DO?
- Specific steps to follow
- Analysis criteria or evaluation points
- Tools or methods to use
- Order of operations

### 3. OUTPUT: What do you WANT back?
- Format specification (structured vs conversational)
- Required sections or fields
- Level of detail needed
- Who will consume this output (you or another agent)

---

## Three Output Patterns

### Pattern 1: Context Loading (e.g., `/prime`)
- **Produces**: Agent understanding loaded into context
- **Consumer**: YOU (human) — to verify understanding
- **Output format**: Conversational, easy to scan, bullet points
- **When to use**: Session start, switching context, before major work

### Pattern 2: Document Creation (e.g., `/planning`)
- **Produces**: Document/artifact saved to a file
- **Consumer**: ANOTHER AGENT — must be explicit and unambiguous
- **Output format**: Structured, specific file paths, exact commands
- **When to use**: Creating reusable intelligence, agent-to-agent handoff

### Pattern 3: Action Automation (e.g., `/commit`)
- **Produces**: Side effect (git commit, deployment, etc.)
- **Consumer**: SYSTEM (git, APIs) and YOU (confirmation)
- **Output format**: Action confirmation with details
- **When to use**: Repetitive workflows you want automated

---

## Command Features Reference

### Arguments
```markdown
$ARGUMENTS          # All arguments as single string
$1, $2, $3          # Individual positional arguments
```
Usage: `/my-command arg1 arg2` → `$1`="arg1", `$2`="arg2"

### Bash Execution
```markdown
!`git status`       # Runs command, loads output into context
!`git log -5`       # Output available before prompt runs
```
Requires frontmatter: `allowed-tools: Bash(git status:*)`

### File References
```markdown
@path/to/file.md    # Loads file content into context
@reference/guide.md # Great for loading on-demand guides
```

### Frontmatter
```yaml
---
description: Brief description (shown in /help)
argument-hint: [expected-args]
allowed-tools: Bash(git:*), Read, Write, Edit
model: claude-sonnet-4
---
```

---

## Starter Template

Copy and adapt this for new commands:

```markdown
---
description: [Brief description for /help]
argument-hint: [expected arguments]
---

# [Command Name]: [Action Description]

## Context (INPUT)

[What context does the agent need? Tech stack, patterns, constraints.]
[Load files with @path/to/file if needed]
[Run bash commands with !`command` if needed]

## Process (PROCESS)

### 1. [First Step]
- [Specific instruction]
- [Specific instruction]

### 2. [Second Step]
- [Specific instruction]
- [Specific instruction]

## Output (OUTPUT)

[Specify the format and structure of the response]

### [Section 1]
- [What to include]

### [Section 2]
- [What to include]
```

---

## Consumer Optimization Guide

| Consumer | Optimize For | Example |
|----------|-------------|---------|
| **Human (you)** | Scannable, concise, bullet points | `/prime` summary |
| **Another agent** | Explicit, specific file paths, exact commands | `/planning` output |
| **System (git, API)** | Format-compliant, exact syntax | `/commit` message |

---

## When to Create a Command

Create a slash command when you notice:
- You've typed the same prompt 3+ times
- A workflow has repeatable steps
- You want team standardization
- Context needs loading for specific task types

### Trust Progression
```
Manual Prompts → Trust & Verify → Reusable Commands → Trust & Verify → Chained Commands
```

Don't skip stages. Only automate what you trust completely.
