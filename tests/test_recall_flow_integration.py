"""Integration tests for recall flow with all branch paths."""

from second_brain.contracts.context_packet import RetrievalRequest
from second_brain.orchestration.fallbacks import BranchCodes
from second_brain.agents.recall import RecallOrchestrator, run_recall
from second_brain.services.memory import MemoryService, MemorySearchResult
from second_brain.services.voyage import VoyageRerankService


class TestRecallFlowIntegration:
    """Integration tests for full recall runtime path."""
    
    def test_success_branch_mem0(self):
        """Test SUCCESS branch with Mem0 provider."""
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService(enabled=False)  # Mem0 skips external
        
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
        assert response.next_action.action == "proceed"
        assert response.routing_metadata["selected_provider"] == "mem0"
        assert response.routing_metadata["rerank_type"] == "provider-native"
    
    def test_empty_set_branch(self):
        """Test EMPTY_SET branch with no candidates."""
        memory_service = MemoryService(provider="mem0")
        memory_service.set_mock_data([])
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(
            query="empty set query",
            mode="conversation",
        )
        
        response = orchestrator.run(request)
        
        assert response.context_packet.summary.branch == BranchCodes.EMPTY_SET
        assert response.next_action.action == "fallback"
        assert response.context_packet.candidates == []
    
    def test_low_confidence_branch(self):
        """Test LOW_CONFIDENCE branch."""
        memory_service = MemoryService(provider="mem0")
        memory_service.set_mock_data([
            MemorySearchResult(
                id="low-1",
                content="Low confidence result",
                source="mem0",
                confidence=0.45,
                metadata={},
            ),
        ])
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(
            query="low confidence query",
            mode="conversation",
            threshold=0.6,
        )
        
        response = orchestrator.run(request)
        
        assert response.context_packet.summary.branch == BranchCodes.LOW_CONFIDENCE
        assert response.next_action.action == "clarify"
        assert response.next_action.suggestion is not None
    
    def test_mem0_policy_skip_external_rerank(self):
        """Test Mem0 path skips external rerank by default."""
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService(enabled=True)
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
            feature_flags={"mem0_enabled": True},
        )
        
        request = RetrievalRequest(
            query="mem0 policy test",
            mode="conversation",
        )
        
        response = orchestrator.run(request)
        
        assert response.routing_metadata["skip_external_rerank"] is True
        assert response.routing_metadata["rerank_type"] == "provider-native"
        assert response.routing_metadata["rerank_bypass_reason"] == "mem0-default-policy"
    
    def test_non_mem0_allows_external_rerank(self):
        """Test non-Mem0 path allows external rerank."""
        memory_service = MemoryService(provider="supabase")
        rerank_service = VoyageRerankService(enabled=True)
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
            feature_flags={"mem0_enabled": False, "supabase_enabled": True},
            provider_status={"mem0": "unavailable", "supabase": "available"},
        )
        
        request = RetrievalRequest(
            query="supabase rerank test",
            mode="conversation",
        )
        
        response = orchestrator.run(request)
        
        assert response.routing_metadata["skip_external_rerank"] is False
        assert response.routing_metadata["rerank_type"] == "external"
    
    def test_routing_metadata_complete(self):
        """Test all required routing metadata fields present."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(
            query="metadata test",
            mode="conversation",
        )
        
        response = orchestrator.run(request)
        
        required_fields = [
            "selected_provider",
            "mode",
            "skip_external_rerank",
            "rerank_type",
            "feature_flags_snapshot",
        ]
        
        for field in required_fields:
            assert field in response.routing_metadata, f"Missing field: {field}"
    
    def test_deterministic_repeated_runs(self):
        """Test same inputs produce identical outputs across runs."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(
            query="deterministic test",
            mode="conversation",
        )
        
        results = []
        for _ in range(5):
            response = orchestrator.run(request)
            results.append({
                "branch": response.context_packet.summary.branch,
                "action": response.next_action.action,
                "provider": response.routing_metadata["selected_provider"],
                "rerank_type": response.routing_metadata["rerank_type"],
            })
        
        # All results must be identical
        assert all(r == results[0] for r in results)


class TestValidationModeForcedBranches:
    """Test validation mode with forced branches."""
    
    def test_force_empty_set(self):
        """Force EMPTY_SET branch in validation mode."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(query="test", mode="conversation")
        response = orchestrator.run(
            request,
            validation_mode=True,
            force_branch=BranchCodes.EMPTY_SET,
        )
        
        assert response.context_packet.summary.branch == BranchCodes.EMPTY_SET
        assert response.next_action.action == "fallback"
        assert response.routing_metadata.get("validation_mode") is True
    
    def test_force_low_confidence(self):
        """Force LOW_CONFIDENCE branch in validation mode."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(query="test", mode="conversation")
        response = orchestrator.run(
            request,
            validation_mode=True,
            force_branch=BranchCodes.LOW_CONFIDENCE,
        )
        
        assert response.context_packet.summary.branch == BranchCodes.LOW_CONFIDENCE
        assert response.next_action.action == "clarify"
    
    def test_force_channel_mismatch(self):
        """Force CHANNEL_MISMATCH branch in validation mode."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(query="test", mode="conversation")
        response = orchestrator.run(
            request,
            validation_mode=True,
            force_branch=BranchCodes.CHANNEL_MISMATCH,
        )
        
        assert response.context_packet.summary.branch == BranchCodes.CHANNEL_MISMATCH
        assert response.next_action.action == "escalate"
    
    def test_validation_mode_disabled_by_default(self):
        """Test validation mode is disabled by default."""
        memory_service = MemoryService(provider="mem0")
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=VoyageRerankService(),
        )
        
        request = RetrievalRequest(query="test", mode="conversation")
        response = orchestrator.run(request)  # No validation_mode
        
        assert response.routing_metadata.get("validation_mode") is None


class TestConvenienceFunction:
    """Test run_recall convenience function."""
    
    def test_run_recall_basic(self):
        """Test run_recall convenience function."""
        response = run_recall(
            query="convenience test",
            mode="conversation",
            top_k=5,
            threshold=0.6,
        )
        
        assert response.context_packet is not None
        assert response.next_action is not None
        assert isinstance(response.routing_metadata, dict)
