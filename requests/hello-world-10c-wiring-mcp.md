# Feature: Hello World 10c — LLM Wiring + MCP Transport

Read ALL listed codebase files BEFORE making changes. Execute tasks in order. Run VALIDATE after each.

## Feature Description

Wire the Ollama LLM service (created in 10a) into the planner's response flow, and add FastMCP stdio transport to the MCP server. After this slice, the planner generates LLM-synthesized answers when Ollama is available (falls back to existing f-string formatting when not), and the MCP server can be connected to by any MCP client via stdio.

## Solution Statement

- Wire `OllamaLLMService` into `Planner.__init__` as optional `llm_service` parameter
- Update `Planner._format_proceed()` to call `llm_service.synthesize()` when available, fall back to f-string when not
- Add `_get_last_user_query()` helper to retrieve the user's question for LLM context
- Update `deps.py` `create_planner()` to accept optional `llm_service`
- Update `MCPServer.chat()` to create and inject LLM service
- Add FastMCP transport wrapper around existing MCP server methods
- Add `ingest_markdown` as an MCP tool via FastMCP
- Add `fastmcp` to `pyproject.toml`

## Slice Guardrails

- **Single Outcome**: Planner uses LLM for synthesis + MCP server has wire protocol
- **Scope Boundary**: Does NOT modify retrieval pipeline, ingestion, or contracts. Only touches planner, deps, mcp_server, pyproject.toml.
- **Backward Compat**: When `llm_service=None`, ALL existing behavior is unchanged. ALL 293 existing tests must pass.

---

## CONTEXT REFERENCES

### Relevant Codebase Files — MUST READ BEFORE IMPLEMENTING

- `backend/src/second_brain/orchestration/planner.py` (full file ~306 lines) — The main chat loop. `_format_proceed()` at ~line 187 is where LLM synthesis replaces f-strings. `__init__` needs new `llm_service` param.
- `backend/src/second_brain/deps.py` (full file ~140 lines) — Factory functions. `create_planner()` needs optional `llm_service` param. `create_llm_service()` already exists from 10a.
- `backend/src/second_brain/mcp_server.py` (full file ~290 lines) — `MCPServer.chat()` at ~line 184 creates planner. Must inject LLM service. FastMCP transport goes at bottom.
- `backend/src/second_brain/services/llm.py` (full file) — The `OllamaLLMService` created in 10a. `synthesize(query, context_candidates)` returns `(text, metadata)`.
- `backend/src/second_brain/services/conversation.py` (lines 1-76) — `ConversationStore` and `SessionState`. Need to understand `state.turns` structure for `_get_last_user_query`.
- `backend/src/second_brain/contracts/conversation.py` (full file) — `ConversationTurn` has `role` and `content` fields.
- `backend/pyproject.toml` — Must add `fastmcp` dependency.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `backend/pyproject.toml` — Add fastmcp

Add `"fastmcp>=2.0",` to the dependencies list (after `"supabase>=2.0",`).

Then run: `cd backend && pip install -e .`

- **VALIDATE**: `cd backend && pip install -e . 2>&1 | tail -3 && python -c "import fastmcp; print('OK')"`

### Task 2: UPDATE `backend/src/second_brain/orchestration/planner.py` — Wire LLM synthesis

a) Add `llm_service` parameter to `__init__`:
```python
def __init__(
    self,
    recall_orchestrator: RecallOrchestrator,
    conversation_store: ConversationStore,
    trace_collector: TraceCollector | None = None,
    llm_service: Any | None = None,
):
    self.recall = recall_orchestrator
    self.conversations = conversation_store
    self.trace_collector = trace_collector
    self.llm_service = llm_service
```

Add `from typing import Any` to existing imports if not already present.

b) Add `_get_last_user_query` helper method (before `_format_proceed`):
```python
def _get_last_user_query(self, session_id: str) -> str:
    """Get the last user message from the conversation."""
    state = self.conversations.get_or_create(session_id)
    for turn in reversed(state.turns):
        if turn.role == "user":
            return turn.content
    return ""
```

c) Update `_format_proceed()` to try LLM synthesis first, fall back to existing f-string:

The method currently builds context_parts and returns an f-string response. Replace the ENTIRE `_format_proceed` method with:

```python
def _format_proceed(
    self,
    packet: ContextPacket,
    branch: str,
    session_id: str,
    metadata: dict[str, Any],
) -> PlannerResponse:
    """Format response for proceed action (SUCCESS / RERANK_BYPASSED)."""
    candidates = packet.candidates
    if not candidates:
        return self._format_fallback(packet, branch, session_id, metadata)

    # Try LLM synthesis if service available
    if self.llm_service is not None:
        candidate_dicts = [
            {
                "content": c.content,
                "source": c.source,
                "confidence": c.confidence,
                "metadata": c.metadata,
            }
            for c in candidates
        ]
        query = self._get_last_user_query(session_id)
        response_text, llm_metadata = self.llm_service.synthesize(
            query=query,
            context_candidates=candidate_dicts,
        )
        metadata["llm"] = llm_metadata
        return PlannerResponse(
            response_text=response_text,
            action_taken="proceed",
            branch_code=branch,
            session_id=session_id,
            candidates_used=len(candidates),
            confidence=packet.summary.top_confidence,
            retrieval_metadata=metadata,
        )

    # Fallback: f-string formatting (no LLM)
    context_parts = []
    for i, c in enumerate(candidates[:3], 1):
        content = c.content
        if len(content) > MAX_CANDIDATE_CHARS:
            content = f"{content[:MAX_CANDIDATE_CHARS]}..."
        context_parts.append(f"[{i}] {content}")

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
```

