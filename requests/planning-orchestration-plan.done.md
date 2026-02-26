# Feature: Planning & Orchestration Module

## Feature Description

Build the Planning/Orchestration module that sits between user queries and the retrieval system.
Currently, `RecallOrchestrator.run()` returns a `RetrievalResponse` with `NextAction` (proceed/clarify/
fallback/escalate), but nothing interprets or acts on that signal. This slice adds a `Planner` that
consumes `RetrievalResponse`, interprets `NextAction` deterministically, manages in-memory multi-turn
conversation state, and exposes a `chat` MCP tool for the complete query-to-response loop.

## User Story

As a lifelong learner using Ultima Second Brain, I want to have a conversational interface that
retrieves relevant context and responds intelligently based on retrieval quality, so that I get
useful answers when context is available and clear guidance when it's not.

## Problem Statement

The retrieval foundation (G1-G2) is complete: contracts, router, fallbacks, 3 providers, rerank,
and tracing all work. But the system is a library — `recall_search` returns raw contract envelopes
that no consumer interprets. The `NextAction` field (proceed/clarify/fallback/escalate) is emitted
but ignored. There is no conversation state, no multi-turn awareness, and no response formatting.
The system cannot be used conversationally.

## Solution Statement

- Decision 1: **Deterministic Planner (no LLM)** — The Planner uses pattern matching on `NextAction.action`
  to generate structured responses. LLM-based generation is a follow-up slice. This keeps the module
  testable and deterministic.
- Decision 2: **In-memory ConversationStore** — Dict-backed conversation state with session IDs.
  No persistence (Supabase/Redis) until proven needed — YAGNI.
- Decision 3: **`chat` MCP tool** — Single entry point that runs: query → planner (pre-retrieval) →
  retrieval → planner (post-retrieval) → structured response. This replaces `recall_search` as the
  primary user-facing tool.
- Decision 4: **Template responses per branch** — Each NextAction maps to a response template:
  `proceed` → context-backed answer, `clarify` → clarification request, `fallback` → rephrase
  suggestion, `escalate` → escalation notice. Clean and predictable.
- Decision 5: **Planner lives in `orchestration/`** — Follows the architecture doc's module boundary.
  The `orchestration/` package owns routing, fallbacks, and now planning.

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `orchestration/`, `contracts/`, `services/`, `mcp_server.py`, `deps.py`
- **Dependencies**: None external — pure Python + Pydantic (existing deps only)

### Slice Guardrails (Required)

- **Single Outcome**: A working `chat` MCP tool that runs the full query → retrieval → response loop
  with NextAction interpretation and multi-turn conversation tracking.
- **Expected Files Touched**: 8-10 files (3 new, 5-7 modified)
- **Scope Boundary**: No LLM integration, no specialist agent routing, no persistent storage,
  no query reformulation via AI. Deterministic template responses only.
