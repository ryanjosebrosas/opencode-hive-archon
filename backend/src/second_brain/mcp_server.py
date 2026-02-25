"""MCP server for tool exposure."""
from typing import Any, Optional
from second_brain.agents.recall import run_recall
from second_brain.schemas import MCPCompatibilityResponse


class MCPServer:
    """MCP server exposing recall flow as tools."""
    
    def __init__(self):
        self.debug_mode = False
    
    async def recall_search(
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
        response = run_recall(
            query=query,
            mode=mode,
            top_k=top_k,
            threshold=threshold,
            provider_override=provider_override,
        )
        
        compatibility = MCPCompatibilityResponse.from_retrieval_response(
            response=response,
            include_legacy=True,
        )
        
        return compatibility.model_dump()
    
    async def validate_branch(
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
        
        response = run_recall(
            query=scenario.request.query,
            mode=scenario.request.mode,
            top_k=scenario.request.top_k,
            threshold=scenario.request.threshold,
            validation_mode=True,
            force_branch=scenario.expected_branch if "validation" in scenario.tags else None,
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


async def recall_search_tool(
    query: str,
    mode: str = "conversation",
    top_k: int = 5,
    threshold: float = 0.6,
) -> dict[str, Any]:
    """MCP tool: Search memory."""
    server = get_mcp_server()
    return await server.recall_search(
        query=query,
        mode=mode,
        top_k=top_k,
        threshold=threshold,
    )


async def validate_branch_tool(scenario_id: str) -> dict[str, Any]:
    """MCP tool: Validate branch scenario."""
    server = get_mcp_server()
    return await server.validate_branch(scenario_id)
