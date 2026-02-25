# Feature: Retrieval Trace — Lightweight Structured Tracing for Recall Pipeline

## Feature Description

Add structured trace records to the retrieval pipeline so every call through `RecallOrchestrator.run()` produces a `RetrievalTrace` capturing timing, routing decisions, candidate statistics, rerank behavior, and branch outcomes. Traces are Pydantic models collected via an optional in-memory collector injected into the orchestrator. No external dependencies, no performance overhead when disabled.

## User Story

As a developer operating the Second Brain retrieval system, I want structured trace records for every retrieval call, so that I can inspect pipeline behavior, debug routing decisions, and establish a foundation for future eval scoring without guessing from log output.

## Problem Statement

The retrieval pipeline currently returns a `RetrievalResponse` with routing metadata, but there is no structured record of the full pipeline lifecycle — timing, intermediate states, or historical access. Debugging requires re-running scenarios and manually inspecting response fields. There is no way to compare behavior across runs, measure latency, or feed pipeline data into future eval harnesses. The `routing_metadata` dict is useful but ad-hoc; it lacks timestamps, duration, and pre-rerank candidate counts.

## Solution Statement

Build a trace layer using the same Pydantic-first contract pattern established by the existing retrieval contracts.

- Decision 1: Pure Pydantic `RetrievalTrace` model — because it matches the project's contract-first architecture (ContextPacket, NextAction, RetrievalResponse are all Pydantic). Serializable, testable, no runtime dependencies.
- Decision 2: Optional `TraceCollector` injection into orchestrator — because tracing must not break existing behavior. When no collector is provided, the orchestrator works identically to today. Backwards compatible by default.
- Decision 3: In-memory collector with callback hook — because YAGNI. The simplest useful collector stores traces in a list and optionally calls a callback. This is enough for testing, debugging, and future eval integration. File/DB/OTel exporters can be added later via the callback.
- Decision 4: No Python `logging` for trace data — because traces are structured data records, not log lines. The existing `logging` in `memory.py` handles operational concerns (provider failures, SDK errors). Trace records serve a different purpose: pipeline observability with queryable fields.
- Decision 5: Trace ID propagated in `routing_metadata` — because consumers of `RetrievalResponse` (MCP server, tests) can correlate responses to traces without changing the response schema.

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `backend/src/second_brain/contracts/`, `backend/src/second_brain/services/`, `backend/src/second_brain/agents/recall.py`, `backend/src/second_brain/mcp_server.py`
- **Dependencies**: `pydantic>=2.0` (already installed), `uuid` (stdlib), `time` (stdlib)

### Slice Guardrails (Required)

