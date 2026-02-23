# Plan Quality Assessment Guide

Use this guide to assess plan completeness during `/system-review` Step 2.

## Assessment Criteria

For each template section, check for **required elements**. Mark as:

- **Complete** — All required elements present with feature-specific content
- **Partial** — Some elements present but missing details or generic
- **Missing** — Section empty or contains only placeholder text

## Section Checklist

### 1. Solution Statement

**Required elements:**
- [ ] At least 2 decisions documented
- [ ] Each decision includes "because" reasoning
- [ ] Decisions are feature-specific (not generic)

**Example Complete:**
```markdown
## Solution Statement

- Decision 1: Use JWT sessions instead of OAuth2 — because OAuth2 library incompatible with Express 5.x
- Decision 2: Implement error hierarchy — because existing codebase uses pattern for consistent handling
- Decision 3: Cache user data in Redis — because frequent DB queries identified as bottleneck
```

**Example Partial:**
```markdown
## Solution Statement

We will implement authentication using best practices.
```

**Assessment:** Partial — no specific decisions with rationale

---

### 2. Relevant Codebase Files

**Required elements:**
- [ ] At least 2 file references
- [ ] Each includes line numbers (file:line or file:line-line)
- [ ] Each includes "Why" explanation

**Example Complete:**
```markdown
### Relevant Codebase Files

- `src/services/user.service.ts` (lines 15-45) — Why: Contains service pattern we'll mirror
- `src/routes/auth.routes.ts` (lines 10-30) — Why: Shows route registration approach
- `src/middleware/auth.middleware.ts` (lines 5-25) — Why: JWT validation pattern to reuse
```

**Example Partial:**
```markdown
### Relevant Codebase Files

- `src/services/user.service.ts` — service pattern
- `src/routes/auth.routes.ts`
```

**Assessment:** Partial — missing line numbers and "Why" explanations

---

### 3. Patterns to Follow

**Required elements:**
- [ ] At least 1 pattern with actual code snippet
- [ ] Snippet is from the project (not external)
- [ ] Includes "Why this pattern" explanation
- [ ] Includes "Common gotchas" warnings

**Example Complete:**
```markdown
### Patterns to Follow

**Service Pattern** (from `src/services/user.service.ts:15-45`):
```typescript
export class UserService {
  constructor(
    private userRepository: UserRepository,
    private cacheService: CacheService
  ) {}

  async findById(id: string): Promise<User> {
    // Check cache first
    const cached = await this.cacheService.get(`user:${id}`);
    if (cached) return cached;

    // Fallback to database
    const user = await this.userRepository.findById(id);
    await this.cacheService.set(`user:${id}`, user, 300);
    return user;
  }
}
```
- Why this pattern: Dependency injection enables testing, caching pattern reduces DB load
- Common gotchas: Always inject interfaces, not implementations; cache TTL must be specified
```

**Example Partial:**
```markdown
### Patterns to Follow

**Service Pattern**: We'll follow the existing service pattern with dependency injection.
```

**Assessment:** Partial — no code snippet, no gotchas

---

### 4. Step-by-Step Tasks

**Required elements:**
- [ ] All tasks have ACTION keyword (CREATE/UPDATE/ADD/REMOVE/REFACTOR/MIRROR)
- [ ] All tasks have TARGET file path
- [ ] All tasks have IMPLEMENT description
- [ ] All tasks have PATTERN reference
- [ ] All tasks have IMPORTS specified
- [ ] All tasks have GOTCHA warnings
- [ ] All tasks have VALIDATE command

**Assessment Formula:**
```
Task Completeness = (tasks with all 7 fields) / (total tasks) × 100

Complete: 100%
Partial: 70-99%
Missing: <70%
```

---

### 5. Validation Commands

**Required elements:**
- [ ] Level 1: Syntax & Style commands (lint, format)
- [ ] Level 2: Unit Tests command
- [ ] Level 3: Integration Tests command
- [ ] Level 4: Manual Validation steps
- [ ] Level 5: Additional Validation (optional but should be populated)
- [ ] All commands are executable (not placeholders)

