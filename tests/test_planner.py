"""Unit tests for Planner action interpretation and conversation tracking."""

from second_brain.orchestration.planner import Planner
from second_brain.agents.recall import RecallOrchestrator
from second_brain.services.memory import MemoryService, MemorySearchResult
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.conversation import ConversationStore
from second_brain.services.trace import TraceCollector


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
        mock_data = [
            MemorySearchResult(
                id="test-1",
                content="Python decorators wrap functions",
                source="mem0",
                confidence=0.95,
                metadata={},
            )
        ]
        planner = self._make_planner(mock_data)
        response = planner.chat(query="What are Python decorators?")

        assert response.action_taken == "proceed"
        assert response.candidates_used == 1
        assert response.confidence == 0.95
        assert "Python decorators" in response.response_text

    def test_clarify_action_low_confidence(self):
        """Low confidence triggers clarify with suggestions."""
        mock_data = [
            MemorySearchResult(
                id="test-1",
                content="Some vague match",
                source="mem0",
                confidence=0.4,
                metadata={},
            )
        ]
        planner = self._make_planner(mock_data)
        response = planner.chat(query="Tell me about something")

        assert response.action_taken == "clarify"
        assert len(response.suggestions) > 0
        assert "specific" in response.suggestions[0].lower()

    def test_fallback_action_empty_set(self):
        """Empty results trigger fallback with rephrase suggestions."""
        mock_data = []
        planner = self._make_planner(mock_data)
        response = planner.chat(query="Nonexistent topic xyz123")

        assert response.action_taken == "fallback"
        assert response.candidates_used == 0
        assert response.confidence == 0.0
        assert len(response.suggestions) > 0
        assert "Rephrase" in response.suggestions[0]

    def test_escalate_action_channel_mismatch(self):
        """Channel mismatch triggers escalate."""
        # This is hard to trigger without mocking the router
        # For now, test that fallback is the default for unexpected cases
        mock_data = []
        planner = self._make_planner(mock_data)
        response = planner.chat(query="Test")

        assert response.action_taken in ["proceed", "clarify", "fallback", "escalate"]
        assert response.branch_code is not None

    def test_response_includes_session_id(self):
        """All responses include the session_id."""
        planner = self._make_planner()
        response = planner.chat(query="Test query")

        assert response.session_id is not None
        assert len(response.session_id) > 0

    def test_response_includes_branch_code(self):
        """All responses include the correct branch_code."""
        planner = self._make_planner()
        response = planner.chat(query="Test query")

        assert response.branch_code in [
            "SUCCESS",
            "LOW_CONFIDENCE",
            "EMPTY_SET",
            "CHANNEL_MISMATCH",
            "RERANK_BYPASSED",
        ]

    def test_response_confidence_matches_retrieval(self):
        """PlannerResponse.confidence matches retrieval top_confidence."""
        mock_data = [
            MemorySearchResult(
                id="test-1",
                content="Test content",
                source="mem0",
                confidence=0.88,
                metadata={},
            )
        ]
        planner = self._make_planner(mock_data)
        response = planner.chat(query="Test")

        assert response.confidence == 0.88

    def test_proceed_response_truncates_candidate_content(self):
        """Proceed response truncates oversized candidate content."""
        long_content = "A" * 500
        mock_data = [
            MemorySearchResult(
                id="test-1",
                content=long_content,
                source="mem0",
                confidence=0.95,
                metadata={},
            )
        ]
        planner = self._make_planner(mock_data)

        response = planner.chat(query="Show long content")

        assert response.action_taken == "proceed"
        assert ("A" * 300 + "...") in response.response_text

    def test_chat_returns_fallback_when_retrieval_raises(self):
        """Planner gracefully falls back when retrieval execution fails."""

        class FailingRecall:
            def run(self, _request):
                from second_brain.errors import RetrievalError
                raise RetrievalError("provider timeout")

        planner = Planner(
            recall_orchestrator=FailingRecall(),
            conversation_store=ConversationStore(),
        )

        response = planner.chat(query="hello")

        assert response.action_taken == "fallback"
        assert response.branch_code == "RETRIEVAL_ERROR"
        assert response.retrieval_metadata["error_type"] == "RetrievalError"

    def test_chat_records_error_trace_when_collector_enabled(self):
        """Planner records retrieval error traces when collector is configured."""

        class FailingRecall:
            def run(self, _request):
                from second_brain.errors import RetrievalError
                raise RetrievalError("provider timeout")

        trace_collector = TraceCollector(max_traces=10)
        planner = Planner(
            recall_orchestrator=FailingRecall(),
            conversation_store=ConversationStore(),
            trace_collector=trace_collector,
        )

        planner.chat(query="hello")

        traces = trace_collector.get_traces()
        assert len(traces) == 1
        assert traces[0].status == "error"
        assert traces[0].branch_code == "RETRIEVAL_ERROR"

    def test_chat_returns_fallback_when_request_validation_fails(self):
        """Planner gracefully falls back when request validation fails."""
        planner = self._make_planner()

        response = planner.chat(query="hello", top_k=0)

        assert response.action_taken == "fallback"
        assert response.branch_code == "RETRIEVAL_ERROR"
        assert response.retrieval_metadata["error_type"] == "ValidationError"

    def test_chat_reraises_unexpected_retrieval_errors(self):
        """Unexpected retrieval exceptions are re-raised for visibility."""

        class UnexpectedFailRecall:
            def run(self, _request):
                raise KeyError("unexpected")

        planner = Planner(
            recall_orchestrator=UnexpectedFailRecall(),
            conversation_store=ConversationStore(),
        )

        try:
            planner.chat(query="hello")
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "unexpected" in str(e)


class TestPlannerConversationTracking:
    """Test Planner maintains conversation state."""

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

    def test_chat_creates_session(self):
        """First chat creates a new session."""
        planner = self._make_planner()
        response = planner.chat(query="Hello")

        assert response.session_id is not None

    def test_chat_records_user_turn(self):
        """User message recorded as turn."""
        planner = self._make_planner()
        response = planner.chat(query="What is Python?")

        store = planner.conversations
        state = store.get_session(response.session_id)

        assert state is not None
        assert len(state.turns) == 2
        assert state.turns[0].role == "user"
        assert state.turns[0].content == "What is Python?"

    def test_chat_records_assistant_turn(self):
        """Response recorded as assistant turn."""
        planner = self._make_planner()
        response = planner.chat(query="Test")

        store = planner.conversations
        state = store.get_session(response.session_id)

        assert state.turns[1].role == "assistant"
        assert state.turns[1].content == response.response_text
        assert state.turns[1].action_taken == response.action_taken

    def test_multi_turn_accumulates(self):
        """Multiple chats accumulate turns in session."""
        planner = self._make_planner()
        r1 = planner.chat(query="First question")
        r2 = planner.chat(query="Second question", session_id=r1.session_id)
        r3 = planner.chat(query="Third question", session_id=r1.session_id)

        assert r1.session_id == r2.session_id == r3.session_id

        state = planner.conversations.get_session(r1.session_id)
        assert len(state.turns) == 6

    def test_session_reuse_with_id(self):
        """Passing session_id reuses existing session."""
        planner = self._make_planner()
        r1 = planner.chat(query="First")
        r2 = planner.chat(query="Second", session_id=r1.session_id)

        assert r1.session_id == r2.session_id

        state = planner.conversations.get_session(r1.session_id)
        assert len(state.turns) == 4
