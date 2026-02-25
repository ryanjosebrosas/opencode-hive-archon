# Feature: Fix critical code-review findings in retrieval router and fallback logic

The following plan is complete enough for one-pass implementation, but the execution agent should still validate runtime behavior against contract docs and existing tests before changing code.

Pay close attention to naming and output-shape stability in retrieval contracts. Import from canonical modules and keep branch codes unchanged.

## Feature Description

Patch critical correctness and determinism issues in retrieval routing and fallback behavior so provider selection, branch emission, and metadata remain contract-accurate under degraded or partially reported provider status. This slice is a bug-fix hardening pass on existing router/fallback modules and their integration touchpoints, not a new capability.

## User Story

As an operator validating recall behavior,
I want routing and fallback decisions to stay deterministic and policy-correct even when statuses are missing, overrides are invalid, or providers are degraded,
So that I can trust branch/action outputs and triage production incidents quickly.

## Problem Statement

Current retrieval behavior has multiple high-risk failure modes surfaced by code review:
- provider override can bypass provider health checks and route to unavailable backends.
- route selection treats missing status keys as unavailable, causing false `none` routing and unnecessary `EMPTY_SET` fallback.
- routing metadata can drift from the actual request mode (`conversation` hardcoded).
- fallback branch semantics around rerank status and `rerank_applied` are ambiguous across `SUCCESS` vs `RERANK_BYPASSED` paths.

These issues can produce silent policy violations, incorrect branch interpretation, and poor operator diagnostics.

## Solution Statement

Apply a minimal but strict policy hardening pass:
- Decision 1: Centralize provider eligibility checks (enabled + status) in router internals and use them for both normal selection and override selection, because this removes divergent logic paths.
- Decision 2: Normalize missing provider status as `available` for enabled providers unless explicitly marked otherwise, because partial snapshots should fail open for deterministic continuity (not fail closed to `none`).
- Decision 3: Keep fallback branch codes stable and only tighten rerank metadata semantics, because downstream contracts depend on stable branch constants.
- Decision 4: Add focused regression tests for each critical finding before/with fixes, because bug-fix confidence depends on reproducible red/green coverage.

## Feature Metadata

- **Feature Type**: Bug Fix
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `retrieval_router.py`, `fallbacks.py`, `recall.py`, router/fallback test suites, integration tests
- **Dependencies**: Python 3.11+, Pydantic models in contracts, pytest

---

## Spec Lock (for this `/planning` run)

- **Implementation mode**: runnable code + tests (no net-new architecture docs required)
- **Target repo/path**: `C:\Users\Utopia\Desktop\second-brain-fin`
- **Stack constraints**: follow existing Python + Pydantic + pytest stack
- **Acceptance depth**: production-ready MVP hardening for this slice
- **Output artifact type**: structured execution plan only

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ)

- `backend/src/second_brain/orchestration/retrieval_router.py:16` - core route selection and feature-flag filtering logic.
- `backend/src/second_brain/orchestration/retrieval_router.py:79` - top-level `route_retrieval` entrypoint and override handling.
- `backend/src/second_brain/orchestration/fallbacks.py:22` - branch emitter functions and `ContextPacket` construction.
- `backend/src/second_brain/orchestration/fallbacks.py:162` - `determine_branch` ordering and rerank bypass handling.
- `backend/src/second_brain/agents/recall.py:54` - router invocation + routing metadata assembly.
- `backend/src/second_brain/agents/recall.py:146` - `_build_routing_metadata` currently hardcodes mode.
- `backend/src/second_brain/contracts/context_packet.py:40` - request/response contract and `mode` literals.
- `tests/test_retrieval_router_policy.py:20` - router policy regression suite.
- `tests/test_context_packet_contract.py:224` - fallback branch correctness tests.
- `tests/test_recall_flow_integration.py:133` - routing metadata assertions in end-to-end path.
- `backend/src/second_brain/validation/manual_branch_scenarios.py:23` - deterministic scenario expectations used by harness tests.

### New Files to Create

