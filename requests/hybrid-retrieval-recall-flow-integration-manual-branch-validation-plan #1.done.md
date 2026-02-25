# Feature: Hybrid Retrieval Recall-Flow Integration + Manual Branch Validation

## Feature Description

Integrate the previously implemented retrieval contract foundation into the actual recall flow so runtime calls emit a deterministic `RetrievalResponse` envelope (`context_packet` + `next_action` + routing metadata) on every path. Then add a repeatable manual validation runbook that verifies all critical branches (`SUCCESS`, `LOW_CONFIDENCE`, `EMPTY_SET`, `CHANNEL_MISMATCH`, `RERANK_BYPASSED`) against realistic operator workflows.

## User Story

As a solo operator running a conversation-first retrieval system, I want the live recall flow to use the new contract and deterministic branch emitters, so that every retrieval result is predictable, debuggable, and manually verifiable before broader rollout.

## Problem Statement

The foundation artifacts exist (contracts, router, fallback policy, architecture docs, tests), but runtime integration is incomplete because key integration files are still placeholders (`recall.py`, `memory.py`, `voyage.py`, `mcp_server.py`, `deps.py`, `schemas.py`). Without integration, branch behavior is validated only at unit-level helper functions, not in the end-to-end recall path operators actually use.

## Solution Statement

Use a narrow integration slice that keeps existing architecture decisions intact while wiring the real recall flow:
- Decision 1: Keep router + fallback logic deterministic and side-effect-light, because branch repeatability is the top requirement for manual validation.
- Decision 2: Introduce minimal service interfaces and dependency wiring first, because placeholder files currently block real flow execution.
- Decision 3: Preserve Mem0 duplicate-rerank prevention as default policy, because architecture docs and tests already codify this behavior.
- Decision 4: Add a dedicated manual validation harness and checklist artifacts, because runtime trust requires explicit operator-facing verification, not just unit tests.
- Decision 5: Keep scope to one PIV loop (integration + manual validation), because YAGNI and the existing plan already delivered foundational building blocks.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: High
- **Primary Systems Affected**: `agents/recall.py`, `services/memory.py`, `services/voyage.py`, `deps.py`, `mcp_server.py`, contract orchestration modules, tests, architecture/runbook docs
- **Dependencies**: Pydantic v2 models, existing orchestration modules, optional Mem0/Voyage SDK configuration, pytest

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/contracts/context_packet.py` (lines 1-53) — Why: canonical runtime types (`RetrievalRequest`, `RetrievalResponse`, `ContextPacket`, `NextAction`).
- `backend/src/second_brain/orchestration/retrieval_router.py` (lines 1-116) — Why: deterministic provider and rerank policy selection.
- `backend/src/second_brain/orchestration/fallbacks.py` (lines 1-199) — Why: stable branch code emitters and branch determination.
- `tests/test_context_packet_contract.py` (lines 1-280) — Why: contract invariants and fallback expectations.
- `tests/test_retrieval_router_policy.py` (lines 1-270) — Why: deterministic routing, Mem0 duplicate-rerank policy, feature flags.
- `docs/architecture/conversational-retrieval-contract.md` (lines 1-150) — Why: required output guarantees and branch semantics.
- `docs/architecture/retrieval-planning-separation.md` (lines 1-182) — Why: module ownership boundaries and integration expectations.
- `docs/architecture/retrieval-overlap-policy.md` (lines 1-188) — Why: rerank overlap policy and default-on/default-off behavior.
- `backend/pyproject.toml` (lines 1-20) — Why: lint/type/test command baseline and strict typing posture.
- `memory.md` (lines 10-43) — Why: strict gate workflow guidance, portability caution, and previous session context.

### New Files to Create

- `tests/test_recall_flow_integration.py` — integration test coverage for recall runtime path and branch behavior.
- `tests/test_manual_branch_validation_harness.py` — deterministic harness tests for operator validation fixtures.
- `backend/src/second_brain/validation/manual_branch_scenarios.py` — reusable branch scenario fixtures used by tests/manual checks.
- `docs/validation/recall-branch-manual-validation.md` — runbook for manual branch validation with expected outcomes.
- `requests/execution-reports/hybrid-retrieval-recall-flow-integration-validation-report.md` — template target for `/execute` output report.

### Related Memories (from memory.md)

- Memory: Strict gate workflow (G1-G5) enforced for feature plans — Relevance: this integration plan explicitly gates from syntax -> unit -> integration -> manual verification.
- Memory: Python-first with framework-agnostic contracts — Relevance: we preserve contract portability and avoid framework-specific runtime lock-in.
- Memory: Build order Contracts -> Core Loop -> Eval/Trace -> Memory -> Orchestration -> Ingestion — Relevance: this slice sits in orchestration integration and follows prior contract-first order.
- Memory: Bypass protocol requires evidence and rollback plan — Relevance: manual validation section includes explicit pass/fail evidence and rollback criteria.
- Memory: Pre-gate plans may miss required metadata — Relevance: this plan adds validation traceability and explicit runtime acceptance checklist.

### Relevant Documentation

- [Mem0: Reranker-Enhanced Search](https://docs.mem0.ai/open-source/features/reranker-search)
  - Specific section: Feature anatomy, tune performance/cost, handle failures gracefully
  - Why: confirms rerank can be toggled per request and fallback-to-vector behavior is expected.
- [Mem0: Search Memory](https://docs.mem0.ai/core-concepts/memory-operations/search)
  - Specific section: `top_k`/`threshold`, rerank notes, scoping/filter tips
  - Why: aligns request shaping and threshold handling for recall integration.
- [Voyage: Reranker](https://docs.voyageai.com/docs/reranker)
  - Specific section: Python API parameters and truncation/token constraints
  - Why: constrains external rerank adapter behavior and error handling decisions.
- [Pydantic v2 API Concepts](https://docs.pydantic.dev/latest/)
  - Specific section: model validation, strict fields, model_dump usage
  - Why: ensures `RetrievalResponse` serialization remains contract-safe in MCP outputs.

### Patterns to Follow

**Deterministic Provider Selection** (from `backend/src/second_brain/orchestration/retrieval_router.py:16`):
```python
@staticmethod
def select_route(
    mode: Literal["fast", "accurate", "conversation"],
    available_providers: list[str],
    feature_flags: dict[str, bool],
    provider_status: dict[str, str]
) -> tuple[str, dict]:
    if not available_providers:
        return "none", {"skip_external_rerank": False}

    if mode == "conversation":
        if "mem0" in available_providers and provider_status.get("mem0") == ProviderStatus.AVAILABLE:
            return "mem0", {"skip_external_rerank": True}