- **Single Outcome**: Every `RecallOrchestrator.run()` call can optionally produce a structured `RetrievalTrace` record accessible via an injected `TraceCollector`.
- **Expected Files Touched**: 8 files (3 CREATE, 5 UPDATE) — see New Files to Create and task list below.
- **Scope Boundary**: No eval scoring, no external exporters (OTel/Langfuse/etc.), no persistent storage (DB/file), no dashboard/UI, no changes to branch determination logic.
- **Split Trigger**: If trace collection requires async I/O, external service calls, or schema changes to `RetrievalResponse`, stop and create a follow-up slice.

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/contracts/context_packet.py` (lines 1-53) — Why: Canonical Pydantic model pattern for all contracts. `RetrievalTrace` must follow the same `BaseModel` + `Field` conventions, including `default_factory` for timestamps.
- `backend/src/second_brain/contracts/__init__.py` (lines 1-18) — Why: Export pattern for new contract models. Must add `RetrievalTrace` to `__all__`.
- `backend/src/second_brain/agents/recall.py` (lines 38-148) — Why: `RecallOrchestrator.run()` is the instrumentation target. Trace must wrap the existing 4-step flow (route → retrieve → rerank → branch) without altering behavior.
- `backend/src/second_brain/agents/recall.py` (lines 170-187) — Why: `_build_routing_metadata()` already constructs a metadata dict. Trace fields overlap but are a superset (adds timing, pre-rerank counts, trace_id).
- `backend/src/second_brain/services/memory.py` (lines 1-9) — Why: Existing `logging` usage pattern. `TraceCollector` must not conflict with the operational logger.
- `backend/src/second_brain/services/__init__.py` (lines 1-9) — Why: Export pattern for new service. Must add `TraceCollector` to `__all__`.
- `backend/src/second_brain/mcp_server.py` (lines 15-64) — Why: `recall_search()` creates an orchestrator and runs it. Needs to optionally inject a trace collector and return trace data.
- `backend/src/second_brain/deps.py` (lines 1-55) — Why: Dependency injection helpers. May need a `create_trace_collector()` factory.
- `tests/test_recall_flow_integration.py` (lines 10-35) — Why: Integration test pattern. New trace tests must follow same `RecallOrchestrator` setup + assertion style.
- `tests/test_context_packet_contract.py` — Why: Contract validation test pattern for Pydantic models.

### New Files to Create

- `backend/src/second_brain/contracts/trace.py` — Pydantic `RetrievalTrace` model and related types
- `backend/src/second_brain/services/trace.py` — `TraceCollector` class with in-memory storage and callback hook
- `tests/test_retrieval_trace.py` — Unit tests for trace model and collector; integration tests for trace instrumentation in orchestrator

### Related Memories (from memory.md)

- Memory: "Incremental-by-default slices with full validation every loop" — Relevance: This slice adds tracing without modifying retrieval logic; full validation pyramid still required.
- Memory: "Python-first with framework-agnostic contracts" — Relevance: `RetrievalTrace` must be a pure Pydantic model with no framework-specific dependencies (no FastAPI, no Django, no OTel SDK).
- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" — Relevance: Trace records that capture error info must sanitize sensitive data (API keys) following the same pattern as `_sanitize_error_message` in `memory.py:173-180`.
- Memory: "Avoid mixed-scope loops" — Relevance: This slice is pure trace instrumentation; no retrieval logic changes, no new providers, no eval scoring.

### Relevant Documentation

- [Pydantic v2 Models](https://docs.pydantic.dev/latest/concepts/models/)
  - Specific section: Model configuration, Field validators, serialization
  - Why: `RetrievalTrace` is a Pydantic BaseModel; must follow v2 conventions for `Field`, `default_factory`, `model_dump()`.
- [Python uuid module](https://docs.python.org/3/library/uuid.html)
  - Specific section: `uuid.uuid4()`
  - Why: Trace IDs are UUID4 strings for uniqueness without external dependencies.
- [Python time module](https://docs.python.org/3/library/time.html)
  - Specific section: `time.perf_counter()`, `time.perf_counter_ns()`
  - Why: High-resolution timing for duration measurement. `perf_counter()` is monotonic and not affected by system clock changes.

### Patterns to Follow

**Pydantic contract model with timestamp factory** (from `backend/src/second_brain/contracts/context_packet.py:23-30`):
```python
class ContextPacket(BaseModel):
    """Complete retrieval result envelope."""
    candidates: list[ContextCandidate]
    summary: ConfidenceSummary
    provider: str
    rerank_applied: bool
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```
- Why this pattern: `RetrievalTrace` must use the same `BaseModel` + `Field(default_factory=...)` pattern for its timestamp fields.
- Common gotchas: Do not use `datetime.now()` without timezone — always use `timezone.utc`. Do not use `default=` with mutable values.

**Routing metadata construction** (from `backend/src/second_brain/agents/recall.py:170-187`):
```python
def _build_routing_metadata(
    self,
    provider: str,
    route_options: dict,
    route_options_skip_rerank: bool,
    rerank_metadata: dict,
    mode: str = "conversation",
) -> dict[str, Any]:
    """Build rich routing metadata for response."""
    return {
        "selected_provider": provider,
        "mode": mode,
        "skip_external_rerank": route_options_skip_rerank,
        "rerank_type": rerank_metadata.get("rerank_type", "none"),
        "rerank_bypass_reason": rerank_metadata.get("rerank_bypass_reason"),
        "feature_flags_snapshot": dict(self.feature_flags),
        "provider_status_snapshot": dict(self.provider_status),
    }
```
- Why this pattern: Trace must capture the same data plus additional timing and candidate statistics. The trace does not replace routing_metadata — it is a superset that includes it.
- Common gotchas: `routing_metadata` is a plain dict; `RetrievalTrace` is a typed Pydantic model. Don't mix them — trace captures typed fields, routing_metadata stays a dict for backwards compatibility.

**Package export pattern** (from `backend/src/second_brain/contracts/__init__.py:1-18`):
```python
"""Contracts package - export key models."""
from second_brain.contracts.context_packet import (
    ContextCandidate,
    ConfidenceSummary,
    ContextPacket,
    NextAction,
    RetrievalRequest,
    RetrievalResponse,
)

__all__ = [
    "ContextCandidate",
    "ConfidenceSummary",
    "ContextPacket",
    "NextAction",
    "RetrievalRequest",
    "RetrievalResponse",
]
```
- Why this pattern: All new exports (RetrievalTrace) must follow the same explicit import + `__all__` convention.
- Common gotchas: Forgetting to add to `__all__` causes mypy strict mode to flag implicit re-exports.

**Integration test setup** (from `tests/test_recall_flow_integration.py:10-35`):
```python
class TestRecallFlowIntegration:
    def test_success_branch_mem0(self):
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService(enabled=False)
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
            feature_flags={"mem0_enabled": True, "supabase_enabled": False},
        )
        
        request = RetrievalRequest(
            query="test high confidence query",
            mode="conversation",
            top_k=5,
            threshold=0.6,
        )
        
        response = orchestrator.run(request)
        assert response.context_packet.summary.branch == BranchCodes.RERANK_BYPASSED
