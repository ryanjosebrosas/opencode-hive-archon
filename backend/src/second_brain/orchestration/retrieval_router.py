from typing import Literal
from second_brain.contracts.context_packet import RetrievalRequest


class ProviderStatus:
    """Provider availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class RouteDecision:
    """Deterministic route selection result."""
    
    @staticmethod
    def select_route(
        mode: Literal["fast", "accurate", "conversation"],
        available_providers: list[str],
        feature_flags: dict[str, bool],
        provider_status: dict[str, str]
    ) -> tuple[str, dict]:
        """
        Select provider and route options deterministically.
        
        Returns:
            Tuple of (provider_name, route_options)
            route_options includes skip_external_rerank flag
        """
        if not available_providers:
            return "none", {"skip_external_rerank": False}
        
        # Mode-based selection
        if mode == "conversation":
            # Prefer Mem0 for conversation mode
            if "mem0" in available_providers and provider_status.get("mem0") == ProviderStatus.AVAILABLE:
                return "mem0", {"skip_external_rerank": True}  # Mem0 policy
            if "supabase" in available_providers and provider_status.get("supabase") == ProviderStatus.AVAILABLE:
                return "supabase", {"skip_external_rerank": False}
        
        elif mode == "fast":
            # Single best available provider
            for provider in ["mem0", "supabase", "graphiti"]:
                if provider in available_providers and provider_status.get(provider) == ProviderStatus.AVAILABLE:
                    skip_rerank = provider == "mem0"
                    return provider, {"skip_external_rerank": skip_rerank}
        
        elif mode == "accurate":
            # Multi-provider merge (simplified: first available)
            for provider in available_providers:
                if provider_status.get(provider) == ProviderStatus.AVAILABLE:
                    skip_rerank = provider == "mem0"
                    return provider, {"skip_external_rerank": skip_rerank}
        
        # Fallback to first available
        for provider in available_providers:
            if provider_status.get(provider) in [ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED]:
                skip_rerank = provider == "mem0"
                return provider, {"skip_external_rerank": skip_rerank}
        
        return "none", {"skip_external_rerank": False}
    
    @staticmethod
    def check_feature_flags(feature_flags: dict[str, bool]) -> list[str]:
        """Get list of providers enabled via feature flags."""
        enabled = []
        
        if feature_flags.get("graphiti_enabled", False):
            enabled.append("graphiti")
        
        if feature_flags.get("mem0_enabled", True):  # Default on
            enabled.append("mem0")
        
        if feature_flags.get("supabase_enabled", True):  # Default on
            enabled.append("supabase")
        
        return enabled


def route_retrieval(
    request: RetrievalRequest,
    provider_status: dict[str, str] | None = None,
    feature_flags: dict[str, bool] | None = None
) -> tuple[str, dict]:
    """
    Route retrieval request to appropriate provider.
    
    Args:
        request: Retrieval request with mode and preferences
        provider_status: Current provider health status
        feature_flags: Feature flag configuration
    
    Returns:
        Tuple of (provider, options) where options includes rerank policy
    """
    if provider_status is None:
        provider_status = {}
    if feature_flags is None:
        feature_flags = {}
    
    # Get enabled providers from feature flags
    enabled_providers = RouteDecision.check_feature_flags(feature_flags)
    
    # Apply provider override if specified and available
    if request.provider_override:
        if request.provider_override in enabled_providers:
            skip_rerank = request.provider_override == "mem0"
            return request.provider_override, {"skip_external_rerank": skip_rerank}
        # Override not available, fall through to normal selection
    
    # Deterministic route selection
    return RouteDecision.select_route(
        mode=request.mode,
        available_providers=enabled_providers,
        feature_flags=feature_flags,
        provider_status=provider_status
    )
