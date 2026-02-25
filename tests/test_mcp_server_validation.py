"""Tests for MCP server validation endpoint behavior."""

import pytest

from second_brain.mcp_server import MCPServer
from second_brain.validation.manual_branch_scenarios import get_scenario_by_id
from second_brain.orchestration.fallbacks import BranchCodes


class TestValidateBranchScenarioLookup:
    """Test validate_branch scenario lookup behavior."""
    
    @pytest.mark.asyncio
    async def test_unknown_scenario_returns_failure(self):
        """Unknown scenario ID returns failure payload with error."""
        server = MCPServer()
        
        result = await server.validate_branch("NONEXISTENT_SCENARIO")
        
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_known_scenario_returns_success(self):
        """Known scenario ID returns success payload with expected fields."""
        server = MCPServer()
        
        result = await server.validate_branch("S001")
        
        assert result["success"] is True
        assert result["scenario_id"] == "S001"
        assert "expected_branch" in result
        assert "actual_branch" in result
        assert "provider" in result


class TestValidateBranchScenarioContext:
    """Test validate_branch uses scenario context (feature_flags/provider_status)."""
    
    @pytest.mark.asyncio
    async def test_scenario_feature_flags_honored(self):
        """
        Scenario with custom feature_flags should execute with those flags,
        not default flags. Test S004 which expects supabase-only.
        """
        server = MCPServer()
        
        result = await server.validate_branch("S004")
        
        assert result["success"] is True
        assert result["provider"] == "supabase"
    
    @pytest.mark.asyncio
    async def test_scenario_provider_status_honored(self):
        """
        Scenario with custom provider_status should use that status
        for routing decisions.
        """
        server = MCPServer()
        
        result = await server.validate_branch("S013")
        
        assert result["success"] is True
        assert result["expected_branch"] == BranchCodes.EMPTY_SET


class TestValidateBranchGating:
    """Test validation-only scenario gating logic."""
    
    @pytest.mark.asyncio
    async def test_non_validation_scenario_no_forced_branch(self):
        """
        Non-validation-tagged scenario executes without forced branch
        (natural branch evaluation).
        """
        server = MCPServer()
        scenario = get_scenario_by_id("S001")
        
        assert scenario is not None
        assert "validation" not in scenario.tags
        
        result = await server.validate_branch("S001")
        
        assert result["success"] is True
        assert result.get("forced_branch") is None
    
    @pytest.mark.asyncio
    async def test_validation_tag_scenario_gated_without_debug(self):
        """
        Validation-tagged scenario should not force branch when
        debug mode is disabled (strict gating).
        """
        server = MCPServer()
        server.debug_mode = False
        
        result = await server.validate_branch("S027")
        
        scenario = get_scenario_by_id("S027")
        assert scenario is not None
        assert "validation" in scenario.tags
        
        if not server.debug_mode:
            assert result.get("gated") is True or result.get("forced_branch") is None
    
    @pytest.mark.asyncio
    async def test_validation_tag_scenario_allowed_with_debug(self):
        """
        Validation-tagged scenario can force branch when
        debug mode is enabled.
        """
        server = MCPServer()
        server.enable_debug_mode()
        
        result = await server.validate_branch("S027")
        
        scenario = get_scenario_by_id("S027")
        assert scenario is not None
        assert "validation" in scenario.tags
        
        if server.debug_mode:
            assert result["success"] is True


class TestValidateBranchResponseFormat:
    """Test validate_branch response format compatibility."""
    
    @pytest.mark.asyncio
    async def test_response_includes_required_fields(self):
        """Response includes all required fields for operator UX."""
        server = MCPServer()
        
        result = await server.validate_branch("S001")
        
        required_fields = [
            "success",
            "scenario_id",
            "expected_branch",
            "actual_branch",
            "expected_action",
            "actual_action",
            "branch_match",
            "action_match",
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    @pytest.mark.asyncio
    async def test_branch_match_boolean(self):
        """branch_match field is boolean."""
        server = MCPServer()
        
        result = await server.validate_branch("S001")
        
        assert isinstance(result["branch_match"], bool)
    
    @pytest.mark.asyncio
    async def test_action_match_boolean(self):
        """action_match field is boolean."""
        server = MCPServer()
        
        result = await server.validate_branch("S001")
        
        assert isinstance(result["action_match"], bool)