```
- Why this pattern: Trace integration tests must follow the same pattern — construct orchestrator with explicit deps, run a request, assert trace fields.
- Common gotchas: Tests must work with the existing mock/fallback data paths. Do not require real Mem0 credentials.

**Service with optional injection** (from `backend/src/second_brain/agents/recall.py:24-36`):
```python
class RecallOrchestrator:
    def __init__(
        self,
        memory_service: MemoryService,
        rerank_service: VoyageRerankService,
        feature_flags: Optional[dict[str, bool]] = None,
        provider_status: Optional[dict[str, str]] = None,
        config: Optional[dict[str, Any]] = None,
    ):
```
- Why this pattern: `trace_collector` must be added as another `Optional` parameter with `None` default. When None, no trace is emitted. Fully backwards compatible.
- Common gotchas: Adding a parameter to `__init__` means all existing callers (tests, mcp_server, run_recall) still work because it defaults to None.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation — Trace Contract Model

Create the `RetrievalTrace` Pydantic model that defines the structured trace record. This model captures the full lifecycle of a retrieval call.

**Tasks:**
- Create `RetrievalTrace` model with all trace fields (timing, request, routing, candidates, rerank, branch, error)
- Create supporting enum/literal types for trace status
- Add exports to contracts `__init__.py`

### Phase 2: Core — Trace Collector Service

Create the `TraceCollector` service that stores trace records in memory and supports an optional callback for extensibility.

**Tasks:**
- Create `TraceCollector` class with `record()`, `get_traces()`, `clear()`, `get_by_id()` methods
- Support optional callback function for each recorded trace
- Add exports to services `__init__.py`
- Add factory function to `deps.py`

### Phase 3: Integration — Orchestrator Instrumentation

Instrument `RecallOrchestrator.run()` to build and emit trace records without altering retrieval behavior. Propagate trace ID into `routing_metadata`.

**Tasks:**
- Add optional `trace_collector` parameter to `RecallOrchestrator.__init__()`
- Build trace record around the 4-step flow in `run()`
- Propagate `trace_id` into `routing_metadata`
- Update `run_recall()` convenience function
- Update `MCPServer.recall_search()` to optionally inject collector and return trace data

### Phase 4: Testing & Validation

Create comprehensive tests for the trace model, collector, and orchestrator integration. Verify all existing tests still pass.

**Tasks:**
- Unit tests for `RetrievalTrace` model (construction, serialization, defaults)
- Unit tests for `TraceCollector` (record, retrieve, clear, callback)
- Integration tests for trace emission during orchestrator runs
- Regression tests to verify existing behavior is unchanged
- Run full validation pyramid

---

## STEP-BY-STEP TASKS

### CREATE backend/src/second_brain/contracts/trace.py

- **IMPLEMENT**: Create Pydantic model for structured retrieval trace records:
  ```python
  """Structured trace records for retrieval pipeline observability."""
  import time
  import uuid
  from datetime import datetime, timezone
  from typing import Any, Literal
  
  from pydantic import BaseModel, Field
  
  
  class RetrievalTrace(BaseModel):
      """Structured trace record for a single retrieval pipeline call."""
      
      # Identity
      trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
      
      # Timing
      timestamp: str = Field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      duration_ms: float = Field(default=0.0, ge=0.0)
      
      # Request snapshot
      query: str
      mode: str
      top_k: int
      threshold: float
      provider_override: str | None = None
      
      # Routing decision
      selected_provider: str
      feature_flags_snapshot: dict[str, bool] = Field(default_factory=dict)
      provider_status_snapshot: dict[str, str] = Field(default_factory=dict)
      
      # Retrieval statistics
      raw_candidate_count: int = Field(default=0, ge=0)
      final_candidate_count: int = Field(default=0, ge=0)
      top_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
      
      # Rerank
      rerank_type: str = "none"
      rerank_bypass_reason: str | None = None
      skip_external_rerank: bool = False
      
      # Branch outcome
      branch_code: str
      action: str
      reason: str
      
      # Validation mode
      validation_mode: bool = False
      forced_branch: str | None = None
      
      # Error tracking
      status: Literal["ok", "error"] = "ok"
      error_type: str | None = None
      error_message: str | None = None
  ```
- **PATTERN**: Pydantic model with `Field(default_factory=...)` from `backend/src/second_brain/contracts/context_packet.py:23-30`
- **IMPORTS**: `import time`, `import uuid`, `from datetime import datetime, timezone`, `from typing import Any, Literal`, `from pydantic import BaseModel, Field`
- **GOTCHA**: Use `timezone.utc` for all timestamps. Use `uuid.uuid4()` not `uuid.uuid1()`. Use `Field(ge=0.0)` for non-negative constraints to match existing ContextCandidate patterns.
- **VALIDATE**: `python -c "from second_brain.contracts.trace import RetrievalTrace; t = RetrievalTrace(query='test', mode='conversation', top_k=5, threshold=0.6, selected_provider='mem0', branch_code='SUCCESS', action='proceed', reason='test'); print(t.trace_id, t.status)"`

### UPDATE backend/src/second_brain/contracts/__init__.py

- **IMPLEMENT**: Add `RetrievalTrace` import and export:
  ```python
  from second_brain.contracts.trace import RetrievalTrace
  ```
  Add `"RetrievalTrace"` to the `__all__` list.
- **PATTERN**: Existing export pattern at `backend/src/second_brain/contracts/__init__.py:1-18`
- **IMPORTS**: `from second_brain.contracts.trace import RetrievalTrace`
- **GOTCHA**: Must add to `__all__` list or mypy strict mode flags implicit re-export.
- **VALIDATE**: `python -c "from second_brain.contracts import RetrievalTrace; print(RetrievalTrace.__name__)"`

### CREATE backend/src/second_brain/services/trace.py

- **IMPLEMENT**: Create trace collector service with in-memory storage and callback support:
  ```python
  """Trace collection service for retrieval pipeline observability."""
  from typing import Any, Callable, Optional
  
  from second_brain.contracts.trace import RetrievalTrace
  
  
  # Type alias for trace callback
  TraceCallback = Callable[[RetrievalTrace], None]
  
  
  class TraceCollector:
      """
      In-memory trace collector with optional callback hook.
      
      Stores RetrievalTrace records in a list for inspection.
      Optionally calls a callback for each recorded trace,
      enabling future integration with file/DB/OTel exporters.
      """
      
      def __init__(
          self,
          callback: Optional[TraceCallback] = None,
          max_traces: int = 1000,
      ):
          self._traces: list[RetrievalTrace] = []
          self._callback = callback
          self._max_traces = max_traces
      
      def record(self, trace: RetrievalTrace) -> None:
          """
          Record a trace. Calls callback if registered.
          Evicts oldest trace if max_traces exceeded.
          """
          if len(self._traces) >= self._max_traces:
              self._traces.pop(0)
          self._traces.append(trace)
          if self._callback is not None:
              self._callback(trace)
      
      def get_traces(self) -> list[RetrievalTrace]:
          """Return all recorded traces (newest last)."""
          return list(self._traces)
      
      def get_by_id(self, trace_id: str) -> Optional[RetrievalTrace]:
          """Look up a trace by ID. Returns None if not found."""
          for trace in self._traces:
              if trace.trace_id == trace_id:
                  return trace
          return None
      
      def get_latest(self, n: int = 1) -> list[RetrievalTrace]:
          """Return the N most recent traces."""
          return list(self._traces[-n:])
      
      def clear(self) -> None:
          """Clear all stored traces."""
          self._traces.clear()
      
      @property
      def count(self) -> int:
          """Number of traces currently stored."""
          return len(self._traces)
  ```
- **PATTERN**: Service class pattern from `backend/src/second_brain/services/memory.py:22-28` (class with `__init__` and internal state)
- **IMPORTS**: `from typing import Any, Callable, Optional`, `from second_brain.contracts.trace import RetrievalTrace`
- **GOTCHA**: Max traces cap prevents unbounded memory growth. Use `list.pop(0)` for FIFO eviction — acceptable for small lists; if max_traces were large (>10K), would need `collections.deque` instead. For 1000 traces this is fine (YAGNI).
- **VALIDATE**: `python -c "from second_brain.services.trace import TraceCollector; tc = TraceCollector(); print(tc.count)"`

### UPDATE backend/src/second_brain/services/__init__.py

- **IMPLEMENT**: Add `TraceCollector` import and export:
  ```python
  from second_brain.services.trace import TraceCollector
  ```
  Add `"TraceCollector"` to the `__all__` list.
- **PATTERN**: Existing export pattern at `backend/src/second_brain/services/__init__.py:1-9`
- **IMPORTS**: `from second_brain.services.trace import TraceCollector`
- **GOTCHA**: Must add to `__all__` list for mypy strict compliance.
- **VALIDATE**: `python -c "from second_brain.services import TraceCollector; print(TraceCollector.__name__)"`

### UPDATE backend/src/second_brain/deps.py

- **IMPLEMENT**: Add factory function for trace collector:
  ```python
  from second_brain.services.trace import TraceCollector
  
  def create_trace_collector(
      max_traces: int = 1000,
  ) -> TraceCollector:
      """Create trace collector instance."""
      return TraceCollector(max_traces=max_traces)
  ```
  Add the import at top of file and the function after `create_voyage_rerank_service`.
- **PATTERN**: Factory pattern from `backend/src/second_brain/deps.py:28-33` (`create_memory_service`)
- **IMPORTS**: `from second_brain.services.trace import TraceCollector`
- **GOTCHA**: Keep import at module level with other service imports. Do not import inside function — matches existing pattern.
- **VALIDATE**: `python -c "from second_brain.deps import create_trace_collector; tc = create_trace_collector(); print(type(tc).__name__)"`

### UPDATE backend/src/second_brain/agents/recall.py

- **IMPLEMENT**: Instrument `RecallOrchestrator` with optional trace collection. Changes:

  1. Add `trace_collector` parameter to `__init__`:
     ```python
     from second_brain.services.trace import TraceCollector
     from second_brain.contracts.trace import RetrievalTrace
     ```
     Add to `__init__` signature:
     ```python
     trace_collector: Optional['TraceCollector'] = None,
     ```
     Store as `self.trace_collector = trace_collector`.

  2. Wrap `run()` body with trace timing and recording. The key instrumentation points are:
     - Before step 1 (route): capture `start_time = time.perf_counter()`
     - After step 2 (retrieve): capture `raw_candidate_count = len(candidates)`
     - After step 4 (branch): build `RetrievalTrace` with all fields
     - Before return: if `self.trace_collector`, call `self.trace_collector.record(trace)` and add `trace.trace_id` to `routing_metadata`

  3. Add a `_build_trace()` helper method that constructs the `RetrievalTrace` from request, response, and intermediate values.

  4. Handle errors: if any step raises, capture error info in trace before re-raising.

  **Critical constraint**: The existing 4-step flow (route → retrieve → rerank → branch) must NOT change. Trace code wraps around it, never alters it. All existing tests must pass without modification.

  **Detailed `run()` instrumentation** (pseudo-diff showing additions only):
  ```python
  def run(self, request, validation_mode=False, force_branch=None):
      start_time = time.perf_counter()  # NEW
      raw_candidate_count = 0  # NEW
      
      try:
          # Step 1: Route (unchanged)
          provider, route_options = route_retrieval(...)
          
          # Handle no provider (unchanged, but add trace before return)
          if provider == "none":
              # ... existing code ...
              # NEW: record trace if collector present
              if self.trace_collector is not None:
                  duration_ms = (time.perf_counter() - start_time) * 1000
                  trace = self._build_trace(
                      request=request, duration_ms=duration_ms,
                      provider="none", route_options={"skip_external_rerank": False},
                      raw_candidate_count=0, candidates=[],
                      rerank_metadata={"rerank_type": "none"},
                      context_packet=context_packet, next_action=next_action,
                      skip_external_rerank=False,
                      validation_mode=False, forced_branch=None,
                  )
                  self.trace_collector.record(trace)
                  routing_metadata["trace_id"] = trace.trace_id
              return RetrievalResponse(...)
          
          # Step 2: Retrieve (unchanged)
          candidates, _provider_metadata = memory_service.search_memories(...)
          raw_candidate_count = len(candidates)  # NEW
          
          # Step 3: Rerank (unchanged)
          # Step 4: Branch (unchanged)
          
          # NEW: record trace before return
          if self.trace_collector is not None:
              duration_ms = (time.perf_counter() - start_time) * 1000
              trace = self._build_trace(
                  request=request, duration_ms=duration_ms,
                  provider=provider, route_options=route_options,
                  raw_candidate_count=raw_candidate_count,
                  candidates=context_packet.candidates,
                  rerank_metadata=rerank_metadata,
                  context_packet=context_packet, next_action=next_action,
                  skip_external_rerank=skip_external_rerank,
                  validation_mode=validation_mode,
                  forced_branch=force_branch if validation_mode else None,
              )
              self.trace_collector.record(trace)
              routing_metadata["trace_id"] = trace.trace_id
          
          return RetrievalResponse(...)
      
      except Exception as e:
          # NEW: record error trace
          if self.trace_collector is not None:
              duration_ms = (time.perf_counter() - start_time) * 1000
              trace = RetrievalTrace(
                  query=request.query, mode=request.mode,
                  top_k=request.top_k, threshold=request.threshold,
                  provider_override=request.provider_override,
                  selected_provider="unknown", branch_code="ERROR",
                  action="fallback", reason=str(type(e).__name__),
                  duration_ms=duration_ms, status="error",
                  error_type=type(e).__name__,
                  error_message=str(e)[:200],
              )
              self.trace_collector.record(trace)
          raise
  ```

  5. Add `_build_trace()` helper:
     ```python
     def _build_trace(
         self,
         request: RetrievalRequest,
         duration_ms: float,
         provider: str,
         route_options: dict,
         raw_candidate_count: int,
         candidates: list,
         rerank_metadata: dict,
         context_packet: ContextPacket,
         next_action: NextAction,
         skip_external_rerank: bool,
         validation_mode: bool,
         forced_branch: str | None,
     ) -> RetrievalTrace:
         return RetrievalTrace(
             query=request.query,
             mode=request.mode,
             top_k=request.top_k,
             threshold=request.threshold,
             provider_override=request.provider_override,
             selected_provider=provider,
             feature_flags_snapshot=dict(self.feature_flags),
             provider_status_snapshot=dict(self.provider_status),
             raw_candidate_count=raw_candidate_count,
             final_candidate_count=len(candidates),
             top_confidence=context_packet.summary.top_confidence,
             rerank_type=rerank_metadata.get("rerank_type", "none"),
             rerank_bypass_reason=rerank_metadata.get("rerank_bypass_reason"),
             skip_external_rerank=skip_external_rerank,
             branch_code=context_packet.summary.branch,
             action=next_action.action,
             reason=next_action.reason,
             duration_ms=duration_ms,
             validation_mode=validation_mode,
             forced_branch=forced_branch,
         )
     ```

  6. Update `run_recall()` convenience function to accept optional `trace_collector` parameter and pass it to `RecallOrchestrator`.

- **PATTERN**: Optional injection pattern from `backend/src/second_brain/agents/recall.py:24-36` (existing Optional params with None defaults)
- **IMPORTS**: `import time`, `from second_brain.services.trace import TraceCollector`, `from second_brain.contracts.trace import RetrievalTrace`
- **GOTCHA**: 
  - Use `time.perf_counter()` not `time.time()` — perf_counter is monotonic and more precise.
  - Duration calc: `(end - start) * 1000` for milliseconds.
  - `trace_id` goes into `routing_metadata` dict (not a new field on RetrievalResponse) for backwards compatibility.
  - The try/except for error traces must re-raise the exception — trace collection is observational, never swallows errors.
  - Import `TraceCollector` with a string annotation `'TraceCollector'` or use `from __future__ import annotations` to avoid circular imports if needed. Verify: contracts and services are separate packages, so direct import should work.
- **VALIDATE**: `PYTHONPATH=backend/src python -c "from second_brain.agents.recall import RecallOrchestrator; print('import ok')"`

### UPDATE backend/src/second_brain/mcp_server.py

- **IMPLEMENT**: Update `MCPServer` to optionally use trace collection and expose trace data.

  1. Add a `trace_collector` attribute to `MCPServer.__init__()`:
     ```python
     from second_brain.services.trace import TraceCollector
     
     def __init__(self):
         self.debug_mode = False
         self.trace_collector: TraceCollector | None = None
     ```

  2. Add methods to enable/disable/access traces:
     ```python
     def enable_tracing(self, max_traces: int = 1000) -> None:
         """Enable trace collection."""
         self.trace_collector = TraceCollector(max_traces=max_traces)
     
     def disable_tracing(self) -> None:
         """Disable trace collection."""
         self.trace_collector = None
     
     def get_traces(self, n: int = 10) -> list[dict[str, Any]]:
         """Get recent traces as dicts."""
         if self.trace_collector is None:
             return []
         return [t.model_dump() for t in self.trace_collector.get_latest(n)]
     ```

  3. Pass `trace_collector` to `RecallOrchestrator` in `recall_search()`:
     ```python
     orchestrator = RecallOrchestrator(
         memory_service=memory_service,
         rerank_service=rerank_service,
         feature_flags=get_feature_flags(),
         provider_status=get_provider_status(),
         trace_collector=self.trace_collector,  # NEW
     )
     ```

  4. Same pattern in `validate_branch()`.

- **PATTERN**: Debug mode toggle pattern from `backend/src/second_brain/mcp_server.py:142-148`
- **IMPORTS**: `from second_brain.services.trace import TraceCollector`
- **GOTCHA**: `trace_collector` defaults to None — tracing is disabled by default. MCP consumers see no difference unless they explicitly enable it.
- **VALIDATE**: `PYTHONPATH=backend/src python -c "from second_brain.mcp_server import MCPServer; s = MCPServer(); s.enable_tracing(); print(type(s.trace_collector).__name__)"`

### CREATE tests/test_retrieval_trace.py

- **IMPLEMENT**: Comprehensive test file covering:

  **Unit Tests — RetrievalTrace model**:
  - `test_trace_model_construction`: Build a trace with all required fields, verify defaults (trace_id generated, timestamp set, status="ok")
  - `test_trace_model_serialization`: Verify `model_dump()` produces expected dict structure
  - `test_trace_model_defaults`: Verify optional fields default correctly (error_type=None, forced_branch=None, validation_mode=False)
  - `test_trace_id_uniqueness`: Create multiple traces, verify all trace_ids differ

  **Unit Tests — TraceCollector**:
  - `test_collector_record_and_retrieve`: Record a trace, get_traces returns it
  - `test_collector_get_by_id`: Record trace, look up by trace_id
  - `test_collector_get_by_id_not_found`: Look up nonexistent ID returns None
  - `test_collector_get_latest`: Record 5 traces, get_latest(2) returns last 2
  - `test_collector_clear`: Record traces, clear, verify empty
  - `test_collector_count`: Record 3 traces, count == 3
  - `test_collector_max_traces_eviction`: Set max_traces=3, record 5, verify only last 3 remain
  - `test_collector_callback`: Register callback, record trace, verify callback was called with the trace
  - `test_collector_callback_none`: No callback registered, record works fine

  **Integration Tests — Orchestrator Trace Emission**:
  - `test_orchestrator_emits_trace_on_success`: Run orchestrator with collector, verify trace recorded with correct branch/provider/timing
  - `test_orchestrator_emits_trace_on_empty_set`: Empty set scenario, verify trace has branch_code="EMPTY_SET"
  - `test_orchestrator_emits_trace_on_low_confidence`: Low confidence scenario, verify trace
  - `test_orchestrator_no_trace_without_collector`: Run orchestrator without collector, verify no errors and routing_metadata has no trace_id
  - `test_trace_id_in_routing_metadata`: Run with collector, verify routing_metadata["trace_id"] matches recorded trace
  - `test_trace_duration_positive`: Verify duration_ms > 0 for any real run
  - `test_trace_raw_vs_final_candidate_count`: Set up scenario where rerank changes count, verify raw_candidate_count >= final_candidate_count
  - `test_trace_preserves_existing_behavior`: Run same scenarios as existing integration tests, verify same branch/action outcomes (regression guard)

  **Integration Tests — MCP Server Tracing**:
  - `test_mcp_server_tracing_disabled_by_default`: Verify get_traces returns empty when tracing not enabled
  - `test_mcp_server_enable_tracing`: Enable tracing, run recall_search, verify traces available
  - `test_mcp_server_disable_tracing`: Enable then disable, verify collector is None

- **PATTERN**: Test class structure from `tests/test_recall_flow_integration.py:10-35`
- **IMPORTS**: `from second_brain.contracts.trace import RetrievalTrace`, `from second_brain.services.trace import TraceCollector`, `from second_brain.agents.recall import RecallOrchestrator`, `from second_brain.services.memory import MemoryService, MemorySearchResult`, `from second_brain.services.voyage import VoyageRerankService`, `from second_brain.contracts.context_packet import RetrievalRequest`, `from second_brain.orchestration.fallbacks import BranchCodes`, `from second_brain.mcp_server import MCPServer`
- **GOTCHA**: 
  - Tests must use the same mock/fallback memory data paths as existing tests.
  - Do not compare timestamps for equality — they will differ between creation and assertion. Check they are non-empty ISO format strings instead.
  - Duration assertions: use `> 0` not exact values (timing depends on machine).
  - For callback tests, use a simple list.append lambda to capture calls.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_retrieval_trace.py -v`

