# Subagents: Parallel AI Execution & Context Isolation

This guide explains **how to extend the PIV Loop with specialized worker agents** — covering subagent fundamentals, the context handoff mental model, built-in vs custom agents, the 5-component design framework, output format as the primary control lever, parallel execution patterns, and integration with existing commands.

---

## 1. What This Guide Teaches

### The Journey to Parallel Execution

The System Foundations guide established the **why** — the system gap and mental models. The PIV Loop Practice guide taught the **how** — the PIV Loop in practice. The Global Rules Optimization guide taught **how to build** — modular CLAUDE.md and strategic context loading. The Command Design Framework guide taught **how to automate** — slash commands and the INPUT→PROCESS→OUTPUT framework. The Planning Methodology guide taught **how to plan** — the 6-phase planning methodology. The Implementation Discipline guide taught **execution discipline** — implementing from plans reliably and evolving the system through meta-reasoning. The Validation Discipline guide taught **validation discipline** — the 5-level pyramid, code review, system review, and divergence analysis. The GitHub Orchestration guide taught **remote orchestration** — using GitHub Actions as the orchestration layer for remote, trigger-based workflows. The Remote Agentic System guide taught **remote system architecture** — building a custom application for remote PIV Loops with real-time conversation and persistent sessions. The MCP, Skills & Archon guide taught **external access** — MCP servers for tool access and Cloud Skills for progressive knowledge loading.

This guide teaches **parallel execution and context isolation** — how to extend the PIV Loop with specialized worker agents that run independently, in parallel, each with their own focused instructions and isolated context window.

Like MCP servers, subagents are not critical to the core PIV Loop. But they represent a significant capability upgrade when you need parallel research, isolated analysis, or specialized review workflows.

### What You'll Learn

- **Subagent fundamentals** — what they are, how they differ from commands and skills
- **The context handoff mental model** — two handoff points where information gets lost, and how to mitigate
- **Built-in agents** — Explore, Plan, General-purpose, and when each is best
- **The 5-component design framework** — Role → Mission → Context Gathering → Approach → Output Format
- **Output format as the primary control lever** — six patterns for reliable subagent results
- **Three parallel execution patterns** — same target, different targets, planning research
- **Decision framework** — when subagents are worth the overhead vs overkill
- **Creating custom agents** — three methods, frontmatter reference, file locations
- **Integration with commands** — two patterns connecting agents to your existing workflow

### The Core Insight

> "Output format is the MOST critical part — it controls what the main agent sees and how it responds."

Every reliability issue with subagents traces back to the output format. The analysis logic, the role definition, the context gathering — all important. But the output format is what determines whether the main agent acts correctly on the subagent's findings. Get this right and everything else follows.

### The Key Distinction

Commands define **WHAT** to do (workflows and automation). Skills provide **KNOWLEDGE** (procedures and conventions). Subagents define **WHO** does the work (specialized, isolated workers). All three complement each other — commands orchestrate, skills inform, agents execute.

---

## 2. Subagent Fundamentals

### What Subagents Are

Subagents are isolated AI instances with custom system prompts that run in their own context window. They're invoked via the Task tool, work independently from the main conversation, and return results when complete. The main agent delegates work to them and receives structured results back.

Five defining characteristics:

1. **Isolated context windows** — they can't see the main conversation history
2. **Custom system prompts** — your markdown file IS their entire instruction set
3. **Independent execution** — they work in parallel, don't block each other
4. **Delegated workers** — main agent sends work, subagent returns results
5. **Up to 10 concurrent** — the real power is parallelization, not just isolation

> Subagents are really just another markdown file — another prompt in your prompt toolbox.

### How They Compare

| Aspect | Main Agent | Subagents | Slash Commands | Skills |
|--------|------------|-----------|----------------|--------|
| **Context** | Full conversation history | Isolated, own window | Main conversation | Main conversation |
| **Execution** | Interactive, sequential | Isolated, can be parallel | Sequential in main thread | Sequential in main thread |
| **Purpose** | Primary chat interface | Specialized parallel work | Reusable workflows | Knowledge & procedures |
| **Configuration** | System-wide settings | Custom system prompt + frontmatter | Markdown prompts | Directory + SKILL.md |
| **Nesting** | N/A | No nesting allowed | Can invoke subagents | N/A |
| **Best for** | General work | Research, review, analysis | Automation, workflows | Conventions, procedures |

---

