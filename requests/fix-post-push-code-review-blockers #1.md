# Feature: Fix post-push code-review blockers (provider-route consistency, validate_branch gating, memory mock clear behavior)

The following plan is implementation-ready for one-pass execution. The execution agent should still validate all referenced files and rerun focused tests after each atomic task to keep blast radius low.

Pay special attention to runtime consistency between selected provider and retrieval backend, and keep validation-only behavior gated so production paths cannot force synthetic branches.

## Feature Description

This slice fixes three post-push blockers discovered in code review: (1) recall currently routes to a provider but still queries through whichever `MemoryService` instance was injected, which can drift from the selected route; (2) MCP `validate_branch` lacks strict scenario/debug gating and does not execute scenarios with their declared provider/flag context; and (3) `MemoryService.clear_mock_data()` does not fully clear mock mode, causing subsequent calls to stay pinned to empty mock results rather than fallback behavior.

## User Story

As an operator and maintainer, I want recall routing, validation scenario execution, and memory test-mode behavior to be internally consistent and safely gated, so that runtime outputs are trustworthy and validation tooling cannot accidentally distort production behavior.

## Problem Statement

Three defects currently create correctness and safety risks:

- Recall flow can report one selected provider while querying through another provider-bound memory service instance.
- `validate_branch` does not instantiate recall with scenario-specific feature flags/provider status and has no hard guard for validation-only scenarios.
- `clear_mock_data()` sets `_mock_data` to `[]` instead of `None`, so the service remains in mock branch and returns empty results indefinitely.

Together these issues reduce operator confidence, produce misleading diagnostics, and weaken deterministic validation semantics.

## Solution Statement

Apply a narrow bug-fix hardening pass across recall orchestration, MCP validation endpoint, and memory service test helpers.

- Decision 1: Make recall provider resolution explicit at retrieval time (selected route provider must map to the memory service used), because routing metadata is only valid if retrieval backend matches it.
- Decision 2: Run `validate_branch` scenarios through a scenario-scoped orchestrator and add strict validation-only/debug gating, because branch-forcing is a test affordance and should not leak into normal runtime paths.
- Decision 3: Restore canonical mock-clear behavior (`None` = no mock mode), because empty list should mean "mock mode with zero results," not "disable mock mode."
- Decision 4: Add focused regression tests for each blocker before/with implementation, because these bugs are behavior-level and require durable coverage.

## Feature Metadata

- **Feature Type**: Bug Fix
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `agents/recall.py`, `mcp_server.py`, `services/memory.py`, integration/unit tests, validation runbook
- **Dependencies**: Python 3.11, pytest, existing retrieval contracts and orchestration modules

---

## Spec Lock (for this `/planning` run)

- **Implementation mode**: runnable code + tests
- **Target repo/path**: `C:\Users\Utopia\Desktop\second-brain-fin`
- **Stack constraints**: follow existing Python + pytest + pydantic stack
- **Acceptance depth**: production-ready MVP bug-fix hardening for this slice
- **Output artifact type**: structured execution plan

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ)

- `backend/src/second_brain/agents/recall.py:54` - provider route is selected here.
- `backend/src/second_brain/agents/recall.py:80` - retrieval currently uses `self.memory_service` regardless of selected route.
- `backend/src/second_brain/mcp_server.py:49` - `validate_branch` tool logic and current scenario execution flow.
- `backend/src/second_brain/mcp_server.py:73` - `run_recall(...)` call currently ignores scenario feature flags/provider status.
- `backend/src/second_brain/services/memory.py:143` - mock data lifecycle helpers.
- `backend/src/second_brain/services/memory.py:147` - `clear_mock_data()` behavior currently sets `_mock_data` to `[]`.
- `backend/src/second_brain/validation/manual_branch_scenarios.py:23` - scenario catalog and tags used for gating.
- `tests/test_recall_flow_integration.py:111` - existing non-Mem0 path behavior assertions.
- `tests/test_manual_branch_validation_harness.py:67` - scenario-based branch validation expectations.
- `tests/test_retrieval_router_critical_findings.py:156` - metadata correctness regression style.

### New Files to Create

- `tests/test_mcp_server_validation.py` - regression tests for `validate_branch` scenario gating and context wiring.
- `tests/test_memory_service.py` - unit tests for mock data lifecycle (`set_mock_data` / `clear_mock_data`).

