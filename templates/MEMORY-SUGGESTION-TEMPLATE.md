# Memory Suggestion Generator

Use this template to auto-generate `memory.md` entries from execution report divergences and issues.

## Input

- Execution report: `requests/execution-reports/{feature}-report.md`
- System review: `requests/system-reviews/{feature}-review.md`

## Extraction Process

### Step 1: Identify Lessons

Read the execution report and extract:

1. **Divergences** — Any "Divergences from Plan" entries
2. **Challenges** — From "Issues & Notes" section
3. **Workarounds** — Any "had to", "discovered", "unexpectedly" statements
4. **Gotchas** — Any "should have", "wish we knew", "turns out" statements

### Step 2: Categorize Each Lesson

| Category | When to Use | Example |
|----------|-------------|---------|
| **gotcha** | Pitfalls, edge cases, "watch out for" items | "Library X incompatible with Y version" |
| **pattern** | Successful approaches to replicate | "Service pattern with dependency injection" |
| **decision** | Architecture/tech choices with rationale | "Chose JWT over OAuth2 for simplicity" |
| **anti-pattern** | What not to do, with explanation | "Don't skip error hierarchy for 'simplicity'" |

### Step 3: Generate Memory Entry

For each lesson, create:

```markdown
### {Date}: {Short Title}

**Category:** {gotcha|pattern|decision|anti-pattern}

**What:** {one-liner describing the situation}

**Why:** {why this matters / impact on implementation}

**Pattern:** (if applicable)
```
{code pattern or configuration example}
```

**Avoid:** (if applicable)
```
{what not to do / anti-pattern example}
```

**Applied to:**
- AGENTS.md: [{section to update or "new section needed"}]
- Plan template: [{section to enhance}]
- Commands: [{command to update}]
```

### Step 4: Sort by Category

Group memory entries for easy insertion:

```markdown
## Gotchas
{all gotcha entries}

## Patterns
{all pattern entries}

## Decisions
{all decision entries}

## Anti-Patterns
{all anti-pattern entries}
```

## Example Output

```markdown
---
### 2026-02-24: OAuth2 Library Compatibility

**Category:** gotcha

**What:** `passport-oauth2` incompatible with Express 5.x without adapter.

**Why:** Planning phase didn't verify library compatibility, caused mid-implementation pivot to JWT.

**Pattern:**
Before selecting auth approach, verify:
```bash
npm view passport-oauth2 peerDependencies
npm view passport-oauth2 dependencies
```

**Applied to:**
- Plan command: Phase 1 checklist — "Verify library compatibility"
- Plan template: Dependencies field — "Include version constraints"
```

---

### 2026-02-24: Error Hierarchy Pattern

**Category:** pattern

**What:** Custom error classes enable consistent error handling across layers.

**Why:** Skipping error hierarchy led to string-based errors inconsistent with codebase patterns.

**Pattern:**
```typescript
// src/errors/base.ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number = 500
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR', 400);
    this.name = 'ValidationError';
  }
}
```

**Avoid:**
```typescript
// Anti-pattern: string-based error handling
if (!user) {
  throw new Error('User not found'); // No structure, hard to handle
}
```

**Applied to:**
- AGENTS.md: Add "Error Handling Patterns" section
- Plan template: Patterns section — require "why this pattern" explanation
```

---

### 2026-02-24: JWT vs OAuth2 Decision Framework

**Category:** decision

**What:** JWT sessions chosen over OAuth2 for internal-only authentication.

**Why:** OAuth2 adds complexity (refresh tokens, scopes, grants) without benefit for single-client apps.

**Decision Framework:**
- **Use OAuth2** when: Multiple clients, third-party integrations, delegated access needed
- **Use JWT** when: Single client, internal users, simple auth sufficient

**Applied to:**
- Plan template: Solution Statement — require decision framework for architectural choices
- memory.md: Add to Architecture Patterns section
```

---

### 2026-02-24: Skipping Validation Steps

**Category:** anti-pattern

**What:** Skipping integration tests to save time creates false confidence.

**Why:** Unit tests pass but integration failures discovered in manual testing, requiring rework.

**Pattern:**
Always run full validation pyramid:
```bash
# Level 1: Lint
npm run lint

# Level 2: Unit
npm run test:unit

# Level 3: Integration
npm run test:integration

# Level 4: Manual
{feature-specific manual steps}
```

**Avoid:**
```bash
# Anti-pattern: skipping levels
npm run lint && npm run test:unit
# "Looks good, ship it" — integration bugs slip through
```

**Applied to:**
- Execute command: Step 4 — enforce all 5 validation levels
- Plan template: Validation Commands — mark as required (reject if incomplete)
```
```

## Integration with /system-review

The `/system-review` command should:

1. Extract divergences from execution report
2. Categorize each using Step 2
3. Generate memory entries using Step 3
4. Output in "Memory Suggestions" section of review
5. User reviews and approves before appending to `memory.md`

## Appending to memory.md

After user approval, append entries to `memory.md` under appropriate category:

```markdown
<!-- System Review Auto-Append -->

### {Date}: {Title}

{entry content}

---
```

**Important:** Don't auto-append without user approval. Present suggestions and let user decide what to keep.
