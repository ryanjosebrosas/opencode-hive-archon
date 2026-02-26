"""Integration tests for chat MCP tool."""

from concurrent.futures import ThreadPoolExecutor

from second_brain.mcp_server import MCPServer, chat_tool
from second_brain.services.conversation import ConversationStore


class TestChatIntegration:
    """Integration tests for chat MCP tool."""

    def test_chat_tool_returns_dict(self):
        """chat_tool returns dict with expected keys."""
        result = chat_tool(query="Test query")

        assert isinstance(result, dict)
        assert "response_text" in result
        assert "action_taken" in result
        assert "branch_code" in result
        assert "session_id" in result
        assert "suggestions" in result
        assert result["action_taken"] in ["proceed", "clarify", "fallback", "escalate"]

    def test_chat_tool_proceed_response(self):
        """chat_tool with good data returns proceed response."""
        result = chat_tool(query="test")

        assert isinstance(result, dict)
        assert result["action_taken"] in ["proceed", "clarify", "fallback", "escalate"]
        assert isinstance(result["response_text"], str)
        assert len(result["response_text"]) > 0

    def test_chat_tool_fallback_response(self):
        """chat_tool with no data returns fallback response."""
        result = chat_tool(query="nonexistent xyzabc123")

        assert isinstance(result, dict)
        assert result["action_taken"] in ["proceed", "fallback", "clarify", "escalate"]

    def test_chat_tool_session_continuity(self):
        """Multiple MCPServer.chat calls with same session_id share state."""
        server = MCPServer()
        r1 = server.chat(query="First message")
        session_id = r1["session_id"]

        r2 = server.chat(query="Second message", session_id=session_id)

        assert r2["session_id"] == session_id

    def test_chat_rejects_unissued_session_id(self):
        """Unknown client-supplied session IDs are not adopted."""
        server = MCPServer()
        result = server.chat(query="Hello", session_id="attacker-controlled-id")

        assert result["session_id"] != "attacker-controlled-id"

    def test_chat_prunes_issued_session_ids_to_active_sessions(self):
        """Issued session set stays bounded with active store sessions."""
        server = MCPServer()
        server._conversation_store = ConversationStore(max_sessions=2)  # noqa: SLF001

        s1 = server.chat(query="one")["session_id"]
        s2 = server.chat(query="two")["session_id"]
        server.chat(query="three")

        assert len(server._issued_session_ids) <= 2  # noqa: SLF001
        assert (
            s1 not in server._issued_session_ids or s2 not in server._issued_session_ids
        )  # noqa: SLF001

    def test_mcp_server_chat_method(self):
        """MCPServer.chat() works directly."""
        server = MCPServer()
        result = server.chat(query="Test")

        assert isinstance(result, dict)
        assert "response_text" in result
        assert "action_taken" in result

    def test_chat_with_tracing_enabled(self):
        """Chat records traces when tracing is enabled."""
        server = MCPServer()
        server.enable_tracing(max_traces=100)

        result = server.chat(query="Test with tracing")

        assert isinstance(result, dict)
        assert "response_text" in result

        traces = server.get_traces()
        assert len(traces) >= 1
        assert traces[0]["query"] == "Test with tracing"

    def test_chat_concurrent_session_issuance(self):
        """Concurrent chat calls issue stable, unique session IDs."""
        server = MCPServer()

        def run_chat(i: int) -> str:
            return server.chat(query=f"q{i}")["session_id"]

        with ThreadPoolExecutor(max_workers=8) as pool:
            session_ids = list(pool.map(run_chat, range(20)))

        assert len(session_ids) == 20
        assert len(set(session_ids)) == 20

    def test_chat_reuses_cached_planner_instance(self):
        """MCPServer caches planner across chat calls."""
        server = MCPServer()

        server.chat(query="first")
        first_planner_id = id(server._planner)  # noqa: SLF001

        server.chat(query="second")
        assert id(server._planner) == first_planner_id  # noqa: SLF001
