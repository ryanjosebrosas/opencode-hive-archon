"""Test retrieval router policy and deterministic selection."""

from second_brain.contracts.context_packet import RetrievalRequest
from second_brain.orchestration.retrieval_router import (
    route_retrieval,
    RouteDecision,
    ProviderStatus,
)


class TestProviderStatus:
    """Test ProviderStatus constants."""
    
    def test_status_values(self):
        assert ProviderStatus.AVAILABLE == "available"
        assert ProviderStatus.UNAVAILABLE == "unavailable"
        assert ProviderStatus.DEGRADED == "degraded"


class TestRouteDecisionSelectRoute:
    """Test RouteDecision.select_route method."""
    
    def test_conversation_mode_prefers_mem0(self):
        provider, options = RouteDecision.select_route(
            mode="conversation",
            available_providers=["mem0", "supabase"],
            feature_flags={},
            provider_status={
                "mem0": ProviderStatus.AVAILABLE,
                "supabase": ProviderStatus.AVAILABLE,
            }
        )
        assert provider == "mem0"
        assert options["skip_external_rerank"] is True
    
    def test_conversation_mode_fallback_to_supabase(self):
        provider, options = RouteDecision.select_route(
            mode="conversation",
            available_providers=["supabase"],
            feature_flags={},
            provider_status={
                "mem0": ProviderStatus.UNAVAILABLE,
                "supabase": ProviderStatus.AVAILABLE,
            }
        )
        assert provider == "supabase"
        assert options["skip_external_rerank"] is False
    
    def test_fast_mode_selects_first_available(self):
        provider, options = RouteDecision.select_route(
            mode="fast",
            available_providers=["supabase", "mem0"],
            feature_flags={},
            provider_status={
                "mem0": ProviderStatus.AVAILABLE,
                "supabase": ProviderStatus.AVAILABLE,
            }
        )
        assert provider == "mem0"
        assert options["skip_external_rerank"] is True
    
    def test_accurate_mode_with_multiple_providers(self):
        provider, options = RouteDecision.select_route(
            mode="accurate",
            available_providers=["mem0", "supabase", "graphiti"],
            feature_flags={"graphiti_enabled": True},
            provider_status={
                "mem0": ProviderStatus.AVAILABLE,
                "supabase": ProviderStatus.AVAILABLE,
                "graphiti": ProviderStatus.AVAILABLE,
            }
        )
        # Should select first available
        assert provider in ["mem0", "supabase", "graphiti"]
    
    def test_no_available_providers(self):
        provider, options = RouteDecision.select_route(
            mode="conversation",
            available_providers=[],
            feature_flags={},
            provider_status={}
        )
        assert provider == "none"
        assert options["skip_external_rerank"] is False
    
    def test_all_unavailable(self):
        provider, options = RouteDecision.select_route(
            mode="conversation",
            available_providers=["mem0"],
            feature_flags={},
            provider_status={
                "mem0": ProviderStatus.UNAVAILABLE,
            }
        )
        assert provider == "none"
    
    def test_degraded_provider_fallback(self):
        provider, options = RouteDecision.select_route(
            mode="fast",
            available_providers=["supabase"],
            feature_flags={},
            provider_status={
                "supabase": ProviderStatus.DEGRADED,
            }
        )
        assert provider == "supabase"
        assert options["skip_external_rerank"] is False


class TestRouteDecisionCheckFeatureFlags:
    """Test RouteDecision.check_feature_flags method."""
    
    def test_default_flags(self):
        enabled = RouteDecision.check_feature_flags({})
        assert "mem0" in enabled
        assert "supabase" in enabled
        assert "graphiti" not in enabled
    
    def test_graphiti_enabled(self):
        enabled = RouteDecision.check_feature_flags(
            {"graphiti_enabled": True}
        )
        assert "graphiti" in enabled
        assert "mem0" in enabled
        assert "supabase" in enabled
    
    def test_mem0_disabled(self):
        enabled = RouteDecision.check_feature_flags(
            {"mem0_enabled": False}
        )
        assert "mem0" not in enabled
        assert "supabase" in enabled
    
    def test_supabase_disabled(self):
        enabled = RouteDecision.check_feature_flags(
            {"supabase_enabled": False}
        )
        assert "supabase" not in enabled
        assert "mem0" in enabled
    
    def test_all_disabled(self):
        enabled = RouteDecision.check_feature_flags(
            {
                "mem0_enabled": False,
                "supabase_enabled": False,
                "graphiti_enabled": False,
            }
        )
        assert enabled == []