- **Split Trigger**: If intent classification requires >3 heuristic rules, split into separate slice.
  If conversation state needs persistence, split into separate slice.

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/contracts/context_packet.py` (lines 1-59) — Why: Contains all contract
  models (RetrievalRequest, RetrievalResponse, NextAction, ContextPacket) that the Planner consumes.
  The Planner's input/output types are defined here.
- `backend/src/second_brain/agents/recall.py` (lines 27-205) — Why: `RecallOrchestrator.run()` is
  the retrieval entry point the Planner will call. Understand its signature, how it builds
  `RetrievalResponse`, and the trace collector integration.
- `backend/src/second_brain/orchestration/fallbacks.py` (lines 9-16) — Why: `BranchCodes` constants
  that map to NextAction responses. The Planner interprets these.
- `backend/src/second_brain/orchestration/retrieval_router.py` (lines 147-190) — Why: `route_retrieval`
  function called by RecallOrchestrator. Planner doesn't call this directly but must understand
  the provider selection flow it triggers.
- `backend/src/second_brain/mcp_server.py` (lines 1-201) — Why: Current MCP server structure. The
  `chat` tool will be added here following the same pattern as `recall_search`.
- `backend/src/second_brain/deps.py` (lines 1-75) — Why: Factory functions for dependency injection.
  New factories for Planner and ConversationStore go here.
- `backend/src/second_brain/schemas.py` (lines 1-59) — Why: `MCPCompatibilityResponse` pattern for
  MCP response wrapping. The chat response may need a similar wrapper.
- `backend/src/second_brain/services/trace.py` (lines 1-54) — Why: `TraceCollector` pattern for
  in-memory collection with max size. ConversationStore follows the same bounded-collection pattern.
- `backend/src/second_brain/orchestration/__init__.py` (lines 1-21) — Why: Must be updated to export
  new Planner class.
- `backend/src/second_brain/contracts/__init__.py` (lines 1-21) — Why: Must be updated to export
  new conversation contracts.
- `tests/test_recall_flow_integration.py` (lines 1-80) — Why: Test pattern for RecallOrchestrator
  integration tests. Planner tests will follow this exact setup pattern.
- `docs/architecture/retrieval-planning-separation.md` (lines 1-182) — Why: Defines the responsibility
  boundary between retrieval and planning modules. The Planner must own query understanding, intent
  classification, action sequencing, and multi-turn state — NOT provider selection or confidence scoring.

### New Files to Create

- `backend/src/second_brain/contracts/conversation.py` — ConversationTurn, ConversationState,
  PlannerResponse Pydantic models
- `backend/src/second_brain/orchestration/planner.py` — Planner class with NextAction interpretation,
  response generation, and RecallOrchestrator integration
- `backend/src/second_brain/services/conversation.py` — ConversationStore (in-memory, dict-backed)
- `tests/test_planner.py` — Unit tests for Planner (NextAction interpretation per branch)
- `tests/test_conversation_store.py` — Unit tests for ConversationStore
- `tests/test_chat_integration.py` — Integration tests for full chat flow via MCP tool

### Related Memories (from memory.md)

- Memory: "Build order: Contracts → Core Loop → Eval/Trace → Memory → Orchestration → Ingestion" —
  Relevance: This slice is the Orchestration gate (G5). Contracts (G1) and Core Loop (G2) are complete.
- Memory: "Trace-first approach: structured records now, eval scoring as separate follow-up slice" —
  Relevance: Planner should integrate with TraceCollector for observability, following the same
  trace-first pattern.
- Memory: "Incremental-by-default slices with full validation every loop" —
  Relevance: This slice must be self-contained with full lint/type/test validation.
- Memory: "Provider error context: Keep fallback metadata actionable but sanitized" —
  Relevance: Planner responses on fallback/escalate branches must include actionable suggestions
  without exposing internal error details.
- Memory: "Flags default to off" — Relevance: No feature flags needed for this slice (Planner is
  always-on once deployed), but the pattern is noted for future specialist agent gating.

### Relevant Documentation

- `docs/architecture/retrieval-planning-separation.md`
  - Specific section: "Responsibility Boundaries > Planning Module"
  - Why: Canonical definition of what the Planning module owns vs doesn't own
- `docs/architecture/conversational-retrieval-contract.md`
  - Specific section: "Branch Semantics" (lines 66-113)
  - Why: Defines the 5 branch types and their expected NextAction values. The Planner's
    response templates must align with these exact semantics.
- `docs/architecture/retrieval-overlap-policy.md`
  - Specific section: Rerank policy
  - Why: Planner must not second-guess rerank decisions — it respects the retrieval output as-is

### Patterns to Follow

**RecallOrchestrator class pattern** (from `agents/recall.py:27-44`):
```python
class RecallOrchestrator:
    def __init__(
        self,
        memory_service: MemoryService,
        rerank_service: VoyageRerankService,
        feature_flags: Optional[dict[str, bool]] = None,
        provider_status: Optional[dict[str, str]] = None,
        config: Optional[dict[str, Any]] = None,
        trace_collector: Optional[TraceCollector] = None,
    ):
        self.memory_service = memory_service
        self.rerank_service = rerank_service
        self.feature_flags = feature_flags or get_feature_flags()
        # ...
```
- Why this pattern: Constructor injection with optional overrides + defaults from `deps.py`.
  Planner follows the same DI pattern.
- Common gotchas: Don't import deps at module level if they have side effects.

**TraceCollector bounded collection pattern** (from `services/trace.py:1-54`):
```python
class TraceCollector:
    def __init__(self, max_traces: int = 1000):
        self._traces: list[RetrievalTrace] = []
        self._max_traces = max_traces

    def record(self, trace: RetrievalTrace) -> None:
        self._traces.append(trace)
        if len(self._traces) > self._max_traces:
            self._traces = self._traces[-self._max_traces:]
```
- Why this pattern: ConversationStore uses the same bounded-list approach for conversation history.
- Common gotchas: Trim from the front (oldest), keep newest. Use list slicing, not deque.

**MCP tool method pattern** (from `mcp_server.py:32-82`):
```python
def recall_search(
    self,
    query: str,
    mode: str = "conversation",
    top_k: int = 5,
    threshold: float = 0.6,
    provider_override: Optional[str] = None,
) -> dict[str, Any]:
    # Build request, create services, run orchestrator, wrap response
    request = RetrievalRequest(...)
    memory_service = MemoryService(provider="mem0")
    rerank_service = VoyageRerankService(enabled=True)
    orchestrator = RecallOrchestrator(...)
    response = orchestrator.run(request)
    compatibility = MCPCompatibilityResponse.from_retrieval_response(response)
    return compatibility.model_dump()
```
- Why this pattern: The `chat` tool follows the same structure — build request, create services,
  run planner, return dict.
- Common gotchas: Always return `dict[str, Any]` from MCP tools, not Pydantic models directly.

**Pydantic contract model pattern** (from `contracts/context_packet.py:6-13`):
```python
class ContextCandidate(BaseModel):
    """Represents a single retrieval candidate."""
    id: str
    content: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
```
- Why this pattern: All contracts use Pydantic BaseModel with Field validators. Conversation
  contracts must follow the same style.
- Common gotchas: Use `Field(default_factory=...)` for mutable defaults, never `= {}`.

**Integration test pattern** (from `tests/test_recall_flow_integration.py:10-36`):
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
        request = RetrievalRequest(query="test", mode="conversation")
        response = orchestrator.run(request)
        assert response.context_packet.summary.branch == BranchCodes.RERANK_BYPASSED
```
- Why this pattern: Create services with explicit config, run orchestrator, assert on contract fields.
  Chat integration tests follow this exact pattern but with Planner instead of RecallOrchestrator.

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation — Conversation Contracts

