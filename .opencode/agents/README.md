# Custom Subagents

12 subagents for parallel research, code review, and specialist tasks.

## Research Agents

| Agent | Purpose |
|-------|---------|
| `research-codebase` | Parallel codebase exploration: finds files, extracts patterns, reports findings |
| `research-external` | Documentation search, best practices, version compatibility checks |

## Code Review Agents

These four run in parallel during `/code-review`, each checking a different dimension:

| Agent | What It Catches |
|-------|----------------|
| `code-review-type-safety` | Missing type hints, type checking errors, unsafe casts |
| `code-review-security` | SQL injection, XSS, exposed secrets, insecure data handling |
| `code-review-architecture` | Pattern violations, layer breaches, convention drift |
| `code-review-performance` | N+1 queries, inefficient algorithms, memory leaks, unnecessary computation |

## Utility Agents

| Agent | Purpose |
|-------|---------|
| `plan-validator` | Validates plan structure and completeness before execution |
| `test-generator` | Analyzes changed code and suggests test cases following project patterns |

## Specialist Agents

| Agent | Purpose |
|-------|---------|
| `specialist-devops` | CI/CD pipelines, Docker, IaC, monitoring, deployments |
| `specialist-data` | Database design, migrations, queries, data pipelines |
| `specialist-copywriter` | UI copy, microcopy, error messages, UX writing |
| `specialist-tech-writer` | API docs, READMEs, changelogs, architecture documentation |

## Usage

Agents are invoked via the Task tool by the main agent, or can be @mentioned directly:
```
@research-codebase find all authentication-related code
```

## Creating New Agents

Use `/agents` command to create new subagent definitions, or manually create markdown files in `.opencode/agents/`.