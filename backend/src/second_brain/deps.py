"""Dependency injection helpers."""

from typing import Any
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.trace import TraceCollector


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
    embed_model: str = "voyage-4-large",
    embed_enabled: bool = False,
) -> VoyageRerankService:
    """Create voyage rerank service instance."""
    return VoyageRerankService(
        enabled=enabled,
        model=model,
        embed_model=embed_model,
        embed_enabled=embed_enabled,
    )


def create_trace_collector(
    max_traces: int = 1000,
) -> TraceCollector:
    """Create trace collector instance."""
    return TraceCollector(max_traces=max_traces)


def get_default_config() -> dict[str, Any]:
    """Get default configuration for recall flow."""
    return {
        "default_mode": "conversation",
        "default_top_k": 5,
        "default_threshold": 0.6,
        "mem0_rerank_native": True,
        "mem0_skip_external_rerank": True,
        "mem0_use_real_provider": False,
        "mem0_user_id": None,
        "mem0_api_key": None,
        "supabase_use_real_provider": False,
        "supabase_url": None,
        "supabase_key": None,
        "voyage_embed_model": "voyage-4-large",
    }