Define the Pydantic models for conversation state and planner output. These are the typed contracts
that all other components depend on.

**Tasks:**
- Create `ConversationTurn` model (role, content, timestamp, retrieval metadata)
- Create `ConversationState` model (session_id, turns, created_at, last_active)
- Create `PlannerResponse` model (response_text, action_taken, branch_code, suggestions,
  conversation context, retrieval metadata)
- Export from `contracts/__init__.py`

### Phase 2: Core Implementation — Planner and ConversationStore

Build the Planner class that interprets NextAction and the ConversationStore that tracks sessions.

**Tasks:**
- Create `ConversationStore` with in-memory dict, session CRUD, max turns per session
- Create `Planner` class with:
  - `plan()` method: takes query + session_id → runs retrieval → interprets NextAction → returns PlannerResponse
  - `_interpret_action()`: pattern match on NextAction.action → response template
  - `_format_proceed_response()`: format context candidates into readable response
  - `_format_clarify_response()`: ask user for clarification with suggestions
  - `_format_fallback_response()`: suggest query rephrasing
  - `_format_escalate_response()`: notify of channel mismatch
- Wire Planner to RecallOrchestrator (composition, not inheritance)

### Phase 3: Integration — MCP Tool and Deps

Expose the Planner as a `chat` MCP tool and wire dependency injection.

**Tasks:**
- Add `create_planner()` and `create_conversation_store()` to `deps.py`
- Add `chat` method to `MCPServer` class
- Add `chat_tool()` module-level function
- Update `orchestration/__init__.py` to export Planner

### Phase 4: Testing & Validation

Comprehensive tests for all components following existing test patterns.

**Tasks:**
- Unit tests for ConversationStore (create, get, add turn, max turns, session not found)
- Unit tests for Planner (one test per NextAction branch: proceed, clarify, fallback, escalate)
- Unit tests for Planner conversation tracking (multi-turn state accumulation)
- Integration tests for chat flow (full MCP chat tool → response)
- Edge case tests (empty query, missing session, conversation overflow)

---

## STEP-BY-STEP TASKS

### CREATE `backend/src/second_brain/contracts/conversation.py`

- **IMPLEMENT**: Create three Pydantic models:
  ```python
  class ConversationTurn(BaseModel):
      """Single turn in a conversation."""
      role: Literal["user", "assistant"]
      content: str
      timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      branch_code: str | None = None  # Set on assistant turns
      action_taken: str | None = None  # proceed/clarify/fallback/escalate

  class ConversationState(BaseModel):
      """Multi-turn conversation session."""
      session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
      turns: list[ConversationTurn] = Field(default_factory=list)
      created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      last_active: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      metadata: dict[str, Any] = Field(default_factory=dict)

  class PlannerResponse(BaseModel):
      """Structured response from the planning module."""
      response_text: str
      action_taken: Literal["proceed", "clarify", "fallback", "escalate"]
      branch_code: str
      session_id: str
      suggestions: list[str] = Field(default_factory=list)
      candidates_used: int = 0
      confidence: float = 0.0
      retrieval_metadata: dict[str, Any] = Field(default_factory=dict)
  ```
- **PATTERN**: Follow `contracts/context_packet.py:6-13` — Pydantic BaseModel + Field validators
- **IMPORTS**:
  ```python
  import uuid
  from datetime import datetime, timezone
  from typing import Literal, Any
  from pydantic import BaseModel, Field
  ```
- **GOTCHA**: Use `Field(default_factory=...)` for all mutable defaults (list, dict). Never `= []`.
  Use `Literal` for constrained string fields, not bare `str`.
- **VALIDATE**: `python -c "from second_brain.contracts.conversation import ConversationTurn, ConversationState, PlannerResponse; print('OK')"`

### UPDATE `backend/src/second_brain/contracts/__init__.py`

- **IMPLEMENT**: Add exports for the three new conversation models:
  ```python
  from second_brain.contracts.conversation import (
      ConversationTurn,
      ConversationState,
      PlannerResponse,
  )
  ```
  Add to `__all__` list: `"ConversationTurn"`, `"ConversationState"`, `"PlannerResponse"`
- **PATTERN**: Follow existing `__init__.py` export pattern at `contracts/__init__.py:1-21`
- **IMPORTS**: Only the new import line above
- **GOTCHA**: Maintain alphabetical order in `__all__` for consistency with existing entries
- **VALIDATE**: `python -c "from second_brain.contracts import ConversationTurn, ConversationState, PlannerResponse; print('OK')"`

### CREATE `backend/src/second_brain/services/conversation.py`

