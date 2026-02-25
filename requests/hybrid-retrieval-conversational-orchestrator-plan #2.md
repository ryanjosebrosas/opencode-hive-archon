# Feature: Hybrid Retrieval Conversational Orchestrator Foundation (Pebble)

## Feature Description

Build a conversation-first retrieval foundation that separates retrieval and planning responsibilities while sharing a strict output contract. The runtime orchestration must emit deterministic fallback behavior and explicit next actions for all branches. This plan implements a minimal slice to validate routing and contract behavior, not full production rollout.

## User Story

As a solo operator, I want retrieval and planning to be distinct but contract-aligned, so the system can reliably return context with actionable next steps even when confidence is low.

## Problem Statement

Current direction risks inheriting old markdown-first assumptions and mixed responsibility boundaries. Retrieval and planning are conceptually different concerns, but without a shared contract and deterministic fallback system, behavior can drift and become hard to maintain.

## Solution Statement

Use a contract-first orchestrator design:
- Decision 1: Runtime is conversation-first and agent-driven, because markdown should document behavior, not define runtime behavior.
- Decision 2: Retrieval and planning are separate modules, because this reduces coupling and improves debugability.
- Decision 3: Every path emits `context_packet` and `next_action`, because users need explicit actionability in low-confidence states.
- Decision 4: Mem0 native rerank remains default on Mem0 path and external rerank is default off there, because duplicate reranking is redundant unless proven beneficial.

## Feature Metadata

- Feature Type: New Capability
- Estimated Complexity: Medium
- Primary Systems Affected: orchestrator routing, retrieval contracts, fallback behavior, provider adapter policy
- Dependencies: existing retrieval providers (Mem0, Supabase), optional Graphiti integration hooks

---

## CONTEXT REFERENCES

### Relevant Codebase Files

- `backend/src/second_brain/agents/recall.py` - retrieval orchestration baseline to mirror
- `backend/src/second_brain/services/memory.py` - primary memory provider contract and behavior
- `backend/src/second_brain/services/storage.py` - hybrid retrieval and data access behavior
- `backend/src/second_brain/services/graphiti_memory.py` - graph memory adapter pattern
- `backend/src/second_brain/mcp_server.py` - tool exposure and contract boundaries
- `backend/src/second_brain/schemas.py` - output schema conventions
- `backend/src/second_brain/deps.py` - dependency wiring pattern

### New Files to Create

- `docs/architecture/conversational-retrieval-contract.md` - canonical runtime contract and branch semantics
- `docs/architecture/retrieval-planning-separation.md` - responsibility boundary and data flow
- `docs/architecture/retrieval-overlap-policy.md` - duplicate capability avoidance policy
- `backend/src/second_brain/contracts/context_packet.py` - typed contract models for context packet and next action
- `backend/src/second_brain/orchestration/retrieval_router.py` - route policy and mode selection
- `backend/src/second_brain/orchestration/fallbacks.py` - deterministic branch emitters

### Related Memories

- Memory: user prefers step-by-step systemized delivery over trial-and-error.
- Memory: user wants proactive discovery and options matrix before lock-in.
- Memory: user wants timeline fields removed from planning artifacts.

### Relevant Documentation

- Mem0 docs: provider capabilities and managed memory behavior
- Graphiti docs: optional graph retrieval patterns and operational considerations
- Existing repo README: architecture, provider model, and fallback posture

### Patterns to Follow

Pattern 1: adapter-based provider boundary
- Why this pattern: preserves flexibility and prevents provider lock-in.
- Gotcha: keep provider-specific semantics out of shared contract.

Pattern 2: deterministic branch outputs
- Why this pattern: required for predictable behavior and testability.
- Gotcha: avoid free-form fallback messages without branch codes.

Pattern 3: feature-flagged optional paths
- Why this pattern: enables safe incremental adoption of Graphiti.
- Gotcha: default flags must preserve current stable behavior.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Define canonical contracts and branch semantics.

Tasks:
- Create contract architecture docs.
- Define typed `context_packet` + `next_action` model.
- Define route/mode policy and overlap policy.

### Phase 2: Core Implementation

Implement minimal route/fallback orchestration slice.

