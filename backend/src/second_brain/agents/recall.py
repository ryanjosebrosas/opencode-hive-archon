"""Recall agent for retrieval orchestration."""
from typing import Any, Optional

from second_brain.contracts.context_packet import (
    RetrievalRequest,
    RetrievalResponse,
    ContextCandidate,
)
from second_brain.orchestration.retrieval_router import route_retrieval
from second_brain.orchestration.fallbacks import determine_branch, BranchCodes
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.deps import (
    get_feature_flags,
    get_provider_status,
    get_default_config,
)


class RecallOrchestrator:
    """Recall flow orchestrator with contract-aligned output."""
    
    def __init__(
        self,
        memory_service: MemoryService,
        rerank_service: VoyageRerankService,
        feature_flags: Optional[dict[str, bool]] = None,
        provider_status: Optional[dict[str, str]] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        self.memory_service = memory_service
        self.rerank_service = rerank_service
        self.feature_flags = feature_flags or get_feature_flags()
        self.provider_status = provider_status or get_provider_status()
        self.config = config or get_default_config()
    
    def run(
        self,
        request: RetrievalRequest,
        validation_mode: bool = False,
        force_branch: Optional[str] = None,
    ) -> RetrievalResponse:
        """
        Execute recall flow and return contract-aligned response.
        
        Args:
            request: Retrieval request with query and parameters
            validation_mode: Enable manual validation hooks (debug only)
            force_branch: Force specific branch for testing (validation mode only)
        
        Returns:
            RetrievalResponse with context_packet, next_action, and routing_metadata
        """
        # Step 1: Route provider selection
        provider, route_options = route_retrieval(
            request=request,
            provider_status=self.provider_status,
            feature_flags=self.feature_flags,
        )
        
        # Handle no provider available
        if provider == "none":
            from second_brain.orchestration.fallbacks import FallbackEmitter
            context_packet, next_action = FallbackEmitter.emit_empty_set("none")
            return RetrievalResponse(
                context_packet=context_packet,
                next_action=next_action,
                routing_metadata={
                    "selected_provider": "none",
                    "mode": request.mode,
                    "skip_external_rerank": False,
                    "rerank_type": "none",
                    "feature_flags_snapshot": dict(self.feature_flags),
                    "provider_status_snapshot": dict(self.provider_status),
                },
            )
        
        # Step 2: Retrieve candidates from memory service
        skip_external_rerank = route_options.get("skip_external_rerank", False)
        candidates, provider_metadata = self.memory_service.search_memories(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            rerank=not skip_external_rerank,
        )
        
        # Step 3: Apply external rerank if needed (non-Mem0 paths)
        external_rerank_enabled = self.feature_flags.get("external_rerank_enabled", True)
        rerank_metadata = {"rerank_type": "none"}  # type: ignore
        if not skip_external_rerank and candidates and external_rerank_enabled:
            reranked, rerank_metadata = self.rerank_service.rerank(  # type: ignore
                query=request.query,
                candidates=candidates,
                top_k=request.top_k,
            )
            candidates = reranked
        elif skip_external_rerank:
            rerank_metadata["rerank_type"] = "provider-native"
            rerank_metadata["rerank_bypass_reason"] = "mem0-default-policy"
        elif not external_rerank_enabled and candidates:
            rerank_metadata["rerank_type"] = "none"
            rerank_metadata["rerank_bypass_reason"] = "external_rerank_disabled"
        
        # Step 4: Determine branch (with optional validation override)
        if validation_mode and force_branch:
            # Validation mode: force specific branch for testing
            routing_metadata = self._build_routing_metadata(
                provider=provider,
                route_options=route_options,
                route_options_skip_rerank=skip_external_rerank,
                rerank_metadata=rerank_metadata,
                mode=request.mode,
            )
            routing_metadata["validation_mode"] = True
            routing_metadata["forced_branch"] = force_branch
            
            # Force branch via override
            context_packet, next_action = self._force_branch_output(
                candidates=candidates,
                force_branch=force_branch,
                provider=provider,
                skip_external_rerank=skip_external_rerank,
                threshold=request.threshold,
            )
        else:
            # Normal mode: deterministic branch from determine_branch
            context_packet, next_action = determine_branch(
                candidates=candidates,
                threshold=request.threshold,
                rerank_bypassed=skip_external_rerank,
                provider=provider,
            )
            
            routing_metadata = self._build_routing_metadata(
                provider=provider,
                route_options=route_options,
                route_options_skip_rerank=skip_external_rerank,
                rerank_metadata=rerank_metadata,
                mode=request.mode,
            )
        
        return RetrievalResponse(
            context_packet=context_packet,
            next_action=next_action,
            routing_metadata=routing_metadata,
        )
    
    def _build_routing_metadata(
        self,
        provider: str,
        route_options: dict,
        route_options_skip_rerank: bool,
        rerank_metadata: dict,
        mode: str = "conversation",
    ) -> dict[str, Any]:
        """Build rich routing metadata for response."""
        return {
            "selected_provider": provider,
            "mode": mode,
            "skip_external_rerank": route_options_skip_rerank,
            "rerank_type": rerank_metadata.get("rerank_type", "none"),
            "rerank_bypass_reason": rerank_metadata.get("rerank_bypass_reason"),
            "feature_flags_snapshot": dict(self.feature_flags),
            "provider_status_snapshot": dict(self.provider_status),
        }
    
    def _force_branch_output(
        self,
        candidates: list[ContextCandidate],
        force_branch: str,
        provider: str,
        skip_external_rerank: bool,
        threshold: float,
    ) -> tuple:
        """Force specific branch output for validation testing."""
        from second_brain.orchestration.fallbacks import FallbackEmitter
        
        if force_branch == BranchCodes.EMPTY_SET:
            return FallbackEmitter.emit_empty_set(provider)
        elif force_branch == BranchCodes.LOW_CONFIDENCE:
            low_conf_candidates = [
                ContextCandidate(
                    id=c.id,
                    content=c.content,
                    source=c.source,
                    confidence=0.4,  # Below threshold
                    metadata=c.metadata,
                )
                for c in candidates
            ] if candidates else []
            return FallbackEmitter.emit_low_confidence(
                low_conf_candidates, 0.4, threshold, provider
            )
        elif force_branch == BranchCodes.CHANNEL_MISMATCH:
            return FallbackEmitter.emit_channel_mismatch(
                candidates or [], "test_channel", provider
            )
        elif force_branch == BranchCodes.RERANK_BYPASSED:
            return FallbackEmitter.emit_rerank_bypassed(
                candidates or [
                    ContextCandidate(
                        id="forced",
                        content="Forced rerank bypass",
                        source=provider,
                        confidence=0.85,
                        metadata={},
                    )
                ],
                provider,
            )
        elif force_branch == BranchCodes.SUCCESS:
            return FallbackEmitter.emit_success(
                candidates or [
                    ContextCandidate(
                        id="forced",
                        content="Forced success",
                        source=provider,
                        confidence=0.9,
                        metadata={},
                    )
                ],
                provider,
                rerank_applied=skip_external_rerank,
            )
        else:
            # Unknown branch, fall through to normal determination
            return determine_branch(
                candidates=candidates,
                threshold=threshold,
                rerank_bypassed=skip_external_rerank,
                provider=provider,
            )


def run_recall(
    query: str,
    mode: str = "conversation",
    top_k: int = 5,
    threshold: float = 0.6,
    provider_override: Optional[str] = None,
    validation_mode: bool = False,
    force_branch: Optional[str] = None,
) -> RetrievalResponse:
    """
    Convenience function for running recall flow.
    
    Args:
        query: Search query
        mode: Retrieval mode (fast, accurate, conversation)
        top_k: Number of results
        threshold: Confidence threshold
        provider_override: Optional provider override
        validation_mode: Enable validation hooks
        force_branch: Force branch for testing
    
    Returns:
        RetrievalResponse with full contract envelope
    """
    request = RetrievalRequest(
        query=query,
        mode=mode,  # type: ignore
        top_k=top_k,
        threshold=threshold,
        provider_override=provider_override,
    )
    
    memory_service = MemoryService(provider="mem0")
    rerank_service = VoyageRerankService(enabled=True)
    
    orchestrator = RecallOrchestrator(
        memory_service=memory_service,
        rerank_service=rerank_service,
    )
    
    return orchestrator.run(
        request=request,
        validation_mode=validation_mode,
        force_branch=force_branch,
    )