- **IMPLEMENT**: Create in-memory ConversationStore:
  ```python
  class ConversationStore:
      """In-memory conversation state store."""

      def __init__(self, max_turns_per_session: int = 50, max_sessions: int = 100):
          self._sessions: dict[str, ConversationState] = {}
          self._max_turns = max_turns_per_session
          self._max_sessions = max_sessions

      def get_or_create(self, session_id: str | None = None) -> ConversationState:
          """Get existing session or create new one."""
          if session_id and session_id in self._sessions:
              return self._sessions[session_id]
          state = ConversationState()
          if session_id:
              state.session_id = session_id
          self._sessions[state.session_id] = state
          self._enforce_session_limit()
          return state

      def add_turn(self, session_id: str, turn: ConversationTurn) -> None:
          """Add a turn to session, enforcing max turns."""
          if session_id not in self._sessions:
              raise KeyError(f"Session {session_id} not found")
          state = self._sessions[session_id]
          state.turns.append(turn)
          if len(state.turns) > self._max_turns:
              state.turns = state.turns[-self._max_turns:]
          state.last_active = datetime.now(timezone.utc).isoformat()

      def get_session(self, session_id: str) -> ConversationState | None:
          """Get session by ID, or None if not found."""
          return self._sessions.get(session_id)

      def delete_session(self, session_id: str) -> bool:
          """Delete session. Returns True if existed."""
          return self._sessions.pop(session_id, None) is not None

      def _enforce_session_limit(self) -> None:
          """Evict oldest sessions if over limit."""
          if len(self._sessions) > self._max_sessions:
              sorted_ids = sorted(
                  self._sessions.keys(),
                  key=lambda sid: self._sessions[sid].last_active,
              )
              for sid in sorted_ids[:len(self._sessions) - self._max_sessions]:
                  del self._sessions[sid]
  ```
- **PATTERN**: Follow `services/trace.py` bounded collection pattern — append + trim
- **IMPORTS**:
  ```python
  from datetime import datetime, timezone
  from second_brain.contracts.conversation import ConversationTurn, ConversationState
  ```
- **GOTCHA**: Session eviction must sort by `last_active`, not `created_at`. Oldest inactive
  sessions get evicted first. Don't use `OrderedDict` — explicit sort is clearer.
- **VALIDATE**: `python -c "from second_brain.services.conversation import ConversationStore; s = ConversationStore(); state = s.get_or_create(); print(f'Session: {state.session_id}')"`

### UPDATE `backend/src/second_brain/services/__init__.py`

- **IMPLEMENT**: Add ConversationStore export:
  ```python
  from second_brain.services.conversation import ConversationStore
  ```
  Add `"ConversationStore"` to `__all__`.
- **PATTERN**: Follow existing `services/__init__.py` export pattern
- **IMPORTS**: Only the new import line
- **GOTCHA**: Check existing `__init__.py` content first — it may already have several imports.
  Append, don't overwrite.
- **VALIDATE**: `python -c "from second_brain.services import ConversationStore; print('OK')"`

### CREATE `backend/src/second_brain/orchestration/planner.py`