class TestRouteRetrieval:
    """Test route_retrieval function."""
    
    def test_basic_routing(self):
        request = RetrievalRequest(
            query="test query",
            mode="conversation",
        )
        provider, options = route_retrieval(request)
        assert provider in ["mem0", "supabase", "none"]
    
    def test_provider_override(self):
        request = RetrievalRequest(
            query="test query",
            mode="conversation",
            provider_override="supabase",
        )
        provider, options = route_retrieval(
            request,
            feature_flags={"mem0_enabled": True, "supabase_enabled": True}
        )
        assert provider == "supabase"
        assert options["skip_external_rerank"] is False
    
    def test_override_unavailable(self):
        request = RetrievalRequest(
            query="test query",
            mode="conversation",
            provider_override="graphiti",
        )
        provider, options = route_retrieval(
            request,
            feature_flags={"graphiti_enabled": False}
        )
        # Falls back to normal selection
        assert provider != "graphiti"
    
    def test_custom_threshold(self):
        request = RetrievalRequest(
            query="test query",
            mode="fast",
            threshold=0.8,
            top_k=3,
        )
        provider, options = route_retrieval(request)
        assert request.threshold == 0.8
        assert request.top_k == 3


class TestMem0DuplicateRerankPrevention:
    """Regression test for Mem0 duplicate-rerank policy."""
    
    def test_mem0_path_skips_external_rerank(self):
        """Mem0 provider MUST set skip_external_rerank=True."""
        provider, options = RouteDecision.select_route(
            mode="conversation",
            available_providers=["mem0"],
            feature_flags={},
            provider_status={"mem0": ProviderStatus.AVAILABLE}
        )
        assert provider == "mem0"
        assert options["skip_external_rerank"] is True
    
    def test_supabase_path_allows_external_rerank(self):
        """Supabase provider uses external rerank per config."""
        provider, options = RouteDecision.select_route(
            mode="conversation",
            available_providers=["supabase"],
            feature_flags={},
            provider_status={"supabase": ProviderStatus.AVAILABLE}
        )
        assert provider == "supabase"
        assert options["skip_external_rerank"] is False
    
    def test_mem0_policy_is_deterministic(self):
        """Same inputs MUST produce same Mem0 policy."""
        results = []
        for _ in range(5):
            provider, options = RouteDecision.select_route(
                mode="conversation",
                available_providers=["mem0", "supabase"],
                feature_flags={},
                provider_status={
                    "mem0": ProviderStatus.AVAILABLE,
                    "supabase": ProviderStatus.AVAILABLE,
                }
            )
            results.append((provider, options["skip_external_rerank"]))
        
        # All results must be identical
        assert all(r == results[0] for r in results)
        assert results[0][0] == "mem0"
        assert results[0][1] is True


class TestDeterministicRouting:
    """Test routing determinism."""
    
    def test_same_inputs_same_output(self):
        """Identical inputs MUST produce identical routing."""
        test_cases = [
            ("conversation", ["mem0", "supabase"]),
            ("fast", ["supabase"]),
            ("accurate", ["mem0", "supabase", "graphiti"]),
        ]
        
        for mode, providers in test_cases:
            results = []
            for _ in range(3):
                provider, options = RouteDecision.select_route(
                    mode=mode,
                    available_providers=providers,
                    feature_flags={"graphiti_enabled": True},
                    provider_status={p: ProviderStatus.AVAILABLE for p in providers}
                )
                results.append((provider, options["skip_external_rerank"]))
            
            # All runs must match
            assert all(r == results[0] for r in results)
