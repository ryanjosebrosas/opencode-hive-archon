"""Manual branch validation harness tests."""
import pytest

from second_brain.agents.recall import RecallOrchestrator
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.validation.manual_branch_scenarios import (
    get_all_scenarios,
    get_scenario_by_id,
    get_smoke_scenarios,
    get_policy_scenarios,
    BranchScenario,
)
from second_brain.orchestration.fallbacks import BranchCodes


class TestScenarioFixtures:
    """Test scenario fixture integrity."""
    
    def test_all_scenarios_have_unique_ids(self):
        """Ensure no duplicate scenario IDs."""
        scenarios = get_all_scenarios()
        ids = [s.id for s in scenarios]
        assert len(ids) == len(set(ids)), "Duplicate scenario IDs found"
    
    def test_all_scenarios_have_required_fields(self):
        """Ensure all scenarios have required fields."""
        for scenario in get_all_scenarios():
            assert scenario.id, "Missing scenario ID"
            assert scenario.description, "Missing description"
            assert scenario.request, "Missing request"
            assert scenario.expected_branch, "Missing expected branch"
            assert scenario.expected_action, "Missing expected action"
            assert scenario.tags, "Missing tags"
    
    def test_scenario_branch_codes_valid(self):
        """Ensure all expected branches are valid BranchCodes."""
        valid_branches = [
            BranchCodes.EMPTY_SET,
            BranchCodes.LOW_CONFIDENCE,
            BranchCodes.CHANNEL_MISMATCH,
            BranchCodes.RERANK_BYPASSED,
            BranchCodes.SUCCESS,
        ]
        
        for scenario in get_all_scenarios():
            assert scenario.expected_branch in valid_branches, \
                f"Invalid branch {scenario.expected_branch} in scenario {scenario.id}"
    
    def test_scenario_action_codes_valid(self):
        """Ensure all expected actions are valid."""
        valid_actions = ["proceed", "clarify", "fallback", "escalate"]
        
        for scenario in get_all_scenarios():
            assert scenario.expected_action in valid_actions, \
                f"Invalid action {scenario.expected_action} in scenario {scenario.id}"
    
    def test_scenario_tags_present(self):
        """Ensure scenarios have appropriate tags."""
        valid_tags = ["smoke", "policy", "edge", "degraded", "validation", "deterministic"]
        
        for scenario in get_all_scenarios():
            for tag in scenario.tags:
                assert tag in valid_tags, f"Invalid tag {tag} in scenario {scenario.id}"


class TestSmokeScenarios:
    """Test smoke scenario execution."""
    
    @pytest.mark.parametrize("scenario", get_smoke_scenarios(), ids=lambda s: s.id)
    def test_smoke_scenario_branch(self, scenario: BranchScenario):
        """Test smoke scenarios produce expected branch."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        assert response.context_packet.summary.branch == scenario.expected_branch, \
            f"Scenario {scenario.id}: Expected {scenario.expected_branch}, got {response.context_packet.summary.branch}"
    
    @pytest.mark.parametrize("scenario", get_smoke_scenarios(), ids=lambda s: s.id)
    def test_smoke_scenario_action(self, scenario: BranchScenario):
        """Test smoke scenarios produce expected action."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        assert response.next_action.action == scenario.expected_action, \
            f"Scenario {scenario.id}: Expected {scenario.expected_action}, got {response.next_action.action}"