## 3. The Context Handoff Mental Model

### The Two Handoff Points

This is the most important mental model for working with subagents:

```
You → Main Agent → Subagent → Main Agent → You
         ↓              ↓
    Handoff #1     Handoff #2
   (Can lose       (Can lose
    context)        context)
```

**Handoff #1** (Main → Sub): The main agent summarizes YOUR request for the subagent. Your nuanced instructions may be oversimplified. Specific file paths, exact requirements, or context about WHY something matters can get lost in translation.

**Handoff #2** (Sub → Main): The subagent summarizes ITS findings for the main agent. Detailed analysis gets compressed. Nuance disappears. Critical details may be omitted entirely.

### What Gets Lost

At each handoff, information can be:
- **Oversimplified** — complex requirements reduced to bullet points
- **Misinterpreted** — agent infers wrong intent from ambiguous instructions
- **Missing critical details** — specific file paths, line numbers, severity context
- **Lost priority context** — what matters most vs what's nice-to-have

### The Solution

**Obsessively control output formats.** You can't directly control Handoff #1 (how the main agent summarizes your request). But you CAN control Handoff #2 by specifying exactly what the subagent should return and in what structure.

When a subagent produces bad results, the instinct is to fix the analysis logic. But 80% of the time, the real fix is improving the output format specification. See Section 6 for the complete output format deep dive.

---

## 4. Built-in Agents

Claude Code ships with several built-in agents you can use immediately:

| Agent | Model | Tools | Best For |
|-------|-------|-------|----------|
| **Explore** | Haiku (fast) | Read-only (Glob, Grep, Read) | File discovery, codebase search, quick reconnaissance |
| **Plan** | Inherits from parent | All tools | Codebase analysis, thorough exploration, planning research |
| **General-purpose** | Inherits from parent | All tools | Complex multi-step research, tasks needing write access |
| **Status Line** | Default | Limited | Internal/system use, not typically invoked manually |

### Already in Use

The `/planning` command (Phases 2 & 3) launches Explore and general-purpose agents in parallel for research. You've been using subagents since the planning methodology without explicitly realizing it.

### Model Choice Logic

- **Explore** uses Haiku because speed matters more than depth for file discovery and pattern searching
- **Plan** and **General-purpose** inherit the parent model (usually Sonnet) because deeper analysis justifies the cost
- When Explore isn't enough — if you need write access, multi-step reasoning, or tools beyond read-only — use general-purpose instead

### The `/planning` Command: Subagents in Action

The `/planning` command demonstrates Pattern C (Parallel Research) with built-in agents:

- **Phase 2** launches an **Explore** agent for codebase intelligence — finding similar implementations, mapping integration points, and extracting project patterns
- **Phase 3** launches a **general-purpose** agent for external research — library documentation, best practices, version compatibility, gotchas
- Both run **simultaneously**, cutting research time by 40-50%
- The main conversation **synthesizes** both agents' findings into the structured plan

This is the template for all custom parallel agent workflows: launch focused agents, get structured results, synthesize in the main conversation.

---

## 5. The Agent Design Framework

Every effective subagent needs five components. This framework ensures your agents are focused, reliable, and produce actionable results.

### 1. Role Definition

**Purpose**: Clear identity and specialized purpose.

**Key questions**: What is this agent's singular focus? Why does it exist? How is it different from a general-purpose agent?

**Example**: *"You are an expert code reviewer specializing in Python FastAPI applications with vertical slice architecture. Your role is to thoroughly review newly written code against the project's established standards."*

### 2. Core Mission

**Purpose**: The "why" behind the agent's existence.

**Key questions**: What problem does this agent solve? What makes it valuable? When should someone use this vs doing it manually?

**Example**: *"Your mission is to catch architectural violations, type safety issues, and pattern inconsistencies before they reach production. You prevent technical debt by enforcing standards at code review time."*

### 3. Context Gathering

**Purpose**: Define what the agent receives and what it must fetch.

**Key questions**: What does it receive from the main agent? What additional context must it read? What are the input/output file paths?

**Example**: *"Receives from main agent: target file paths or git diff. Must fetch: project logging standards, type safety rules, architecture documentation. Output saved to: `.agents/code-reviews/agent-reviews/{feature}-review.md`"*

### 4. Analysis Approach

**Purpose**: Specific steps to accomplish the mission.

**Key questions**: What steps should the agent follow? In what order? What heuristics or rules guide the analysis? What makes a finding "critical" vs "minor"?