```
- Why this pattern: deterministic branching is required for stable manual branch validation.
- Common gotchas: do not introduce non-deterministic ordering from unordered collections.

**Stable Branch Emitters** (from `backend/src/second_brain/orchestration/fallbacks.py:9`):
```python
class BranchCodes:
    EMPTY_SET = "EMPTY_SET"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    RERANK_BYPASSED = "RERANK_BYPASSED"
    SUCCESS = "SUCCESS"
```
- Why this pattern: stable branch codes are the runtime truth for operator workflows.
- Common gotchas: avoid inline magic strings in recall path; always reference constants.

**Contract Validation in Tests** (from `tests/test_context_packet_contract.py:224`):
```python
def test_mem0_rerank_bypass(self):
    candidates = [
        ContextCandidate(
            id="c1",
            content="Mem0 with native rerank",
            source="mem0",
            confidence=0.85,
        )
    ]
    packet, action = determine_branch(candidates, 0.6, True, "mem0")
    assert packet.summary.branch == BranchCodes.RERANK_BYPASSED
    assert packet.rerank_applied is True
```
- Why this pattern: expected policy behavior is codified as assertions and should remain unchanged.
- Common gotchas: integration tests must preserve this exact policy behavior for Mem0 paths.

**Feature Flag Provider Gating** (from `backend/src/second_brain/orchestration/retrieval_router.py:63`):
```python
if feature_flags.get("graphiti_enabled", False):
    enabled.append("graphiti")

if feature_flags.get("mem0_enabled", True):
    enabled.append("mem0")

if feature_flags.get("supabase_enabled", True):
    enabled.append("supabase")
```
- Why this pattern: safe incremental rollout and reproducible manual checks.
- Common gotchas: keep default values stable to avoid accidental behavior drift.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Create minimal runtime-capable scaffolding for placeholder integration files without over-engineering. Establish typed interfaces for memory retrieval and rerank integration so recall flow can orchestrate all branches consistently.

**Tasks:**
- Implement baseline service contracts in `services/memory.py` and `services/voyage.py` (minimal, deterministic, mock-friendly).
- Implement dependency providers in `deps.py` to supply service instances and feature flags.
- Expand `schemas.py` only as needed for MCP-facing compatibility wrappers.
- Create branch scenario fixtures in `validation/manual_branch_scenarios.py` for manual + automated validation parity.

### Phase 2: Core Implementation

Build actual recall runtime orchestration that maps `RetrievalRequest` input to routed provider retrieval, optional external rerank, branch determination, and final `RetrievalResponse` output.

**Tasks:**
- Implement `recall.py` as thin orchestrator using `route_retrieval` and `determine_branch`.
- Add explicit metadata fields for route decision, rerank policy, and branch origin.
- Enforce Mem0 default skip of external rerank unless explicit override exists.
- Keep channel mismatch support hook (optional input signal) without coupling business intent logic.

### Phase 3: Integration

Wire the recall flow into MCP tool surface with backward-compatible response shape and add runtime hooks for operator-driven validation commands.

**Tasks:**
- Implement MCP endpoint wrapper in `mcp_server.py` that can expose contract envelope.
- Provide compatibility mode output to avoid breaking existing consumers.
- Add lightweight CLI/manual harness entry points for branch simulation.
- Ensure dependencies, settings, and defaults are discoverable and deterministic.

### Phase 4: Testing & Validation

Add integration tests and explicit manual validation runbook to prove runtime behavior, determinism, and policy compliance.

**Tasks:**
- Create `test_recall_flow_integration.py` covering all branch paths and metadata invariants.
- Create `test_manual_branch_validation_harness.py` verifying scenario fixtures and expected branch outputs.
- Author `docs/validation/recall-branch-manual-validation.md` with step-by-step runtime checklist.
- Execute full 5-level validation pyramid and produce execution report artifact.

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### UPDATE backend/src/second_brain/services/memory.py

- **IMPLEMENT**: Replace placeholder with minimal `MemoryService` abstraction exposing `search_memories(query, top_k, threshold, provider, rerank, filters)` returning normalized list of `ContextCandidate` objects plus provider metadata. Include deterministic in-memory fallback adapter for tests when external providers are unavailable.
- **PATTERN**: `backend/src/second_brain/contracts/context_packet.py:6` for candidate structure; `docs/architecture/retrieval-overlap-policy.md:19` for Mem0 rerank behavior.
- **IMPORTS**: `from dataclasses import dataclass`, `from typing import Any`, `from second_brain.contracts.context_packet import ContextCandidate`
- **GOTCHA**: Do not embed planning/business logic in memory service; only retrieval normalization.
- **VALIDATE**: `python -m pytest -q tests/test_context_packet_contract.py -k candidate`

### UPDATE backend/src/second_brain/services/voyage.py

- **IMPLEMENT**: Replace placeholder with `VoyageRerankService` wrapper that receives query + candidate list and returns reranked candidates; add bypass no-op mode for disabled/unsupported paths.
- **PATTERN**: `docs/architecture/retrieval-overlap-policy.md:53` guard conditions and metadata requirements.
- **IMPORTS**: `from typing import Sequence`, `from second_brain.contracts.context_packet import ContextCandidate`
- **GOTCHA**: Preserve candidate identity; only reorder and optionally adjust confidence metadata.
- **VALIDATE**: `python -m pytest -q tests -k rerank`

### UPDATE backend/src/second_brain/deps.py

- **IMPLEMENT**: Replace placeholder with dependency constructors for `MemoryService`, `VoyageRerankService`, `feature_flags`, and `provider_status` snapshots. Keep pure functions for easy test injection.
- **PATTERN**: deterministic defaults in `backend/src/second_brain/orchestration/retrieval_router.py:95`.
- **IMPORTS**: `from typing import Callable`, `from second_brain.services.memory import MemoryService`, `from second_brain.services.voyage import VoyageRerankService`
- **GOTCHA**: Avoid global mutable singleton state that can leak across tests.
- **VALIDATE**: `python -m pytest -q tests/test_retrieval_router_policy.py -k default`

### UPDATE backend/src/second_brain/schemas.py

- **IMPLEMENT**: Replace placeholder with compatibility response schema (if needed) that can include both legacy flat fields and nested contract envelope; keep conversion helpers from `RetrievalResponse` to MCP payload.
- **PATTERN**: `backend/src/second_brain/contracts/context_packet.py:49` response model.
- **IMPORTS**: `from pydantic import BaseModel, Field`, `from second_brain.contracts.context_packet import RetrievalResponse`
- **GOTCHA**: Do not duplicate contract model definitions; wrap or reference existing models.
- **VALIDATE**: `python -m pytest -q tests -k schema`

### UPDATE backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Replace placeholder with recall orchestrator function/class that accepts `RetrievalRequest`, routes provider via `route_retrieval`, executes memory search, optionally applies external rerank, computes branch with `determine_branch`, and returns `RetrievalResponse` with routing metadata.
- **PATTERN**: `backend/src/second_brain/orchestration/retrieval_router.py:79`, `backend/src/second_brain/orchestration/fallbacks.py:162`.
- **IMPORTS**: `from second_brain.contracts.context_packet import RetrievalRequest, RetrievalResponse`, `from second_brain.orchestration.retrieval_router import route_retrieval`, `from second_brain.orchestration.fallbacks import determine_branch`
- **GOTCHA**: Keep ordering deterministic before branch eval; unstable sorting can break branch reproducibility.
- **VALIDATE**: `python -m pytest -q tests -k recall`

### UPDATE backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Add explicit branch override hook for manual validation mode (test-only or debug-only) to force `CHANNEL_MISMATCH` when scenario requires it; keep disabled by default.
- **PATTERN**: Branch constants from `backend/src/second_brain/orchestration/fallbacks.py:9`.
- **IMPORTS**: `from second_brain.orchestration.fallbacks import FallbackEmitter, BranchCodes`
- **GOTCHA**: Ensure override hook cannot affect production flows unless explicitly enabled.
- **VALIDATE**: `python -m pytest -q tests -k channel_mismatch`

### UPDATE backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Add rich `routing_metadata` fields: selected provider, requested mode, skip_external_rerank flag, rerank_type (`provider-native|external|none`), rerank_bypass_reason, feature_flags snapshot.
- **PATTERN**: metadata expectations in `docs/architecture/retrieval-overlap-policy.md:60`.
- **IMPORTS**: `from typing import Any`
- **GOTCHA**: Metadata keys must be stable and documented to support manual branch validation logs.
- **VALIDATE**: `python -m pytest -q tests -k routing_metadata`

### UPDATE backend/src/second_brain/mcp_server.py

- **IMPLEMENT**: Replace placeholder with MCP tool endpoint exposing recall flow; include optional compatibility response shaping and debug mode for manual scenario execution.
- **PATTERN**: interface contract in `docs/architecture/retrieval-planning-separation.md:136`.
- **IMPORTS**: `from second_brain.agents.recall import run_recall`, `from second_brain.contracts.context_packet import RetrievalRequest`
- **GOTCHA**: Keep backward compatibility by adding fields, not removing existing top-level keys.
- **VALIDATE**: `python -m pytest -q tests -k mcp`

### ADD backend/src/second_brain/validation/manual_branch_scenarios.py

- **IMPLEMENT**: Create deterministic scenario factory definitions for each target branch with controlled inputs (candidates, provider status, flags, thresholds, expected branch code, expected action, expected metadata).
- **PATTERN**: test fixture style from `tests/test_retrieval_router_policy.py:247` deterministic loop checks.
- **IMPORTS**: `from dataclasses import dataclass`, `from second_brain.contracts.context_packet import RetrievalRequest, ContextCandidate`, `from second_brain.orchestration.fallbacks import BranchCodes`
- **GOTCHA**: Scenarios must be deterministic and independent from external API availability.
- **VALIDATE**: `python -m pytest -q tests -k manual_branch_scenarios`

### CREATE tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add integration tests covering recall runtime path for all branch outcomes and rerank policy metadata assertions.
- **PATTERN**: assertions style in `tests/test_context_packet_contract.py:224` and route checks in `tests/test_retrieval_router_policy.py:201`.
- **IMPORTS**: `import pytest`, recall entrypoint, contract models, scenario fixtures.
- **GOTCHA**: Avoid brittle string snapshots for timestamps; assert structure and semantic fields.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py`