### Related Memories (from memory.md)

- Memory: strict gate workflow and explicit validation steps are required - Relevance: this slice is blocker cleanup and must remain tightly scoped with clear pass/fail checks.
- Memory: build order favors contract/orchestration correctness before expansion - Relevance: these fixes protect existing retrieval contract fidelity.
- Memory: pre-gate plans can miss concrete execution details - Relevance: this plan includes atomic tasks with command-level validation.

### Relevant Documentation

- `docs/architecture/conversational-retrieval-contract.md`
  - Specific section: branch/action output guarantees and operator-facing metadata expectations
  - Why: provider-route consistency and validation outputs must preserve contract semantics.
- `docs/architecture/retrieval-overlap-policy.md`
  - Specific section: Mem0 rerank bypass policy and external rerank boundaries
  - Why: provider consistency changes must not violate rerank policy assumptions.
- `docs/validation/recall-branch-manual-validation.md`
  - Specific section: scenario expectations and operator run commands
  - Why: validation gating changes must be reflected in runbook behavior.
- [pytest parametrization docs](https://docs.pytest.org/en/stable/how-to/parametrize.html)
  - Specific section: parameterized scenario testing
  - Why: scenario-gating regressions are best covered via scenario/tag matrices.

### Patterns to Follow

**Deterministic route selection with explicit outputs** (from `backend/src/second_brain/orchestration/retrieval_router.py:140`):
```python
def route_retrieval(
    request: RetrievalRequest,
    provider_status: dict[str, str] | None = None,
    feature_flags: dict[str, bool] | None = None
) -> tuple[str, dict]:
    ...
    return RouteDecision.select_route(...)
```
- Why this pattern: route decision stays deterministic and explicit (`provider`, `options`) for downstream orchestration.
- Common gotchas: do not override returned provider silently in recall.

**Recall metadata builder used in both normal and validation paths** (from `backend/src/second_brain/agents/recall.py:148`):
```python
def _build_routing_metadata(..., mode: str = "conversation") -> dict[str, Any]:
    return {
        "selected_provider": provider,
        "mode": mode,
        "skip_external_rerank": route_options_skip_rerank,
    }
```
- Why this pattern: one metadata envelope prevents divergence between execution branches.
- Common gotchas: metadata correctness is insufficient if retrieval backend is inconsistent.

**Scenario lookup and forced-branch hook** (from `backend/src/second_brain/mcp_server.py:64`):
```python
scenario = get_scenario_by_id(scenario_id)
...
response = run_recall(
    ...,
    validation_mode=True,
    force_branch=scenario.expected_branch if "validation" in scenario.tags else None,
)
```
- Why this pattern: scenario tags already express which scenarios are validation-only.
- Common gotchas: current implementation does not apply scenario provider/feature context and does not gate validation-only execution.

**Mock-path branching in memory service** (from `backend/src/second_brain/services/memory.py:49`):
```python
if self._mock_data is not None:
    results = self._search_mock(query, top_k, threshold)
else:
    results = self._search_fallback(query, top_k, threshold)
```
- Why this pattern: `None` is the canonical switch between mock mode and fallback mode.
- Common gotchas: setting `_mock_data = []` still keeps mock mode active.

---

## IMPLEMENTATION PLAN

### Phase 1: Reproduce blockers in tests

Create focused failing tests (or adjust existing ones) for each blocker before changing logic:

- provider-route mismatch in recall retrieval execution
- `validate_branch` scenario/debug gating and scenario context wiring
- mock clear lifecycle semantics in memory service

**Tasks:**
- add recall integration assertions that candidate source/provider align with selected route.
- add MCP validation tests for validation-tag scenario gating and scenario context usage.
- add memory service tests proving `clear_mock_data()` restores fallback behavior.

### Phase 2: Recall provider-route consistency fix

Update recall orchestration to use the selected provider when resolving memory retrieval dependency.

**Tasks:**
- introduce internal provider-aware memory service resolution.
- preserve current injectable behavior when injected service provider already matches route.
- keep rerank metadata and response shape unchanged.

### Phase 3: validate_branch scenario gating fix

Update MCP validation execution path to respect scenario metadata and enforce validation-only constraints.

**Tasks:**
- gate validation-only branch-forcing behavior behind explicit condition(s).
- execute scenario with its declared `feature_flags` and `provider_status`.
- preserve non-validation scenario deterministic evaluation.

### Phase 4: Memory mock clear behavior fix

Make mock lifecycle semantics explicit and intuitive.

**Tasks:**
- change `clear_mock_data()` to disable mock mode (`None`).
- ensure empty mock list still works when explicitly set via `set_mock_data([])`.
- add regression tests for both transitions.

### Phase 5: Validation + docs alignment

Run targeted validation and update operator-facing runbook notes where behavior changed.

**Tasks:**
- execute focused tests for recall, mcp validation, memory service.
- run broader retrieval suite to ensure no regressions.
- update runbook section for validation scenario gating if behavior/usage changes.

---

## STEP-BY-STEP TASKS

### UPDATE tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add regression test(s) that force routing to non-default provider and assert retrieval candidates/source align with `response.routing_metadata["selected_provider"]`. Include a case where injected `MemoryService(provider="mem0")` but route selects `supabase`, proving recall now resolves provider-consistent backend before search.
- **PATTERN**: `tests/test_recall_flow_integration.py:111`, `tests/test_recall_flow_integration.py:133`
- **IMPORTS**: existing imports plus any helper import already used in file (`MemoryService`, `VoyageRerankService`, `RetrievalRequest`).
- **GOTCHA**: avoid asserting internal implementation detail (object identity); assert observable behavior (`selected_provider`, candidate `source`, rerank metadata).
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py -q`

### CREATE tests/test_mcp_server_validation.py

- **IMPLEMENT**: Add async pytest tests for MCP `validate_branch` covering:
  1) unknown scenario returns failure payload,
  2) non-validation scenario executes without forced branch,
  3) validation-tagged scenario branch forcing is gated as designed,
  4) scenario-provided flags/status are respected (not defaults).
- **PATTERN**: `tests/test_manual_branch_validation_harness.py:20`, `backend/src/second_brain/mcp_server.py:49`
- **IMPORTS**: `import pytest`, `from second_brain.mcp_server import MCPServer`, scenario helpers from `second_brain.validation.manual_branch_scenarios` as needed.
- **GOTCHA**: if using async tests, apply project-consistent async execution approach (e.g., `pytest.mark.asyncio` if available); do not introduce new async plugins unless already present.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_mcp_server_validation.py -q`

### CREATE tests/test_memory_service.py

- **IMPLEMENT**: Add unit tests verifying mock data lifecycle:
  1) with `set_mock_data([...])` service uses mock results,
  2) with `set_mock_data([])` service stays in mock mode and returns empty,
  3) after `clear_mock_data()` service uses fallback deterministic path again.