### UPDATE tests/test_recall_flow_integration.py

- **IMPLEMENT**: Add a small test class verifying trace does not interfere with existing behavior:
  ```python
  class TestTraceBackwardsCompatibility:
      """Verify tracing does not alter existing orchestrator behavior."""
      
      def test_existing_tests_pass_with_collector(self):
          """Run a standard success scenario WITH collector, verify same outcome."""
          from second_brain.services.trace import TraceCollector
          
          collector = TraceCollector()
          memory_service = MemoryService(provider="mem0")
          rerank_service = VoyageRerankService(enabled=False)
          
          orchestrator = RecallOrchestrator(
              memory_service=memory_service,
              rerank_service=rerank_service,
              feature_flags={"mem0_enabled": True, "supabase_enabled": False},
              trace_collector=collector,
          )
          
          request = RetrievalRequest(
              query="test high confidence query",
              mode="conversation",
              top_k=5,
              threshold=0.6,
          )
          
          response = orchestrator.run(request)
          
          # Same assertions as test_success_branch_mem0
          assert response.context_packet.summary.branch == BranchCodes.RERANK_BYPASSED
          assert response.next_action.action == "proceed"
          assert response.routing_metadata["selected_provider"] == "mem0"
          
          # Plus: trace was recorded
          assert collector.count == 1
          trace = collector.get_traces()[0]
          assert trace.branch_code == BranchCodes.RERANK_BYPASSED
          assert "trace_id" in response.routing_metadata
  ```