**Example Complete:**
```markdown
## Validation Commands

### Level 1: Syntax & Style
```bash
npm run lint
npm run format:check
```

### Level 2: Unit Tests
```bash
npm run test:unit -- src/services/auth.service.test.ts
```

### Level 3: Integration Tests
```bash
npm run test:integration -- tests/integration/auth-flow.test.ts
```

### Level 4: Manual Validation
```bash
# Start server and test endpoints
npm run dev
# POST /auth/login with valid credentials → 200 OK + JWT
# POST /auth/login with invalid credentials → 401 Unauthorized
```

### Level 5: Additional Validation
```bash
# UBS bug scanner
ubs . --fail-on-warning
```
```

**Example Missing:**
```markdown
## Validation Commands

### Level 1: Syntax & Style
```bash
npm run lint
```
```

**Assessment:** Missing — only 1 of 5 levels populated

---

### 6. Acceptance Criteria

**Required elements:**
- [ ] Split into "Implementation" and "Runtime" subsections
- [ ] Implementation items are checkboxes
- [ ] Runtime items are checkboxes
- [ ] At least 3 Implementation criteria
- [ ] At least 2 Runtime criteria

**Example Complete:**
```markdown
## Acceptance Criteria

### Implementation (verify during execution)

- [ ] Feature implements all specified functionality
- [ ] Code follows project conventions and patterns
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage meets project requirements
- [ ] Documentation updated (if applicable)

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify end-to-end workflows
- [ ] Feature works correctly in manual testing
- [ ] No regressions in existing functionality
```

**Example Partial:**
```markdown
## Acceptance Criteria

- [ ] Feature works
- [ ] Tests pass
```

**Assessment:** Partial — not split, too generic, insufficient criteria

---

### 7. Notes (Confidence Score)

**Required elements:**
- [ ] Confidence Score X/10
- [ ] Strengths list
- [ ] Uncertainties list
- [ ] Mitigations for uncertainties

**Example Complete:**
```markdown
## Notes

### Confidence Score: 8/10

**Strengths:**
- Clear requirements from user
- Existing patterns well-documented in codebase
- Dependencies verified compatible

**Uncertainties:**
- User traffic patterns unknown (could impact caching strategy)
- Third-party API rate limits not confirmed

**Mitigations:**
- Start with conservative cache TTL (5 min), adjust based on metrics
- Add rate limiting middleware as precaution
```

**Assessment:** Complete — all elements present

---

## Overall Plan Quality Score

Calculate:

```
Plan Quality Score = (% of sections marked Complete)

90-100%: Excellent plan
70-89%:  Good plan (minor gaps)
50-69%:  Fair plan (needs improvement)
<50%:    Poor plan (reject, send back to planning)
```

## Red Flags

**Reject plan if any of these are Missing:**

1. Step-by-Step Tasks (cannot execute without tasks)
2. Validation Commands (cannot verify without validation)
3. Solution Statement (unclear what to build)

**Send back for revision if:**

1. More than 3 sections are Partial or Missing
2. Any "Red Flag" section is Partial
3. Plan is under 700 lines (per template requirement)

## Assessment Output Format

```markdown
### Plan Quality Assessment

```
Section                          | Status    | Notes
---------------------------------|-----------|---------------------------
Solution Statement               | Complete  | 3 decisions with rationale
Relevant Codebase Files          | Partial   | Missing line numbers in 2 refs
Patterns to Follow               | Complete  | 2 patterns with code snippets
Step-by-Step Tasks               | Complete  | All 7 fields present in 12/14 tasks
Validation Commands              | Missing   | Only 2 of 5 levels populated
Acceptance Criteria              | Complete  | Properly split Implementation/Runtime
Notes (Confidence Score)         | Partial   | Missing mitigations for uncertainties

Plan Quality Score: 57% (4/7 sections Complete)
```

**Recommendation:** Send back for revision — Validation Commands missing, multiple sections Partial
```