### CREATE tests/test_manual_branch_validation_harness.py

- **IMPLEMENT**: Add harness tests ensuring each manual scenario maps to expected branch/action/metadata and remains stable across repeated runs.
- **PATTERN**: deterministic repeat assertion from `tests/test_retrieval_router_policy.py:258`.
- **IMPORTS**: `import pytest`, scenario fixtures, recall entrypoint, branch constants.
- **GOTCHA**: Ensure tests isolate environment-driven defaults (feature flags) with explicit fixtures.
- **VALIDATE**: `python -m pytest -q tests/test_manual_branch_validation_harness.py`

### CREATE docs/validation/recall-branch-manual-validation.md

- **IMPLEMENT**: Author runbook with prerequisites, environment setup, branch scenario execution commands, expected outputs, pass/fail capture template, and rollback criteria.
- **PATTERN**: policy language from `docs/architecture/retrieval-overlap-policy.md:126` and branch semantics from `docs/architecture/conversational-retrieval-contract.md:66`.
- **IMPORTS**: none
- **GOTCHA**: Manual steps must include exact expected branch code and next action, not generic descriptions.
- **VALIDATE**: `python -m pytest -q tests -k manual_validation_doc_reference`

### UPDATE docs/architecture/retrieval-planning-separation.md

- **IMPLEMENT**: Add implementation status note that recall flow now emits contract runtime output and clarify where manual branch validation sits in operator workflow.
- **PATTERN**: existing section style in same file (benefits, pitfalls, integration points).
- **IMPORTS**: none
- **GOTCHA**: Keep this architectural; avoid embedding test command spam.
- **VALIDATE**: `python -m pytest -q tests -k docs`

### UPDATE docs/architecture/retrieval-overlap-policy.md

- **IMPLEMENT**: Add explicit integration note for `rerank_type` and `rerank_bypass_reason` metadata from live recall flow.
- **PATTERN**: metadata block at lines 64-70 in existing doc.
- **IMPORTS**: none
- **GOTCHA**: Keep defaults unchanged: Mem0 native ON, external OFF by default.
- **VALIDATE**: `python -m pytest -q tests -k overlap_policy`

### UPDATE backend/src/second_brain/contracts/__init__.py

- **IMPLEMENT**: Export key contract models to simplify imports across recall/mcp/tests.
- **PATTERN**: package export style in `backend/src/second_brain/orchestration/__init__.py` and other `__init__.py` files.
- **IMPORTS**: from local module only.
- **GOTCHA**: Avoid wildcard exports that hide explicit dependencies.
- **VALIDATE**: `python -m pytest -q tests -k import`

### UPDATE backend/src/second_brain/orchestration/__init__.py

- **IMPLEMENT**: Export `route_retrieval`, `determine_branch`, `BranchCodes` for integration convenience.
- **PATTERN**: import re-export conventions in Python packages.
- **IMPORTS**: from local orchestration modules.
- **GOTCHA**: No side effects in package init.
- **VALIDATE**: `python -m pytest -q tests -k orchestration_imports`

### UPDATE backend/src/second_brain/services/__init__.py

- **IMPLEMENT**: Export service abstractions for DI layer.
- **PATTERN**: explicit exports pattern.
- **IMPORTS**: from `.memory` and `.voyage`.
- **GOTCHA**: Keep import graph acyclic.
- **VALIDATE**: `python -m pytest -q tests -k services_imports`

### UPDATE backend/src/second_brain/agents/__init__.py

