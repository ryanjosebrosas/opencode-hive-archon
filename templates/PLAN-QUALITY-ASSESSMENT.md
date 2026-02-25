# Plan Quality Assessment Guide

> Used by `/system-review` to assess plan file completeness
> Scores each major section: Complete / Partial / Missing

---

## Assessment Checklist

### Feature Description (lines ~10-30)
- [ ] Names specific systems/components
- [ ] Explains architectural relationships
- [ ] Mentions key capabilities
- [ ] One paragraph (3-5 sentences)

**Status:** Complete / Partial / Missing

---

### User Story (lines ~32-36)
- [ ] Specific user role (not just "user")
- [ ] Concrete action with specificity
- [ ] Clear benefit explaining "why"

**Status:** Complete / Partial / Missing

---

### Solution Statement (lines ~38-45)
- [ ] Each decision paired with "because" reasoning
- [ ] At least 2-3 decisions documented
- [ ] Trade-offs or alternatives mentioned

**Status:** Complete / Partial / Missing

---

### Relevant Codebase Files (lines ~50-60)
- [ ] File paths with line numbers
- [ ] "Why" explanation for each file
- [ ] At least 3-5 files referenced
- [ ] Patterns to mirror identified

**Status:** Complete / Partial / Missing

---

### Patterns to Follow (lines ~85-100)
- [ ] Actual code snippets from project
- [ ] file:line citations for each pattern
- [ ] "Why this pattern" explanation
- [ ] Gotchas/warnings included

**Status:** Complete / Partial / Missing

---

### Step-by-Step Tasks (lines ~145-175)
- [ ] All 7 fields present (ACTION, TARGET, IMPLEMENT, PATTERN, IMPORTS, GOTCHA, VALIDATE)
- [ ] Tasks in dependency order
- [ ] At least 5-10 tasks for medium complexity
- [ ] Executable VALIDATE commands

**Status:** Complete / Partial / Missing

---

### Testing Strategy (lines ~175-195)
- [ ] Unit test scope defined
- [ ] Integration test scenarios described
- [ ] Edge cases listed (at least 3)

**Status:** Complete / Partial / Missing

---

### Validation Commands (lines ~195-220)
- [ ] 5 levels present (Syntax, Unit, Integration, Manual, Additional)
- [ ] Executable commands for each level
- [ ] Commands match project tooling

**Status:** Complete / Partial / Missing

---

### Acceptance Criteria (lines ~220-245)
- [ ] Implementation criteria (verifiable during /execute)
- [ ] Runtime criteria (verifiable after testing)
- [ ] Specific, measurable criteria

**Status:** Complete / Partial / Missing

---

### Spec Lock and Approval Gate
- [ ] Spec Lock present (implementation mode, target repo, stack/framework, maturity, artifact type)
- [ ] User approval captured before final plan file write
- [ ] Assumptions explicitly labeled and justified

**Status:** Complete / Partial / Missing

---

## Scoring

| Section | Status | Points |
|---------|--------|--------|
| Feature Description | | /10 |
| User Story | | /10 |
| Solution Statement | | /10 |
| Relevant Files | | /15 |
| Patterns to Follow | | /15 |
| Step-by-Step Tasks | | /15 |
| Testing Strategy | | /10 |
| Validation Commands | | /10 |
| Acceptance Criteria | | /5 |
| Spec Lock + Approval | | /10 |
| **Total** | | **/110** |

---

## Quality Score Interpretation

- **98-110**: Excellent plan — ready for execution
- **78-97**: Good plan — minor gaps acceptable
- **56-77**: Incomplete — send back for revision
- **<56**: Reject — missing critical sections

---

## Usage

1. `/system-review` reads plan file
2. Assessor scores each section
3. Calculates overall Plan Quality Score
4. Includes score in system review report
5. If <70%, recommends plan template updates