- **PATTERN**: `tests/test_recall_flow_integration.py:40`, `backend/src/second_brain/services/memory.py:49`
- **IMPORTS**: `from second_brain.services.memory import MemoryService, MemorySearchResult`
- **GOTCHA**: assert on returned candidates and metadata (`raw_count`, provider) to avoid brittle query-string assumptions.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_memory_service.py -q`

### UPDATE backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Introduce provider-aware memory service resolution in `RecallOrchestrator.run`:
  - If selected provider matches injected `self.memory_service.provider`, reuse existing instance.
  - If mismatched, create/resolve provider-specific `MemoryService` (using existing deps factory or local helper) and perform `search_memories` through that resolved service.
  - Keep existing response contracts and metadata keys intact.
- **PATTERN**: `backend/src/second_brain/agents/recall.py:54`, `backend/src/second_brain/deps.py:28`
- **IMPORTS**: add `create_memory_service` from `second_brain.deps` if used; keep typing imports explicit.
- **GOTCHA**: do not mutate shared injected service provider at runtime; resolve provider-specific instance per run or via safe cache.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py tests/test_retrieval_router_critical_findings.py -q`

### REFACTOR backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Add small internal helper (e.g., `_resolve_memory_service_for_provider(provider: str) -> MemoryService`) to isolate provider-service selection from run logic. Keep method private and deterministic.
- **PATTERN**: existing helper extraction style in `backend/src/second_brain/agents/recall.py:148`
- **IMPORTS**: no new third-party imports.
- **GOTCHA**: helper must not obscure runtime behavior; keep logic straightforward and test-covered.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py -q`

### UPDATE backend/src/second_brain/mcp_server.py

- **IMPLEMENT**: Replace direct `run_recall(...)` usage in `validate_branch` with scenario-scoped orchestrator execution so scenario `feature_flags` and `provider_status` are actually applied. Maintain existing response payload fields.
- **PATTERN**: `tests/test_manual_branch_validation_harness.py:75` (orchestrator with scenario context), `backend/src/second_brain/mcp_server.py:73`
- **IMPORTS**: `RecallOrchestrator`, `MemoryService`, `VoyageRerankService` (module-level or local import consistent with file style).
- **GOTCHA**: keep tool response backward-compatible (`success`, expected/actual fields, match booleans).
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_mcp_server_validation.py -q`