- **IMPLEMENT**: Export recall runner API.
- **PATTERN**: explicit package exports.
- **IMPORTS**: from `.recall`.
- **GOTCHA**: Avoid eager runtime initialization.
- **VALIDATE**: `python -m pytest -q tests -k agents_imports`

### UPDATE backend/src/second_brain/__init__.py

- **IMPLEMENT**: Keep top-level package metadata minimal; optionally expose semantic version and high-level public entrypoints.
- **PATTERN**: minimalist package init pattern.
- **IMPORTS**: none or safe local imports.
- **GOTCHA**: Do not create deep import side effects impacting test collection speed.
- **VALIDATE**: `python -m pytest -q tests -k package_init`

### UPDATE backend/src/second_brain/mcp_server.py

- **IMPLEMENT**: Add manual validation endpoint/helper that runs a named scenario and returns normalized result for operators.
- **PATTERN**: scenario fixture approach from `backend/src/second_brain/validation/manual_branch_scenarios.py`.
- **IMPORTS**: scenario module and recall entrypoint.
- **GOTCHA**: Ensure debug endpoints are explicit and can be disabled.
- **VALIDATE**: `python -m pytest -q tests -k scenario_endpoint`

### UPDATE tests/test_retrieval_router_policy.py

- **IMPLEMENT**: Add integration-aligned expectations for route metadata flags consumed by recall flow.
- **PATTERN**: existing deterministic tests in same file.
- **IMPORTS**: existing imports only or incremental additions.
- **GOTCHA**: Keep route unit tests focused on routing, not downstream branch behavior.
- **VALIDATE**: `python -m pytest -q tests/test_retrieval_router_policy.py`

### UPDATE tests/test_context_packet_contract.py

- **IMPLEMENT**: Add assertions for metadata compatibility assumptions used by recall integration (if contract wrappers introduced).
- **PATTERN**: existing model-level assertion style in same file.
- **IMPORTS**: existing models and emitter helpers.
- **GOTCHA**: Do not over-constrain timestamp formatting beyond ISO-string type.
- **VALIDATE**: `python -m pytest -q tests/test_context_packet_contract.py`

### CREATE requests/execution-reports/hybrid-retrieval-recall-flow-integration-validation-report.md

- **IMPLEMENT**: Pre-create a skeleton report document with sections for command outputs, manual branch evidence, regressions, and unresolved risks; this is the destination for `/execute` report details.
- **PATTERN**: execution report usage noted in `memory.md:38` (save report first, then inline display).
- **IMPORTS**: none
- **GOTCHA**: Keep this as a report scaffold, not a fake completed report.
- **VALIDATE**: `python -m pytest -q tests -k execution_report_placeholder`

### REFACTOR backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Split recall orchestration into small pure helpers: `build_request_context`, `retrieve_candidates`, `apply_rerank_policy`, `emit_branch_response`; keep top-level function short and readable.
- **PATTERN**: KISS + deterministic helper decomposition.
- **IMPORTS**: local helper typing imports.
- **GOTCHA**: Ensure helper boundaries do not duplicate router/fallback logic.
- **VALIDATE**: `python -m pytest -q tests -k recall and not slow`

### ADD tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add repeated-run determinism test: same scenario invoked N times must produce identical branch/action/provider/rerank metadata.
- **PATTERN**: repeated-run checks from `tests/test_retrieval_router_policy.py:226`.
- **IMPORTS**: `pytest`, scenarios, recall entrypoint.
- **GOTCHA**: Strip timestamp when comparing full payload snapshots.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py -k deterministic`

### ADD tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add Mem0 policy test at integration level asserting `skip_external_rerank=True` implies `rerank_type=provider-native` and no external rerank invocation.
- **PATTERN**: overlap policy defaults in `docs/architecture/retrieval-overlap-policy.md:91`.
- **IMPORTS**: mock/spies if needed for rerank service.
- **GOTCHA**: avoid asserting implementation-specific function names; assert behavior.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py -k mem0`

