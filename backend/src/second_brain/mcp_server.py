"""MCP server for tool exposure."""

from typing import Any, Optional, Literal, cast
from second_brain.agents.recall import RecallOrchestrator
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.trace import TraceCollector
from second_brain.schemas import MCPCompatibilityResponse


class MCPServer:
    """MCP server exposing recall flow as tools."""

    def __init__(self):
        self.debug_mode = False
        self.trace_collector: TraceCollector | None = None

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

    def recall_search(
        self,
        query: str,
        mode: str = "conversation",
        top_k: int = 5,
        threshold: float = 0.6,
        provider_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Search memory with contract-aligned response.

        Args:
            query: Search query string
            mode: Retrieval mode (fast, accurate, conversation)
            top_k: Maximum results
            threshold: Confidence threshold
            provider_override: Optional provider override

        Returns:
            Compatibility response with contract envelope + legacy fields
        """
        from second_brain.contracts.context_packet import RetrievalRequest
        from second_brain.deps import get_feature_flags, get_provider_status

        request = RetrievalRequest(
            query=query,
            mode=cast(Literal["fast", "accurate", "conversation"], mode),
            top_k=top_k,
            threshold=threshold,
            provider_override=provider_override,
        )

        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService(enabled=True)

        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
            feature_flags=get_feature_flags(),
            provider_status=get_provider_status(),
            trace_collector=self.trace_collector,
        )

        response = orchestrator.run(request)

        compatibility = MCPCompatibilityResponse.from_retrieval_response(
            response=response,
            include_legacy=True,
        )

        return compatibility.model_dump()

    def validate_branch(
        self,
        scenario_id: str,
    ) -> dict[str, Any]:
        """
        Run validation scenario and return result.

        Debug/validation endpoint for manual branch testing.

        Args:
            scenario_id: Scenario ID from manual_branch_scenarios

        Returns:
            Validation result with branch, action, metadata
        """
        from second_brain.validation.manual_branch_scenarios import get_scenario_by_id

        scenario = get_scenario_by_id(scenario_id)
        if not scenario:
            return {
                "success": False,
                "error": f"Scenario {scenario_id} not found",
            }

        is_validation_tagged = "validation" in scenario.tags

        if is_validation_tagged and not self.debug_mode:
            return {
                "success": False,
                "gated": True,
                "error": (
                    f"Scenario {scenario_id} is validation-only. "
                    "Enable debug mode to execute validation-tagged scenarios."
                ),
                "scenario_id": scenario_id,
                "description": scenario.description,
            }

        # Placeholder service - orchestrator resolves provider-consistent instance via
        # _resolve_memory_service_for_provider based on scenario's feature_flags/provider_status
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService(enabled=True)

        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
            trace_collector=self.trace_collector,
        )

        force_branch = None
        if is_validation_tagged and self.debug_mode:
            force_branch = scenario.expected_branch

        response = orchestrator.run(
            request=scenario.request,
            validation_mode=self.debug_mode,
            force_branch=force_branch,
        )

        return {
            "success": True,
            "scenario_id": scenario_id,
            "description": scenario.description,
            "expected_branch": scenario.expected_branch,
            "actual_branch": response.context_packet.summary.branch,
            "expected_action": scenario.expected_action,
            "actual_action": response.next_action.action,
            "rerank_type": response.routing_metadata.get("rerank_type"),
            "provider": response.routing_metadata.get("selected_provider"),
            "branch_match": response.context_packet.summary.branch == scenario.expected_branch,
            "action_match": response.next_action.action == scenario.expected_action,
            "forced_branch": force_branch,
            "gated": False,
        }

    def enable_debug_mode(self) -> None:
        """Enable debug mode for validation endpoints."""
        self.debug_mode = True

    def disable_debug_mode(self) -> None:
        """Disable debug mode."""
        self.debug_mode = False


# Global MCP server instance
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get or create MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


def recall_search_tool(
    query: str,
    mode: str = "conversation",
    top_k: int = 5,
    threshold: float = 0.6,
) -> dict[str, Any]:
    """MCP tool: Search memory."""
    server = get_mcp_server()
    return server.recall_search(
        query=query,
        mode=mode,
        top_k=top_k,
        threshold=threshold,
    )


def validate_branch_tool(scenario_id: str) -> dict[str, Any]:
    """MCP tool: Validate branch scenario."""
    server = get_mcp_server()
    return server.validate_branch(scenario_id)
