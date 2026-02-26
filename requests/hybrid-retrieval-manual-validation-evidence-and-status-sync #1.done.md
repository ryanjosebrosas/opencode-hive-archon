# Feature: Hybrid Retrieval Manual Validation Evidence + Status Sync

## Feature Description

Run a focused post-integration slice that converts existing automated/manual validation scaffolding into explicit operator evidence, then synchronize project status docs so the current branch state is accurate and review-ready.

## User Story

As a maintainer of the hybrid retrieval orchestrator, I want a reproducible validation evidence bundle and aligned status docs, so that we can confidently move forward without ambiguity about branch behavior or feature completion.

## Problem Statement

Core integration code and tests are in place, but project state still shows drift between workflow metadata and implementation reality. We need one tight slice to (1) execute and capture manual-branch evidence from the existing harness/runbook and (2) update status artifacts that still read as pending or stale.

## Solution Statement

Use a validation-first, no-new-logic slice:
- Decision 1: Reuse existing orchestrator/harness paths, because behavior is already implemented and should be verified, not redesigned.
- Decision 2: Capture evidence in docs/reports, because this is a trust and traceability gap, not a code architecture gap.
- Decision 3: Update only status-bearing docs, because YAGNI and single-outcome scope control.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `docs/validation/`, `requests/execution-reports/`, `AGENTS.md` (status block only), `requests/PR-UPDATE.md` (release summary sync)
- **Dependencies**: pytest, existing recall integration tests, existing manual scenario fixtures

### Slice Guardrails (Required)

- **Single Outcome**: A committed evidence-backed validation report plus synchronized status docs for the hybrid retrieval slice.
- **Expected Files Touched**: `docs/validation/recall-branch-manual-validation.md`, `requests/execution-reports/hybrid-retrieval-manual-validation-evidence #1.md`, `AGENTS.md`, `requests/PR-UPDATE.md`.
- **Scope Boundary**: No new retrieval business logic, no contract schema redesign, no router/fallback behavior changes.
- **Split Trigger**: If validation reveals branch correctness defects requiring production logic edits, stop and create a new fix slice plan.

---

## CONTEXT REFERENCES

### Relevant Codebase Files

- `backend/src/second_brain/agents/recall.py:38` - Orchestrator runtime path and routing metadata production.
- `backend/src/second_brain/agents/recall.py:107` - Validation mode + forced branch hook behavior.
- `backend/src/second_brain/validation/manual_branch_scenarios.py:23` - Scenario catalog and expected outcomes.
- `tests/test_manual_branch_validation_harness.py` - Automated scenario assertion suite used as evidence base.
- `tests/test_recall_flow_integration.py:188` - Forced-branch validation tests for CHANNEL_MISMATCH and related branches.
- `docs/validation/recall-branch-manual-validation.md:184` - Evidence capture table template to populate.
- `requests/PR-UPDATE.md:1` - Current completion narrative that should align with validated evidence.

### New Files to Create

- `requests/execution-reports/hybrid-retrieval-manual-validation-evidence #1.md` - Execution evidence artifact for this slice.

### Related Memories (from memory.md)

- Memory: Incremental-by-default slices with full validation every loop - Relevance: this slice is validation-only but still runs full gates.
- Memory: Avoid mixed-scope loops - Relevance: keep this slice to evidence + status sync only.
- Memory: Execution report timing (save report first, then present) - Relevance: report file is first-class output.
- Memory: Pre-gate plans may miss required metadata - Relevance: status docs must reflect validated reality, not stale intent.

### Relevant Documentation