**Example**: *"1. Initial assessment (obvious issues). 2. Detailed analysis (each component vs standards). 3. Logging verification (event taxonomy). 4. Type checking (strict mode compliance). 5. Testing coverage (test existence and patterns)."*

### 5. Output Format

**Purpose**: Structured, parsable results for downstream use. **This is THE MOST CRITICAL component.**

**Key questions**: What structure makes findings actionable? What metadata is needed (files reviewed, line numbers, severity)? What should the main agent do with results? Save to file or return inline?

This component is so important it gets its own section — see Section 6.

### How the Components Connect

The five components form a pipeline:

```
Role → Mission → Context Gathering → Approach → Output Format
WHO      WHY          WHAT             HOW          WHAT TO RETURN
```

Each component constrains the next. A vague role leads to an unfocused mission, which leads to gathering too much context, which leads to an unfocused analysis, which leads to unstructured output.

**Common mistake**: Skipping straight to the Output Format. The output format is critical, but it's only effective when the preceding four components properly constrain what the agent is doing. Start from Role and work your way down.

**References**: `templates/AGENT-TEMPLATE.md` for the complete starter template.

---

## 6. Output Format — The Primary Control Lever

The output format specification in your agent's system prompt is the single most impactful thing you can write. It's your only control over Handoff #2 (sub → main). Without it, the subagent returns unstructured text, the main agent improvises a response, and behavior becomes unpredictable.

### Six Critical Patterns

**Pattern 1: Prevent Unwanted Automation**

The most common frustration: main agent receives review findings and immediately starts fixing ALL issues without asking.

Solution — include this in your output format:

> *"IMPORTANT: When you have written the report, instruct the main agent to NOT start fixing any issues without the user's approval."*

This single line prevents the most common subagent problem.

**Pattern 2: Include Metadata**

Include: files reviewed (count + paths), lines analyzed, severity breakdown (critical/major/minor). Why: makes findings verifiable and parsable by downstream commands like `/code-review-fix`.

**Pattern 3: Mission Understanding**

Include a "Mission Understanding" section where the agent explains what it thinks its job is. Why: debugging tool — if the agent misunderstood its mission, you see it immediately in the output. Catches Handoff #1 failures.

**Pattern 4: Structured Severity Levels**

Three tiers: **Critical** (must fix before commit), **Major** (should fix soon), **Minor** (nice to have). Why: enables selective automation — "fix only critical issues" becomes a feasible instruction.

**Pattern 5: File Paths and Line Numbers**

Every finding must include: `file_path:line_number`, category, description, suggested fix. Why: the main agent (or `/code-review-fix` command) can locate and fix issues without additional searching.

**Pattern 6: Save to File vs Return Inline**

| Criteria | Save to File | Return Inline |
|----------|-------------|---------------|
| **When** | Persistent record needed | Results are short |
| **When** | Another command will consume it | Main agent acts immediately |
| **When** | Results are long (450+ lines) | No historical record needed |
| **Convention** | `.agents/code-reviews/agent-reviews/{name}-review.md` | Direct return to main agent |

**The anti-pattern**: No output format specified = subagent returns freeform text = main agent guesses what to do = unpredictable results. Always specify output format explicitly.

### A Complete Output Format Template

Here's a proven output format you can adapt for any review or analysis agent:

```markdown
## Output Format

Provide your analysis in this structure:

### Mission Understanding
[Explain your understanding of your mission in 1-2 sentences]

### Files Reviewed
- File: {path} — Lines: {count} — Changes: {summary}

### Findings

**Critical Issues** (must fix before commit)
- **File**: {path}:{line}
- **Category**: {type-safety|architecture|logging|security}
- **Description**: {what's wrong}
- **Suggested Fix**: {how to fix}

**Major Issues** (should fix soon)
[same structure]

**Minor Issues** (nice to have)
[same structure]

### Summary
- Total findings: {count}
- Critical: {count} | Major: {count} | Minor: {count}
- Overall assessment: {Ready to commit | Needs revision | Needs major changes}

---

IMPORTANT: When you have written the report, instruct the main agent
to NOT start fixing any issues without the user's approval.
```

This template includes all six patterns: automation prevention, metadata, mission understanding, severity levels, file paths with line numbers, and a clear file-vs-inline decision.

---

## 7. Parallel Execution Patterns

### Concurrency Limits