- **GOTCHA**: `Any` must be imported from typing. The `llm_service` is optional — when None, existing f-string behavior is preserved. ALL existing tests must pass unchanged because they don't inject an llm_service.
- **VALIDATE**: `cd backend && python -m pytest ../tests/ -q 2>&1 | tail -3`

### Task 3: UPDATE `backend/src/second_brain/deps.py` — Accept llm_service in create_planner

Update the `create_planner` function signature to accept and pass `llm_service`:

```python
def create_planner(
    memory_service: MemoryService | None = None,
    rerank_service: VoyageRerankService | None = None,
    conversation_store: ConversationStore | None = None,
    trace_collector: TraceCollector | None = None,
    llm_service: Any | None = None,
) -> Planner:
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
        llm_service=llm_service,
    )
```

- **GOTCHA**: `Any` is already in the typing imports from 10a changes. The `llm_service` defaults to None — backward compatible.
- **VALIDATE**: `cd backend && python -m pytest ../tests/ -q 2>&1 | tail -3`

### Task 4: UPDATE `backend/src/second_brain/mcp_server.py` — Inject LLM + FastMCP transport

a) In the `chat()` method, inject LLM service when creating the planner. Find the block where `self._planner is None` and update:

```python
if self._planner is None:
    from second_brain.deps import create_planner, create_llm_service
    llm = create_llm_service()
    self._planner = create_planner(
        conversation_store=self._conversation_store,
        trace_collector=self.trace_collector,
        llm_service=llm,
    )
```

(Replace the existing block that only imports `create_planner` without `create_llm_service`.)

b) Add `import logging` at the top if not already present.

c) Add `logger = logging.getLogger(__name__)` after imports if not present.

d) Add FastMCP transport at the bottom of the file (before any `if __name__` block, or at the very end):

```python
def create_fastmcp_server():
    """Create FastMCP server wrapping MCPServer methods."""
    try:
        from fastmcp import FastMCP
    except ImportError:
        logger.warning("fastmcp not installed — MCP transport unavailable")
        return None

    mcp = FastMCP("Second Brain")
    server = get_mcp_server()

    @mcp.tool()
    def recall_search(
        query: str,
        mode: str = "conversation",
        top_k: int = 5,
        threshold: float = 0.6,
    ) -> dict:
        """Search your knowledge base for relevant context."""
        return server.recall_search(
            query=query, mode=mode, top_k=top_k, threshold=threshold
        )

    @mcp.tool()
    def chat(
        query: str,
        session_id: str | None = None,
        mode: str = "conversation",
    ) -> dict:
        """Ask a question and get an answer grounded in your knowledge base."""
        return server.chat(
            query=query, session_id=session_id, mode=mode
        )

    @mcp.tool()
    def ingest_markdown(
        directory: str,
        knowledge_type: str = "note",
        source_origin: str = "obsidian",
    ) -> dict:
        """Ingest markdown files from a directory into your knowledge base."""
        from second_brain.ingestion.markdown import ingest_markdown_directory

        return ingest_markdown_directory(
            directory=directory,
            knowledge_type=knowledge_type,
            source_origin=source_origin,
        )

    return mcp


if __name__ == "__main__":
    mcp = create_fastmcp_server()
    if mcp:
        mcp.run()
```

- **GOTCHA**: FastMCP `@mcp.tool()` auto-generates tool schema from type hints. `mcp.run()` starts stdio transport. The `if __name__ == "__main__"` guard allows `python -m second_brain.mcp_server`. Keep ALL existing methods unchanged — FastMCP wraps them. The `dict` return type (not `dict[str, Any]`) is intentional for FastMCP schema generation simplicity.
- **VALIDATE**: `cd backend && python -m ruff check src/second_brain/mcp_server.py && python -m mypy src/second_brain/mcp_server.py --ignore-missing-imports`

### Task 5: VALIDATE — Full regression

Run all validation levels:
1. `cd backend && python -m ruff check src/second_brain/ ../tests/`
2. `cd backend && python -m mypy src/second_brain/orchestration/planner.py src/second_brain/deps.py src/second_brain/mcp_server.py --ignore-missing-imports`
3. `cd backend && python -m pytest ../tests/ -q`

ALL 293+ tests must pass. Zero ruff errors. Zero mypy errors.

---

## ACCEPTANCE CRITERIA

- [ ] `planner.py` has `llm_service` param, `_get_last_user_query()`, LLM synthesis in `_format_proceed()`
- [ ] `planner.py` falls back to f-string when `llm_service=None`
- [ ] `deps.py` `create_planner()` accepts `llm_service`
- [ ] `mcp_server.py` injects LLM service into planner
- [ ] `mcp_server.py` has `create_fastmcp_server()` with `recall_search`, `chat`, `ingest_markdown` tools
- [ ] `mcp_server.py` has `if __name__ == "__main__"` entry point
- [ ] `pyproject.toml` has `fastmcp>=2.0`
- [ ] ALL existing tests pass (293+)
- [ ] Ruff clean, mypy clean

## Confidence Score: 8/10
