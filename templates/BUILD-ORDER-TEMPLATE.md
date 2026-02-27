# Build Order — {Project Name}

Generated: {date}
Status: 0/{total} complete

---

## Layer 0: Foundations

- [ ] `01` **{spec-name}** ({light|standard|heavy}) — {1-line purpose}
  - depends: none
  - touches: {files created/modified}
  - acceptance: {concrete test that proves it works}

- [ ] `02` **{spec-name}** ({light|standard|heavy}) — {1-line purpose}
  - depends: 01
  - touches: {files}
  - acceptance: {test}

## Layer 1: Data

- [ ] `03` **{spec-name}** ({light|standard|heavy}) — {1-line purpose}
  - depends: 01, 02
  - touches: {files}
  - acceptance: {test}

## Layer 2: Services

- [ ] `04` **{spec-name}** ({light|standard|heavy}) — {1-line purpose}
  - depends: 02, 03
  - touches: {files}
  - acceptance: {test}

## Layer 3: Interface

- [ ] `05` **{spec-name}** ({light|standard|heavy}) — {1-line purpose}
  - depends: 04
  - touches: {files}
  - acceptance: {test}

## Layer 4: Integration

- [ ] `06` **{spec-name}** ({light|standard|heavy}) — {1-line purpose}
  - depends: 04, 05
  - touches: {files}
  - acceptance: {test}

---

## Complexity Guide

| Tag | Plan Size | When |
|-----|-----------|------|
| `light` | ~100 lines | Scaffolding, config, simple CRUD, well-known patterns |
| `standard` | ~300 lines | Services, integrations, moderate business logic |
| `heavy` | ~700 lines | Core algorithms, AI/ML, complex orchestration |

## Spec Format Reference

Each spec must have:
- **Number** — Sequential, determines default build order within a layer
- **Name** — Short kebab-case identifier
- **Depth tag** — light, standard, or heavy
- **Purpose** — One line describing what this spec delivers
- **depends** — List of spec numbers that must be `[x]` before this can start
- **touches** — Files this spec will create or modify (helps detect conflicts)
- **acceptance** — Concrete, verifiable test that proves the spec is complete
