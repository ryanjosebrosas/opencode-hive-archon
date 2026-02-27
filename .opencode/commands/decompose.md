---
description: Break PRD into dependency-sorted spec list (BUILD_ORDER.md)
agent: build
---

# Decompose: PRD → Build Order

Break the MVP vision into concrete, dependency-sorted specs. Produces `specs/BUILD_ORDER.md` — the single source of truth for what to build and in what order.

## Usage

```
/decompose [focus area]
```

`$ARGUMENTS` — Optional: focus on a specific capability or re-decompose a section.

---

## Pipeline Position

```
/mvp → /prd → /pillars → /decompose → /build next (repeat) → /ship
```

This is Step 4. Requires a PRD document to exist (produced by `/prd`). Falls back to `mvp.md` if no PRD found. `/pillars` (Step 3) is optional but recommended — if run, its output guides spec grouping.

---

## Step 1: Read Product Requirements

1. Look for a PRD file (e.g., `PRD.md`, `docs/PRD.md`, or any file matching `*-prd.md`). This is the primary input — it contains detailed product requirements, user stories, and success criteria.
2. If no PRD found, fall back to `mvp.md`. If neither exists, report: "No PRD or mvp.md found. Run `/prd` first (or `/mvp` for a quick vision doc)." and stop.
3. Also read `mvp.md` if it exists alongside the PRD — it provides high-level vision context.
4. Read `specs/PILLARS.md` if it exists (produced by `/pillars`). When present, this is the primary structural guide — specs should be grouped by pillar rather than generic layers.

Extract the Core Capabilities / Feature Requirements — these become the high-level groupings for specs.

---

## Step 2: Decompose into Specs

For each Core Capability, break it into concrete buildable specs. Each spec must be:

- **Atomic** — one clear deliverable, implementable in one `/build` session
- **Testable** — has a concrete acceptance test
- **Dependency-aware** — explicitly lists what it needs built first

Think in layers:

| Layer | What | Examples |
|-------|------|---------|
| 0 | Foundations | Project scaffold, config, core types, database setup |
| 1 | Data | Models, schemas, migrations, basic CRUD |
| 2 | Services | Business logic, integrations, processing |
| 3 | API/Interface | Endpoints, CLI, MCP tools, UI components |
| 4 | Integration | Cross-cutting: auth wiring, error handling, logging |

**Cross-cutting concerns** (auth, logging, error handling) should be explicit specs in Layer 0 or 1, not spread across other specs.

**If `specs/PILLARS.md` exists:** Use the pillar definitions as the primary grouping structure instead of generic layers. Each pillar becomes a section in BUILD_ORDER.md. The layers table above is the fallback when no PILLARS.md is available.

---

## Step 3: Build Dependency Graph

For each spec, determine:
- `depends_on`: list of spec IDs that must be complete first
- `touches`: files/modules this spec will create or modify

**Check for issues:**
- Run cycle detection: no circular dependencies allowed
- Flag overlapping `touches` across same-layer specs (potential conflicts)
- Ensure every dependency target exists in the spec list

---

## Step 4: Assign Complexity Tags

Each spec gets a depth tag that controls plan size in `/build`:

| Tag | Plan Size | When |
|-----|-----------|------|
| `light` | ~100 lines | Scaffolding, config, simple CRUD, well-known patterns |
| `standard` | ~300 lines | Services, integrations, moderate business logic |
| `heavy` | ~700 lines | Core algorithms, AI/ML, complex orchestration |

Heuristic: if the spec touches >3 files or has >2 dependencies, bump up one level.

---

## Step 5: Topological Sort

Sort specs into build order:
1. Layer 0 specs first (no dependencies)
2. Then Layer 1 (depend only on L0)
3. Then Layer 2, 3, etc.
4. Within a layer, order by: fewer dependencies first, then alphabetical

Number each spec sequentially: `01`, `02`, `03`, ...

---

## Step 6: Write BUILD_ORDER.md

Create `specs/` directory if needed. Write `specs/BUILD_ORDER.md`:

```markdown
# Build Order — {Project Name}

Generated: {date} | Re-decomposed: {date if re-run}
Status: 0/{total} complete

## Layer 0: Foundations

- [ ] `01` **scaffold** (light) — Project structure, dependencies, config
  - depends: none
  - touches: pyproject.toml, src/__init__.py, config.py
  - acceptance: `ruff check` passes, project imports work

- [ ] `02` **core-types** (light) — Shared Pydantic models and types
  - depends: 01
  - touches: src/models.py, src/types.py
  - acceptance: `mypy` passes, models instantiate

## Layer 1: Data

- [ ] `03` **database** (standard) — Schema, migrations, connection pool
  - depends: 01, 02
  - touches: src/db.py, migrations/001_init.sql
  - acceptance: migration runs, CRUD smoke test passes

## Layer 2: Services

- [ ] `04` **retrieval** (heavy) — Vector search + reranking pipeline
  - depends: 02, 03
  - touches: src/services/retrieval.py, src/services/embeddings.py
  - acceptance: search returns relevant results for test query

## Layer 3: Interface

- [ ] `05` **api** (standard) — REST/MCP endpoints
  - depends: 04
  - touches: src/api.py, src/mcp_server.py
  - acceptance: curl test returns valid response
```

### Pillar-Aware Format (when specs/PILLARS.md exists)

When `PILLARS.md` is available, use pillar headers instead of layer headers:

```markdown
# Build Order — {Project Name}

Generated: {date} | Pillars: {N} | Status: 0/{total} complete

## Pillar 1: {Name from PILLARS.md}

- [ ] `01` **{spec-name}** ({depth}) — {description}
  - depends: none
  - touches: {files}
  - acceptance: {test}

- [ ] `02` **{spec-name}** ({depth}) — {description}
  - depends: 01
  - touches: {files}
  - acceptance: {test}

- [ ] `P1-GATE` **pillar-1-gate** (light) — Run Pillar 1 gate criteria from PILLARS.md
  - depends: 01, 02
  - acceptance: All gate criteria from PILLARS.md Pillar 1 pass

## Pillar 2: {Name from PILLARS.md}

- [ ] `03` **{spec-name}** ({depth}) — {description}
  - depends: 01, 02
  - touches: {files}
  - acceptance: {test}

- [ ] `P2-GATE` **pillar-2-gate** (light) — Run Pillar 2 gate criteria
  - depends: 03
  - acceptance: All gate criteria from PILLARS.md Pillar 2 pass
```

**Gate specs:** Automatically append a gate spec (P{N}-GATE) at the end of each pillar. Gate specs:
- Are tagged `light` (they run validation, not implementation)
- Depend on all specs in their pillar
- Their acceptance criteria come directly from PILLARS.md gate criteria
- Must pass before any spec from the next pillar can start

---

## Step 7: Human Validation

Present the BUILD_ORDER to the user as a summary:

```
Build Order: {N} specs across {L} layers

Layer 0 (Foundations): {count} specs — {names}
Layer 1 (Data):        {count} specs — {names}
Layer 2 (Services):    {count} specs — {names}
Layer 3 (Interface):   {count} specs — {names}

Estimated effort: {light}L + {standard}S + {heavy}H specs

Review the dependency graph. Any specs to add, remove, reorder, or re-tag?
```

When pillars are available, present the pillar-grouped summary instead:

```
Build Order: {N} specs across {P} pillars

Pillar 1 ({Name}):  {count} specs + gate — {spec names}
Pillar 2 ({Name}):  {count} specs + gate — {spec names}
...

Estimated effort: {light}L + {standard}S + {heavy}H specs + {P} gates
```

Wait for approval. Adjust if requested.

---

## Step 8: Council Validation (Optional)

If the project has >10 specs or complex dependencies, suggest running a council:

```
This decomposition has {N} specs with complex dependencies.
Run /council to get multi-model validation? [y/n]
```

If yes, dispatch BUILD_ORDER.md to `/council` for critique.

---

## Re-Decompose (Mid-Project)

`/decompose` can be re-run at any time. When re-running:

1. Read existing `specs/BUILD_ORDER.md`
2. Preserve completed specs (marked `[x]`)
3. Re-analyze remaining specs against actual codebase state
4. Flag any completed specs whose definitions changed
5. Ask human to confirm changes before overwriting

---

## Notes

- Keep specs small — if one feels too big, split it
- `depends_on` should reference spec numbers, not names
- `touches` helps detect conflicts between parallel specs
- The build order is committed to git — it's a living document
- Foundation specs should be genuinely foundational (shared by 2+ later specs)