### UPDATE backend/src/second_brain/mcp_server.py

- **IMPLEMENT**: Add explicit validation scenario gating logic:
  - Validation-tag scenarios can force branch only when validation/debug policy allows.
  - Non-validation-tag scenarios should never force branch.
  - Return clear error/denial payload when gated scenario execution is disallowed.
- **PATTERN**: `backend/src/second_brain/mcp_server.py:96` (`debug_mode` toggles already exist), `backend/src/second_brain/validation/manual_branch_scenarios.py:227`
- **IMPORTS**: no external imports needed.
- **GOTCHA**: do not silently ignore denied validation scenarios; explicit failure reason improves operator UX.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_mcp_server_validation.py -q`

### UPDATE backend/src/second_brain/services/memory.py

- **IMPLEMENT**: Change `clear_mock_data()` to set `_mock_data = None` and update docstring to clarify semantics: clear disables mock mode and restores fallback search path.
- **PATTERN**: `backend/src/second_brain/services/memory.py:49` mock-mode branch condition.
- **IMPORTS**: none.
- **GOTCHA**: preserve `set_mock_data([])` behavior for explicit empty mock scenarios used by tests.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_memory_service.py tests/test_recall_flow_integration.py -q`

### UPDATE tests/test_manual_branch_validation_harness.py

- **IMPLEMENT**: Add scenario(s) or assertions ensuring validation-only tagged scenarios are not treated as normal smoke/policy paths unless expected. Keep deterministic operator-friendly assertion messages.
- **PATTERN**: `tests/test_manual_branch_validation_harness.py:58`, `tests/test_manual_branch_validation_harness.py:224`
- **IMPORTS**: existing imports; add `get_scenario_by_id` usage if needed.
- **GOTCHA**: avoid coupling harness to MCP-specific debug flags unless explicitly intended.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py -q`

### UPDATE docs/validation/recall-branch-manual-validation.md

- **IMPLEMENT**: Document validation scenario gating behavior and expected usage for validation-only scenarios (e.g., S027). Clarify that scenario context (flags/status) is now honored by `validate_branch` tool.
- **PATTERN**: existing section formatting in same file (`Quick Start`, `Branch Scenario Execution Commands`).
- **IMPORTS**: N/A
- **GOTCHA**: keep runbook aligned with actual command behavior; remove outdated expectations if changed.
- **VALIDATE**: `python -m pytest -q tests/test_mcp_server_validation.py`

### VALIDATE targeted blocker fix set

- **IMPLEMENT**: Run blocker-focused test group after all updates.
- **PATTERN**: command style from existing plans (`PYTHONPATH=backend/src pytest ... -q`).
- **IMPORTS**: N/A
- **GOTCHA**: run from repo root to ensure `pythonpath` resolution is consistent.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py tests/test_mcp_server_validation.py tests/test_memory_service.py tests/test_manual_branch_validation_harness.py -q`

### VALIDATE retrieval regression surface

