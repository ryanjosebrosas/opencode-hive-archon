# Enhanced /system-review Integration Guide

## Overview

The enhanced `/system-review` command adds four major capabilities:

1. **Auto-Diff** — Programmatically compare plan vs. git diff
2. **Code-Review Integration** — Re-run 4 review agents post-implementation
3. **Memory Suggestions** — Auto-generate lessons from execution patterns
4. **Plan Quality Assessment** — Score template section completeness

## New Files Created

| File | Purpose |
|------|---------|
| `.opencode/commands/system-review.md` | Enhanced command (replaces existing) |
| `scripts/analyze-plan-diff.js` | Auto-diff analysis helper |
| `templates/MEMORY-SUGGESTION-TEMPLATE.md` | Memory entry generation |
| `templates/PLAN-QUALITY-ASSESSMENT.md` | Plan quality scoring guide |

## Enhanced Workflow

```
/execute completes
    ↓
Execution report saved to requests/execution-reports/{feature}-report.md
    ↓
/system-review executed (auto-triggers /code-review if not run)
    ↓
Step 0: Code Review Results (quality score)
Step 1: Auto-Diff (plan adherence %)
Step 2: Plan Quality Assessment (template completeness)
Step 3-5: Divergence Analysis + Root Causes
Step 6: Memory Suggestions (auto-generated lessons)
Step 7: Process Improvements (action items)
    ↓
Review saved to requests/system-reviews/{feature}-review.md
    ↓
User reviews and approves memory suggestions
    ↓
/commit appends approved lessons to memory.md
```

## Step-by-Step Breakdown

### Step 0: Pre-Review Code Quality Check

**What changed:** Auto-triggers `/code-review` if not already run.

**Why:** Distinguish between:
- **Plan deviation issues** — agent ignored the plan
- **Implementation bugs** — agent followed plan but introduced bugs

**Integration point:** Calls `/code-review` command, reads review report.

**Output:** Code quality score (10% of alignment score).

---

### Step 1: Auto-Diff — Plan vs. Git Diff

**What changed:** Programmatic analysis instead of manual comparison.

**How it works:**

```bash
# Helper script extracts planned files from plan
node scripts/analyze-plan-diff.js requests/{feature}-plan.md

# Script parses:
# - "New Files to Create" section
# - "Step-by-Step Tasks" headers (ACTION + TARGET)
# - "Patterns to Follow" references
# - "Relevant Codebase Files" section

# Cross-references with git diff:
git diff --name-only HEAD~1 HEAD
git diff --cached --name-only

# Calculates:
# - File Adherence %
# - Task Completion % (from execution report)
# - Pattern Compliance %
# - Scope Creep count
```

**Metrics:**

```
Plan Adherence Score = (File Adherence + Task Completion + Pattern Compliance) / 3
```

**Output:** Quantitative adherence metrics with specific file lists.

**Integration point:** Uses git commands, parses plan file structure.

---

### Step 2: Plan Quality Assessment

**What changed:** Systematic scoring of template section completeness.

**How it works:**

Each template section assessed against required elements:

| Section | Required Elements |
|---------|-------------------|
| Solution Statement | Decisions with "because" reasoning |
| Relevant Codebase Files | file:line refs + "Why" explanations |
| Patterns to Follow | Actual code snippets from project |
| Step-by-Step Tasks | All 7 fields (ACTION, TARGET, IMPLEMENT, PATTERN, IMPORTS, GOTCHA, VALIDATE) |
| Validation Commands | All 5 levels with executable commands |
| Acceptance Criteria | Split Implementation + Runtime |

**Scoring:**

```
Plan Quality Score = (% of sections marked Complete)

90-100%: Excellent plan
70-89%:  Good plan
50-69%:  Fair plan (needs improvement)
<50%:    Poor plan (reject)
```

**Output:** Table showing status of each section with notes.

**Integration point:** References `templates/STRUCTURED-PLAN-TEMPLATE.md`, uses `reference/plan-quality-assessment.md` guide.

---

### Step 3-5: Divergence Analysis (Enhanced)

**What changed:** Added code review impact classification.

**New field in divergence output:**

```
code_review_impact: [none | improved | degraded]
```

**Why:** Helps determine if divergence:
- **Improved** quality (justified deviation)
- **Degraded** quality (problematic deviation)
- Had **no impact** (neutral)

**Output:** Enhanced divergence classification with quality impact.

---

### Step 6: Auto-Generate Memory Suggestions

**What changed:** Structured lesson extraction from execution patterns.

**How it works:**

1. Parse execution report for:
   - Divergences
   - Challenges
   - Workarounds
   - Gotchas

2. Categorize each lesson:
   - **gotcha** — Pitfalls, edge cases
   - **pattern** — Successful approaches
   - **decision** — Architecture choices
   - **anti-pattern** — What not to do

