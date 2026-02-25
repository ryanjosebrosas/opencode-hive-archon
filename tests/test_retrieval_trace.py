"""Tests for retrieval trace functionality."""

from second_brain.contracts.trace import RetrievalTrace
from second_brain.services.trace import TraceCollector
from second_brain.agents.recall import RecallOrchestrator
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.contracts.context_packet import RetrievalRequest
from second_brain.mcp_server import MCPServer


class TestRetrievalTraceModel:
    """Unit tests for RetrievalTrace Pydantic model."""

    def test_trace_model_construction(self):
        """Build a trace with all required fields, verify defaults."""
        trace = RetrievalTrace(
            query="test query",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test trace",
        )

        assert trace.trace_id is not None
        assert len(trace.trace_id) > 0
        assert trace.timestamp is not None
        assert trace.status == "ok"
        assert trace.duration_ms == 0.0
        assert trace.error_type is None
        assert trace.error_message is None

    def test_trace_model_serialization(self):
        """Verify model_dump() produces expected dict structure."""
        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )

        data = trace.model_dump()
        assert data["query"] == "test"
        assert data["mode"] == "conversation"
        assert data["selected_provider"] == "mem0"
        assert data["branch_code"] == "SUCCESS"
        assert "trace_id" in data
        assert "timestamp" in data

    def test_trace_model_defaults(self):
        """Verify optional fields default correctly."""
        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )

        assert trace.error_type is None
        assert trace.error_message is None
        assert trace.forced_branch is None
        assert trace.validation_mode is False
        assert trace.rerank_type == "none"
        assert trace.skip_external_rerank is False

    def test_trace_id_uniqueness(self):
        """Create multiple traces, verify all trace_ids differ."""
        traces = [
            RetrievalTrace(
                query=f"test {i}",
                mode="conversation",
                top_k=5,
                threshold=0.6,
                selected_provider="mem0",
                branch_code="SUCCESS",
                action="proceed",
                reason=f"test {i}",
            )
            for i in range(5)
        ]

        trace_ids = [t.trace_id for t in traces]
        assert len(set(trace_ids)) == len(trace_ids)


class TestTraceCollector:
    """Unit tests for TraceCollector service."""

    def test_collector_record_and_retrieve(self):
        """Record a trace, get_traces returns it."""
        collector = TraceCollector()
        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )

        collector.record(trace)

        assert collector.count == 1
        assert collector.get_traces()[0] == trace

    def test_collector_get_by_id(self):
        """Record trace, look up by trace_id."""
        collector = TraceCollector()
        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )

        collector.record(trace)
        retrieved = collector.get_by_id(trace.trace_id)

        assert retrieved == trace

    def test_collector_get_by_id_not_found(self):
        """Look up nonexistent ID returns None."""
        collector = TraceCollector()

        result = collector.get_by_id("nonexistent-id")

        assert result is None

    def test_collector_get_latest(self):
        """Record 5 traces, get_latest(2) returns last 2."""
        collector = TraceCollector()
        traces = [
            RetrievalTrace(
                query=f"test {i}",
                mode="conversation",
                top_k=5,
                threshold=0.6,
                selected_provider="mem0",
                branch_code="SUCCESS",
                action="proceed",
                reason=f"test {i}",
            )
            for i in range(5)
        ]

        for t in traces:
            collector.record(t)

        latest = collector.get_latest(2)

        assert len(latest) == 2
        assert latest[0] == traces[3]
        assert latest[1] == traces[4]

    def test_collector_clear(self):
        """Record traces, clear, verify empty."""
        collector = TraceCollector()
        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )

        collector.record(trace)
        collector.clear()

        assert collector.count == 0
        assert len(collector.get_traces()) == 0

    def test_collector_count(self):
        """Record 3 traces, count == 3."""
        collector = TraceCollector()

        for i in range(3):
            collector.record(
                RetrievalTrace(
                    query=f"test {i}",
                    mode="conversation",
                    top_k=5,
                    threshold=0.6,
                    selected_provider="mem0",
                    branch_code="SUCCESS",
                    action="proceed",
                    reason=f"test {i}",
                )
            )

        assert collector.count == 3

    def test_collector_max_traces_eviction(self):
        """Set max_traces=3, record 5, verify only last 3 remain."""
        collector = TraceCollector(max_traces=3)
        traces = [
            RetrievalTrace(
                query=f"test {i}",
                mode="conversation",
                top_k=5,
                threshold=0.6,
                selected_provider="mem0",
                branch_code="SUCCESS",
                action="proceed",
                reason=f"test {i}",
            )
            for i in range(5)
        ]

        for t in traces:
            collector.record(t)

        assert collector.count == 3
        stored = collector.get_traces()
        assert stored[0] == traces[2]
        assert stored[1] == traces[3]
        assert stored[2] == traces[4]

    def test_collector_callback(self):
        """Register callback, record trace, verify callback was called."""
        calls = []

        def callback(t: RetrievalTrace) -> None:
            calls.append(t)

        collector = TraceCollector(callback=callback)

        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )
        collector.record(trace)

        assert len(calls) == 1
        assert calls[0] == trace

    def test_collector_callback_none(self):
        """No callback registered, record works fine."""
        collector = TraceCollector(callback=None)
        trace = RetrievalTrace(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
            selected_provider="mem0",
            branch_code="SUCCESS",
            action="proceed",
            reason="test",
        )

        collector.record(trace)

        assert collector.count == 1


class TestOrchestratorTraceEmission:
    """Integration tests for trace emission during orchestrator runs."""

    def test_orchestrator_emits_trace_on_success(self):
        """Run orchestrator with collector, verify trace recorded."""
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

        assert collector.count == 1
        trace = collector.get_traces()[0]
        assert trace.status == "ok"
        assert trace.duration_ms > 0
        assert "trace_id" in response.routing_metadata

    def test_orchestrator_no_trace_without_collector(self):
        """Run orchestrator without collector, verify no errors."""
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService(enabled=False)

        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
            feature_flags={"mem0_enabled": True, "supabase_enabled": False},
        )

        request = RetrievalRequest(
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
        )

        response = orchestrator.run(request)

        assert "trace_id" not in response.routing_metadata

    def test_trace_duration_positive(self):
        """Verify duration_ms > 0 for any real run."""
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
            query="test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
        )

        orchestrator.run(request)
        trace = collector.get_traces()[0]

        assert trace.duration_ms > 0


class TestMCPServerTracing:
    """Integration tests for MCP server tracing."""

    def test_mcp_server_tracing_disabled_by_default(self):
        """Verify get_traces returns empty when tracing not enabled."""
        server = MCPServer()

        traces = server.get_traces()

        assert traces == []
        assert server.trace_collector is None

    def test_mcp_server_enable_tracing(self):
        """Enable tracing, run recall_search, verify traces available."""
        server = MCPServer()
        server.enable_tracing()

        assert server.trace_collector is not None

        server.recall_search(
            query="test query",
            mode="conversation",
            top_k=5,
            threshold=0.6,
        )

        traces = server.get_traces()
        assert len(traces) >= 1
        assert "trace_id" in traces[0]

    def test_mcp_server_disable_tracing(self):
        """Enable then disable, verify collector is None."""
        server = MCPServer()
        server.enable_tracing()
        server.disable_tracing()

        assert server.trace_collector is None
        assert server.get_traces() == []