- [Pytest Usage](https://docs.pytest.org/en/stable/how-to/usage.html)
  - Specific section: Selecting tests and verbose mode
  - Why: execute targeted scenario classes and produce precise evidence quickly.
- [Pydantic v2 Models](https://docs.pydantic.dev/latest/)
  - Specific section: model output/validation behavior
  - Why: helps interpret envelope fields in validation output checks.

### Patterns to Follow

**Deterministic metadata assertions** (from `tests/test_recall_flow_integration.py:160`):
```python
results = []
for _ in range(5):
    response = orchestrator.run(request)
    results.append({
        "branch": response.context_packet.summary.branch,
        "action": response.next_action.action,
        "provider": response.routing_metadata["selected_provider"],
        "rerank_type": response.routing_metadata["rerank_type"],
    })
assert all(r == results[0] for r in results)
```
- Why this pattern: evidence must prove repeatability, not one-off success.
- Common gotchas: do not compare timestamp fields for deterministic assertions.

**Scenario-driven validation** (from `backend/src/second_brain/validation/manual_branch_scenarios.py:23`):
```python
def get_all_scenarios() -> list[BranchScenario]:
    return [
        BranchScenario(
            id="S001",
            description="Conversation Mem0 high confidence",
            ...
        ),
    ]
```
- Why this pattern: single source of truth for expected branch/action outcomes.
- Common gotchas: status docs must not invent scenario outcomes outside fixture definitions.

---

## IMPLEMENTATION PLAN

### Phase 1: Baseline Verification

Run full validation gates for the existing hybrid retrieval integration to establish baseline pass/fail state.

**Tasks:**
- Execute lint and type checks.
- Execute targeted unit + integration test suites.
- Capture outputs in a timestamped execution report file.

### Phase 2: Manual Evidence Capture

Run scenario-focused commands from the existing runbook and populate evidence fields with actual results.

**Tasks:**
- Execute smoke/policy/edge/degraded scenario subsets.
- Capture expected vs actual branch/action/rerank fields.
- Record discrepancies and triage pointers (if any).

### Phase 3: Status Synchronization

Update status artifacts to match verified state and reference the report artifact.

**Tasks:**
- Update current implementation status wording in `AGENTS.md`.
- Update release summary wording in `requests/PR-UPDATE.md`.
- Ensure status artifacts reference manual validation artifact location.

### Phase 4: Exit Criteria Check

Confirm this slice stays non-invasive and passes all acceptance checks.

**Tasks:**
- Re-run quick smoke checks after doc updates.
- Confirm no source-code behavior changes were introduced.
- Mark checklist and handoff notes in report.

---

## STEP-BY-STEP TASKS

### CREATE requests/execution-reports/

- **IMPLEMENT**: Ensure report directory exists before writing evidence artifact; if missing, create it.
- **PATTERN**: Execution report location convention from `AGENTS.md:295`.
- **IMPORTS**: None
- **GOTCHA**: Directory is gitignored by design; create folder without forcing tracked report files unless requested.
- **VALIDATE**: `python -c "import os; print(os.path.isdir('requests/execution-reports'))"`

### UPDATE requests/execution-reports/hybrid-retrieval-manual-validation-evidence #1.md

- **IMPLEMENT**: Create report with sections: environment, command log, validation pyramid outputs, scenario evidence table, issues found, follow-up recommendation.
- **PATTERN**: `requests/code-loops/memory-service-real-provider-adapter-loop-report #1.md:1` report structure (summary -> findings -> validation -> follow-up).
- **IMPORTS**: None
- **GOTCHA**: Evidence table entries must be factual command outputs; no pre-filled pass claims.
- **VALIDATE**: `python -m pytest -q tests/test_manual_branch_validation_harness.py`

### UPDATE docs/validation/recall-branch-manual-validation.md

- **IMPLEMENT**: Fill Evidence Capture table rows for scenarios executed in this slice and add run timestamp + operator notes section.
- **PATTERN**: Existing table template at `docs/validation/recall-branch-manual-validation.md:188`.
- **IMPORTS**: None
- **GOTCHA**: Keep expected values unchanged; only add actual values and pass/fail evidence.
- **VALIDATE**: `python -m pytest -q tests/test_recall_flow_integration.py -k "ValidationModeForcedBranches or deterministic"`

### UPDATE AGENTS.md

- **IMPLEMENT**: Align "Current Implementation Status" for hybrid retrieval to reflect validated integration and note any remaining runtime rollout work only.
- **PATTERN**: Status bullets under AGENTS implementation section.
- **IMPORTS**: None
- **GOTCHA**: Do not rewrite methodology sections; touch status lines only.
- **VALIDATE**: `ruff check backend/src tests`

### UPDATE requests/PR-UPDATE.md

- **IMPLEMENT**: Align summary/results counts and status claims with the latest validation evidence from this slice; add explicit pointer to execution report path.
- **PATTERN**: Existing summary + validation table format in `requests/PR-UPDATE.md:1`.
- **IMPORTS**: None
- **GOTCHA**: Do not inflate totals; only report results produced by executed commands.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py tests/test_recall_flow_integration.py -q`

### RUN validation command bundle

- **IMPLEMENT**: Execute all required commands in Validation Commands section; copy outputs into execution report.
- **PATTERN**: 5-level pyramid from `sections/02_piv_loop.md` and existing runbook command blocks.
- **IMPORTS**: None
- **GOTCHA**: If any gate fails, stop status-sync edits and create follow-up fix plan.
- **VALIDATE**: `mypy backend/src/second_brain && PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py tests/test_recall_flow_integration.py -q`

---

## TESTING STRATEGY

### Unit Tests

- Validate scenario integrity and expected mappings in `tests/test_manual_branch_validation_harness.py`.

### Integration Tests

- Validate full recall envelope behavior and forced branch paths in `tests/test_recall_flow_integration.py`.

### Edge Cases

- Validation-tagged scenarios executed without debug mode should remain gated.
- Mem0 path must not regress into external rerank by default.
- Metadata mode must match request mode across `fast`, `accurate`, `conversation`.

---

## VALIDATION COMMANDS

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
PYTHONPATH=backend/src pytest tests/test_context_packet_contract.py tests/test_retrieval_router_policy.py tests/test_manual_branch_validation_harness.py -q
```

### Level 4: Integration Tests
```bash
PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py -q
```

### Level 5: Manual Validation

1. Run smoke scenarios and fill S001-S004 actual results.
2. Run edge/degraded/policy scenarios (at minimum S013, S014, S015, S027, S022).
3. Compare expected vs actual branch/action/rerank columns.
4. Record pass/fail counts and triage notes.

### Level 6: Additional Validation (Optional)

- Run MCP `validate_branch` for S027 with debug mode enabled and record gated vs allowed behavior.

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] Validation report file exists with command outputs and scenario evidence.
- [x] Runbook evidence table is populated for executed scenarios.
- [x] AGENTS status text is aligned with validated state.
- [x] PR update summary is aligned with validated state.
- [x] No retrieval runtime logic files changed in this slice.

### Runtime (verify after testing/deployment)

- [x] All required scenario branches produce expected outcomes.
- [x] Deterministic replay remains stable.
- [x] Validation evidence is sufficient for reviewer signoff.

---

## COMPLETION CHECKLIST

- [x] All tasks completed in order
- [x] Each task validation passed
- [x] Full validation pyramid executed
- [x] Evidence and status docs synchronized
- [x] Follow-up slice documented if failures found

---

## NOTES

### Key Design Decisions
- Treat this as a verification slice, not an implementation slice.
- Prefer traceable evidence artifacts over narrative-only status updates.

### Risks
- Risk: status docs drift again after future code changes. Mitigation: include report path in status notes.
- Risk: hidden environment differences affect scenario results. Mitigation: capture env details in report header.

### Confidence Score: 8.7/10
- **Strengths**: existing integration and test harness are already present and extensive.
- **Uncertainties**: real-provider environment variance can alter some scenario outcomes.
- **Mitigations**: focus on deterministic harness scenarios and annotate environment-specific deviations.
