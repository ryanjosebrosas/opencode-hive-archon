# System Simplification Plan v2

> **Goal**: Reduce complexity while maximizing agent ecosystem (Ollama/Model Studio optimization)
> **Target**: Solo developer workflow with Swarm+UBS+Research agents fully integrated
> **File Impact**: 58 files → 28 files (cut 30, add 4, net -26)

---

## Executive Summary

### What We're Doing

| Action | Count | Details |
|--------|-------|---------|
| **Cut** | 30 files | 8 agents + 9 commands + 10 guides + 3 templates |
| **Keep** | 28 files | 9 agents + 8 commands + 11 guides + 5 templates |
| **Add** | 4 files | 3 new agents + 1 consolidated guide |
| **Update** | 6 files | /planning, /system-review, AGENTS.md, plan template, research agents |

### Key Decisions (Q1-Q4 + abc)

| Question | Decision |
|----------|----------|
| **Q1: Research agents** | Integrate into `/planning` (Phase 2-3 call pre-defined agents), keep free-form output |
| **Q2: /system-review** | Enhance with auto-diff, code-review re-run, memory suggestions |
| **Q3: Plan length** | Keep 700-1000 lines min, keep decomposition (10-20 sub-tasks for robust features) |
| **Agent scaling** | abc — integrate existing + add 3 new + full ecosystem audit |

---

## Phase 1: Cut Orphaned Infrastructure

### 1A: Agents (5 files to cut)

```bash
rm .opencode/agents/specialist-devops.md
rm .opencode/agents/specialist-data.md
rm .opencode/agents/specialist-copywriter.md
rm .opencode/agents/specialist-tech-writer.md
rm .opencode/agents/test-generator.md
```

**Research agents** (`research-codebase.md`, `research-external.md`) are **UPDATED, not cut** (Phase 2).

### 1B: Commands (9 files to cut)

```bash
rm .opencode/commands/create-prd.md
rm .opencode/commands/create-pr.md
rm .opencode/commands/rca.md
rm .opencode/commands/implement-fix.md
rm .opencode/commands/init-c.md
rm .opencode/commands/agents.md
rm .opencode/commands/end-to-end-feature.md
rm .opencode/commands/execution-report.md
rm .opencode/commands/system-review.md
```

### 1C: Guides (6 files to cut)

```bash
rm reference/SWARMTOOLS-INSTALLATION.md
rm reference/SWARMTOOLS-QUICKSTART.md
rm reference/PRACTICAL-SWARM-UBS-SETUP.md
rm reference/AUTONOMOUS-SWARM-ECOSYSTEM.md
rm reference/swarmtools-integration.md
rm reference/bailian-coding-plan-setup.md
```

### 1D: Templates (3 files to cut)

```bash
rm templates/SUB-PLAN-TEMPLATE.md
rm templates/PLAN-OVERVIEW-TEMPLATE.md
rm templates/COMMAND-TEMPLATE.md
```

---

## Phase 2: Integrate Research Agents into `/planning`

### 2A: Update `/planning` Command

**Phase 2** (lines 68-96): Replace 2 custom agents → `@research-codebase` (2 parallel calls with focused queries)
**Phase 3** (lines 99-117): Replace custom agent → `@research-external` delegation
**Phase 3b** (lines 119-137): Merge with Phase 3 (same agent, Archon RAG query)
**Phase 4** (lines 151-158): Update synthesis to handle structured agent output

### 2B: Update Research Agents

**research-codebase.md**:
- Add instruction: "Include file:line references for ALL findings"
- Add instruction: "Note which files should be read by implementer"
- Add tools: `archon_rag_search_code_examples` (optional)

**research-external.md**:
- Add tools: `archon_rag_search_knowledge_base`, `archon_rag_read_full_page`
- Add instruction: "Include specific doc section links, not just URLs"

---

## Phase 3: Enhance `/system-review`

### 3A: New `/system-review` Flow

