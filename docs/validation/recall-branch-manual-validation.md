# Manual Branch Validation Runbook

**Purpose**: Repeatable operator validation for all retrieval branches  
**Version**: 1.1.0  
**Last Updated**: 2026-02-25

---

## Changelog

### v1.1.0 (2026-02-25)
- **Critical Fix**: Provider override now gated by health/feature checks
- **Critical Fix**: Missing provider status defaults to `available` for enabled providers
- **Critical Fix**: Rerank semantics corrected for SUCCESS branch (non-mem0)
- **Enhancement**: Mode propagation verified for all request modes

---

## Prerequisites Checklist

- [ ] Working tree clean (no uncommitted changes)
- [ ] Python 3.11+ installed
- [ ] Dependencies installed: `pip install pydantic pytest`
- [ ] Test environment ready (isolated from production)

---

## Environment Setup

```bash
# Set PYTHONPATH for imports
export PYTHONPATH=backend/src  # Unix/macOS
$env:PYTHONPATH = "backend/src"  # Windows PowerShell

# Verify installation
python -c "from second_brain.agents.recall import run_recall; print('OK')"
```

---

## Quick Start: Run All Validation Scenarios

```bash
# Run smoke scenarios (minimum required)
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestSmokeScenarios -v

# Run policy scenarios
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestPolicyScenarios -v

# Run edge scenarios
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestEdgeScenarios -v

# Run degraded scenarios
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestDegradedScenarios -v
```

---

## Branch Scenario Execution Commands

### S001: Conversation Mem0 High Confidence

```bash
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestSmokeScenarios::test_smoke_scenario_branch[S001] -v
```

**Expected**:
- Branch: `RERANK_BYPASSED`
- Action: `proceed`
- Rerank Type: `provider-native`

---

### S002: Conversation Mem0 No Candidates

```bash
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestSmokeScenarios::test_smoke_scenario_branch[S002] -v
```

**Expected**:
- Branch: `EMPTY_SET`
- Action: `fallback`
- Rerank Type: `none`

---

### S003: Conversation Mem0 Low Confidence

```bash
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestSmokeScenarios::test_smoke_scenario_branch[S003] -v
```

**Expected**:
- Branch: `LOW_CONFIDENCE`
- Action: `clarify`
- Rerank Type: `provider-native`

---

### S004: Conversation Supabase High Confidence

```bash
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestSmokeScenarios::test_smoke_scenario_branch[S004] -v
```

**Expected**:
- Branch: `SUCCESS`
- Action: `proceed`
- Rerank Type: `external`

---

### S013: All Providers Disabled

```bash
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestEdgeScenarios::test_all_providers_disabled_returns_empty_set -v
```

**Expected**:
- Branch: `EMPTY_SET`
- Action: `fallback`

---

### S015: Mem0 Degraded Fallback

```bash
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py::TestDegradedScenarios::test_degraded_mem0_falls_back_to_supabase -v
```

**Expected**:
- Branch: `SUCCESS` or `RERANK_BYPASSED`
- Action: `proceed`

---

### S027: Channel Mismatch (Validation Mode)

```bash
PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py::TestValidationModeForcedBranches::test_force_channel_mismatch -v
```

**Expected**:
- Branch: `CHANNEL_MISMATCH`
- Action: `escalate`

> **Note**: S027 is a validation-tagged scenario. When using the MCP `validate_branch` tool,
> validation-tagged scenarios require debug mode to be enabled for forced branch execution.
> Without debug mode, the tool returns a gated response with `success: false` and `gated: true`.

---

## Validation Scenario Gating

The MCP `validate_branch` tool enforces strict gating for validation-only scenarios:

| Scenario Type | Debug Mode Off | Debug Mode On |
|---------------|----------------|---------------|
| Non-validation (smoke, policy, edge) | Natural evaluation | Natural evaluation |
| Validation-tagged | **Gated** (error response) | Forced branch execution |

### Debug Mode Usage

```python
from second_brain.mcp_server import MCPServer

server = MCPServer()
server.enable_debug_mode()  # Allow validation-tagged scenarios
result = await server.validate_branch("S027")
# result["forced_branch"] == "CHANNEL_MISMATCH"
# result["gated"] == False
```

### Scenario Context

The `validate_branch` tool now honors scenario-defined context:
- `feature_flags` from scenario are used for routing decisions
- `provider_status` from scenario are used for provider selection

This ensures validation outcomes reflect the scenario's intended environment, not global defaults.

---

## Evidence Capture Template

Use this table to record validation results:

| Scenario ID | Description | Expected Branch | Actual Branch | Expected Action | Actual Action | Rerank Type | Pass/Fail | Notes |
|-------------|-------------|-----------------|---------------|-----------------|---------------|-------------|-----------|-------|
| S001 | Conversation Mem0 high confidence | RERANK_BYPASSED | RERANK_BYPASSED | proceed | proceed | provider-native | PASS | |
| S002 | Conversation Mem0 no candidates | EMPTY_SET | EMPTY_SET | fallback | fallback | none | PASS | |
| S003 | Conversation Mem0 low confidence | LOW_CONFIDENCE | LOW_CONFIDENCE | clarify | clarify | provider-native | PASS | |
| S004 | Conversation Supabase high confidence | SUCCESS | SUCCESS | proceed | proceed | external | PASS | |
| S013 | All providers disabled | EMPTY_SET | EMPTY_SET | fallback | fallback | none | PASS | |
| S014 | All providers unavailable | EMPTY_SET | EMPTY_SET | fallback | fallback | none | PASS | |
| S015 | Mem0 degraded fallback | LOW_CONFIDENCE | LOW_CONFIDENCE | clarify | clarify | none | PASS | Falls back to supabase |
| S016 | Mem0 available, Supabase degraded | RERANK_BYPASSED | RERANK_BYPASSED | proceed | proceed | provider-native | PASS | |
| S022 | Rerank service disabled | SUCCESS | SUCCESS | proceed | proceed | none | PASS | |
| S025 | Mem0 external override on | RERANK_BYPASSED | RERANK_BYPASSED | proceed | proceed | provider-native | PASS | Mem0 policy skips external |
| S026 | Mem0 external override off | RERANK_BYPASSED | RERANK_BYPASSED | proceed | proceed | provider-native | PASS | |
| S027 | Channel mismatch validation | CHANNEL_MISMATCH | CHANNEL_MISMATCH | escalate | escalate | none | PASS | Requires validation_mode |
| S048 | Deterministic replay test | RERANK_BYPASSED | RERANK_BYPASSED | proceed | proceed | provider-native | PASS | |

**Evidence Run**: 2026-02-26 | **Operator**: AI Agent | **Total**: 13/13 PASS | **Report**: `requests/execution-reports/hybrid-retrieval-manual-validation-evidence #1.md`

---

## Pass/Fail Criteria

### Pass
- All smoke scenarios (S001-S004) produce expected branch + action
- All policy scenarios have correct rerank metadata
- Deterministic replay tests show identical results across runs

### Fail
- Any smoke scenario produces unexpected branch or action
- Mem0 path applies external rerank (policy violation)
- Non-deterministic behavior detected

---

## Triage Guide: Branch Mismatches

| Symptom | Likely Root Cause | File to Check |
|---------|------------------|---------------|
| Wrong provider selected | Router logic drift | `orchestration/retrieval_router.py` |
| Missing rerank metadata | Service wrapper gap | `services/voyage.py` |
| Branch code mismatch | Fallback emitter logic | `orchestration/fallbacks.py` |
| Non-deterministic results | Unordered collections | `agents/recall.py` (line ~40) |
| EMPTY_SET when should succeed | Provider status check | `deps.py` |
| Override selects unavailable provider | Override gating failure | `orchestration/retrieval_router.py:168-176` |
| Missing status causes false none | Status normalization failure | `orchestration/retrieval_router.py:5-29` |
| Mode mismatch in metadata | Mode propagation failure | `agents/recall.py:170-187` |

### Critical Fix Notes

1. **Override Health-Gating Rule**: Provider override requests are now validated against both feature flags AND provider health status. Override is rejected if provider is disabled, unavailable, or degraded.

2. **Missing-Status Normalization Rule**: When provider status is missing from the snapshot, enabled providers default to `available` status. This prevents false `none` routing when health snapshots are incomplete.

3. **Mode Fidelity Check**: Routing metadata `mode` field now reliably reflects the request mode (`fast`, `accurate`, `conversation`) rather than being hardcoded.

---

## Rollback Criteria

Roll back to previous commit if:
1. ≥2 smoke scenarios fail with same root cause
2. Mem0 duplicate-rerank regression detected
3. Deterministic behavior breaks

**Rollback Steps**:
```bash
git stash
git checkout <previous-commit>
PYTHONPATH=backend/src pytest tests/test_manual_branch_validation_harness.py -v
```

---

## Operator Signoff

| Field | Value |
|-------|-------|
| Operator | |
| Date | |
| Scenarios Run | |
| Pass Count | |
| Fail Count | |
| Regression Detected | Yes / No |
| Signoff | |

---

## Appendix A: Full Scenario Catalog

See `backend/src/second_brain/validation/manual_branch_scenarios.py` for complete scenario definitions.

## Appendix B: Related Documentation

- `docs/architecture/conversational-retrieval-contract.md` — Branch semantics
- `docs/architecture/retrieval-overlap-policy.md` — Rerank policy
- `docs/architecture/retrieval-planning-separation.md` — Module boundaries

## Appendix C: Validation Commands

```bash
# Level 1: Lint
ruff check backend/src tests

# Level 2: Type check
mypy backend/src/second_brain --ignore-missing-imports

# Level 3: Unit tests
PYTHONPATH=backend/src pytest tests/test_context_packet_contract.py tests/test_retrieval_router_policy.py -q

# Level 4: Integration tests
PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py tests/test_manual_branch_validation_harness.py -q
```