- **IMPLEMENT**: Create the Planner class:
  ```python
  class Planner:
      """Planning module — interprets retrieval results and manages conversation flow."""

      def __init__(
          self,
          recall_orchestrator: RecallOrchestrator,
          conversation_store: ConversationStore,
          trace_collector: TraceCollector | None = None,
      ):
          self.recall = recall_orchestrator
          self.conversations = conversation_store
          self.trace_collector = trace_collector

      def chat(
          self,
          query: str,
          session_id: str | None = None,
          mode: str = "conversation",
          top_k: int = 5,
          threshold: float = 0.6,
      ) -> PlannerResponse:
          """
          Full chat loop: query → retrieval → interpret → respond.

          1. Get or create conversation session
          2. Record user turn
          3. Build RetrievalRequest
          4. Run recall orchestrator
          5. Interpret NextAction
          6. Record assistant turn
          7. Return PlannerResponse
          """
          # 1. Session management
          state = self.conversations.get_or_create(session_id)

          # 2. Record user turn
          user_turn = ConversationTurn(role="user", content=query)
          self.conversations.add_turn(state.session_id, user_turn)

          # 3. Build retrieval request
          request = RetrievalRequest(
              query=query,
              mode=mode,  # type: ignore[arg-type]
              top_k=top_k,
              threshold=threshold,
          )

          # 4. Run retrieval
          retrieval_response = self.recall.run(request)

          # 5. Interpret NextAction
          response = self._interpret_action(
              retrieval_response=retrieval_response,
              session_id=state.session_id,
          )

          # 6. Record assistant turn
          assistant_turn = ConversationTurn(
              role="assistant",
              content=response.response_text,
              branch_code=response.branch_code,
              action_taken=response.action_taken,
          )
          self.conversations.add_turn(state.session_id, assistant_turn)

          return response

      def _interpret_action(
          self,
          retrieval_response: RetrievalResponse,
          session_id: str,
      ) -> PlannerResponse:
          """Interpret NextAction and generate structured response."""
          action = retrieval_response.next_action.action
          branch = retrieval_response.next_action.branch_code
          packet = retrieval_response.context_packet

          base_metadata = {
              "provider": packet.provider,
              "rerank_applied": packet.rerank_applied,
              "routing": retrieval_response.routing_metadata,
          }

          if action == "proceed":
              return self._format_proceed(packet, branch, session_id, base_metadata)
          elif action == "clarify":
              return self._format_clarify(packet, branch, session_id, base_metadata)
          elif action == "fallback":
              return self._format_fallback(packet, branch, session_id, base_metadata)
          elif action == "escalate":
              return self._format_escalate(packet, branch, session_id, base_metadata)
          else:
              # Defensive: unknown action treated as fallback
              return self._format_fallback(packet, branch, session_id, base_metadata)

      def _format_proceed(self, packet, branch, session_id, metadata) -> PlannerResponse:
          """Format response for proceed action (SUCCESS / RERANK_BYPASSED)."""
          candidates = packet.candidates
          if not candidates:
              return self._format_fallback(packet, branch, session_id, metadata)

          # Build context summary from top candidates
          context_parts = []
          for i, c in enumerate(candidates[:3], 1):
              context_parts.append(f"[{i}] {c.content}")

          response_text = (
              f"Based on {len(candidates)} retrieved context(s) "
              f"(top confidence: {packet.summary.top_confidence:.2f}):\n\n"
              + "\n\n".join(context_parts)
          )

          return PlannerResponse(
              response_text=response_text,
              action_taken="proceed",
              branch_code=branch,
              session_id=session_id,
              candidates_used=len(candidates),
              confidence=packet.summary.top_confidence,
              retrieval_metadata=metadata,
          )

      def _format_clarify(self, packet, branch, session_id, metadata) -> PlannerResponse:
          """Format response for clarify action (LOW_CONFIDENCE)."""
          suggestion = retrieval_response_suggestion(packet)
          response_text = (
              f"I found some results but confidence is low "
              f"({packet.summary.top_confidence:.2f}). "
              f"Could you provide more detail about what you're looking for?"
          )
          suggestions = [
              "Try being more specific about the topic",
              "Include keywords from the content you're looking for",
              "Narrow the scope to a particular source or time period",
          ]

          return PlannerResponse(
              response_text=response_text,
              action_taken="clarify",
              branch_code=branch,
              session_id=session_id,
              suggestions=suggestions,
              candidates_used=packet.summary.candidate_count,
              confidence=packet.summary.top_confidence,
              retrieval_metadata=metadata,
          )

      def _format_fallback(self, packet, branch, session_id, metadata) -> PlannerResponse:
          """Format response for fallback action (EMPTY_SET)."""
          response_text = (
              "I couldn't find relevant context for your query. "
              "Try rephrasing or providing more context."
          )

          return PlannerResponse(
              response_text=response_text,
              action_taken="fallback",
              branch_code=branch,
              session_id=session_id,
              suggestions=[
                  "Rephrase your question with different keywords",
                  "Provide more context about what you need",
                  "Try a broader search term",
              ],
              candidates_used=0,
              confidence=0.0,
              retrieval_metadata=metadata,
          )

      def _format_escalate(self, packet, branch, session_id, metadata) -> PlannerResponse:
          """Format response for escalate action (CHANNEL_MISMATCH)."""
          response_text = (
              "The retrieved context doesn't seem to match your query intent. "
              "This may require manual review or a different approach."
          )

          return PlannerResponse(
              response_text=response_text,
              action_taken="escalate",
              branch_code=branch,
              session_id=session_id,
              suggestions=[
                  "Try specifying the exact topic or domain",
                  "Check if the content has been ingested into the system",
              ],
              candidates_used=packet.summary.candidate_count,
              confidence=packet.summary.top_confidence,
              retrieval_metadata=metadata,
          )
  ```

  Also add a module-level helper:
  ```python
  def retrieval_response_suggestion(packet: ContextPacket) -> str | None:
      """Extract suggestion text from packet candidates if available."""
      if packet.candidates:
          return f"Best match: {packet.candidates[0].content[:100]}..."
      return None
  ```

- **PATTERN**: Follow `agents/recall.py:27-44` constructor injection pattern. Follow
  `orchestration/fallbacks.py:19-155` for deterministic response generation.
- **IMPORTS**:
  ```python
  from typing import Any
  from second_brain.contracts.context_packet import (
      RetrievalRequest,
      RetrievalResponse,
      ContextPacket,
  )
  from second_brain.contracts.conversation import (
      ConversationTurn,
      PlannerResponse,
  )
  from second_brain.agents.recall import RecallOrchestrator
  from second_brain.services.conversation import ConversationStore
  from second_brain.services.trace import TraceCollector
  ```
- **GOTCHA**: The `_format_clarify` method references a `retrieval_response_suggestion` helper —
  define it as a module-level function, not a method. The `mode` parameter in `chat()` needs a
  `type: ignore[arg-type]` comment for the Literal cast, same pattern as `recall.py:406`.
  Do NOT import from `deps.py` in this module — accept all dependencies via constructor.
- **VALIDATE**: `python -c "from second_brain.orchestration.planner import Planner; print('OK')"`

### UPDATE `backend/src/second_brain/orchestration/__init__.py`

- **IMPLEMENT**: Add Planner export:
  ```python
  from second_brain.orchestration.planner import Planner
  ```
  Add `"Planner"` to `__all__`.
- **PATTERN**: Follow existing `orchestration/__init__.py:1-21`
- **IMPORTS**: Only the new import line
- **GOTCHA**: Keep existing imports intact. Only append.
- **VALIDATE**: `python -c "from second_brain.orchestration import Planner; print('OK')"`

### UPDATE `backend/src/second_brain/deps.py`