3. Generate structured memory entry:

```markdown
### 2026-02-24: {Short Title}

**Category:** {category}

**What:** {one-liner}

**Why:** {why this matters}

**Pattern:** (if applicable)
```
{code pattern example}
```

**Avoid:** (if applicable)
```
{anti-pattern example}
```

**Applied to:**
- AGENTS.md: [section to update]
- Plan template: [section to enhance]
- Commands: [command to update]
```

**Output:** Ready-to-append memory entries in "Memory Suggestions" section.

**Integration point:** Uses `templates/MEMORY-SUGGESTION-TEMPLATE.md`, feeds into `/commit`.

---

### Step 7: Generate Process Improvements (Enhanced)

**What changed:** More specific action items tied to assessment findings.

**New categories:**

| Category | Trigger |
|----------|---------|
| Update AGENTS.md | Pattern compliance failures, repeated anti-patterns |
| Update Plan Command | Plan quality section failures, missing research steps |
| Update Execute Command | Divergence root causes, validation gaps |
| Update Templates | Template assessment gaps, missing required fields |
| Create New Command | Manual processes repeated 3+ times |

**Output:** Actionable checklist with specific file paths.

---

## Output Format Changes

### Before (Original)

```markdown
### Overall Alignment Score: __/10

### Divergence Analysis
{free-form text}

### Pattern Compliance
{yes/no checklist}

### System Improvement Actions
{bulleted list}
```

### After (Enhanced)

```markdown
### Overall Alignment Score: __/10

**Scoring breakdown:**
| Component | Weight | Score |
|-----------|--------|-------|
| Plan Adherence | 40% | __/10 |
| Plan Quality | 20% | __/10 |
| Divergence Justification | 30% | __/10 |
| Code Quality | 10% | __/10 |

### Plan Quality Assessment
```
Section | Status | Notes
--------|--------|------
Solution Statement | Complete | 3 decisions with rationale
...
```

### Auto-Diff Analysis
```
Planned Files: 8
Actual Files:  10
Overlap:       7

File Adherence:    87.5%
Task Completion:   92.8%
Pattern Compliance: 100%
Scope Creep:       +2 files
```

### Memory Suggestions
```markdown
### 2026-02-24: {Title}
**Category:** gotcha
**What:** {one-liner}
**Why:** {why it matters}
...
```

### System Improvement Actions
**Update AGENTS.md:**
- [ ] Specific action with section reference
...
```

---

## Integration with Other Commands

### With `/code-review`

**Before:** Independent commands

**After:** `/system-review` auto-triggers `/code-review` if not run:

```markdown
### Step 0: Pre-Review Code Quality Check

**If code review report exists:** Read it

**If no code review report:** Execute `/code-review` first
```

**Data flow:**
```
/code-review → requests/code-reviews/{feature}-review.md
    ↓
/system-review reads review → code quality score
    ↓
Impacts alignment score (10% weight)
```

---

### With `/commit`

**Before:** Manual memory updates

**After:** Auto-suggested lessons from system review:

```markdown
## Output Report (from /system-review)

### Memory Suggestions
{auto-generated entries}

---

## /commit Workflow

1. Run /system-review (if not already done)
2. Review memory suggestions
3. Approve/reject each suggestion
4. /commit appends approved lessons to memory.md
```

**Data flow:**
```
/system-review → Memory Suggestions section
    ↓
User approves suggestions
    ↓
/commit → appends to memory.md under <!-- System Review Auto-Append -->
```

---

### With `/planning`

**Before:** No feedback loop

**After:** Plan quality assessment feeds back:

```markdown
## Plan Quality Feedback Loop

/system-review Step 2 → Plan Quality Score
    ↓
If score < 70%:
- Update planning.md instructions
- Enhance template required fields
- Add enforcement rules

Example: If "Validation Commands" consistently Missing:
→ Update planning.md Phase 6: "Enforce all 5 levels required"
→ Update template: Add validation warning if incomplete
```

**Data flow:**
```
/system-review → Plan Quality Assessment
    ↓
Pattern: Validation Commands Missing in 3+ plans
    ↓
Update planning.md + template
    ↓
Future plans enforced to complete all sections
```

---

### With `/execute`

**Before:** Divergence only reported

**After:** Divergence analyzed for root causes:

```markdown
## Root Cause → Execute Command Updates

Root Cause: "Plan was unclear"
→ Update execute.md: "Report divergence immediately when discovered"

Root Cause: "Missing validation"
→ Update execute.md Step 4: "Block completion if validation fails"
```

**Data flow:**
```
/system-review → Root Cause Analysis
    ↓
Pattern: Divergences due to "unclear plan"
    ↓
Update execute.md: Add divergence reporting requirement
```

---

## Usage Examples

### Example 1: Standard Review

