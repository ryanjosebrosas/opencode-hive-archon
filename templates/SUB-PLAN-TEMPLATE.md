# Sub-Plan {NN}: {Phase Name}

> **Parent Plan**: `requests/{feature}-plan-overview.md`
> **Sub-Plan**: {NN} of {total}
> **Phase**: {Phase Name}
> **Tasks**: {N}
> **Estimated Context Load**: {Low / Medium}
>
> **Target Length**: This sub-plan should be **500-700 lines**. Sub-plans must be
> self-contained — the execution agent has no memory of previous sub-plans. Every section
> must contain feature-specific content. Include full context references, pattern examples
> with code snippets, and detailed task specifications. Complex phases should target 700 lines.

---

## Scope

This sub-plan implements **{phase description}**. For full feature context, architecture
decisions, and shared patterns, see the overview file.

**What this sub-plan delivers**:
- {Deliverable 1}
- {Deliverable 2}
- {Deliverable 3}

**Prerequisites from previous sub-plans**:
- {What must exist before this sub-plan runs — or "None (first sub-plan)" }

---

## CONTEXT FOR THIS SUB-PLAN

> Only the files and docs relevant to THIS sub-plan's tasks. For shared context
> (patterns, documentation, memories), see the overview's CONTEXT REFERENCES section.

### Files to Read Before Implementing

- `path/to/file` (lines X-Y) — Why: {relevant to this phase}
- `path/to/file` (lines X-Y) — Why: {relevant to this phase}

### Files Created by Previous Sub-Plans

> Skip this section for sub-plan 01. For later sub-plans, list files created
> by earlier sub-plans that this one depends on.

- `path/to/file` — Created in sub-plan {NN}: {what it contains}

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.
>
> **Action keywords**: CREATE (new files), UPDATE (modify existing), ADD (insert new functionality),
> REMOVE (delete deprecated code), REFACTOR (restructure without changing behavior), MIRROR (copy pattern)

### {ACTION} `{target_file_path}`

- **IMPLEMENT**: {what to implement — code-level detail}
- **PATTERN**: {reference to codebase pattern — file:line}
- **IMPORTS**: {exact imports needed, copy-paste ready}
- **GOTCHA**: {known pitfalls and how to avoid them}
- **VALIDATE**: `{executable command to verify task completion}`

### {ACTION} `{target_file_path}`

- **IMPLEMENT**: {what to implement — code-level detail}
- **PATTERN**: {reference to codebase pattern — file:line}
- **IMPORTS**: {exact imports needed, copy-paste ready}
- **GOTCHA**: {known pitfalls and how to avoid them}
- **VALIDATE**: `{executable command to verify task completion}`

{Continue for all tasks in this sub-plan (5-8 tasks max)...}

---

## VALIDATION COMMANDS

> Only validations for THIS sub-plan's tasks.

### Syntax & Structure
```bash
{commands to verify files exist and are well-formed}
```

### Content Verification
```bash
{commands to verify key content is present in modified/created files}
```

### Cross-Reference Check
```bash
{commands to verify references between files are correct}
```

---

## SUB-PLAN CHECKLIST

- [ ] All {N} tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] No broken references to other files

---

## ACCEPTANCE CRITERIA

> Per-sub-plan criteria. Feature-wide criteria are in the overview.

- [ ] All deliverables listed in Scope section are complete
- [ ] All task validations passed
- [ ] No regressions in files modified
- [ ] {Add sub-plan-specific criteria here}

---

## HANDOFF NOTES

> What the NEXT sub-plan needs to know about what was done here.
> This section is critical — the next sub-plan runs in a fresh conversation
> with no memory of this one. Be explicit about state left behind.

### Files Created
- `path/to/file` — {what it contains, key exports/sections}

### Files Modified
- `path/to/file` — {what changed, new sections added}

### Patterns Established
- {Pattern name}: {brief description of pattern that later sub-plans should follow}

### State for Next Sub-Plan
- {Any important state, configuration, or context the next sub-plan needs}
- {E.g., "New template created at X — sub-plan 02 references it in command Y"}