### ADD tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add non-Mem0 path test asserting external rerank path metadata appears when enabled and available.
- **PATTERN**: route policies from router tests.
- **IMPORTS**: same as integration suite.
- **GOTCHA**: ensure test controls feature flags explicitly.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py -k external_rerank`

### ADD tests/test_manual_branch_validation_harness.py

- **IMPLEMENT**: Add operator-friendly assertion messages so failing scenario immediately identifies branch mismatch and suggested fix area.
- **PATTERN**: test readability conventions in existing tests.
- **IMPORTS**: `pytest`.
- **GOTCHA**: avoid over-verbose assertions that obscure root cause.
- **VALIDATE**: `python -m pytest -q tests/test_manual_branch_validation_harness.py -k branch`

### UPDATE docs/validation/recall-branch-manual-validation.md

- **IMPLEMENT**: Add branch evidence table template with columns: scenario id, expected branch, actual branch, expected action, actual action, rerank metadata, notes, pass/fail.
- **PATTERN**: deterministic branch requirement in contract doc lines 117-120.
- **IMPORTS**: none
- **GOTCHA**: table must use stable scenario ids aligned with scenario fixture module.
- **VALIDATE**: `python -m pytest -q tests -k scenario_id_alignment`

### UPDATE README.md

- **IMPLEMENT**: Add short implementation status note under current feature section: foundation complete + recall flow integration and manual branch validation now planned/implemented (depending execution state).
- **PATTERN**: existing status sections and concise bullet format.
- **IMPORTS**: none
- **GOTCHA**: do not claim completion until validation passes.
- **VALIDATE**: `python -m pytest -q tests -k readme_consistency`

### UPDATE memory.md

- **IMPLEMENT**: Append post-implementation memory entry only after validation succeeds (not during initial coding), capturing key gotcha(s) discovered in integration.
- **PATTERN**: concise entries in `memory.md` sizing rules.
- **IMPORTS**: none
- **GOTCHA**: keep file under 100 lines.
- **VALIDATE**: `python -m pytest -q tests -k memory_file_constraints`

### MIRROR backend/src/second_brain/orchestration/fallbacks.py

- **IMPLEMENT**: Reuse `determine_branch` as single branch source of truth; do not reimplement branch comparisons in `recall.py`.
- **PATTERN**: `determine_branch` central logic lines 180-199.
- **IMPORTS**: `determine_branch`.
- **GOTCHA**: duplicate branch logic can diverge and break tests.
- **VALIDATE**: `python -m pytest -q tests -k determine_branch`

### MIRROR backend/src/second_brain/orchestration/retrieval_router.py

- **IMPLEMENT**: Route provider only through router module; no ad-hoc provider selection in recall implementation.
- **PATTERN**: `route_retrieval` function lines 79-116.
- **IMPORTS**: `route_retrieval`.
- **GOTCHA**: bypassing router defeats deterministic policy tests.
- **VALIDATE**: `python -m pytest -q tests -k route_retrieval`

### UPDATE backend/src/second_brain/validation/manual_branch_scenarios.py

- **IMPLEMENT**: Add scenario tags (`smoke`, `policy`, `edge`, `degraded`) to support focused manual runs.
- **PATTERN**: lightweight data fixture patterns.
- **IMPORTS**: stdlib only.
- **GOTCHA**: avoid hidden randomness in scenario generation.
- **VALIDATE**: `python -m pytest -q tests/test_manual_branch_validation_harness.py -k tags`

### UPDATE docs/validation/recall-branch-manual-validation.md

- **IMPLEMENT**: Include triage guide mapping branch mismatches to likely file roots (router, fallbacks, recall, services).
- **PATTERN**: architecture separation boundaries doc.
- **IMPORTS**: none
- **GOTCHA**: keep triage suggestions as heuristics, not absolute guarantees.
- **VALIDATE**: `python -m pytest -q tests -k triage_guide`

### UPDATE requests/hybrid-retrieval-recall-flow-integration-manual-branch-validation-plan.md

- **IMPLEMENT**: During execution handoff, mark implementation checklist items only when each validation gate passes; do not pre-check runtime criteria.
- **PATTERN**: acceptance criteria split implementation vs runtime in template.
- **IMPORTS**: none
- **GOTCHA**: avoid optimistic checklist updates before evidence exists.
- **VALIDATE**: `python -m pytest -q tests -k checklist_integrity`

---

## TESTING STRATEGY

### Unit Tests

- Router: verify deterministic provider selection and policy flags across mode/feature/provider status combinations.
- Fallbacks: verify each branch emits required fields and stable branch codes.
- Contracts: validate field bounds, action literals, and envelope shape.
- Services: validate memory normalization and rerank bypass/enable branching in isolation.
- Dependency wiring: verify default providers/flags are explicit and reproducible.

### Integration Tests

- Full recall runtime from `RetrievalRequest` to `RetrievalResponse` for all branch outcomes.
- MCP wrapper compatibility response shape (contract nested + optional legacy fields).
- Mem0 path ensures no external rerank invocation by default.
- Supabase/Graphiti-like path supports optional external rerank when enabled.
- Deterministic repeatability under identical inputs.

### Edge Cases

- Empty candidate list from provider returns `EMPTY_SET` with actionable fallback guidance.
- Candidate list non-empty but top confidence under threshold returns `LOW_CONFIDENCE`.
- Degraded provider status fallback still deterministic and metadata-complete.
- Explicit provider override unavailable should fall back safely and record metadata.
- Rerank service failure should degrade gracefully and still return valid contract envelope.
- Timestamp field should remain valid string without breaking deterministic semantic assertions.
- Feature flag combinations that disable all providers must return `EMPTY_SET` branch.
- Manual override hooks disabled by default in non-validation runtime.

### Manual Branch Validation Philosophy

- Manual validation confirms operator trust signals not captured by code assertions alone.
- Every branch scenario must include expected branch code and expected next action.
- Evidence capture must include command, key output fields, and final pass/fail note.
- Failed manual checks should map directly to triage ownership boundaries.

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style
```bash
ruff check backend/src tests
ruff format --check backend/src tests
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain
```

### Level 3: Unit Tests
```bash
pytest tests/test_context_packet_contract.py tests/test_retrieval_router_policy.py -q
pytest tests/test_manual_branch_validation_harness.py -q
```

### Level 4: Integration Tests
```bash
pytest tests/test_recall_flow_integration.py -q
pytest tests -k "recall or mcp or rerank" -q
```

### Level 5: Manual Validation

1. Run smoke scenario set and capture branch/action/provider metadata for each case.
2. Confirm Mem0 conversation-mode scenarios emit `RERANK_BYPASSED` or `SUCCESS` with provider-native rerank metadata.
3. Confirm low-confidence scenario emits `LOW_CONFIDENCE` + `clarify` action with threshold details.
4. Confirm empty result scenario emits `EMPTY_SET` + `fallback` action.
5. Trigger channel mismatch scenario (validation mode) and confirm `CHANNEL_MISMATCH` + `escalate` action.
6. Validate one non-Mem0 route with external rerank enabled to confirm `rerank_type=external`.
7. Validate one degraded provider scenario to ensure deterministic fallback provider selection.
8. Record all evidence in `docs/validation/recall-branch-manual-validation.md` evidence table.

### Additional Validation (Optional)

- Use Archon task/document tracking to store manual validation results and follow-up tasks.
- Add lightweight runtime logging assertions for branch distribution sanity checks.

---

## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable only after running the code).

### Implementation (verify during execution)

- [ ] `recall.py` is fully implemented and emits `RetrievalResponse` envelope on every path.
- [ ] Placeholder service files (`memory.py`, `voyage.py`, `deps.py`, `schemas.py`, `mcp_server.py`) are replaced with minimal but functional integration code.
- [ ] Router and fallback modules remain the single source of truth for routing/branch decisions.
- [ ] Mem0 duplicate-rerank prevention is preserved in integration behavior and metadata.
- [ ] New integration tests and manual harness tests exist and pass.
- [ ] Manual validation runbook exists with clear scenario IDs and expected outputs.
- [ ] No linting or mypy regressions introduced.
- [ ] Architecture docs updated to reflect integrated runtime behavior.

### Runtime (verify after testing/deployment)

- [ ] Manual branch validation confirms all target branches with expected actions.
- [ ] Operator can reproduce branch outcomes using documented runbook.
- [ ] MCP consumers can read contract envelope without compatibility regressions.
- [ ] Branch metadata is sufficient for triage without additional code inspection.
- [ ] No regressions observed in existing retrieval behavior beyond planned contract output improvements.

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in sequence
- [ ] Each task-level validate command passed
- [ ] Lint and type checks passed
- [ ] Unit tests passed
- [ ] Integration tests passed
- [ ] Manual branch validation executed
- [ ] Evidence table completed
- [ ] Architecture docs updated
- [ ] Execution report generated
- [ ] Runtime acceptance criteria verified

---

## NOTES

### Key Design Decisions

- Keep integration thin and deterministic instead of introducing premature abstractions.
- Preserve current contract and policy definitions as fixed invariants.
- Introduce manual validation fixtures that are reusable in both automation and operator workflows.
- Prefer metadata-rich response envelopes over hidden side-channel logs for debugging.

### Risks

- Risk: placeholder replacement may accidentally over-design service layer. Mitigation: keep minimal interfaces and add only required fields.
- Risk: deterministic assumptions can break if unordered provider lists are introduced. Mitigation: explicit ordering in router inputs.
- Risk: manual validation docs drift from real scenario fixtures. Mitigation: scenario IDs sourced from single fixture module and cross-checked in tests.
- Risk: compatibility concerns for MCP consumers. Mitigation: additive response changes and targeted compatibility tests.

### Confidence Score: 8.4/10

- **Strengths**: clear architecture contracts, existing unit coverage for core policy primitives, explicit scope and deterministic requirements.
- **Uncertainties**: exact legacy MCP response expectations are not visible because current file is placeholder.
- **Mitigations**: implement additive compatibility wrappers, validate with integration tests, and capture operator feedback in manual runbook.

---

## APPENDIX A: Branch Validation Scenario Catalog

S001 - conversation_mem0_high_confidence - expect branch `RERANK_BYPASSED` or `SUCCESS` based on rerank metadata.
S002 - conversation_mem0_no_candidates - expect `EMPTY_SET` + action `fallback`.
S003 - conversation_mem0_low_confidence - expect `LOW_CONFIDENCE` + action `clarify`.
S004 - conversation_supabase_high_confidence - expect `SUCCESS` + action `proceed`.
S005 - conversation_supabase_low_confidence - expect `LOW_CONFIDENCE` + action `clarify`.
S006 - fast_mem0_high_confidence - expect deterministic provider `mem0` when available.
S007 - fast_supabase_only - expect provider `supabase` and external rerank policy false by default.
S008 - accurate_multi_provider_mem0_first - expect provider per deterministic order input.
S009 - accurate_multi_provider_supabase_first - expect provider per deterministic order input.
S010 - accurate_graphiti_enabled_no_mem0 - expect graphiti or supabase per order and availability.
S011 - override_supabase_available - expect provider override honored.
S012 - override_graphiti_disabled - expect safe fallback and metadata note.
S013 - all_providers_disabled - expect `EMPTY_SET` path.
S014 - all_providers_unavailable - expect `EMPTY_SET` path.
S015 - mem0_degraded_supabase_available - expect deterministic fallback provider.
S016 - mem0_available_supabase_degraded - expect `mem0` in conversation mode.
S017 - threshold_exact_match - expect threshold_met true for equal boundary.
S018 - threshold_just_below - expect `LOW_CONFIDENCE`.
S019 - threshold_just_above - expect `SUCCESS`.
S020 - empty_query_guard - expect controlled failure or safe fallback response.
S021 - large_top_k_with_small_dataset - expect stable response shape.
S022 - rerank_service_disabled - expect rerank metadata type `none` or `provider-native`.
S023 - rerank_service_failure_non_mem0 - expect graceful degradation.
S024 - rerank_service_failure_mem0 - expect unaffected native behavior.
S025 - mem0_external_override_on - expect explicit metadata showing override.
S026 - mem0_external_override_off - expect default bypass behavior.
S027 - channel_mismatch_forced_validation - expect `CHANNEL_MISMATCH` + `escalate`.
S028 - channel_mismatch_disabled_default - expect normal branch path.
S029 - provider_status_missing_defaults - expect deterministic fallback behavior.
S030 - feature_flags_missing_defaults - expect mem0+supabase enabled defaults.
S031 - feature_flags_graphiti_only - expect graphiti route when available.
S032 - feature_flags_mem0_only - expect mem0 route and bypass policy.
S033 - feature_flags_supabase_only - expect supabase route and optional rerank policy.
S034 - provider_override_mem0_with_disable_flag - expect fallback route.
S035 - provider_override_none - expect standard route.
S036 - candidate_metadata_preserved - expect metadata passthrough after branch emission.
S037 - candidate_order_after_external_rerank - expect reordered list and metadata.
S038 - candidate_order_without_external_rerank - expect source order or provider order.
S039 - timestamp_present_every_response - expect non-empty timestamp string.
S040 - next_action_reason_non_empty - expect human-readable reason string.
S041 - next_action_suggestion_optional_success - expect `None` allowed.
S042 - next_action_suggestion_present_clarify - expect suggestion text.
S043 - branch_code_constant_success - expect stable literal.
S044 - branch_code_constant_low_confidence - expect stable literal.
S045 - branch_code_constant_empty_set - expect stable literal.
S046 - branch_code_constant_channel_mismatch - expect stable literal.
S047 - branch_code_constant_rerank_bypassed - expect stable literal.
S048 - deterministic_replay_1 - run same inputs 3 times and compare semantics.
S049 - deterministic_replay_2 - run same inputs 5 times and compare semantics.
S050 - deterministic_replay_3 - run same inputs 10 times and compare semantics.
S051 - compatibility_payload_contains_context_packet - expect nested payload field.
S052 - compatibility_payload_contains_next_action - expect nested payload field.
S053 - compatibility_payload_legacy_fields_preserved - expect additive compatibility.
S054 - mcp_tool_invalid_input_validation - expect clear validation error.
S055 - mcp_tool_missing_query - expect clear validation error.
S056 - mcp_tool_unknown_mode - expect clear validation error.
S057 - mcp_tool_provider_override_unknown - expect fallback or validation error.
S058 - scenario_catalog_id_uniqueness - expect no duplicates.
S059 - scenario_catalog_tag_smoke - expect minimum smoke coverage.
S060 - scenario_catalog_tag_policy - expect policy scenarios present.
S061 - scenario_catalog_tag_edge - expect edge scenarios present.
S062 - scenario_catalog_tag_degraded - expect degraded scenarios present.
S063 - docs_table_references_existing_scenario - expect one-to-one mapping.
S064 - docs_expected_branch_matches_fixture - expect strict alignment.
S065 - docs_expected_action_matches_fixture - expect strict alignment.
S066 - docs_command_example_runs - expect command success.
S067 - report_template_has_evidence_section - expect section present.
S068 - report_template_has_regression_section - expect section present.
S069 - report_template_has_risk_section - expect section present.
S070 - report_template_has_followups_section - expect section present.
S071 - provider_metadata_includes_selected_provider - expect field present.
S072 - provider_metadata_includes_mode - expect field present.
S073 - provider_metadata_includes_skip_external_rerank - expect field present.
S074 - provider_metadata_includes_rerank_type - expect field present.
S075 - provider_metadata_includes_rerank_bypass_reason - expect field present when applicable.
S076 - provider_metadata_includes_feature_flags_snapshot - expect field present.
S077 - provider_metadata_includes_provider_status_snapshot - expect field present or justified omission.
S078 - no_magic_branch_strings_in_recall - expect constants usage.
S079 - no_provider_selection_logic_duplication - expect router usage only.
S080 - no_branch_logic_duplication - expect fallback usage only.
S081 - recall_handles_zero_top_k_input_guard - expect validation.
S082 - recall_handles_negative_threshold_guard - expect validation.
S083 - recall_handles_threshold_above_one_guard - expect validation.
S084 - recall_handles_empty_provider_list - expect empty set behavior.
S085 - recall_handles_none_feature_flags - expect defaults.
S086 - recall_handles_none_provider_status - expect defaults.
S087 - recall_handles_candidate_confidence_bounds - expect valid range or normalization.
S088 - rerank_adapter_handles_empty_candidates - expect no-op safe return.
S089 - rerank_adapter_handles_single_candidate - expect stable behavior.
S090 - rerank_adapter_handles_large_candidate_count - expect deterministic top-k behavior.
S091 - memory_adapter_returns_normalized_candidates - expect schema conformity.
S092 - memory_adapter_preserves_source_field - expect source set.
S093 - memory_adapter_handles_missing_metadata - expect default dict.
S094 - memory_adapter_handles_null_content - expect validation or sanitization.
S095 - memory_adapter_handles_duplicate_ids - expect deterministic handling.
S096 - memory_adapter_handles_special_characters - expect valid serialization.
S097 - integration_with_mcp_roundtrip_smoke - expect successful response shape.
S098 - integration_with_mcp_roundtrip_policy - expect policy metadata correctness.
S099 - integration_with_mcp_roundtrip_edge - expect safe fallback behavior.
S100 - integration_with_mcp_roundtrip_degraded - expect deterministic fallback.
S101 - manual_runbook_prerequisites_complete - expect checklist item.
S102 - manual_runbook_env_vars_documented - expect checklist item.
S103 - manual_runbook_command_sequence_linear - expect checklist item.
S104 - manual_runbook_expected_output_examples - expect checklist item.
S105 - manual_runbook_failure_triage_map - expect checklist item.
S106 - manual_runbook_rollback_steps_defined - expect checklist item.
S107 - manual_runbook_signoff_fields_defined - expect checklist item.
S108 - manual_runbook_timestamp_capture_defined - expect checklist item.
S109 - manual_runbook_operator_notes_section - expect checklist item.
S110 - manual_runbook_issue_link_section - expect checklist item.
S111 - runtime_smoke_branch_success - expect stable success behavior.
S112 - runtime_smoke_branch_low_confidence - expect stable clarify behavior.
S113 - runtime_smoke_branch_empty_set - expect stable fallback behavior.
S114 - runtime_smoke_branch_channel_mismatch - expect stable escalate behavior.
S115 - runtime_smoke_branch_rerank_bypassed - expect stable provider-native behavior.
S116 - runtime_policy_mem0_default_skip_external - expect true.
S117 - runtime_policy_supabase_allows_external - expect configurable.
S118 - runtime_policy_graphiti_opt_in - expect gated.
S119 - runtime_policy_override_documented - expect metadata reason.
S120 - runtime_policy_failure_fallback_documented - expect graceful behavior.

## APPENDIX B: Manual Validation Run Sequence (Operator Checklist)

MV001 - Confirm working tree clean enough for deterministic run.
MV002 - Confirm Python version matches project requirement.
MV003 - Install dependencies in isolated environment.
MV004 - Run baseline lint checks.
MV005 - Run baseline type checks.
MV006 - Run baseline unit tests.
MV007 - Run baseline integration smoke tests.
MV008 - Open validation runbook file.
MV009 - Open scenario catalog fixture module.
MV010 - Confirm scenario IDs match between docs and fixtures.
MV011 - Execute smoke scenario S001.
MV012 - Record expected vs actual branch for S001.
MV013 - Record expected vs actual action for S001.
MV014 - Record rerank metadata for S001.
MV015 - Execute smoke scenario S002.
MV016 - Record expected vs actual branch for S002.
MV017 - Record expected vs actual action for S002.
MV018 - Execute smoke scenario S003.
MV019 - Record expected vs actual branch for S003.
MV020 - Record expected vs actual action for S003.
MV021 - Execute smoke scenario S004.
MV022 - Record expected vs actual branch for S004.
MV023 - Record expected vs actual action for S004.
MV024 - Execute policy scenario S022.
MV025 - Verify rerank metadata no-op behavior.
MV026 - Execute policy scenario S025.
MV027 - Verify override metadata correctness.
MV028 - Execute policy scenario S026.
MV029 - Verify default bypass metadata correctness.
MV030 - Execute degraded scenario S015.
MV031 - Verify deterministic fallback provider.
MV032 - Execute degraded scenario S016.
MV033 - Verify deterministic route with mixed statuses.
MV034 - Execute edge scenario S013.
MV035 - Verify `EMPTY_SET` behavior with all providers disabled.
MV036 - Execute edge scenario S014.
MV037 - Verify `EMPTY_SET` behavior with all providers unavailable.
MV038 - Execute channel scenario S027.
MV039 - Verify `CHANNEL_MISMATCH` and `escalate` action.
MV040 - Execute deterministic replay S048.
MV041 - Confirm semantic output stability across repeats.
MV042 - Execute deterministic replay S049.
MV043 - Confirm semantic output stability across repeats.
MV044 - Execute deterministic replay S050.
MV045 - Confirm semantic output stability across repeats.
MV046 - Execute compatibility scenario S051.
MV047 - Verify `context_packet` presence.
MV048 - Execute compatibility scenario S052.
MV049 - Verify `next_action` presence.
MV050 - Execute compatibility scenario S053.
MV051 - Verify legacy field compatibility where applicable.
MV052 - Execute metadata scenario S071.
MV053 - Verify selected provider metadata present.
MV054 - Execute metadata scenario S072.
MV055 - Verify mode metadata present.
MV056 - Execute metadata scenario S073.
MV057 - Verify skip rerank metadata present.
MV058 - Execute metadata scenario S074.
MV059 - Verify rerank type metadata present.
MV060 - Execute metadata scenario S075.
MV061 - Verify rerank bypass reason metadata conditional presence.
MV062 - Execute docs alignment scenario S063.
MV063 - Verify doc references resolve to fixture IDs.
MV064 - Execute docs alignment scenario S064.
MV065 - Verify expected branches aligned.
MV066 - Execute docs alignment scenario S065.
MV067 - Verify expected actions aligned.
MV068 - Execute runbook quality scenario S101.
MV069 - Verify prerequisites section complete.
MV070 - Execute runbook quality scenario S102.
MV071 - Verify environment variables documented.
MV072 - Execute runbook quality scenario S103.
MV073 - Verify command sequence is linear and reproducible.
MV074 - Execute runbook quality scenario S104.
MV075 - Verify expected output examples are present.
MV076 - Execute runbook quality scenario S105.
MV077 - Verify triage map completeness.
MV078 - Execute runbook quality scenario S106.
MV079 - Verify rollback steps clarity.
MV080 - Execute runbook quality scenario S107.
MV081 - Verify signoff fields completeness.
MV082 - Run focused integration tests for mem0 policy.
MV083 - Run focused integration tests for non-mem0 rerank.
MV084 - Run focused integration tests for empty set behavior.
MV085 - Run focused integration tests for low confidence behavior.
MV086 - Run focused integration tests for channel mismatch behavior.
MV087 - Collect test outputs into report draft.
MV088 - Summarize branch pass count.
MV089 - Summarize branch fail count.
MV090 - List all failed scenarios with root-cause guesses.
MV091 - Map each failure to likely code area.
MV092 - Propose fix plan for each failure.
MV093 - Re-run failed scenarios only.
MV094 - Confirm previously failing scenarios pass.
MV095 - Re-run full smoke suite.
MV096 - Confirm no regressions after fixes.
MV097 - Update validation report with final evidence.
MV098 - Mark runtime acceptance criteria pass/fail.
MV099 - Capture unresolved risks if any.
MV100 - Add final operator signoff line.

## APPENDIX C: Validation Matrix Expansion

VM001 - Syntax lint pass.
VM002 - Format check pass.
VM003 - Type check pass.
VM004 - Unit contract tests pass.
VM005 - Unit router tests pass.
VM006 - Unit harness tests pass.
VM007 - Integration recall tests pass.
VM008 - Integration mcp tests pass.
VM009 - Manual smoke pass count >= required minimum.
VM010 - Manual policy pass count >= required minimum.
VM011 - Manual edge pass count >= required minimum.
VM012 - Deterministic replay pass.
VM013 - Metadata completeness pass.
VM014 - Compatibility shape pass.
VM015 - Docs alignment pass.
VM016 - Runbook completeness pass.
VM017 - Triage map completeness pass.
VM018 - Rollback steps readiness pass.
VM019 - Scenario ID uniqueness pass.
VM020 - Scenario tag coverage pass.
VM021 - Mem0 default policy pass.
VM022 - External rerank policy pass.
VM023 - Graphiti flag gating pass.
VM024 - Provider override pass.
VM025 - Provider fallback pass.
VM026 - Empty set branch pass.
VM027 - Low confidence branch pass.
VM028 - Success branch pass.
VM029 - Channel mismatch branch pass.
VM030 - Rerank bypassed branch pass.
VM031 - Next action proceed pass.
VM032 - Next action clarify pass.
VM033 - Next action fallback pass.
VM034 - Next action escalate pass.
VM035 - Context packet always present pass.
VM036 - Next action always present pass.
VM037 - Routing metadata always present pass.
VM038 - Timestamp always present pass.
VM039 - Candidate confidence bounds pass.
VM040 - Candidate metadata defaults pass.
VM041 - Candidate source set pass.
VM042 - Candidate id set pass.
VM043 - Candidate content set pass.
VM044 - Threshold boundary equal pass.
VM045 - Threshold below boundary pass.
VM046 - Threshold above boundary pass.
VM047 - Top-k boundary pass.
VM048 - Feature flag defaults pass.
VM049 - Provider status defaults pass.
VM050 - Explicit disable all providers pass.
VM051 - Explicit unavailable all providers pass.
VM052 - Degraded provider fallback pass.
VM053 - External rerank unavailable pass.
VM054 - External rerank failure fallback pass.
VM055 - Mem0 rerank unaffected by external failure pass.
VM056 - Compatibility additive fields pass.
VM057 - No field removals pass.
VM058 - No branch code renames pass.
VM059 - No action literal changes pass.
VM060 - No routing non-determinism pass.
VM061 - No unordered provider iteration bugs pass.
VM062 - No duplicate branch logic pass.
VM063 - No duplicate provider selection logic pass.
VM064 - No hidden mutable global state pass.
VM065 - No circular imports pass.
VM066 - No unintended side effects in `__init__` pass.
VM067 - No hardcoded secrets pass.
VM068 - No environment-only hidden assumptions pass.
VM069 - No speculative fields in contract pass.
VM070 - No architecture boundary violations pass.
VM071 - Retrieval module remains retrieval-only pass.
VM072 - Planning logic not leaked into retrieval pass.
VM073 - MCP tool output remains parseable pass.
VM074 - MCP tool errors are clear pass.
VM075 - MCP tool input validation pass.
VM076 - Scenario command examples execute pass.
VM077 - Scenario evidence rows complete pass.
VM078 - Scenario fail triage mapping complete pass.
VM079 - Scenario rerun process documented pass.
VM080 - Scenario signoff process documented pass.
VM081 - Execution report scaffold present pass.
VM082 - Execution report evidence captured pass.
VM083 - Execution report regressions section filled pass.
VM084 - Execution report risks section filled pass.
VM085 - Execution report followups section filled pass.
VM086 - Acceptance implementation checks complete.
VM087 - Acceptance runtime checks complete.
VM088 - Completion checklist complete.
VM089 - Memory update post-validation complete.
VM090 - README status update accurate.
VM091 - Architecture docs status update accurate.
VM092 - Tests include deterministic replay.
VM093 - Tests include metadata validation.
VM094 - Tests include policy validation.
VM095 - Tests include branch validation.
VM096 - Tests include compatibility validation.
VM097 - Tests include error handling validation.
VM098 - Tests include feature flag validation.
VM099 - Tests include provider status validation.
VM100 - Tests include override validation.
VM101 - Tests include empty candidates validation.
VM102 - Tests include low confidence validation.
VM103 - Tests include high confidence validation.
VM104 - Tests include rerank bypassed validation.
VM105 - Tests include channel mismatch validation.
VM106 - Tests include action reason validation.
VM107 - Tests include suggestion optionality validation.
VM108 - Tests include confidence summary validation.
VM109 - Tests include candidate count validation.
VM110 - Tests include threshold_met validation.
VM111 - Tests include provider metadata validation.
VM112 - Tests include rerank metadata validation.
VM113 - Tests include feature flag snapshot validation.
VM114 - Tests include provider status snapshot validation.
VM115 - Tests include route mode metadata validation.
VM116 - Tests include route provider metadata validation.
VM117 - Tests include skip external rerank metadata validation.
VM118 - Tests include rerank type metadata validation.
VM119 - Tests include rerank bypass reason metadata validation.
VM120 - Tests include timestamp format sanity validation.
VM121 - Tests include no random ordering validation.
VM122 - Tests include no flaky comparisons validation.
VM123 - Tests include deterministic semantic comparison validation.
VM124 - Tests include snapshot sanitation validation.
VM125 - Tests include fixture isolation validation.
VM126 - Tests include monkeypatch cleanup validation.
VM127 - Tests include dependency injection override validation.
VM128 - Tests include service no-op fallback validation.
VM129 - Tests include service exception handling validation.
VM130 - Tests include service normalization validation.
VM131 - Tests include contract serialization validation.
VM132 - Tests include model_dump compatibility validation.
VM133 - Tests include pydantic bound checks validation.
VM134 - Tests include literal action constraints validation.
VM135 - Tests include branch constants stability validation.
VM136 - Tests include provider status constants stability validation.
VM137 - Tests include defaults stability validation.
VM138 - Tests include docs scenario alignment validation.
VM139 - Tests include report artifact path validation.
VM140 - Tests include manual checklist completeness validation.