Tasks:
- Add retrieval router with mode and provider selection.
- Add fallback emitters with branch-specific next actions.
- Add rerank policy guard to prevent duplicate rerank on Mem0 path.

### Phase 3: Integration

Integrate contracts into retrieval flow with minimal disruption.

Tasks:
- Wire contract models into recall pathway output.
- Ensure feature flags gate optional Graphiti path.
- Keep existing MCP/REST shape compatibility where needed.

### Phase 4: Testing and Validation

Validate deterministic behavior and route policy.

Tasks:
- Add branch scenario tests.
- Add routing policy tests.
- Run targeted flow checks for output consistency.

---

## STEP-BY-STEP TASKS

### CREATE docs/architecture/conversational-retrieval-contract.md

- IMPLEMENT: Define canonical contract schema, mode policy, branch semantics, and required output guarantees.
- PATTERN: backend contract documentation style used in existing architecture docs.
- IMPORTS: none
- GOTCHA: avoid embedding provider-specific fields in global contract.
- VALIDATE: `python -m pytest -q tests -k contract`

### CREATE docs/architecture/retrieval-planning-separation.md

- IMPLEMENT: Document retrieval vs planning responsibilities and message/data flow between them.
- PATTERN: existing architecture overview style from repo README and service docs.
- IMPORTS: none
- GOTCHA: do not duplicate low-level implementation details better placed in code docs.
- VALIDATE: `python -m pytest -q tests -k orchestrator`

### CREATE docs/architecture/retrieval-overlap-policy.md

- IMPLEMENT: Define capability overlap checks and default-on/default-off rules.
- PATTERN: policy-style docs with explicit decision tables.
- IMPORTS: none
- GOTCHA: ensure Mem0 rerank policy is explicit and unambiguous.
- VALIDATE: `python -m pytest -q tests -k rerank`

### CREATE backend/src/second_brain/contracts/context_packet.py

- IMPLEMENT: Add typed models for `ContextCandidate`, `ConfidenceSummary`, `ContextPacket`, and `NextAction`.
- PATTERN: existing Pydantic schema conventions in `backend/src/second_brain/schemas.py`.
- IMPORTS: `from pydantic import BaseModel, Field`, `from typing import Literal`
- GOTCHA: keep models stable and minimal; avoid speculative fields.
- VALIDATE: `python -m pytest -q tests -k context_packet`

### CREATE backend/src/second_brain/orchestration/retrieval_router.py

- IMPLEMENT: Add route selection function using mode + feature flags + provider availability.
- PATTERN: dependency/config access conventions from `backend/src/second_brain/deps.py`.
- IMPORTS: config/deps interfaces and route literals.
- GOTCHA: routing must be deterministic for same inputs.
- VALIDATE: `python -m pytest -q tests -k retrieval_router`

### CREATE backend/src/second_brain/orchestration/fallbacks.py

- IMPLEMENT: Add branch emitters for `EMPTY_SET`, `LOW_CONFIDENCE`, `CHANNEL_MISMATCH`, `RERANK_BYPASSED` that produce `next_action` consistently.
- PATTERN: existing error/result normalization style from agents.
- IMPORTS: context contract models.
- GOTCHA: branch codes must remain stable constants.
- VALIDATE: `python -m pytest -q tests -k fallback`

### UPDATE backend/src/second_brain/agents/recall.py

- IMPLEMENT: Integrate router and fallback emitters, emit contract-aligned output envelope.
- PATTERN: existing recall agent flow and output validator pattern.
- IMPORTS: new router/fallback modules and contract models.
- GOTCHA: preserve existing successful-path behavior while extending output structure.
- VALIDATE: `python -m pytest -q tests -k recall`

### UPDATE backend/src/second_brain/services/memory.py

- IMPLEMENT: Add explicit policy hook so Mem0 path marks provider-native rerank and avoids external duplicate rerank.
- PATTERN: existing service method options/config parameters.
- IMPORTS: existing config and service types.
- GOTCHA: do not break current API calls that omit rerank flags.
- VALIDATE: `python -m pytest -q tests -k memory`

### UPDATE backend/src/second_brain/services/voyage.py