```
Step 0: Pre-check — Run /code-review if not done
Step 1: Auto-Diff — Compare plan files vs. git diff (quantitative score)
Step 2: Plan Quality — Assess template section completeness
Step 3: Divergence Analysis — Classify good vs. bad divergence
Step 4: Code Review Integration — Re-run 4 agents, catch post-fix bugs
Step 5: Validation Pyramid Check — Verify tests/lint actually ran
Step 6: Memory Suggestions — Auto-generate lessons for memory.md
Step 7: Generate Report — Alignment score + actionable improvements
```

### 3B: New Files to Create

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/analyze-plan-diff.js` | Auto-diff helper | ~150 |
| `templates/MEMORY-SUGGESTION-TEMPLATE.md` | Structured lesson format | ~50 |
| `templates/PLAN-QUALITY-ASSESSMENT.md` | Section completeness checklist | ~40 |

---

## Phase 4: Add New Agents (abc Scaling)

### 4A: New Agent Definitions

| Agent | Purpose | Integration Point |
|-------|---------|-------------------|
| `research-ai-patterns.md` | AI/LLM integration patterns | `/planning` for AI features |
| `code-review-ai-specific.md` | AI-specific issues | `/code-review` (5th agent) |
| `memory-curator.md` | Auto-suggest lessons for `memory.md` | `/commit` or `/system-review` |

---

## Phase 5: Consolidate Guides

### 5A: Create Consolidated Guide

**New file**: `reference/swarm-ubs-setup.md` (~200 lines)

### 5B: Update Existing Guides

| Guide | Update |
|-------|--------|
| `reference/validation-discipline.md` | Remove system-review refs |
| `reference/piv-loop-practice.md` | Add research agent integration examples |

---

## Phase 6: Update Core Files

### 6A: AGENTS.md
- Command table: 17 → 8 rows
- Agent table: 16 → 11 agents
- Guide table: 16 → 11 rows
- Add "Solo Developer Mode" note + "Agent Ecosystem" section

### 6B: sections/02_piv_loop.md
- Update workflow diagram with enhanced `/system-review`
- Add research agent integration notes

### 6C: templates/STRUCTURED-PLAN-TEMPLATE.md
- Keep 700-1000 lines minimum
- Add inline examples to all 7 major sections
- Add checklists per section

---

## STEP-BY-STEP TASKS

### Task 1: Backup
```bash
git checkout -b system-simplification-backup
git push origin system-simplification-backup
git checkout master
```
**VALIDATE**: `git branch` shows `system-simplification-backup`

### Task 2: Cut Orphaned Agents (5 files)
```bash
rm .opencode/agents/specialist-*.md
rm .opencode/agents/test-generator.md
```
**VALIDATE**: `ls .opencode/agents/` shows 12 files

### Task 3: Cut Unused Commands (9 files)
```bash
rm .opencode/commands/create-prd.md .opencode/commands/create-pr.md .opencode/commands/rca.md .opencode/commands/implement-fix.md .opencode/commands/init-c.md .opencode/commands/agents.md .opencode/commands/end-to-end-feature.md .opencode/commands/execution-report.md .opencode/commands/system-review.md
```
**VALIDATE**: `ls .opencode/commands/` shows 8 files

### Task 4: Cut Unused Guides (6 files)
```bash
rm reference/SWARMTOOLS-*.md reference/PRACTICAL-SWARM-UBS-SETUP.md reference/AUTONOMOUS-SWARM-ECOSYSTEM.md reference/swarmtools-integration.md reference/bailian-coding-plan-setup.md
```
**VALIDATE**: `ls reference/` shows 10 files

### Task 5: Cut Unused Templates (3 files)
```bash
rm templates/SUB-PLAN-TEMPLATE.md templates/PLAN-OVERVIEW-TEMPLATE.md templates/COMMAND-TEMPLATE.md
```
**VALIDATE**: `ls templates/` shows 5 files

### Task 6: Update Research Agents (2 files)
- Update `research-codebase.md` with Archon tools + improved instructions
- Update `research-external.md` with Archon tools + improved instructions
**VALIDATE**: Both agents have `archon_rag_*` tools in frontmatter

### Task 7: Integrate Research into `/planning`
- Update Phase 2-3 to call `@research-codebase` and `@research-external`
- Merge Phase 3b into Phase 3
- Update Phase 4 synthesis for structured output
**VALIDATE**: `/planning test-feature` successfully delegates to research agents

### Task 8: Create Enhanced `/system-review`
- Create `scripts/analyze-plan-diff.js`
- Create `templates/MEMORY-SUGGESTION-TEMPLATE.md`
- Create `templates/PLAN-QUALITY-ASSESSMENT.md`
- Replace `.opencode/commands/system-review.md` with 7-step enhanced version
**VALIDATE**: `/system-review` runs all 7 steps

### Task 9: Add New Agents (3 files)
- Create `research-ai-patterns.md`
- Create `code-review-ai-specific.md`
- Create `memory-curator.md`
**VALIDATE**: All 3 agents have complete 5-component structure

### Task 10: Create Consolidated Guide
- Create `reference/swarm-ubs-setup.md` (~200 lines)
**VALIDATE**: Guide covers quick start + full setup + troubleshooting

### Task 11: Update Guides (2 files)
- Update `reference/validation-discipline.md`
- Update `reference/piv-loop-practice.md`
**VALIDATE**: No broken references to cut files

### Task 12: Update AGENTS.md
- Update all tables (commands, agents, guides)
- Add "Solo Developer Mode" note
- Add "Agent Ecosystem" section
- Update Quick Start workflow
**VALIDATE**: `/prime` loads without errors

### Task 13: Update sections/02_piv_loop.md
- Update workflow diagram
- Add research agent integration notes
**VALIDATE**: No broken references

### Task 14: Update Plan Template
- Add inline examples to all 7 major sections
- Add checklists per section
**VALIDATE**: Template is 900-1100 lines with examples

### Task 15: Validation
```bash
/prime
/planning test-integration-feature
```
**VALIDATE**: Research agents called, plan is 700+ lines

---

## TESTING STRATEGY

### Unit Tests
- Each cut directory has correct remaining files
- Each new agent file has valid frontmatter
- Each new script runs without syntax errors

### Integration Tests
- `/planning` successfully delegates to research agents
- `/system-review` runs all 7 steps
- `/prime` loads without errors

### Edge Cases
- Research agents with no results — graceful handling
- Auto-diff with no plan file — clear error message
- Archon MCP unavailable — skip gracefully

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
ls .opencode/agents/ | wc -l
ls .opencode/commands/ | wc -l
ls reference/ | wc -l
ls templates/ | wc -l
```