Confirmed limit: **10 concurrent subagents**. You can queue more in the same conversation — they execute when slots free up. This is the real power of subagents: running 5-10 focused agents simultaneously instead of one agent doing everything sequentially.

### Three Patterns

| Pattern | Description | Example | Benefits |
|---------|-------------|---------|----------|
| **A: Parallel Missions, Same Target** | Multiple specialized reviews on same code | 4 agents: type-safety, security, architecture, performance | Deeper per-area analysis, faster total review |
| **B: Parallel Reports, Different Targets** | Same analysis across multiple modules | Logging analysis across 4 features | Comprehensive coverage, consistent standards |
| **C: Parallel Research for Planning** | Different aspects researched simultaneously | 5 agents: API docs, architecture, patterns, tests, costs | 40-50% faster planning phase |

### Pattern A in Practice

The `/code-review` command uses Pattern A when agents exist in `.claude/agents/`. Four specialized agents review the same diff in parallel — each expert in one area (type-safety, security, architecture, performance). Results are combined into a comprehensive review.

### Pattern C in Practice

The `/planning` command uses Pattern C in Phases 2 & 3. An Explore agent maps the codebase while a general-purpose agent researches external documentation. Both run simultaneously, cutting research time by 40-50%.

### Context Consumption Warning

Many agents returning detailed inline results can exhaust the main context window. 5 agents each returning 500 lines = 2,500 lines of main context consumed. For long reports, use file-based output (Pattern 6 from Section 6) so agents write to disk instead of returning everything inline.

### Speed vs Cost

More parallel agents = faster results but higher token cost. Start with 2-3 agents for your first parallel workflow. Measure the speed improvement vs token cost. Scale up to 5-10 as confidence grows. For code review, 4 specialized agents is a proven sweet spot.

---

## 8. When to Use Subagents (Decision Framework)

### Great For

| Use Case | Why It Works |
|----------|--------------|
| Parallel research (5-10 simultaneous) | 40-50% speed improvement, each agent focused on one aspect |
| Code review with controlled feedback | Structured output prevents unwanted automation |
| System compliance checks across modules | Each agent becomes expert on specific area |
| Plan vs execution analysis | Isolated analysis without polluting main thread |
| Context-heavy tasks | Keeps irrelevant information out of main conversation |

### Not Ideal For

| Use Case | Why It Fails |
|----------|--------------|
| Simple sequential tasks | Overhead of context handoff not worth it |
| Priming your main agent | Too much context gets lost in handoff |
| Tasks requiring ALL context | Subagents work with summaries, not full history |
| Quick targeted changes | Faster to do directly in main conversation |
| Iterative back-and-forth | Handoff friction makes iteration slow |

### The Overhead Question

Each subagent has approximately **20K token startup overhead** (loading context, system prompt, tools). Rule of thumb: if the task takes less than 2 minutes to do manually in the main conversation, a subagent adds more overhead than value.

### The Context Budget

Each agent's results consume main context tokens when returned. 5 agents each returning 500 lines = 2,500 lines of main context consumed. Factor this into your parallel execution planning — use file-based output for verbose reports.

### Quick Decision Guide

Ask yourself these three questions in order:

1. **Is this task substantial?** If it takes less than 2 minutes manually → do it in main conversation.
2. **Does it benefit from isolation?** If the task generates a lot of irrelevant context → use a subagent to keep the main thread clean.
3. **Can I parallelize?** If you have 2+ independent research/review tasks → launch multiple agents simultaneously.

If you answered "no" to all three, subagents add overhead without benefit. Stick with the main conversation or a slash command.

---

## 9. Creating Custom Agents

### Three Creation Methods

1. **Manual**: Create `.claude/agents/your-agent.md` with YAML frontmatter + markdown body. Full control, recommended for experienced users.

2. **`/agents` command**: Claude generates the agent based on your task description. Good starting point — automatically pulls in project patterns. Customize the output afterward.

3. **Meta-agent (advanced)**: Create an agent whose job is creating other agents following YOUR standards. Encodes your preferences into agent creation, compounds learning over time.

### File Locations

- `.claude/agents/*.md` — project-specific agents (committed to repo, shared with team)
- `~/.claude/agents/*.md` — personal agents (your machine only, across all projects)

