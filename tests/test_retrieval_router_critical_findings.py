"""Regression tests for critical retrieval router findings."""

from second_brain.contracts.context_packet import RetrievalRequest
from second_brain.orchestration.retrieval_router import (
    route_retrieval,
    ProviderStatus,
)


class TestProviderOverrideHealthGating:
    """Test that provider override respects health checks."""
    
    def test_override_rejected_when_provider_unavailable(self):
        """Provider override should not bypass unavailable status."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
            provider_override="mem0",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={"mem0": ProviderStatus.UNAVAILABLE, "supabase": ProviderStatus.AVAILABLE},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
        )
        
        # Override should be rejected, fall back to supabase
        assert provider == "supabase"
        assert options["skip_external_rerank"] is False
    
    def test_override_rejected_when_provider_degraded(self):
        """Provider override should not bypass degraded status."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
            provider_override="mem0",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={"mem0": ProviderStatus.DEGRADED, "supabase": ProviderStatus.AVAILABLE},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
        )
        
        # Override should be rejected, fall back to supabase
        assert provider == "supabase"
    
    def test_override_accepted_when_provider_available(self):
        """Provider override accepted when provider is available."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
            provider_override="supabase",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={"mem0": ProviderStatus.AVAILABLE, "supabase": ProviderStatus.AVAILABLE},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
        )
        
        # Override should be accepted
        assert provider == "supabase"
        assert options["skip_external_rerank"] is False
    
    def test_override_rejected_when_provider_disabled(self):
        """Provider override should not bypass disabled feature flag."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
            provider_override="mem0",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={"mem0": ProviderStatus.AVAILABLE},
            feature_flags={"mem0_enabled": False, "supabase_enabled": True},
        )
        
        # Override rejected (mem0 disabled), fall back to supabase
        assert provider == "supabase"
    
    def test_override_unknown_provider_falls_through(self):
        """Override with unknown provider falls through to normal selection."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
            provider_override="unknown_provider",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={"mem0": ProviderStatus.AVAILABLE},
            feature_flags={"mem0_enabled": True, "supabase_enabled": False},
        )
        
        # Falls through to normal selection
        assert provider == "mem0"


class TestMissingProviderStatusNormalization:
    """Test that missing status keys don't cause false 'none' routing."""
    
    def test_missing_status_defaults_to_available_for_enabled_provider(self):
        """Missing status key should not force 'none' when provider enabled."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={},  # Empty status
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
        )
        
        # Should select mem0 (missing status defaults to available)
        assert provider == "mem0"
        assert options["skip_external_rerank"] is True
    
    def test_explicit_unavailable_still_respected(self):
        """Explicit unavailable status should still prevent selection."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={"mem0": ProviderStatus.UNAVAILABLE},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
        )
        
        # mem0 unavailable, should fall back to supabase
        assert provider == "supabase"
    
    def test_all_providers_explicitly_unavailable_returns_none(self):
        """All providers explicitly unavailable should return 'none'."""
        request = RetrievalRequest(
            query="test",
            mode="conversation",
        )
        
        provider, options = route_retrieval(
            request,
            provider_status={
                "mem0": ProviderStatus.UNAVAILABLE,
                "supabase": ProviderStatus.UNAVAILABLE,
            },
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
        )
        
        assert provider == "none"


class TestRoutingMetadataModeFidelity:
    """Test that routing metadata mode matches request mode."""
    
    def test_metadata_mode_matches_conversation_request(self):
        """Routing metadata mode should match conversation request."""
        from second_brain.agents.recall import RecallOrchestrator
        from second_brain.services.memory import MemoryService
        from second_brain.services.voyage import VoyageRerankService
        
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService()
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
        )
        
        request = RetrievalRequest(
            query="test",
            mode="conversation",  # type: ignore
        )
        
        response = orchestrator.run(request)
        
        assert response.routing_metadata["mode"] == "conversation"
    
    def test_metadata_mode_matches_fast_request(self):
        """Routing metadata mode should match fast request."""
        from second_brain.agents.recall import RecallOrchestrator
        from second_brain.services.memory import MemoryService
        from second_brain.services.voyage import VoyageRerankService
        
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService()
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
        )
        
        request = RetrievalRequest(
            query="test",
            mode="fast",  # type: ignore
        )
        
        response = orchestrator.run(request)
        
        assert response.routing_metadata["mode"] == "fast"
    
    def test_metadata_mode_matches_accurate_request(self):
        """Routing metadata mode should match accurate request."""
        from second_brain.agents.recall import RecallOrchestrator
        from second_brain.services.memory import MemoryService
        from second_brain.services.voyage import VoyageRerankService
        
        memory_service = MemoryService(provider="mem0")
        rerank_service = VoyageRerankService()
        
        orchestrator = RecallOrchestrator(
            memory_service=memory_service,
            rerank_service=rerank_service,
        )
        
        request = RetrievalRequest(
            query="test",
            mode="accurate",  # type: ignore
        )
        
        response = orchestrator.run(request)
        
        assert response.routing_metadata["mode"] == "accurate"


class TestDeterministicOutputAfterNormalization:
    """Test deterministic output remains stable after status normalization."""
    
    def test_deterministic_routing_with_missing_status(self):
        """Routing should be deterministic even with missing status keys."""
        request = RetrievalRequest(
            query="deterministic test",
            mode="conversation",
        )
        
        results = []
        for _ in range(5):
            provider, options = route_retrieval(
                request,
                provider_status={},  # Empty status
                feature_flags={"mem0_enabled": True, "supabase_enabled": True},
            )
            results.append((provider, options["skip_external_rerank"]))
        
        # All results must be identical
        assert all(r == results[0] for r in results)
        assert results[0][0] == "mem0"
        assert results[0][1] is True
    
    def test_deterministic_routing_with_partial_status(self):
        """Routing should be deterministic with partial status snapshot."""
        request = RetrievalRequest(
            query="partial status test",
            mode="fast",
        )
        
        results = []
        for _ in range(5):
            provider, options = route_retrieval(
                request,
                provider_status={"mem0": ProviderStatus.AVAILABLE},  # Only mem0 status
                feature_flags={"mem0_enabled": True, "supabase_enabled": True},
            )
            results.append((provider, options["skip_external_rerank"]))
        
        # All results must be identical
        assert all(r == results[0] for r in results)
        assert results[0][0] == "mem0"