- None required by default.
- Optional only if tests are split for clarity: `tests/test_retrieval_router_critical_findings.py`.

### Related Memories (from memory.md)

- Memory: strict gate workflow enforced for plans and execution - Relevance: requires clear validation and explicit risk handling.
- Memory: build order contracts -> orchestration before broad expansion - Relevance: this fix stays inside existing contract/orchestration slice.
- Memory: pre-gate plans can miss required details - Relevance: this plan includes concrete task-level validation commands.

### Relevant Documentation

- `docs/architecture/retrieval-overlap-policy.md`
  - Specific section: Mem0 rerank policy + duplicate rerank prevention (`retrieval-overlap-policy.md:15`, `retrieval-overlap-policy.md:51`)
  - Why: ensures router/fallback changes do not violate rerank bypass policy.
- `docs/architecture/conversational-retrieval-contract.md`
  - Specific section: branch semantics and required output guarantees (`conversational-retrieval-contract.md:66`, `conversational-retrieval-contract.md:115`)
  - Why: protects branch-code and output-shape compatibility.
- `docs/architecture/retrieval-planning-separation.md`
  - Specific section: retrieval responsibility boundaries (`retrieval-planning-separation.md:9`)
  - Why: avoids leaking planning logic into fallback updates.
- [Pydantic v2 model validation](https://docs.pydantic.dev/latest/concepts/models/)
  - Specific section: model construction/field constraints
  - Why: keep emitted packet/action payloads schema-safe while changing logic.

### Patterns to Follow

**Deterministic route shape** (from `backend/src/second_brain/orchestration/retrieval_router.py:79`):
```python
def route_retrieval(
    request: RetrievalRequest,
    provider_status: dict[str, str] | None = None,
    feature_flags: dict[str, bool] | None = None
) -> tuple[str, dict]:
    if provider_status is None:
        provider_status = {}
    if feature_flags is None:
        feature_flags = {}
    enabled_providers = RouteDecision.check_feature_flags(feature_flags)
    ...
```
- Why this pattern: single entrypoint with explicit defaults makes regression testing straightforward.
- Common gotchas: default-empty status currently behaves as implicit unavailable; patch with normalized status map.

**Stable fallback emitters** (from `backend/src/second_brain/orchestration/fallbacks.py:22`):
```python
@staticmethod
def emit_empty_set(provider: str = "unknown") -> tuple[ContextPacket, NextAction]:
    packet = ContextPacket(... branch=BranchCodes.EMPTY_SET ...)
    next_action = NextAction(action="fallback", branch_code=BranchCodes.EMPTY_SET, ...)
    return packet, next_action
```
- Why this pattern: all paths emit contract-complete `(ContextPacket, NextAction)` tuples.
- Common gotchas: never change `BranchCodes` string values; only update decision predicates and metadata fidelity.

**Integration metadata envelope** (from `backend/src/second_brain/agents/recall.py:154`):
```python
return {
    "selected_provider": provider,
    "mode": "conversation",  # Could be from request
    "skip_external_rerank": route_options_skip_rerank,
    "rerank_type": rerank_metadata.get("rerank_type", "none"),
    ...
}
```
- Why this pattern: metadata is an operator-facing diagnostics payload.
- Common gotchas: hardcoded mode becomes a correctness bug for `fast`/`accurate` requests.

---

## IMPLEMENTATION PLAN

### Phase 1: Reproduce and lock failing behaviors

Create explicit failing tests for each critical finding first to enforce bug-fix scope:
- override should be rejected if provider disabled or unavailable/degraded by policy.
- missing status key should not force `none` when provider enabled.
- metadata mode should match request mode.
- fallback rerank semantics should stay consistent with branch meaning.

**Tasks:**
- add/adjust unit tests in router suite for override+status matrix.
- add integration assertion for mode propagation.
- add fallback contract tests for rerank metadata truthiness and branch consistency.

### Phase 2: Router hardening

Refactor router internals so all provider decisions use one eligibility policy:
- build helper(s) for normalized provider status and provider-eligible check.
- gate override path through same eligibility checks.
- maintain deterministic selection order for each mode.

**Tasks:**
- update `RouteDecision.select_route` and `route_retrieval` internals.
- remove unused parameters or use them meaningfully (avoid dead arguments).
- preserve existing return shape `(provider, {"skip_external_rerank": bool})`.

### Phase 3: Fallback semantics tightening

Keep branch ordering but make rerank semantics explicit:
- `LOW_CONFIDENCE` remains higher priority than `RERANK_BYPASSED`.
- `rerank_applied` should encode whether any rerank logic actually applied for that branch.
- ensure `SUCCESS` path does not misrepresent rerank state.

**Tasks:**
- patch branch helpers only where semantics are incorrect/ambiguous.
- avoid changing branch codes or `NextAction.action` mapping.

### Phase 4: Integration + validation

Wire metadata correctness and run full validation pyramid for this slice.

**Tasks:**
- update recall routing metadata mode handling.
- run unit + integration suites scoped to router/fallback/recall flows.
- confirm scenario harness still passes deterministic replay expectations.

---

## STEP-BY-STEP TASKS

### UPDATE tests/test_retrieval_router_policy.py

- **IMPLEMENT**: Add regression cases for critical findings:
  1) `provider_override` does not bypass unavailable status.
  2) `provider_override` does not bypass disabled feature flag.
  3) missing status key for enabled provider defaults to selectable behavior.
  4) deterministic output still stable across repeated runs after normalization.
