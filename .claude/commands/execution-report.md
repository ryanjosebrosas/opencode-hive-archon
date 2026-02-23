---
description: Generate implementation report for system review
---

# Execution Report

**IMPORTANT**: Run this command in the SAME conversation context as the implementation — before any validation or commit. The AI has full memory of what happened during implementation, making the report accurate and detailed.

Review and deeply analyze the implementation you just completed.

## Context

Reflect on:

- What you implemented
- How it aligns with the plan
- What challenges you encountered
- What diverged and why

## Generate Report

Save to: `requests/execution-reports/[feature-name]-report.md`

### Meta Information

- Plan file: [path to plan that guided this implementation]
- Files added: [list with paths]
- Files modified: [list with paths]
- Lines changed: +X -Y

### Validation Results

- Syntax & Linting: PASS/FAIL [details if failed]
- Type Checking: PASS/FAIL [details if failed]
- Unit Tests: PASS/FAIL [X passed, Y failed]
- Integration Tests: PASS/FAIL [X passed, Y failed]

### What Went Well

List specific things that worked smoothly:

- [concrete examples]

### Challenges Encountered

List specific difficulties:

- [what was difficult and why]

### Divergences from Plan

For each divergence, document:

**[Divergence Title]**

- Planned: [what the plan specified]
- Actual: [what was implemented instead]
- Reason: [why this divergence occurred]
- Type: [Better approach found | Plan assumption wrong | Security concern | Performance issue | Other]

### Skipped Items

List anything from the plan that was not implemented:

- [what was skipped]
- Reason: [why it was skipped]

### Recommendations

Based on this implementation, what should change for next time?

- Plan command improvements: [suggestions]
- Execute command improvements: [suggestions]
- CLAUDE.md additions: [suggestions]
