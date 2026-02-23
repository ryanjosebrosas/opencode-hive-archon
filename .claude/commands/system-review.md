---
description: Analyze implementation against plan for process improvements
argument-hint: [plan-path] [execution-report-path]
---

# System Review

Perform a meta-level analysis of how well the implementation followed the plan and identify process improvements.

## Purpose

**System review is NOT code review.** You're not looking for bugs in the code — you're looking for bugs in the process.

**Your job:**

- Analyze plan adherence and divergence patterns
- Identify which divergences were justified vs problematic
- Surface process improvements that prevent future issues
- Suggest updates to Layer 1 assets (CLAUDE.md, plan templates, commands)

**Philosophy:**

- Good divergence reveals plan limitations — improve planning
- Bad divergence reveals unclear requirements — improve communication
- Repeated issues reveal missing automation — create commands

## Context & Inputs

You will analyze four key artifacts:

**Plan Command:**
Read this to understand the planning process and what instructions guide plan creation.
@.claude/commands/planning.md

**Generated Plan:**
Read this to understand what the agent was SUPPOSED to do.
Plan file: $1

**Execute Command:**
Read this to understand the execution process and what instructions guide implementation.
@.claude/commands/execute.md

**Execution Report:**
Read this to understand what the agent ACTUALLY did and why.
Execution report: $2

## Analysis Workflow

### Step 1: Understand the Planned Approach

Read the generated plan ($1) and extract:

- What features were planned?
- What architecture was specified?
- What validation steps were defined?
- What patterns were referenced?

### Step 2: Understand the Actual Implementation

Read the execution report ($2) and extract:

- What was implemented?
- What diverged from the plan?
- What challenges were encountered?
- What was skipped and why?

### Step 3: Classify Each Divergence

For each divergence identified in the execution report, classify as:

**Good Divergence (Justified):**

- Plan assumed something that didn't exist in the codebase
- Better pattern discovered during implementation
- Performance optimization needed
- Security issue discovered that required different approach

**Bad Divergence (Problematic):**

- Ignored explicit constraints in plan
- Created new architecture instead of following existing patterns
- Took shortcuts that introduce tech debt
- Misunderstood requirements

### Step 4: Trace Root Causes

For each problematic divergence, identify the root cause:

- Was the plan unclear? Where, why?
- Was context missing? Where, why?
- Was validation missing? Where, why?
- Was a manual step repeated? Where, why?

### Step 5: Generate Process Improvements

Based on patterns across divergences, suggest:

- **CLAUDE.md updates:** Universal patterns or anti-patterns to document
- **Plan command updates:** Instructions that need clarification or missing steps
- **Execute command updates:** Validation steps to add to execution checklist
- **New commands:** Manual processes that should be automated

## Output Format

Save your analysis to: `requests/system-reviews/[feature-name]-review.md`

### Overall Alignment Score: __/10

Scoring guide:

- 10: Perfect adherence, all divergences justified
- 7-9: Minor justified divergences
- 4-6: Mix of justified and problematic divergences
- 1-3: Major problematic divergences

### Divergence Analysis

For each divergence from the execution report:

```
divergence: [what changed]
planned: [what plan specified]
actual: [what was implemented]
reason: [agent's stated reason from report]
classification: good | bad
justified: yes/no
root_cause: [unclear plan | missing context | missing validation | other]
```

### Pattern Compliance

- Followed codebase architecture: yes/no
- Used documented patterns (from CLAUDE.md): yes/no
- Applied testing patterns correctly: yes/no
- Met validation requirements: yes/no

### System Improvement Actions

**Update CLAUDE.md:**
- [specific patterns or anti-patterns to document]

**Update Plan Command:**
- [instructions to clarify or steps to add]

**Update Execute Command:**
- [validation steps to add to execution checklist]

**Create New Command:**
- [manual processes repeated 3+ times to automate]

### Key Learnings

- What worked well
- What needs improvement
- Concrete improvements for next implementation

## Important

- **Be specific:** Don't say "plan was unclear" — say "plan didn't specify which auth pattern to use"
- **Focus on patterns:** One-off issues aren't actionable. Look for repeated problems.
- **Action-oriented:** Every finding should have a concrete asset update suggestion
- **Be selective:** LLMs tend to over-engineer and recommend many small, low-value changes. Only action on recommendations that will genuinely improve future PIV loops. Don't bloat global rules with one-off fixes.