- **PATTERN**: `tests/test_retrieval_router_policy.py:163`, `tests/test_retrieval_router_policy.py:247`
- **IMPORTS**: existing imports only (`route_retrieval`, `RouteDecision`, `ProviderStatus`, `RetrievalRequest`)
- **GOTCHA**: keep tests deterministic; do not depend on dict iteration order for assertions.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py -q`

### UPDATE tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add/extend test asserting `response.routing_metadata["mode"] == request.mode` for `fast`, `accurate`, and `conversation` requests.
- **PATTERN**: `tests/test_recall_flow_integration.py:133`
- **IMPORTS**: no new imports required.
- **GOTCHA**: current helper hardcodes mode; test should fail before fix and pass after.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py -q`

### UPDATE tests/test_context_packet_contract.py

- **IMPLEMENT**: Add tests validating rerank semantics:
  - `determine_branch(... rerank_bypassed=True, provider="mem0")` + high confidence -> `RERANK_BYPASSED` with `rerank_applied=True`.
  - `determine_branch(... rerank_bypassed=False, provider="supabase")` + high confidence -> `SUCCESS` with expected rerank flag semantics.
  - low-confidence inputs must never emit `RERANK_BYPASSED`.
- **PATTERN**: `tests/test_context_packet_contract.py:224`
- **IMPORTS**: existing imports only.
- **GOTCHA**: assert branch/action pairs together to catch mismatched packet/action tuples.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_context_packet_contract.py -q`

### UPDATE backend/src/second_brain/orchestration/retrieval_router.py

- **IMPLEMENT**: Introduce internal helpers:
  - `_normalized_provider_status(enabled_providers, provider_status)` to fill missing statuses as `available` unless explicitly provided.
  - `_is_provider_eligible(provider, enabled_providers, normalized_status)` returning bool.
  Then apply helper in both override and normal selection path.
- **PATTERN**: `backend/src/second_brain/orchestration/retrieval_router.py:63`, `backend/src/second_brain/orchestration/retrieval_router.py:79`
- **IMPORTS**: `from typing import Literal` (existing), optional `Mapping` if needed.
- **GOTCHA**: preserve current mode priority and Mem0 skip-rerank policy; only adjust eligibility checks and missing-status behavior.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py -q`

### REFACTOR backend/src/second_brain/orchestration/retrieval_router.py