- **IMPLEMENT**: Add factory functions:
  ```python
  def create_conversation_store(
      max_turns: int = 50,
      max_sessions: int = 100,
  ) -> ConversationStore:
      """Create conversation store instance."""
      return ConversationStore(
          max_turns_per_session=max_turns,
          max_sessions=max_sessions,
      )

  def create_planner(
      memory_service: MemoryService | None = None,
      rerank_service: VoyageRerankService | None = None,
      conversation_store: ConversationStore | None = None,
      trace_collector: TraceCollector | None = None,
  ) -> "Planner":
      """Create planner with default dependencies."""
      from second_brain.orchestration.planner import Planner
      from second_brain.agents.recall import RecallOrchestrator

      _memory = memory_service or create_memory_service()
      _rerank = rerank_service or create_voyage_rerank_service()
      _conversations = conversation_store or create_conversation_store()

      orchestrator = RecallOrchestrator(
          memory_service=_memory,
          rerank_service=_rerank,
          feature_flags=get_feature_flags(),
          provider_status=get_provider_status(),
          trace_collector=trace_collector,
      )

      return Planner(
          recall_orchestrator=orchestrator,
          conversation_store=_conversations,
          trace_collector=trace_collector,
      )
  ```
  Also add import at top:
  ```python
  from second_brain.services.conversation import ConversationStore
  ```
- **PATTERN**: Follow existing factory pattern at `deps.py:30-57`
- **IMPORTS**: `from second_brain.services.conversation import ConversationStore` at top.
  `Planner` and `RecallOrchestrator` imported inside function to avoid circular imports.
- **GOTCHA**: Use lazy import for `Planner` inside `create_planner()` to avoid circular dependency
  (planner.py imports from deps indirectly via RecallOrchestrator). Return type annotation uses
  string literal `"Planner"` for forward reference.
- **VALIDATE**: `python -c "from second_brain.deps import create_planner, create_conversation_store; print('OK')"`

### UPDATE `backend/src/second_brain/mcp_server.py`

- **IMPLEMENT**: Add `chat` method and module-level tool function:
  ```python
  # In MCPServer class:
  def chat(
      self,
      query: str,
      session_id: str | None = None,
      mode: str = "conversation",
      top_k: int = 5,
      threshold: float = 0.6,
  ) -> dict[str, Any]:
      """
      Chat with the second brain — full query → retrieval → response loop.

      Args:
          query: User's question or request
          session_id: Optional session ID for multi-turn conversation
          mode: Retrieval mode (fast, accurate, conversation)
          top_k: Maximum context candidates to retrieve
          threshold: Confidence threshold for retrieval

      Returns:
          PlannerResponse as dict with response_text, action_taken,
          branch_code, suggestions, and retrieval metadata
      """
      from second_brain.deps import create_planner

      planner = create_planner(trace_collector=self.trace_collector)
      response = planner.chat(
          query=query,
          session_id=session_id,
          mode=mode,
          top_k=top_k,
          threshold=threshold,
      )
      return response.model_dump()
  ```

  Module-level tool:
  ```python
  def chat_tool(
      query: str,
      session_id: str | None = None,
      mode: str = "conversation",
      top_k: int = 5,
      threshold: float = 0.6,
  ) -> dict[str, Any]:
      """MCP tool: Chat with second brain."""
      server = get_mcp_server()
      return server.chat(
          query=query,
          session_id=session_id,
          mode=mode,
          top_k=top_k,
          threshold=threshold,
      )
  ```
- **PATTERN**: Follow `mcp_server.py:32-82` `recall_search` pattern exactly
- **IMPORTS**: No new top-level imports needed. `create_planner` is lazy-imported inside the method.
- **GOTCHA**: `create_planner` creates a fresh Planner per call, which means ConversationStore is
  not shared across calls. For stateful multi-turn, the MCPServer needs to hold a shared
  ConversationStore. Solution: add `self._conversation_store` to `MCPServer.__init__` and pass it
  to `create_planner`. This is the one structural change needed:
  ```python
  # In __init__:
  self._conversation_store: ConversationStore | None = None

  # In chat():
  if self._conversation_store is None:
      from second_brain.services.conversation import ConversationStore
      self._conversation_store = ConversationStore()
  planner = create_planner(
      conversation_store=self._conversation_store,
      trace_collector=self.trace_collector,
  )
  ```
- **VALIDATE**: `python -c "from second_brain.mcp_server import chat_tool; print('OK')"`

### CREATE `tests/test_conversation_store.py`

- **IMPLEMENT**: Unit tests for ConversationStore:
  ```python
  class TestConversationStore:
      def test_get_or_create_new_session(self):
          """Creating a new session returns valid ConversationState."""

      def test_get_or_create_existing_session(self):
          """Getting existing session returns same state."""

      def test_get_or_create_with_explicit_id(self):
          """Passing session_id uses that ID."""

      def test_add_turn(self):
          """Adding turn appends to session."""

      def test_add_turn_unknown_session_raises(self):
          """Adding turn to unknown session raises KeyError."""

      def test_max_turns_enforcement(self):
          """Sessions enforce max turns by trimming oldest."""

      def test_session_limit_eviction(self):
          """Oldest inactive sessions evicted when over limit."""

      def test_delete_session(self):
          """Deleting session removes it."""

      def test_delete_nonexistent_session(self):
          """Deleting nonexistent session returns False."""

      def test_get_session_returns_none_for_missing(self):
          """get_session returns None for unknown ID."""

      def test_last_active_updated_on_turn(self):
          """last_active timestamp updates when turn added."""
  ```
  Each test creates a `ConversationStore(max_turns_per_session=5, max_sessions=3)` with small
  limits for easy testing. Assert on ConversationState fields.