### Level 2: File Existence
```bash
test -f .opencode/commands/planning.md && echo "OK" || echo "MISSING"
test -f .opencode/commands/system-review.md && echo "OK" || echo "MISSING"
test -f scripts/analyze-plan-diff.js && echo "OK" || echo "MISSING"
```

### Level 3: Script Validation
```bash
node --check scripts/analyze-plan-diff.js
```

### Level 4: Integration Tests
```bash
/prime
/planning test-feature
```

### Level 5: Manual Validation
- Review cut files — confirm none are needed
- Review new agents — confirm useful output format
- Test `/system-review` with recent feature

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)
- [ ] All 15 tasks completed
- [ ] All validation commands pass
- [ ] New agents have complete structure
- [ ] No broken references in kept files

### Runtime (verify after testing)
- [ ] `/planning` works with research agent integration
- [ ] `/system-review` generates useful reports
- [ ] `/prime` loads without errors
- [ ] No regressions in existing workflows

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions
- Research agents integrated (not cut) — preserves context window isolation
- `/system-review` enhanced — auto-diff + code-review re-run + memory suggestions
- Plan length kept at 700-1000 — AI needs context
- 3 new agents added — abc scaling for Ollama/Model Studio

### Risks
- Research agent integration may need tuning — test thoroughly in Task 15
- New agents may become orphaned — measure usage after 5-10 features
- Auto-diff script may have edge cases — standalone, can run manually

### Confidence Score: 8.5/10
- **Strengths**: Evidence-based cuts, preserves differentiation, maximizes agent ecosystem
- **Uncertainties**: Research agent delegation quality, new agent utility
- **Mitigations**: Backup branch, all cuts reversible, test integration thoroughly