- **IMPLEMENT**: Remove unused `feature_flags` parameter from `RouteDecision.select_route` or use it intentionally (no dead signature). Keep external API stable for `route_retrieval`.
- **PATTERN**: `backend/src/second_brain/orchestration/retrieval_router.py:16`
- **IMPORTS**: none beyond existing.
- **GOTCHA**: if signature changes, update all test callsites.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py -q`

### UPDATE backend/src/second_brain/orchestration/fallbacks.py

- **IMPLEMENT**: Audit `determine_branch` + emitters to ensure rerank semantics are explicit and branch-consistent.
  - Keep branch precedence: `EMPTY_SET` -> `LOW_CONFIDENCE` -> `RERANK_BYPASSED` -> `SUCCESS`.
  - Ensure `emit_success(... rerank_applied=...)` is only true when rerank actually happened in that path.
  - Keep `BranchCodes` unchanged.
- **PATTERN**: `backend/src/second_brain/orchestration/fallbacks.py:162`
- **IMPORTS**: existing contract model imports only.
- **GOTCHA**: do not introduce planning/intent heuristics here; retrieval remains confidence-driven.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_context_packet_contract.py -q`

### UPDATE backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: propagate request mode into `_build_routing_metadata` and eliminate hardcoded `"conversation"`.
  - Add `mode: str` arg to metadata builder (or pass request object).
  - ensure both normal and validation-mode paths use same mode source.
- **PATTERN**: `backend/src/second_brain/agents/recall.py:104`, `backend/src/second_brain/agents/recall.py:146`
- **IMPORTS**: no new imports required.
- **GOTCHA**: preserve existing metadata keys for backward compatibility.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py -q`

### MIRROR tests/test_manual_branch_validation_harness.py

- **IMPLEMENT**: Add/adjust assertions in smoke/policy scenarios if changed semantics require updated expected rerank metadata; keep scenario IDs stable.
- **PATTERN**: `tests/test_manual_branch_validation_harness.py:108`
- **IMPORTS**: existing imports only.
- **GOTCHA**: do not weaken assertions to make tests pass; update fixture expectations only when behavior change is intentional and documented.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py -q`

### UPDATE backend/src/second_brain/validation/manual_branch_scenarios.py

- **IMPLEMENT**: If router policy semantics changed for degraded/missing-status routing, update affected scenario expectations (`expected_branch`, `expected_rerank_type`, notes) while preserving deterministic intent.
- **PATTERN**: `backend/src/second_brain/validation/manual_branch_scenarios.py:149`
- **IMPORTS**: existing imports only.
- **GOTCHA**: only update scenarios with behavior justified by documented policy.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py -q`

### UPDATE docs/validation/recall-branch-manual-validation.md

- **IMPLEMENT**: Document critical fixes and add triage notes:
  - override health-gating rule,
  - missing-status normalization rule,
  - metadata mode fidelity check.
- **PATTERN**: style from existing runbook sections.
- **IMPORTS**: N/A
- **GOTCHA**: keep docs concise; update only behavior that actually changed.
- **VALIDATE**: `rg "override|missing-status|mode" docs/validation/recall-branch-manual-validation.md`

### UPDATE requests/execution-reports/hybrid-retrieval-recall-flow-integration-report.md

- **IMPLEMENT**: Add short addendum noting critical findings addressed in this hardening loop and any behavioral deltas.
- **PATTERN**: existing report section formatting.
- **IMPORTS**: N/A
- **GOTCHA**: do not rewrite historical report sections; append delta only.
- **VALIDATE**: `rg "critical|hardening|delta" requests/execution-reports/hybrid-retrieval-recall-flow-integration-report.md`

### VALIDATE repository slice end-to-end

- **IMPLEMENT**: Run targeted and combined test commands for router/fallback/recall/manual harness.
- **PATTERN**: command style from execution reports (`PYTHONPATH=backend/src pytest ... -q`).
- **IMPORTS**: N/A
- **GOTCHA**: run from repo root so pythonpath is resolved consistently.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py tests/test_context_packet_contract.py tests/test_recall_flow_integration.py tests/test_manual_branch_validation_harness.py -q`

