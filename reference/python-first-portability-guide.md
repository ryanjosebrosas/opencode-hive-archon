# Python-First Portability Guide

Use this guide when planning features that will be implemented in Python (often with PydanticAI) but must stay portable to other frameworks.

---

## 1) Default Runtime Policy

- **Default runtime**: Python-first for implementation speed and ecosystem maturity.
- **Default adapter**: PydanticAI is allowed as the first runtime adapter.
- **Non-negotiable**: Core contracts and domain logic must not depend on PydanticAI internals.

This is **Python-first**, not **Python-only**.

---

## 2) Contracts-First Rule

Define portable contracts before framework wiring:

- Request/response models
- Tool call and tool result envelopes
- State and event schemas
- Eval case/result schemas

Use Pydantic models to emit JSON Schema for neutral contracts.

Checklist:
- [ ] Schema versioning defined (SemVer or equivalent)
- [ ] Additive vs breaking changes documented
- [ ] No framework-native objects in contract layer

---

## 3) Port and Adapter Boundary

Use Protocol-style ports for framework neutrality.

Core layer depends on ports, adapters depend on frameworks.

Example boundary:
- `AgentRuntimePort`
- `ToolExecutorPort`
- `MemoryStorePort`
- `EvalRunnerPort`

Adapter examples:
- `PydanticAIRuntimeAdapter` (current)
- `OtherFrameworkRuntimeAdapter` (future)

Checklist:
- [ ] Domain imports no framework SDK modules
- [ ] Adapter owns framework-specific types
- [ ] Port signatures use neutral DTOs/contracts

---

## 4) Framework-Agnostic Eval Contract

Evals must survive adapter swaps.

Required:
- Same golden task dataset across adapters
- Same grading criteria across adapters
- Same pass threshold across adapters
- Trace fields mapped to a stable schema

`Eval Portability Check` in plans should answer:
- Can we run the same 10-30 tasks against another adapter with no dataset changes?

---

## 5) Anti-Lock-In Checklist

Before approving a plan:

- [ ] **Implementation Runtime Default** is declared
- [ ] **Portability Boundary** is declared
- [ ] **Adapter Swap Criteria** is declared
- [ ] **Eval Portability Check** is declared
- [ ] No direct framework types in domain contract definitions
- [ ] Migration path (adapter replacement scope) is documented

If any item is missing, the plan is incomplete.

---

## 6) Planning Prompt Add-on

Use these questions during `/planning`:

1. What is the implementation runtime default?
2. Which contracts must remain framework-agnostic if runtime changes?
3. What adapter swap can happen without changing core contracts?
4. How will eval parity be validated across adapters?

---

## 7) Common Failure Modes

- Treating Python-first as permission to couple domain logic to framework APIs
- Writing evals tied to one framework's trace format only
- Using framework-specific objects inside shared contracts
- Missing migration criteria, then discovering hidden coupling too late

Prevent these by enforcing portability fields in the plan template.