- **IMPLEMENT**: Re-run existing router/fallback critical suites to confirm no side-effects.
- **PATTERN**: `tests/test_retrieval_router_policy.py`, `tests/test_retrieval_router_critical_findings.py`
- **IMPORTS**: N/A
- **GOTCHA**: provider-resolution fix in recall should not alter pure router tests.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py tests/test_retrieval_router_critical_findings.py tests/test_context_packet_contract.py -q`

---

## TESTING STRATEGY

### Unit Tests

- Memory service lifecycle semantics:
  - clear disables mock mode (`None`), not empty mock mode (`[]`).
  - explicit empty mock remains a valid test scenario.
- MCP validation endpoint behavior:
  - scenario lookup failures,
  - gating decisions,
  - forced-branch behavior only for eligible scenarios.

### Integration Tests

- Recall runtime path:
  - selected provider aligns with retrieval backend behavior.
  - routing metadata and candidate source are coherent.
  - rerank policy remains intact across provider switching.
- Manual scenario harness:
  - scenario expectations remain deterministic after gating changes.

### Edge Cases

- Route selects provider different from injected memory service provider.
- Validation-tag scenario requested while validation/debug gate is disabled.
- Unknown scenario ID in MCP tool call.
- `set_mock_data([])` followed by `clear_mock_data()` and repeated search.
- Mixed provider status snapshots during scenario execution.

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
PYTHONPATH=backend/src pytest tests/test_memory_service.py tests/test_mcp_server_validation.py -q
```

### Level 4: Integration Tests
```bash
PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py tests/test_manual_branch_validation_harness.py -q
```

### Level 5: Additional Regression Validation
```bash
PYTHONPATH=backend/src pytest tests/test_retrieval_router_policy.py tests/test_retrieval_router_critical_findings.py tests/test_context_packet_contract.py -q
```

### Manual Validation

1. Execute one non-validation scenario via MCP `validate_branch` and confirm natural branch evaluation (no forced branch).
2. Execute one validation-tag scenario with gate disabled and confirm explicit denial behavior (or documented allowed behavior if debug enabled).
3. Enable debug/validation gate (if required by implementation), rerun validation-tag scenario, confirm expected forced branch and action.
4. Compare `selected_provider` and returned candidate `source` in at least one supabase-routed scenario.

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] Recall uses provider-consistent memory retrieval based on selected route.
- [x] Routing metadata remains shape-compatible and value-consistent with runtime provider path.
- [x] `validate_branch` executes scenarios with scenario-defined flags/status context.
- [x] Validation-only scenario behavior is explicitly gated and test-covered.
- [x] `clear_mock_data()` disables mock mode (restores fallback mode).
- [x] New/updated tests for all three blockers pass.
- [x] Existing retrieval router/fallback suites show no regressions.

### Runtime (verify after testing/deployment)

- [ ] Operator-visible outputs no longer show provider-route drift.
- [ ] Validation tooling cannot force synthetic branches outside intended gating policy.
- [ ] Manual validation runbook steps produce expected outcomes with updated gating behavior.

---

## COMPLETION CHECKLIST

- [x] Added failing/targeted tests for each blocker.
- [x] Implemented recall provider-resolution fix.
- [x] Implemented `validate_branch` scenario context + gating fix.
- [x] Implemented memory mock clear semantics fix.
- [x] Updated validation docs where behavior changed.
- [x] Ran all validation commands successfully.
- [x] Confirmed no regressions in existing retrieval tests.

---

## NOTES

### Key Design Decisions
- Keep scope limited to blocker fixes only; no new retrieval features.
- Prefer local helper extraction over broad refactors to minimize risk.
- Treat validation gating as explicit policy, not implicit side-effect.

### Risks
- Risk: provider-aware memory resolution may affect tests relying on injected singleton behavior.
  - Mitigation: assert contract-level outputs and preserve reuse when provider already matches.
- Risk: stricter validation gating could break existing ad-hoc operator workflows.
  - Mitigation: document behavior clearly and include explicit denial messages.
- Risk: mock lifecycle change could shift expectations in existing tests.
  - Mitigation: add direct lifecycle unit tests and keep `set_mock_data([])` semantics unchanged.

### Alternatives Considered
- Keep existing recall injection model and only patch metadata: rejected because it hides real provider drift rather than fixing it.
- Leave `validate_branch` on `run_recall` defaults: rejected because scenario data is then unused and validation outcomes can be misleading.
- Keep `clear_mock_data()` returning empty mock list behavior: rejected because it conflates two distinct states (`clear` vs `explicit empty`).

### Confidence Score: 8.5/10
- **Strengths**: blockers are well-scoped, code touchpoints are clear, regression tests are straightforward.
- **Uncertainties**: exact debug-gating policy for validation-tag scenarios may need minor tuning based on operator expectations.
- **Mitigations**: encode gating policy explicitly in tests + runbook and keep payload-level compatibility.
