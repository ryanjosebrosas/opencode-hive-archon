"""Dependency injection helpers."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.trace import TraceCollector
from second_brain.services.conversation import ConversationStore

if TYPE_CHECKING:
    from second_brain.orchestration.planner import Planner


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
    embed_model: str | None = None,
    embed_enabled: bool | None = None,
    use_real_rerank: bool | None = None,
) -> VoyageRerankService:
    """Create voyage rerank service instance with env-var defaults."""
    _embed_model = embed_model or os.getenv("VOYAGE_EMBED_MODEL") or "voyage-4-large"
    _embed_enabled = (
        embed_enabled
        if embed_enabled is not None
        else os.getenv("VOYAGE_EMBED_ENABLED", "false").lower() == "true"
    )
    _use_real_rerank = (
        use_real_rerank
        if use_real_rerank is not None
        else os.getenv("VOYAGE_USE_REAL_RERANK", "false").lower() == "true"
    )
    return VoyageRerankService(
        enabled=enabled,
        model=model,
        embed_model=_embed_model,
        embed_enabled=_embed_enabled,
        use_real_rerank=_use_real_rerank,
    )


def create_trace_collector(
    max_traces: int = 1000,
) -> TraceCollector:
    """Create trace collector instance."""
    return TraceCollector(max_traces=max_traces)


def create_conversation_store(
    max_turns: int = 50,
    max_sessions: int = 100,
) -> ConversationStore:
    """Create conversation store instance."""
    return ConversationStore(
        max_turns_per_session=max_turns,
        max_sessions=max_sessions,
    )


def create_llm_service() -> Any:
    """Create LLM service for synthesis. Returns OllamaLLMService instance."""
    from second_brain.services.llm import OllamaLLMService

    return OllamaLLMService()


def create_planner(
    memory_service: MemoryService | None = None,
    rerank_service: VoyageRerankService | None = None,
    conversation_store: ConversationStore | None = None,
    trace_collector: TraceCollector | None = None,
    llm_service: Any | None = None,
) -> Planner:
    """Create planner with default dependencies."""
    from second_brain.orchestration.planner import Planner
    from second_brain.agents.recall import RecallOrchestrator

    _memory = memory_service or create_memory_service()
    _rerank = rerank_service or create_voyage_rerank_service()
    _conversations = conversation_store or create_conversation_store()

    orchestrator = RecallOrchestrator(
        memory_service=_memory,
        rerank_service=_rerank,
        feature_flags=get_feature_flags(),
        provider_status=get_provider_status(),
        trace_collector=trace_collector,
    )

    return Planner(
        recall_orchestrator=orchestrator,
        conversation_store=_conversations,
        trace_collector=trace_collector,
        llm_service=llm_service,
    )


def get_default_config() -> dict[str, Any]:
    """Get configuration from environment variables with safe defaults."""
    return {
        "default_mode": "conversation",
        "default_top_k": 5,
        "default_threshold": 0.6,
        "mem0_rerank_native": True,
        "mem0_skip_external_rerank": True,
        "mem0_use_real_provider": os.getenv("MEM0_USE_REAL_PROVIDER", "false").lower() == "true",
        "mem0_user_id": os.getenv("MEM0_USER_ID"),
        "mem0_api_key": os.getenv("MEM0_API_KEY"),
        "supabase_use_real_provider": os.getenv("SUPABASE_USE_REAL_PROVIDER", "false").lower()
        == "true",
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key": os.getenv("SUPABASE_KEY"),
        "voyage_embed_model": os.getenv("VOYAGE_EMBED_MODEL", "voyage-4-large"),
    }
