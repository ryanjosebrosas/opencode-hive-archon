# Product Requirements Document (PRD)

# Product: Conversational Hybrid Retrieval Foundation (Pebble)

## Executive Summary

This pebble builds the retrieval and planning foundation for `second-brain-ultimatum` as a conversation-first system, not a markdown-first system. The runtime source of truth will be the orchestrator and agent contracts. Markdown remains useful for planning and auditing, but it does not define runtime behavior.

The selected direction is a hybrid stack with replaceable adapters:
- Primary: Mem0 + Supabase hybrid retrieval
- Optional fallback: Graphiti adapter behind feature flags
- Reranking policy: avoid duplicate layers; use Mem0 native rerank on Mem0 path, disable external rerank by default on that path

This brick delivers both specification and a minimal working alpha wiring slice to validate routing, fallback behavior, and contract consistency.

## Mission

Create a deterministic, conversation-first retrieval and planning foundation that:
- separates retrieval from planning responsibilities,
- standardizes output via a shared `context_packet`,
- emits explicit `next_action` on every branch,
- and supports provider flexibility through adapter boundaries.

Core principles:
1. Contract-first, provider-second.
2. No duplicate retrieval layers without A/B evidence.
3. Deterministic fallback with actionability.
4. Small validated slices over broad speculative buildout.

## Project Requirements Baseline (Spec Lock)

- Implementation Mode: both (spec + minimal working alpha)
- Target Repository: `https://github.com/ryanjosebrosas/second-brain-ultimatum`
- Stack/Framework: follow existing Python/FastAPI/Pydantic AI architecture
- Maturity Target: pebble foundation (pre-alpha infrastructure slice)
- Primary Artifacts: PRD + structured implementation plan

Technical boundaries:
- Architecture style: modular monolith with pluggable adapters
- Data/storage: Mem0 + Supabase/pgvector hybrid, optional Graphiti path
- Interfaces: MCP tools + internal orchestrator contracts
- Security baseline: existing env-based secret management and service wrappers
- Non-functional priorities: speed, quality, maintainability, stability/flexibility, cost

Delivery constraints:
- Team constraints: solo-developer-driven implementation
- Risk tolerance: medium (allow controlled feature flags, avoid irreversible lock-in)
- Must-have vs nice-to-have: focus on deterministic contract and routing validation first

## Target Users

Primary user:
- solo operator building memory-heavy agent workflows who needs consistent retrieval quality and predictable behavior.

Secondary user:
- maintainer iterating on orchestration and retrieval adapters with minimal rewrites.

Key needs:
- reliable context retrieval across varied query complexity,
- explicit next steps when retrieval confidence is low,
- ability to swap or combine providers without refactoring command semantics.

## MVP Scope (Pebble Scope)

### In Scope

- Define canonical conversation-first retrieval pipeline contract.
- Define separation of concerns:
  - retrieval responsibility,
  - planning/contextualization responsibility.
- Define shared output schema (`context_packet`) and required `next_action` envelope.
- Define deterministic fallback branches and branch-specific next actions.
- Define adapter policy for Mem0 primary + Graphiti optional fallback.
- Implement minimal alpha wiring sufficient to validate:
  - provider routing,
  - fallback emission,
  - branch determinism,
  - contract shape consistency.

### Out of Scope

- Full production hardening and complete observability pipeline.
- Large-scale Graphiti-first migration.
- End-to-end latency optimization and benchmark suite.
- Cross-team governance and SLA-oriented rollout.

## User Stories

1. As an operator, I want retrieval and planning to be distinct, so each stage is understandable and debuggable.
2. As an operator, I want every response path to include `next_action`, so low-confidence cases remain actionable.
3. As a maintainer, I want a shared `context_packet` contract, so adapter changes do not require command rewrites.
4. As a maintainer, I want feature-flagged provider routing, so Graphiti can be introduced safely.
5. As a product owner, I want deterministic fallback branches, so system behavior is predictable and auditable.

## Repository Evidence (Current Baseline)

From `second-brain-ultimatum` repository overview and README:
- Existing architecture already uses Mem0, Supabase hybrid retrieval, Voyage rerank, optional graph memory path.
- Existing interfaces include MCP server, REST API, and CLI.
- Existing services already emphasize pluggability and resilience wrappers.

Implication:
- This brick should extend and standardize current direction, not restart architecture.

## Alternatives Considered

| Option | Pros | Cons | Fit | Decision |
|---|---|---|---|---|
| A. Hybrid baseline + adapters | Fast to ship, strong flexibility, minimal rewrite | Some policy complexity | High | Selected |
| B. Graph-first OSS | High long-term flexibility | Higher near-term ops complexity | Medium | Rejected now |
| C. Managed-only Mem0 path | Fastest initial implementation | Higher provider lock risk | Medium | Rejected now |
| D. Full OSS vector+graph stack | Low lock-in | Slowest execution for pebble | Low | Rejected now |

## Capability Overlap Check

- Provider-native capabilities in use:
  - Mem0 native rerank
  - Mem0 filtering/search primitives
- External add-ons available:
  - external reranker for non-Mem0 path
  - hybrid fusion policy at orchestrator layer
- Default-on:
  - Mem0 native rerank for Mem0 path
  - deterministic fallback emission