### Frontmatter Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | Yes | Unique identifier (lowercase-with-hyphens) | `code-reviewer` |
| `description` | Yes | When to use — guides autonomous delegation | `Use when reviewing newly written code...` |
| `model` | No | haiku, sonnet, opus (default: inherits parent) | `sonnet` |
| `tools` | No | Tool list or `["*"]` (default: inherits all) | `["Read", "Glob", "Grep"]` |
| `color` | No | Visual identification when invoked | `red` |

### Key Rules

- **Agents are project-specific** — create agents in `.claude/agents/` for your project
- **Session restart required** — manually added agents require restarting the Claude Code session to load
- **The markdown body IS the system prompt** — everything after the YAML frontmatter becomes the agent's instructions
- **Test before parallelizing** — verify a single agent works correctly before running multiple in parallel

For the full step-by-step creation walkthrough, see the sections below and `templates/AGENT-TEMPLATE.md`.

---

## 10. Integration with Commands & Workflows

### Two Integration Patterns

**Pattern 1: Command invokes agent** — A slash command instructs the main agent to delegate to a specific subagent, then acts on results. Example: `/code-review` delegates to 4 parallel review agents, then presents combined findings to the user.

**Pattern 2: Agent produces artifact for command** — A subagent saves a report file that a subsequent command consumes. Example: review agent writes report to `.agents/code-reviews/` → `/code-review-fix` reads and fixes the issues.

### Already in Use

- **`/planning`** command: Launches Explore + general-purpose agents in parallel for research (Phases 2 & 3)
- **`/code-review`** command: Uses parallel review agents when available in `.claude/agents/`

### Trust Progression

```
Manual → Commands → Chained → Subagents
  ↑ trust & verify ↑  ↑ trust & verify ↑  ↑ trust & verify ↑
```

**Before creating subagents**: Your manual prompts for the task work reliably 5+ times. You know what instructions produce good results. The pattern is stable.

**Before parallelizing**: Your single-agent workflow produces consistent results. Results are predictable. Don't skip stages — parallel execution amplifies both good patterns AND bad ones.

### Debugging Agent Handoffs

When a subagent produces unexpected results, work backwards through this checklist:

1. **Check the output format** — Is the agent's output structured as specified? If not, the output format section in the system prompt needs work.
2. **Check mission understanding** — Did the "Mission Understanding" section (if included) match your intent? If not, Handoff #1 failed — the main agent mis-summarized your request.
3. **Check context gathering** — Did the agent read the right files? If not, the context gathering section needs more specific file paths.
4. **Check the analysis** — Are findings accurate? If not, the analysis approach needs clearer steps or heuristics.
5. **Check the role** — Is the agent's focus too broad or too narrow? If too broad, it tries to do everything and does nothing well. If too narrow, it misses relevant issues.

80% of problems are in steps 1-2 (output format and handoff). Start there before touching the analysis logic.

---

## 11. Practical Exercises

### Exercise 1: Create a System Review Agent

**Challenge**: Create a subagent that analyzes an execution report against the original plan to find divergences and recommend system improvements.

**Steps**:
1. Define frontmatter: `name: system-reviewer`, `model: sonnet`, tools: read-only (`["Read", "Glob", "Grep"]`)
2. Write role definition — expert at comparing plans vs execution outcomes
3. Define context gathering — receives plan file path + execution report path from main agent
4. Write a 5-step analysis approach: read plan, read report, classify divergences (intentional vs unintentional), identify root causes, recommend system improvements
5. Design output format with: mission understanding, context analyzed, findings with severity stars, summary metrics, actionable recommendations, and instruction to NOT auto-fix

**Success criteria**: Agent produces a structured review with categorized findings and actionable recommendations. Main agent presents findings without automatically acting on them.

### Exercise 2: Parallelize the System Review

**Challenge**: Run the same system-reviewer agent in parallel on 2-3 different plan/report pairs simultaneously.

**Steps**:
1. Prepare 2-3 different plan/report pairs from past features
2. Launch system-reviewer agents in parallel using the Task tool (one per pair)
3. Compare results — are reports structured identically? Can the main agent combine findings?
4. Measure speed improvement vs running sequentially

**Success criteria**: Approximately 60% faster than sequential execution. All reports follow identical structure. Main agent can coherently synthesize findings from multiple reports.

### Exercise 3: Build a Parallel Code Review

**Challenge**: Create 2+ specialized review agents and run them in parallel on the same diff.