- **PATTERN**: Follow `tests/test_recall_flow_integration.py:10-36` class-based test pattern
- **IMPORTS**:
  ```python
  import time
  from second_brain.services.conversation import ConversationStore
  from second_brain.contracts.conversation import ConversationTurn, ConversationState
  ```
- **GOTCHA**: Time-dependent tests (last_active ordering) need `time.sleep(0.01)` between
  operations to ensure different timestamps. Keep sleeps minimal.
- **VALIDATE**: `python -m pytest tests/test_conversation_store.py -v`

### CREATE `tests/test_planner.py`

- **IMPLEMENT**: Unit tests for Planner NextAction interpretation:
  ```python
  class TestPlannerActionInterpretation:
      """Test Planner interprets each NextAction correctly."""

      def _make_planner(self, mock_data=None):
          """Helper to create Planner with mock memory data."""
          memory_service = MemoryService(provider="mem0")
          if mock_data is not None:
              memory_service.set_mock_data(mock_data)
          rerank_service = VoyageRerankService(enabled=False)
          conversation_store = ConversationStore()
          orchestrator = RecallOrchestrator(
              memory_service=memory_service,
              rerank_service=rerank_service,
              feature_flags={"mem0_enabled": True, "supabase_enabled": False},
          )
          return Planner(
              recall_orchestrator=orchestrator,
              conversation_store=conversation_store,
          )

      def test_proceed_action_with_candidates(self):
          """proceed action returns context summary."""

      def test_clarify_action_low_confidence(self):
          """Low confidence triggers clarify with suggestions."""

      def test_fallback_action_empty_set(self):
          """Empty results trigger fallback with rephrase suggestions."""

      def test_escalate_action_channel_mismatch(self):
          """Channel mismatch triggers escalate."""

      def test_response_includes_session_id(self):
          """All responses include the session_id."""

      def test_response_includes_branch_code(self):
          """All responses include the correct branch_code."""

      def test_response_confidence_matches_retrieval(self):
          """PlannerResponse.confidence matches retrieval top_confidence."""

  class TestPlannerConversationTracking:
      """Test Planner maintains conversation state."""

      def test_chat_creates_session(self):
          """First chat creates a new session."""

      def test_chat_records_user_turn(self):
          """User message recorded as turn."""

      def test_chat_records_assistant_turn(self):
          """Response recorded as assistant turn."""

      def test_multi_turn_accumulates(self):
          """Multiple chats accumulate turns in session."""

      def test_session_reuse_with_id(self):
          """Passing session_id reuses existing session."""
  ```
- **PATTERN**: Follow `tests/test_recall_flow_integration.py` setup pattern
- **IMPORTS**:
  ```python
  from second_brain.orchestration.planner import Planner
  from second_brain.agents.recall import RecallOrchestrator
  from second_brain.services.memory import MemoryService, MemorySearchResult
  from second_brain.services.voyage import VoyageRerankService
  from second_brain.services.conversation import ConversationStore
  from second_brain.contracts.conversation import PlannerResponse
  ```
- **GOTCHA**: To test `clarify` branch, set mock data with low confidence (0.4). To test `fallback`,
  set mock data to `[]`. The default mock data in MemoryService returns high-confidence results,
  which triggers `proceed` (or `RERANK_BYPASSED` for mem0). Use `memory_service.set_mock_data()`
  to control the retrieval outcome.
- **VALIDATE**: `python -m pytest tests/test_planner.py -v`

### CREATE `tests/test_chat_integration.py`

- **IMPLEMENT**: Integration tests for the full chat MCP tool:
  ```python
  class TestChatIntegration:
      """Integration tests for chat MCP tool."""

      def test_chat_tool_returns_dict(self):
          """chat_tool returns dict with expected keys."""

      def test_chat_tool_proceed_response(self):
          """chat_tool with good data returns proceed response."""

      def test_chat_tool_fallback_response(self):
          """chat_tool with no data returns fallback response."""

      def test_chat_tool_session_continuity(self):
          """Multiple chat_tool calls with same session_id share state."""

      def test_mcp_server_chat_method(self):
          """MCPServer.chat() works directly."""

      def test_chat_with_tracing_enabled(self):
          """Chat records traces when tracing is enabled."""
  ```
- **PATTERN**: Follow `tests/test_mcp_server_validation.py` pattern for MCPServer testing
- **IMPORTS**:
  ```python
  from second_brain.mcp_server import MCPServer, chat_tool
  ```
- **GOTCHA**: For session continuity test, need to access the MCPServer's shared ConversationStore.
  Create MCPServer directly and call `chat()` method twice with same session_id. Cannot test
  session continuity via `chat_tool()` since it uses global server state.
- **VALIDATE**: `python -m pytest tests/test_chat_integration.py -v`