- Default-off:
  - external rerank on Mem0 path
  - Graphiti path unless feature flag enabled
- Redundant layers removed:
  - default double-rerank removed to reduce latency/complexity

## Core Architecture and Patterns

### Runtime Model

Conversation-first runtime, contract-driven orchestration:

1. Input query arrives at orchestrator.
2. Orchestrator classifies mode and route.
3. Retrieval module collects and normalizes candidates.
4. Planning module contextualizes candidates to requested intent/output.
5. Confidence gates applied.
6. Fallback path selected deterministically when needed.
7. Output emits `context_packet` + `next_action`.

### Responsibility Split

- Retrieval:
  - fetch candidates,
  - score/fuse/rerank,
  - produce confidence metrics.

- Planning:
  - convert ranked context into actionable plan context,
  - infer and emit next step envelope,
  - preserve branch reason and assumptions.

### Required Contract (Minimum)

```json
{
  "context_packet": {
    "query": "string",
    "mode": "quick|balanced|precise",
    "route": "mem0|supabase|graphiti|hybrid",
    "candidates": [
      {
        "id": "string",
        "source": "string",
        "base_score": 0.0,
        "confidence": 0.0
      }
    ],
    "confidence_summary": {
      "top_score": 0.0,
      "threshold": 0.0,
      "branch": "OK|EMPTY_SET|LOW_CONFIDENCE|CHANNEL_MISMATCH|RERANK_BYPASSED"
    },
    "fallback_reason": "string|null",
    "final_context": ["string"]
  },
  "next_action": {
    "type": "answer|clarify|broaden_query|switch_mode|request_signal",
    "message": "string",
    "inputs_required": []
  }
}
```

## Fallback Policy (Deterministic)

Branch rules:
- `EMPTY_SET`: no candidates
- `LOW_CONFIDENCE`: best score under threshold
- `CHANNEL_MISMATCH`: relevant candidates but poor intent/channel fit
- `RERANK_BYPASSED`: rerank skipped due policy/budget/provider state

Each branch must return:
- stable branch code,
- explicit reason,
- user-visible next action,
- structured fields for logging later.

## Retrieval Modes

- `quick`: low latency, minimal post-processing
- `balanced`: default mode, robust fusion + threshold checks
- `precise`: stricter filtering and higher confidence requirement

## Technology Stack (This Brick)

- Python + Pydantic AI + FastAPI baseline
- Mem0 as primary memory provider
- Supabase/pgvector hybrid retrieval baseline
- Optional Graphiti adapter (off by default)
- Optional external reranker for non-Mem0 routes

## Security and Configuration

In scope:
- strict feature flagging for provider routes,
- environment-based configuration,
- safe fallback when optional providers unavailable.

Out of scope:
- deep auth/tenant model redesign,
- secret management platform migration.

## Success Criteria

Functional:
- Shared `context_packet` and `next_action` contract is defined and used by minimal wiring.
- Retrieval and planning responsibilities are separated in architecture and implementation notes.
- Deterministic fallback branches are implemented and testable.
- Mem0 path does not use duplicate reranker by default.
- Graphiti remains optional and replaceable via adapter boundary.

Quality:
- No contradictory retrieval semantics in updated docs/plans.
- Branch outputs are action-oriented and machine-parseable.
- Minimal alpha wiring validates route + fallback behavior end to end.

## Implementation Phases

### Phase 1: Contract Foundation
Goal: define contracts and branch rules.

Deliverables:
- canonical contract doc,
- fallback policy doc,
- mode and route policy table.

Validation:
- contract schema includes required keys,
- branch rules map to next actions.

### Phase 2: Adapter and Routing Slice
Goal: wire minimal orchestrator path with feature flags.

Deliverables:
- route decision layer,
- Mem0-first path,
- Graphiti optional hook,
- rerank policy guard.

Validation:
- Mem0 path avoids duplicate rerank,
- feature flag toggles route safely.

### Phase 3: Fallback and Output Determinism
Goal: ensure branch outputs are deterministic and actionable.

Deliverables:
- branch-specific next action emitters,
- test scenarios for each fallback branch.

Validation:
- scenario checks pass for all branch codes.

### Phase 4: Minimal Alpha Verification
Goal: confirm pebble behavior in realistic flows.

Deliverables:
- basic scenario runbook,
- evidence of route/fallback/output correctness.

Validation:
- manual and automated checks show stable behavior.

## Risks and Mitigations

1. Risk: Contract drift across modules.
   Mitigation: one canonical contract definition and mandatory cross-reference.

2. Risk: Provider complexity creeps into orchestration.
   Mitigation: strict adapter boundary and route policy table.

3. Risk: Latency regression from redundant processing.
   Mitigation: overlap policy with default-off duplicate reranking.

4. Risk: Graph path destabilizes early phases.
   Mitigation: keep Graphiti behind feature flags.

## Appendix

Related sources:
- `https://github.com/ryanjosebrosas/second-brain-ultimatum`
- `https://github.com/getzep/graphiti`
- `https://docs.mem0.ai`

Notes:
- This PRD intentionally avoids timeline fields.
- This PRD treats markdown artifacts as planning evidence, not runtime architecture.
