---
description: Define or refine the product MVP vision
agent: build
---

# MVP: Define Product Vision

Establish or update the product vision that drives everything else. This is the first command in the build pipeline.

## Usage

```
/mvp [topic or direction]
```

`$ARGUMENTS` — Optional: specific direction, pivot, or aspect to focus on.

---

## Pipeline Position

```
/mvp → /decompose → /build next (repeat) → /ship
```

This is Step 1. Output feeds directly into `/decompose`.

---

## Step 1: Check Existing MVP

Check if `mvp.md` exists at the project root.

**If exists:**
1. Read `mvp.md` fully.
2. Summarize the current vision in 2-3 sentences.
3. Ask: "Is this still the direction, or do you want to revise?"
4. If satisfied → skip to Step 3 (confirm and done).
5. If revising → continue to Step 2 with the revision context.

**If doesn't exist:**
1. Continue to Step 2 (discovery).

---

## Step 2: Vision Discovery

Have a focused conversation to establish the big idea. Ask at most 3-4 questions:

1. **What** are you building? (one sentence)
2. **Who** is it for? (primary user)
3. **What problem** does it solve? (the pain point)
4. **What does "done" look like?** (2-3 success signals)

If `$ARGUMENTS` provides enough context, synthesize directly — don't re-ask what's already clear.

---

## Step 3: Write mvp.md

Write or update `mvp.md` at the project root using this structure:

```markdown
# {Product Name}

## Big Idea

{2-3 sentences: what it is, why it matters, what makes it different}

## Users and Problems

- **Primary user**: {who}
- **Problem 1**: {pain point}
- **Problem 2**: {pain point}

## Core Capabilities (Foundation Bricks)

1. {Capability — one line each}
2. {Capability}
3. {Capability}
4. {Capability}

## Out of Scope (for MVP)

- {Deferred item}
- {Deferred item}

## MVP Done When

- [ ] {Concrete success signal 1}
- [ ] {Concrete success signal 2}
- [ ] {Concrete success signal 3}
```

---

## Step 4: Confirm

Show the user the mvp.md content and ask:

```
MVP defined. Next step: /decompose to break this into buildable specs.

Proceed with /decompose? [y/n]
```

---

## Notes

- Keep mvp.md SHORT — under 40 lines. It's a compass, not a spec.
- Core Capabilities should be 4-8 items max. Each becomes specs in /decompose.
- "MVP Done When" criteria are checked by /ship at the end.
- If the user already has a clear mvp.md and just wants to build, skip discovery and confirm quickly.
