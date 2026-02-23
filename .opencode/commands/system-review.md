---
description: Analyze implementation against plan with auto-diff, code-review integration, and memory suggestions
agent: build
---

# System Review (Enhanced)

Perform a meta-level analysis of how well the implementation followed the plan and identify process improvements.

## Purpose

**System review is NOT code review.** You're looking for bugs in the **process**, not the code.

**Your job:**
- Analyze plan adherence and divergence patterns
- Classify divergences as justified vs. problematic
- Generate process improvements for Layer 1 assets
- Auto-suggest lessons for `memory.md`

**Philosophy:**
- Good divergence → plan limitations → improve planning
- Bad divergence → unclear requirements → improve communication
- Repeated issues → missing automation → create commands

---

## Execution Workflow

### Step 0: Pre-Check (Code Review Integration)

**Check if `/code-review` was run:**
```bash
# Look for code review artifacts or ask user
```

**If NOT run:**
```
⚠️ Code review not detected. Running 4 parallel review agents now...
```
- Delegate to `@code-review-type-safety`, `@code-review-security`, `@code-review-architecture`, `@code-review-performance`
- Aggregate findings → use in Step 4 (Code Quality Score)

**If run:** Read code review findings for quality score.

---

### Step 1: Auto-Diff (Plan vs. Reality)

**Run auto-diff script:**
```bash
node scripts/analyze-plan-diff.js {plan-file} --json
```

**Extract metrics:**
- File Adherence % (planned files that were modified)
- Pattern Compliance % (referenced patterns appear in diff)
- Scope Creep (+N files not in plan)
- Missed Files (N files in plan but not modified)

**Calculate Plan Adherence Score:**
```
Plan Adherence = (File Adherence + Pattern Compliance) / 2
```

---

### Step 2: Plan Quality Assessment

**Read plan file** and assess each section using `templates/PLAN-QUALITY-ASSESSMENT.md`:

| Section | Status | Points |
|---------|--------|--------|
| Feature Description | Complete/Partial/Missing | /10 |
| User Story | Complete/Partial/Missing | /10 |
| Solution Statement | Complete/Partial/Missing | /10 |
| Relevant Files | Complete/Partial/Missing | /15 |
| Patterns to Follow | Complete/Partial/Missing | /15 |
| Step-by-Step Tasks | Complete/Partial/Missing | /15 |
| Testing Strategy | Complete/Partial/Missing | /10 |
| Validation Commands | Complete/Partial/Missing | /10 |
| Acceptance Criteria | Complete/Partial/Missing | /5 |
| **Total** | | **/100** |

**Plan Quality Score** = Total Points / 100 * 10

---

### Step 3: Read Execution Report

**Read**: `requests/execution-reports/{feature}-report.md`

**Extract:**
- Completed tasks (count / total)
- Divergences from plan (list each with reason)
- Issues & Notes (challenges encountered)
- Validation results (pass/fail status)

**Classify each divergence:**

**Good Divergence (Justified):**
- Plan assumed something that didn't exist
- Better pattern discovered during implementation
- Performance/security issue required different approach

**Bad Divergence (Problematic):**
- Ignored explicit constraints
- Created new architecture vs. following patterns
- Shortcuts introducing tech debt
- Misunderstood requirements

---

### Step 4: Code Quality Score

**From Step 0 code review findings:**
- Type Safety Issues: count Critical/Major/Minor
- Security Issues: count Critical/Major/Minor
- Architecture Issues: count Critical/Major/Minor
- Performance Issues: count Critical/Major/Minor

**Calculate Code Quality Score:**
```
Code Quality = 10 - (Critical*2 + Major*1 + Minor*0.5)
Min: 0, Max: 10
```

---

### Step 5: Validation Pyramid Check

**Verify 5-level validation was followed:**

| Level | Check | Pass/Fail |
|-------|-------|-----------|
| 1: Syntax & Style | Lint commands run? | |
| 2: Unit Tests | Unit tests created + pass? | |
| 3: Integration Tests | Integration tests created + pass? | |
| 4: Manual Validation | Manual steps documented + tested? | |
| 5: Additional | Any extra validation specified? | |

**Validation Score** = (Pass count / 5) * 10

---

### Step 6: Memory Suggestions

**Generate lessons** using `templates/MEMORY-SUGGESTION-TEMPLATE.md`:

**Extract from execution report:**
1. Divergences → lessons about planning gaps
2. Challenges → gotchas for future features
3. Workarounds → patterns to replicate
4. "Wish we knew" → decisions to document

**Categorize each lesson:**
- **gotcha**: Pitfalls, edge cases
- **pattern**: Successful approaches to replicate
- **decision**: Architecture/tech choices with rationale
- **anti-pattern**: What not to do

**Output format:**
```markdown
### {Date}: {Title}
**Category:** {category}
**What:** {one-liner}
**Why:** {why this matters}
**Applied to:** {which commands/templates/agents to update}
```

---

### Step 7: Generate Report

**Save to**: `requests/system-reviews/{feature}-review.md`

**Overall Alignment Score:**
```
Alignment = (
  Plan Adherence * 0.40 +
  Plan Quality * 0.20 +
  Divergence Justification * 0.30 +
  Code Quality * 0.10
)
```

**Scoring breakdown table:**
| Component | Weight | Score |
|-----------|--------|-------|
| Plan Adherence | 40% | /10 |
| Plan Quality | 20% | /10 |
| Divergence Justification | 30% | /10 |
| Code Quality | 10% | /10 |
| **Total** | **100%** | **/10** |

---

## Output Format

### Overall Alignment Score: __/10

**Scoring breakdown:**
| Component | Weight | Score |
|-----------|--------|-------|
| Plan Adherence | 40% | /10 |
| Plan Quality | 20% | /10 |
| Divergence Justification | 30% | /10 |
| Code Quality | 10% | /10 |

**Classification:**
- 9-10: Excellent — process working well
- 7-8: Good — minor improvements needed
- 5-6: Fair — significant gaps identified
- <5: Poor — process breakdown, needs attention

---

### Auto-Diff Analysis

```
Planned Files: N
Actual Files: N
Overlap: N

File Adherence: X%
Pattern Compliance: X%
Scope Creep: +N files
Missed Files: N files
```

---

### Plan Quality Assessment

| Section | Status | Notes |
|---------|--------|-------|
| Feature Description | | |
| User Story | | |
| Solution Statement | | |
| Relevant Files | | |
| Patterns to Follow | | |
| Step-by-Step Tasks | | |
| Testing Strategy | | |
| Validation Commands | | |
| Acceptance Criteria | | |

**Plan Quality Score:** __/10

---

### Divergence Analysis

For each divergence from execution report:

```
**Divergence:** {what changed}
**Planned:** {what plan specified}
**Actual:** {what was implemented}
**Reason:** {agent's stated reason}
**Classification:** Good / Bad
**Root Cause:** {unclear plan | missing context | missing validation | other}
```

**Divergence Justification Score:** __/10
- (Good divergences / Total divergences) * 10

---

### Code Quality Summary

| Review Type | Critical | Major | Minor |
|-------------|----------|-------|-------|
| Type Safety | | | |
| Security | | | |
| Architecture | | | |
| Performance | | | |

**Code Quality Score:** __/10

---

### Validation Pyramid

| Level | Check | Pass/Fail |
|-------|-------|-----------|
| 1: Syntax & Style | | |
| 2: Unit Tests | | |
| 3: Integration Tests | | |
| 4: Manual Validation | | |
| 5: Additional | | |

**Validation Score:** __/10

---

### Memory Suggestions

> Review these before appending to `memory.md`. Remove duplicates, keep valuable lessons.

```markdown
<!-- Copy-approved entries to memory.md -->

### {Date}: {Title}
**Category:** {category}
**What:** {one-liner}
**Why:** {why this matters}
**Applied to:** {affected areas}

...
```

---

### System Improvement Actions

**Update AGENTS.md:**
- {specific patterns or anti-patterns to document}

**Update Plan Command:**
- {instructions to clarify or steps to add}

**Update Execute Command:**
- {validation steps to add to execution checklist}

**Create New Command:**
- {manual processes repeated 3+ times to automate}

---

### Key Learnings

**What worked well:**
- {list 2-3 successes}

**What needs improvement:**
- {list 2-3 gaps}

**Concrete improvements for next implementation:**
1. {actionable item}
2. {actionable item}
3. {actionable item}

---

## Important Rules

- **Be specific:** Don't say "plan was unclear" — say "plan didn't specify X"
- **Focus on patterns:** Look for repeated problems, not one-offs
- **Action-oriented:** Every finding should have a concrete asset update suggestion
- **Be selective:** Only action on recommendations that genuinely improve future PIV loops