- **PATTERN**: Test class pattern from `tests/test_recall_flow_integration.py:10-35`
- **IMPORTS**: `from second_brain.services.trace import TraceCollector` (add inside test or at top of file)
- **GOTCHA**: Do not modify any existing test methods. Only ADD a new test class at the end of the file.
- **VALIDATE**: `PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py -v`

---

## TESTING STRATEGY

### Unit Tests

- **RetrievalTrace model**: Construction with required fields, default field verification, serialization roundtrip, trace_id uniqueness across instances.
- **TraceCollector service**: Record/retrieve lifecycle, ID lookup, latest-N retrieval, FIFO eviction at max capacity, callback invocation, empty collector behavior.

### Integration Tests

- **Orchestrator + Collector**: Verify traces are emitted for all 5 branch codes (EMPTY_SET, LOW_CONFIDENCE, CHANNEL_MISMATCH, RERANK_BYPASSED, SUCCESS). Verify trace fields match response fields. Verify timing is positive. Verify trace_id propagates to routing_metadata.
- **Backwards Compatibility**: Verify all existing test scenarios produce identical results when a collector is present vs absent.
- **MCP Server**: Verify tracing enable/disable lifecycle, trace retrieval after recall_search calls.

### Edge Cases

- Orchestrator run with `trace_collector=None` — no trace recorded, no trace_id in metadata, no errors
- Collector at max capacity — oldest trace evicted, newest preserved
- Collector callback that raises — should not crash trace recording (if we want resilience) OR should propagate (if we want strict behavior). Decision: propagate for now (fail-fast), add error swallowing only if needed later.
- Trace on provider "none" path (all providers unavailable)
- Trace on validation_mode forced branch path
- Trace on error path (if orchestrator raises during run)

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.
> Full validation depth is required for every slice.

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
PYTHONPATH=backend/src pytest tests/test_retrieval_trace.py tests/test_context_packet_contract.py -v
```

### Level 4: Integration Tests
```bash
PYTHONPATH=backend/src pytest tests/test_recall_flow_integration.py tests/test_retrieval_trace.py -v
```

### Level 5: Full Suite
```bash
PYTHONPATH=backend/src pytest tests/ -v
```

### Level 6: Manual Validation

1. Import and construct a `RetrievalTrace` in Python REPL — verify all fields serialize correctly:
   ```python
   from second_brain.contracts.trace import RetrievalTrace
   t = RetrievalTrace(
       query="test", mode="conversation", top_k=5, threshold=0.6,
       selected_provider="mem0", branch_code="SUCCESS",
       action="proceed", reason="test trace"
   )
   print(t.model_dump_json(indent=2))
   ```

2. Run orchestrator with collector and inspect trace:
   ```python
   from second_brain.services.trace import TraceCollector
   from second_brain.agents.recall import RecallOrchestrator
   from second_brain.services.memory import MemoryService
   from second_brain.services.voyage import VoyageRerankService
   from second_brain.contracts.context_packet import RetrievalRequest
   
   collector = TraceCollector()
   orch = RecallOrchestrator(
       memory_service=MemoryService(provider="mem0"),
       rerank_service=VoyageRerankService(),
       trace_collector=collector,
   )
   resp = orch.run(RetrievalRequest(query="hello", mode="conversation"))
   print(f"Traces: {collector.count}")
   print(collector.get_traces()[0].model_dump_json(indent=2))
   ```

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `RetrievalTrace` model created with all specified fields and correct types
- [ ] `TraceCollector` service created with record/retrieve/clear/callback functionality
- [ ] `RecallOrchestrator.run()` emits trace when collector is present
- [ ] `trace_id` propagated to `routing_metadata` when collector is present
- [ ] No trace emitted when collector is None (backwards compatible)
- [ ] `MCPServer` supports enable/disable tracing and trace retrieval
- [ ] `deps.py` has `create_trace_collector()` factory
- [ ] All new code exports added to `__init__.py` files
- [ ] All validation commands pass with zero errors

### Runtime (verify after testing/deployment)

- [ ] All existing 133 tests pass without modification
- [ ] New trace tests pass (unit + integration)
- [ ] Trace duration_ms reflects actual execution time (> 0)
- [ ] Trace fields match corresponding RetrievalResponse fields
- [ ] MCP server tracing lifecycle works (enable → search → get_traces → disable)

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (all existing + new tests)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms trace collection works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions
- **Pydantic over dataclass**: Consistent with existing contract architecture. Provides validation, serialization, and schema generation for free.
- **In-memory over persistent**: YAGNI. Persistent storage (file, DB) adds complexity with no immediate consumer. The callback hook provides an extension point for when persistence is needed.
- **trace_id in routing_metadata rather than new RetrievalResponse field**: Avoids schema changes to the canonical response contract. routing_metadata is already a flexible dict.
- **Callback propagates errors**: Fail-fast approach. If a callback breaks, we want to know immediately rather than silently dropping traces.

### Risks
- Risk: Adding `time.perf_counter()` calls to the hot path adds ~microseconds per call. Mitigation: Negligible compared to actual memory search time (milliseconds). And tracing is skipped entirely when collector is None.
- Risk: Error trace path may miss some fields if exception occurs very early (before routing). Mitigation: Error trace uses "unknown" defaults and captures what's available.
- Risk: Future eval scoring may need to change the trace schema. Mitigation: Pydantic models support optional fields — eval fields can be added with defaults without breaking existing traces.

### Confidence Score: 9/10
- **Strengths**: Clear scope (trace only, no eval), follows established patterns exactly, no external dependencies, backwards compatible by design, well-defined test matrix.
- **Uncertainties**: Exact error handling behavior in edge cases (exception during routing before provider selection). Minor mypy strict mode surprises with Optional type annotations.
- **Mitigations**: Error trace captures what's available with safe defaults. mypy issues caught by Level 2 validation gate.