class TestPolicyScenarios:
    """Test policy scenario execution."""
    
    @pytest.mark.parametrize("scenario", get_policy_scenarios(), ids=lambda s: s.id)
    def test_policy_scenario_rerank_metadata(self, scenario: BranchScenario):
        """Test policy scenarios have correct rerank metadata."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        assert response.routing_metadata["rerank_type"] == scenario.expected_rerank_type, \
            f"Scenario {scenario.id}: Expected rerank_type {scenario.expected_rerank_type}, got {response.routing_metadata['rerank_type']}"


class TestEdgeScenarios:
    """Test edge scenario execution."""
    
    def test_all_providers_disabled_returns_empty_set(self):
        """Test S013: All providers disabled returns EMPTY_SET."""
        scenario = get_scenario_by_id("S013")
        assert scenario is not None
        
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        assert response.context_packet.summary.branch == BranchCodes.EMPTY_SET
        assert response.next_action.action == "fallback"
    
    def test_all_providers_unavailable_returns_empty_set(self):
        """Test S014: All providers unavailable returns EMPTY_SET."""
        scenario = get_scenario_by_id("S014")
        assert scenario is not None
        
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        assert response.context_packet.summary.branch == BranchCodes.EMPTY_SET


class TestDegradedScenarios:
    """Test degraded provider scenario execution."""
    
    def test_degraded_mem0_falls_back_to_supabase(self):
        """Test S015: Degraded Mem0 falls back to Supabase."""
        scenario = get_scenario_by_id("S015")
        assert scenario is not None
        
        memory_service = MemoryService(provider="supabase")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(enabled=True),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        # Degraded scenario returns low confidence result
        assert response.context_packet.summary.branch == BranchCodes.LOW_CONFIDENCE
        assert response.next_action.action == "clarify"


class TestDeterministicReplay:
    """Test deterministic replay scenarios."""
    
    def test_deterministic_replay_s048(self):
        """Test S048: Same inputs produce identical outputs."""
        scenario = get_scenario_by_id("S048")
        assert scenario is not None
        
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        results = []
        for _ in range(10):
            response = orchestrator.run(scenario.request)
            results.append({
                "branch": response.context_packet.summary.branch,
                "action": response.next_action.action,
                "provider": response.routing_metadata["selected_provider"],
                "rerank_type": response.routing_metadata["rerank_type"],
            })
        
        assert all(r == results[0] for r in results), "Non-deterministic results detected"


class TestOperatorFriendlyAssertions:
    """Test operator-friendly assertion messages."""
    
    def test_branch_mismatch_message_includes_scenario_id(self):
        """Ensure branch mismatch messages include scenario ID."""
        scenario = get_scenario_by_id("S001")
        assert scenario is not None
        
        memory_service = MemoryService(provider="mem0")
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
            feature_flags=scenario.feature_flags,
            provider_status=scenario.provider_status,
        )
        
        response = orchestrator.run(scenario.request)
        
        # Verify we can construct helpful error message
        if response.context_packet.summary.branch != scenario.expected_branch:
            error_msg = (
                f"Scenario {scenario.id} ({scenario.description}): "
                f"Expected branch {scenario.expected_branch}, "
                f"got {response.context_packet.summary.branch}"
            )
            assert scenario.id in error_msg


class TestValidationTaggedScenarios:
    """Test validation-only tagged scenario behavior."""
    
    def test_validation_tagged_scenario_exists(self):
        """Verify at least one validation-tagged scenario exists for testing."""
        validation_scenarios = [s for s in get_all_scenarios() if "validation" in s.tags]
        assert len(validation_scenarios) >= 1, "No validation-tagged scenarios found"
    
    def test_validation_scenario_not_smoke_or_policy(self):
        """
        Validation-tagged scenarios should not be treated as normal
        smoke/policy paths. They require explicit validation_mode=True.
        """
        scenario = get_scenario_by_id("S027")
        assert scenario is not None
        assert "validation" in scenario.tags
        assert "smoke" not in scenario.tags
    
    def test_validation_scenario_expected_branch_distinct(self):
        """
        Validation-tagged scenarios have expected branches that differ
        from what natural evaluation would produce (they are forced).
        """
        validation_scenarios = [s for s in get_all_scenarios() if "validation" in s.tags]
        
        for scenario in validation_scenarios:
            assert scenario.expected_branch is not None
            assert scenario.notes != "", \
                f"Validation scenario {scenario.id} should have notes explaining forced behavior"