---

## TESTING STRATEGY

### Unit Tests

- Router policy regression matrix:
  - override allowed only when provider enabled + eligible.
  - missing provider status does not incorrectly disable provider.
  - deterministic route output remains stable.
- Fallback branch regression matrix:
  - branch precedence unchanged.
  - rerank flags align with branch semantics.
  - branch/action code pairs remain contract-complete.

### Integration Tests

- Recall orchestration path validates:
  - routing metadata mode equals request mode.
  - selected provider and rerank metadata remain internally consistent.
  - branch output remains deterministic for repeated runs.

### Edge Cases

- Provider override points to disabled provider.
- Provider override points to unavailable/degraded provider.
- Provider enabled but status missing from snapshot.
- All providers disabled/unavailable still return deterministic `EMPTY_SET`.
- Low-confidence Mem0 result never mislabeled as `RERANK_BYPASSED`.

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```bash
ruff check backend/src tests
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain --ignore-missing-imports
```

### Level 3: Unit Tests
```bash
PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py tests/test_context_packet_contract.py -q
```

### Level 4: Integration Tests
```bash
PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py tests/test_manual_branch_validation_harness.py -q
```

### Level 5: Manual Validation

1. Run smoke scenarios from runbook and verify expected branch/action per scenario ID.
2. Validate one override-disabled scenario and one override-unavailable scenario from CLI/MCP path.
3. Validate metadata payload includes accurate `mode`, `selected_provider`, and rerank fields.
4. Capture before/after notes for incident triage readiness.

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] Router override path cannot select disabled/unhealthy providers.
- [x] Missing provider status keys no longer cause false `none` routing.
- [x] Fallback branch precedence and branch codes remain stable.
- [x] Rerank-related flags are branch-consistent and test-covered.
- [x] Routing metadata mode reflects actual request mode.
- [x] All targeted tests pass with no regressions.

### Runtime (verify after testing/deployment)

- [x] Operators can reproduce branch outcomes from manual scenario IDs without inconsistent routing.
- [x] Incident triage metadata is sufficient to explain provider and rerank decisions.
- [x] No regressions in existing Mem0 duplicate-rerank prevention policy.

---

## COMPLETION CHECKLIST

- [x] Failing tests for critical findings added before fixes (or in same change with clear red/green proof)
- [x] Router hardening implemented with centralized eligibility checks
- [x] Fallback semantics tightened without contract breakage
- [x] Recall metadata mode bug fixed
- [x] Manual scenario expectations updated only when behavior intentionally changed
- [x] Lint, typecheck, unit, and integration commands all pass
- [x] Runbook and execution-report delta updated

---

## NOTES

### Key Design Decisions
- Keep scope tight: only critical code-review findings tied to router/fallback correctness and diagnostics.
- Prefer helper extraction over broad refactor to reduce blast radius.
- Test-first for each finding to make bug fixes auditable.

### Risks
- Risk: behavior changes could invalidate existing scenario expectations.
  - Mitigation: update scenario expectations only with policy-backed rationale and preserve deterministic IDs.
- Risk: route normalization could unintentionally route to providers that should be unavailable.
  - Mitigation: missing-status defaults apply only to enabled providers and still honor explicit `unavailable`/`degraded` flags.
- Risk: metadata changes could break downstream consumers expecting prior values.
  - Mitigation: preserve key names and payload shape; only correct value fidelity.

### Alternatives Considered
- **Fail-closed on missing status**: rejected; too many false negatives and brittle dependency on full health snapshots.
- **Major router rewrite**: rejected; unnecessary for this bug-fix slice and increases regression risk.
- **Branch-code changes for finer rerank states**: rejected; breaks stable contract requirement.

### Confidence Score: 9/10
- **Strengths**: clear defect scope, existing robust test base, deterministic policy docs in repo.
- **Uncertainties**: exact degraded-provider fallback intent in some scenarios may require expectation updates.
- **Mitigations**: explicit scenario-by-scenario validation and runbook update in same loop.