```bash
# After implementation completes
> /system-review requests/user-auth-plan.md

# Auto-detects feature name from plan path
# Runs code-review if needed
# Generates comprehensive review
```

**Output:** `requests/system-reviews/user-auth-review.md`

---

### Example 2: Review with Plan Series

```bash
> /system-review requests/payment-flow-plan-overview.md

# Detects plan series from <!-- PLAN-SERIES --> marker
# Analyzes all sub-plans + overview
# Aggregates metrics across sub-plans
```

**Output:** `requests/system-reviews/payment-flow-review.md`

---

### Example 3: Review with Memory Update

```bash
> /system-review requests/user-auth-plan.md

# Review completes with Memory Suggestions section
# User reviews suggestions
> /commit -m "feat: user authentication"

# /commit checks for pending system review
# Appends approved lessons to memory.md
```

---

## Migration Guide

### For Existing Users

**No breaking changes.** The enhanced command:

- Reads same inputs (plan + execution report)
- Produces same output file (enhanced format)
- Backwards compatible with existing plans

**New dependencies:**

1. `scripts/analyze-plan-diff.js` — Optional, enhances Step 1
2. `templates/MEMORY-SUGGESTION-TEMPLATE.md` — Optional, guides Step 6
3. `reference/plan-quality-assessment.md` — Optional, guides Step 2

**If helpers missing:** Command falls back to manual analysis with degraded metrics.

---

### For New Users

**Setup:**

```bash
# Helpers are included in templates/ and scripts/
# No additional setup needed

# Run first review
> /system-review requests/{feature}-plan.md
```

**Recommended workflow:**

1. Implement feature with `/execute`
2. Run `/code-review` (or let system-review auto-run)
3. Run `/system-review`
4. Review memory suggestions
5. Run `/commit` to save lessons

---

## Success Metrics

Track these to measure improvement:

| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| Plan Adherence | 70% | 90% | Auto-diff Step 1 |
| Plan Quality | 60% | 85% | Assessment Step 2 |
| Divergence Justification | 50% | 80% | Classification Step 4 |
| Memory Updates/Feature | 0-1 | 2-3 | Step 6 suggestions |
| Process Improvements/Feature | 0 | 1-2 | Step 7 actions implemented |

---

## Troubleshooting

### Issue: Auto-diff script fails

**Symptom:** `node scripts/analyze-plan-diff.js` errors

**Solution:** 
- Check Node.js is installed: `node --version`
- Verify plan file path is correct
- Script is optional — manual analysis still works

---

### Issue: Code review not running

**Symptom:** Step 0 reports "code review not found" indefinitely

**Solution:**
- Manually run `/code-review` first
- Check `.opencode/agents/code-review-*.md` exist
- Verify feature name matches between reports

---

### Issue: Memory suggestions empty

**Symptom:** Step 6 produces no suggestions

**Solution:**
- Check execution report has "Divergences" or "Issues & Notes"
- Verify execution report was saved to correct path
- If implementation was perfect (no divergences), this is correct

---

### Issue: Plan quality score seems low

**Symptom:** Plan scored <70% despite seeming complete

**Solution:**
- Review assessment table — which sections marked Partial/Missing?
- Check template required elements (see `reference/plan-quality-assessment.md`)
- Common issue: "Validation Commands" incomplete (only 1-2 levels)
- Common issue: "Patterns to Follow" missing code snippets

---

## Future Enhancements

### Phase 2 (Not Implemented)

- [ ] Auto-run parallel dispatch for 15+ task plans
- [ ] Parallel system-review agents (one per divergence category)
- [ ] Trend analysis across multiple reviews
- [ ] Auto-update AGENTS.md based on repeated patterns
- [ ] Integration with Archon for task-level adherence tracking

### Phase 3 (Experimental)

- [ ] ML-based plan quality prediction
- [ ] Automated template enforcement (reject incomplete plans)
- [ ] Cross-project pattern learning
- [ ] Memory suggestion ranking by impact

---

## Summary

The enhanced `/system-review` command transforms post-implementation analysis from:

**Before:**
```
"Looks like the agent diverged from the plan a few times.
Some good reasons, some not. Maybe update the plan template?"
```

**After:**
```
Plan Adherence: 87.5% (7/8 files)
Plan Quality: 71% (5/7 sections complete)
Code Quality: 95% (2 minor issues)

Divergences: 3 total (2 justified, 1 problematic)
Root Causes: 1 unclear plan, 1 missing context, 1 AI assumption

Memory Suggestions: 3 lessons (1 gotcha, 1 pattern, 1 anti-pattern)

Action Items:
- Update AGENTS.md: Add error handling section
- Update planning.md: Add library compatibility check
- Update template: Enforce all 7 task fields
```

**Result:** Data-driven process improvements, not gut feelings.