**Steps**:
1. Customize the pre-installed agents in `.claude/agents/` (start with type-safety + architecture)
2. Adapt frontmatter and system prompts for your project's tech stack
3. Run `/code-review` with the customized agents available
4. Compare: does parallel review catch issues that single-agent review misses?

**Success criteria**: Parallel review identifies issues that a single general-purpose review misses. Each agent produces structured output with severity levels. Total review time is faster than running each review sequentially.

### Common Pitfalls When Building Agents

These mistakes appear frequently when creating your first agents:

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Vague role definition** | Agent produces generic, unfocused analysis | Add singular focus and differentiation from general-purpose |
| **No output format** | Main agent improvises response, unpredictable behavior | Always specify structured output with sections and fields |
| **No main agent instructions** | Main agent auto-fixes everything without asking | Add "do NOT fix without approval" instruction |
| **Too much context** | Agent is slow, expensive, and diluted | Specify exact files to read, not "read everything" |
| **Tool overreach** | Analysis agent modifies code accidentally | Restrict to read-only tools for review/analysis agents |
| **Skipping single-agent test** | Parallel agents all fail the same way | Always verify one agent works before parallelizing |

---

## FAQ: Common Questions

### "Can subagents spawn other subagents?"

**Short answer**: No — no nesting allowed.

**Long answer**: Subagents cannot invoke the Task tool to create other subagents. If you need a chain of agents (Agent A's output feeds Agent B), orchestrate from the main conversation. Launch A, get results, then launch B with A's results as input. The main conversation is always the orchestrator.

### "How do I know if a task is worth a subagent?"

**Short answer**: If the task takes less than 2 minutes manually, skip the subagent.

**Long answer**: Each subagent has ~20K token startup overhead. The task needs to be substantial enough to justify this cost. Good candidates: research requiring multiple file reads, analysis requiring cross-referencing multiple sources, reviews with structured output requirements. Bad candidates: quick lookups, simple edits, tasks requiring the full conversation history.

### "Should I use Haiku or Sonnet for my agent?"

**Short answer**: Haiku for read-only exploration, Sonnet for analysis, Opus for critical decisions.

**Long answer**: Haiku is 10x cheaper and faster — ideal for file discovery, pattern searching, and codebase mapping (like the built-in Explore agent). Sonnet balances cost and capability — ideal for code review, analysis, and multi-step reasoning. Opus for high-stakes decisions where accuracy matters most. Start with Sonnet, downgrade to Haiku if speed matters more than depth.

### "Why does my agent auto-fix issues I just wanted reported?"

**Short answer**: Missing output format control instruction.

**Long answer**: When a subagent returns findings without explicit instructions about what the main agent should do, the main agent defaults to "helpful" behavior — which often means immediately fixing everything. Add this to your output format: *"IMPORTANT: Instruct the main agent to NOT start fixing any issues without the user's approval."* This single line prevents the most common frustration with subagent workflows.

### "How many agents should I run in parallel?"

**Short answer**: Start with 2-3, scale to 5-10 as confidence grows.

**Long answer**: Max 10 concurrent agents. But more isn't always better — each agent's results consume main context tokens. Start with 2-3 agents for your first parallel workflow. Measure speed improvement vs token cost. If results are good and context budget allows, scale up. For code review, 4 specialized agents (type-safety, security, architecture, performance) is a proven sweet spot.

---

## Next Steps

1. Read `templates/AGENT-TEMPLATE.md` for the starter template you can copy to your project
2. Try Exercise 1 — create your first custom agent (system reviewer)
3. Try Exercise 2 — parallelize to experience the speed improvement firsthand
4. Read `reference/implementation-discipline.md` for execution discipline that feeds agent workflows

---

## Related Resources

- **Agent template**: `templates/AGENT-TEMPLATE.md` — starter template for new agents
- **Pre-installed agents**: `.claude/agents/` — 12 agents across 4 categories (research, code review, utility, specialist)
- **Execution discipline**: `reference/implementation-discipline.md` — prerequisite concepts for agent workflows

---

**That's the Subagents Deep Dive guide!** You now understand:
- The context handoff mental model and the two points where information is lost
- Built-in agents (Explore, Plan, General-purpose) and when each is best
- The 5-component agent design framework (Role → Mission → Context → Approach → Output)
- Output format as the primary control lever for subagent reliability
- Three parallel execution patterns and the 10-agent concurrency limit
- The decision framework for when subagents justify their overhead
- How to create custom agents with frontmatter and structured output
- Integration patterns with commands and the trust progression