---

## TESTING STRATEGY

### Unit Tests

- **ConversationStore** (11 tests): Session CRUD, turn management, max limits, eviction, timestamps
- **Planner action interpretation** (7 tests): One per NextAction branch + metadata validation
- **Planner conversation tracking** (5 tests): Multi-turn state, session reuse, turn recording

### Integration Tests

- **Chat flow** (6 tests): Full MCP tool → Planner → RecallOrchestrator → response chain
- **Session continuity**: Multi-turn conversations maintain state across calls
- **Trace integration**: Chat records traces when tracing enabled

### Edge Cases

- Empty query string → should still produce a valid response (fallback)
- Missing session_id → should auto-create session
- Conversation overflow (>max_turns) → should trim oldest turns, not crash
- Unknown NextAction value → should default to fallback (defensive)
- Session limit overflow → should evict oldest inactive sessions

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
python -m ruff check backend/src/second_brain/contracts/conversation.py backend/src/second_brain/services/conversation.py backend/src/second_brain/orchestration/planner.py
python -m ruff check tests/test_conversation_store.py tests/test_planner.py tests/test_chat_integration.py
```

### Level 2: Type Safety
```
python -m mypy backend/src/second_brain/contracts/conversation.py --ignore-missing-imports
python -m mypy backend/src/second_brain/services/conversation.py --ignore-missing-imports
python -m mypy backend/src/second_brain/orchestration/planner.py --ignore-missing-imports
```

### Level 3: Unit Tests
```
python -m pytest tests/test_conversation_store.py tests/test_planner.py -v
```

### Level 4: Integration Tests
```
python -m pytest tests/test_chat_integration.py -v
```

### Level 5: Manual Validation

1. Run full test suite to verify zero regressions:
   ```
   python -m pytest tests/ -v
   ```
2. Verify import chain works end-to-end:
   ```python
   from second_brain.mcp_server import chat_tool
   result = chat_tool(query="What did I learn about Python decorators?")
   assert "response_text" in result
   assert "action_taken" in result
   assert result["action_taken"] in ["proceed", "clarify", "fallback", "escalate"]
   ```
3. Verify multi-turn session works:
   ```python
   from second_brain.mcp_server import MCPServer
   server = MCPServer()
   r1 = server.chat(query="Tell me about decorators")
   session_id = r1["session_id"]
   r2 = server.chat(query="Show me an example", session_id=session_id)
   assert r2["session_id"] == session_id
   ```

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [x] `ConversationTurn`, `ConversationState`, `PlannerResponse` contracts created and exported
- [x] `ConversationStore` implements in-memory session management with bounded limits
- [x] `Planner.chat()` runs full query → retrieval → interpret → respond loop
- [x] `Planner._interpret_action()` handles all 4 NextAction types (proceed/clarify/fallback/escalate)
- [x] `MCPServer.chat()` and `chat_tool()` expose the planning flow as MCP tools
- [x] `deps.py` has `create_planner()` and `create_conversation_store()` factories
- [x] All validation commands pass with zero errors
- [x] 29+ tests pass (11 conversation store + 12 planner + 6 chat integration)

### Runtime (verify after testing/deployment)

- [x] Multi-turn conversations maintain state across calls
- [x] Session eviction works under load (>max_sessions)
- [x] No regressions in existing 175+ tests (219 total now)
- [x] Response templates are readable and actionable for each branch type

---

## COMPLETION CHECKLIST

- [x] All tasks completed in order
- [x] Each task validation passed
- [x] All validation commands executed successfully
- [x] Full test suite passes (unit + integration)
- [x] No linting or type checking errors
- [x] Manual testing confirms feature works
- [x] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Deterministic over generative**: Planner uses template responses, not LLM generation. This
  keeps the module fully testable and predictable. LLM integration is a clean follow-up slice
  that replaces `_format_*` methods with LLM calls.
- **Composition over inheritance**: Planner wraps RecallOrchestrator via composition. This
  preserves the retrieval/planning separation defined in the architecture docs.
- **Stateful MCPServer**: The shared ConversationStore on MCPServer enables multi-turn via
  session_id. This is the minimal state needed — no external persistence.

### Risks

- Risk 1: ConversationStore is in-memory only — server restart loses all sessions.
  Mitigation: Acceptable for this slice. Persistent store is a clean follow-up.
- Risk 2: `create_planner()` in `deps.py` creates a new RecallOrchestrator per call.
  Mitigation: RecallOrchestrator is lightweight (no connection pools). Shared ConversationStore
  ensures session continuity despite fresh orchestrator instances.
- Risk 3: Template responses may feel "robotic" without LLM.
  Mitigation: Templates are intentionally clear and actionable. LLM integration follows once
  the planning skeleton is validated.

### Confidence Score: 9/10

- **Strengths**: Clear contract boundaries from architecture docs, well-understood codebase patterns,
  no external dependencies, comprehensive test plan, deterministic behavior
- **Uncertainties**: Whether the `_format_clarify` helper reference is clean (minor code issue),
  whether MCPServer shared state pattern is the right long-term approach
- **Mitigations**: Both uncertainties are caught by the test suite. The shared ConversationStore
  pattern can be swapped for DI-based approach later without breaking the Planner interface.
