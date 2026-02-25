"""Dependency injection helpers."""
from typing import Any
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService


def get_feature_flags() -> dict[str, bool]:
    """Get default feature flags for provider gating."""
    return {
        "mem0_enabled": True,
        "supabase_enabled": True,
        "graphiti_enabled": False,
        "external_rerank_enabled": True,
    }


def get_provider_status() -> dict[str, str]:
    """Get provider health status snapshot."""
    # In production, this would check actual provider health
    # For testing, return deterministic defaults
    return {
        "mem0": "available",
        "supabase": "available",
        "graphiti": "unavailable",
    }


def create_memory_service(
    provider: str = "mem0",
    config: dict[str, Any] | None = None,
) -> MemoryService:
    """Create memory service instance."""
    return MemoryService(provider=provider, config=config)


def create_voyage_rerank_service(
    enabled: bool = True,
    model: str = "rerank-2",
) -> VoyageRerankService:
    """Create voyage rerank service instance."""
    return VoyageRerankService(enabled=enabled, model=model)


def get_default_config() -> dict[str, Any]:
    """Get default configuration for recall flow."""
    return {
        "default_mode": "conversation",
        "default_top_k": 5,
        "default_threshold": 0.6,
        "mem0_rerank_native": True,
        "mem0_skip_external_rerank": True,
    }
