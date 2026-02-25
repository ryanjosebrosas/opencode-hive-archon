from typing import Literal
from second_brain.contracts.context_packet import RetrievalRequest


def _normalized_provider_status(
    enabled_providers: list[str],
    provider_status: dict[str, str],
) -> dict[str, str]:
    """
    Normalize provider status by filling missing statuses as 'available'.
    
    Missing status keys default to available for enabled providers,
    because partial snapshots should fail open for deterministic continuity.
    Explicitly set statuses (unavailable/degraded) are preserved.
    
    Args:
        enabled_providers: List of enabled provider names
        provider_status: Current provider status snapshot (may be partial)
    
    Returns:
        Normalized status dict with all enabled providers having a status
    """
    normalized = dict(provider_status)
    
    for provider in enabled_providers:
        if provider not in normalized:
            normalized[provider] = ProviderStatus.AVAILABLE
    
    return normalized


def _is_provider_eligible(
    provider: str,
    enabled_providers: list[str],
    provider_status: dict[str, str],
) -> bool:
    """
    Check if provider is eligible for selection.
    
    Provider is eligible when:
    1. Provider is in enabled_providers list
    2. Provider status is available or degraded (not unavailable)
    
    Args:
        provider: Provider name to check
        enabled_providers: List of enabled provider names
        provider_status: Normalized provider status snapshot
    
    Returns:
        True if provider is eligible, False otherwise
    """
    if provider not in enabled_providers:
        return False
    
    status = provider_status.get(provider, ProviderStatus.UNAVAILABLE)
    return status in [ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED]


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
            if "mem0" in available_providers and _is_provider_eligible("mem0", available_providers, provider_status):
                status = provider_status.get("mem0", ProviderStatus.AVAILABLE)
                if status == ProviderStatus.AVAILABLE:
                    return "mem0", {"skip_external_rerank": True}  # Mem0 policy
            if "supabase" in available_providers and _is_provider_eligible("supabase", available_providers, provider_status):
                status = provider_status.get("supabase", ProviderStatus.AVAILABLE)
                if status == ProviderStatus.AVAILABLE:
                    return "supabase", {"skip_external_rerank": False}
        
        elif mode == "fast":
            # Single best available provider
            for provider in ["mem0", "supabase", "graphiti"]:
                if provider in available_providers and _is_provider_eligible(provider, available_providers, provider_status):
                    status = provider_status.get(provider, ProviderStatus.AVAILABLE)
                    if status == ProviderStatus.AVAILABLE:
                        skip_rerank = provider == "mem0"
                        return provider, {"skip_external_rerank": skip_rerank}
        
        elif mode == "accurate":
            # Multi-provider merge (simplified: first available)
            for provider in available_providers:
                if _is_provider_eligible(provider, available_providers, provider_status):
                    status = provider_status.get(provider, ProviderStatus.AVAILABLE)
                    if status == ProviderStatus.AVAILABLE:
                        skip_rerank = provider == "mem0"
                        return provider, {"skip_external_rerank": skip_rerank}
        
        # Fallback to first available (includes degraded)
        for provider in available_providers:
            if _is_provider_eligible(provider, available_providers, provider_status):
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
        provider_status: Current provider health status (partial snapshots ok)
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
    
    # Normalize provider status (missing keys default to available)
    normalized_status = _normalized_provider_status(enabled_providers, provider_status)
    
    # Apply provider override if specified and eligible
    if request.provider_override:
        # Override must pass eligibility check (enabled + not unavailable)
        if _is_provider_eligible(request.provider_override, enabled_providers, normalized_status):
            status = normalized_status.get(request.provider_override, ProviderStatus.AVAILABLE)
            # Override only accepted for available providers (not degraded)
            if status == ProviderStatus.AVAILABLE:
                skip_rerank = request.provider_override == "mem0"
                return request.provider_override, {"skip_external_rerank": skip_rerank}
        # Override not eligible, fall through to normal selection
    
    # Deterministic route selection
    return RouteDecision.select_route(
        mode=request.mode,
        available_providers=enabled_providers,
        provider_status=normalized_status,
    )