- IMPLEMENT: Gate external rerank usage for non-Mem0 routes and maintain explicit opt-in path.
- PATTERN: existing rerank utility interface and call-site behavior.
- IMPORTS: existing rerank config/types.
- GOTCHA: avoid silent rerank suppression without metadata.
- VALIDATE: `python -m pytest -q tests -k voyage`

### UPDATE backend/src/second_brain/mcp_server.py

- IMPLEMENT: Ensure relevant tool outputs can expose or embed contract fields without breaking client compatibility.
- PATTERN: existing MCP tool response formatting style.
- IMPORTS: contract types where needed.
- GOTCHA: avoid backward-incompatible output removal.
- VALIDATE: `python -m pytest -q tests -k mcp`

### CREATE tests/test_context_packet_contract.py

- IMPLEMENT: Validate required fields and branch output shape.
- PATTERN: existing schema and service test structure.
- IMPORTS: contract models and fallback emitters.
- GOTCHA: tests should assert deterministic branch codes and next action fields.
- VALIDATE: `python -m pytest -q tests/test_context_packet_contract.py`

### CREATE tests/test_retrieval_router_policy.py

- IMPLEMENT: Validate deterministic routing under feature-flag and provider combinations.
- PATTERN: existing provider/config parameterized tests.
- IMPORTS: router + mocked deps/config.
- GOTCHA: include regression test for Mem0 duplicate-rerank policy.
- VALIDATE: `python -m pytest -q tests/test_retrieval_router_policy.py`

---

## TESTING STRATEGY

### Unit Tests

- Contract model validation tests.
- Router deterministic selection tests.
- Fallback emitter branch and next action tests.

### Integration Tests

- Recall flow integration using primary Mem0 path.
- Optional Graphiti route under feature flag.
- MCP output compatibility check for existing consumers.

### Edge Cases

- Empty candidate set from all providers.
- Top result below threshold but non-empty set.
- Provider available but rerank unavailable.
- Feature flag on with provider unavailable fallback.

---

## VALIDATION COMMANDS

### Level 1: Syntax and Style
```bash
ruff check backend tests
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain
```

### Level 3: Unit Tests
```bash
pytest tests/test_context_packet_contract.py tests/test_retrieval_router_policy.py -q
```

### Level 4: Integration Tests
```bash
pytest tests -k "recall or mcp or memory" -q
```

### Level 5: Manual Validation

1. Trigger recall in normal case and confirm `context_packet` + `next_action` present.
2. Trigger low-confidence case and confirm `LOW_CONFIDENCE` branch + actionable next step.
3. Enable Graphiti feature flag and confirm route decision metadata changes safely.
4. Confirm Mem0 path does not apply external rerank by default.

---

## ACCEPTANCE CRITERIA

### Implementation (during execution)

- [x] Shared context contract is implemented and used.
- [x] Retrieval and planning responsibilities are explicit and separated.
- [x] Deterministic fallback branches emit stable codes and next actions.
- [x] Mem0 duplicate rerank is prevented by default policy.
- [x] Optional Graphiti path is feature-flagged and non-breaking.

### Runtime (after testing)

- [x] Retrieval outputs are consistent across repeated runs with same inputs.
- [x] Fallback behavior is predictable and actionable in real usage.
- [x] Existing command behavior remains compatible while improved.

---

## COMPLETION CHECKLIST

- [x] Contract docs created
- [x] Route/fallback modules created
- [x] Recall flow integrated with new contract outputs
- [x] Rerank overlap policy enforced
- [x] Tests added and passing
- [ ] Manual branch validation completed

---

## NOTES

Key design decisions:
- Runtime should be conversation-first, not markdown-first.
- Keep provider logic behind adapters and policy tables.
- Prefer deterministic branch outputs over free-form fallback prose.

Risks:
- Coupling can creep back into recall flow if boundaries are not enforced.
- Feature-flag behavior may drift if not covered by tests.

Confidence Score: 8.5/10
- Strengths: clear contract direction, explicit redundancy policy, scoped implementation.
- Uncertainties: exact file-level integration details until target repo branch is inspected locally.
- Mitigations: begin with docs + typed models + router tests before deep integration.
