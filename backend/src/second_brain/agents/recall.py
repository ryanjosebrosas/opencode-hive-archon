"""Recall agent for retrieval orchestration."""

import time
from typing import Any, Literal, Optional

from second_brain.contracts.context_packet import (
    RetrievalRequest,
    RetrievalResponse,
    ContextCandidate,
    ContextPacket,
    NextAction,
)
from second_brain.contracts.trace import RetrievalTrace
from second_brain.orchestration.retrieval_router import route_retrieval
from second_brain.orchestration.fallbacks import determine_branch, BranchCodes
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.trace import TraceCollector
from second_brain.deps import (
    get_feature_flags,
    get_provider_status,
    get_default_config,
    create_memory_service,
)
from second_brain.errors import RetrievalError


class RecallOrchestrator:
    """Recall flow orchestrator with contract-aligned output."""

    def __init__(
        self,
        memory_service: MemoryService,
        rerank_service: VoyageRerankService,
        feature_flags: Optional[dict[str, bool]] = None,
        provider_status: Optional[dict[str, str]] = None,
        config: Optional[dict[str, Any]] = None,
        trace_collector: Optional[TraceCollector] = None,
    ):
        self.memory_service = memory_service
        self.rerank_service = rerank_service
        self.feature_flags = feature_flags or get_feature_flags()
        self.provider_status = provider_status or get_provider_status()
        self.config = config or get_default_config()
        self.trace_collector = trace_collector

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
        start_time = time.perf_counter()
        raw_candidate_count = 0

        try:
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

                routing_metadata = {
                    "selected_provider": "none",
                    "mode": request.mode,
                    "skip_external_rerank": False,
                    "rerank_type": "none",
                    "feature_flags_snapshot": dict(self.feature_flags),
                    "provider_status_snapshot": dict(self.provider_status),
                }

                if self.trace_collector is not None:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    trace = self._build_trace(
                        request=request,
                        duration_ms=duration_ms,
                        provider="none",
                        route_options={"skip_external_rerank": False},
                        raw_candidate_count=0,
                        candidates=[],
                        rerank_metadata={"rerank_type": "none"},
                        context_packet=context_packet,
                        next_action=next_action,
                        skip_external_rerank=False,
                        validation_mode=False,
                        forced_branch=None,
                    )
                    self.trace_collector.record(trace)
                    routing_metadata["trace_id"] = trace.trace_id

                return RetrievalResponse(
                    context_packet=context_packet,
                    next_action=next_action,
                    routing_metadata=routing_metadata,
                )

            # Step 2: Retrieve candidates from provider-consistent memory service
            skip_external_rerank = route_options.get("skip_external_rerank", False)
            memory_service = self._resolve_memory_service_for_provider(provider)
            candidates, provider_metadata = memory_service.search_memories(
                query=request.query,
                top_k=request.top_k,
                threshold=request.threshold,
                rerank=not skip_external_rerank,
            )
            raw_candidate_count = len(candidates)

            # Step 3: Apply external rerank if needed (non-Mem0 paths)
            external_rerank_enabled = self.feature_flags.get("external_rerank_enabled", True)
            rerank_metadata: dict[str, Any] = {"rerank_type": "none"}
            if not skip_external_rerank and candidates and external_rerank_enabled:
                reranked, rerank_metadata = self.rerank_service.rerank(
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
                    provider_metadata=provider_metadata,
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
                    provider_metadata=provider_metadata,
                    mode=request.mode,
                )

            # Record trace if collector present
            if self.trace_collector is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                trace = self._build_trace(
                    request=request,
                    duration_ms=duration_ms,
                    provider=provider,
                    route_options=route_options,
                    raw_candidate_count=raw_candidate_count,
                    candidates=candidates,
                    rerank_metadata=rerank_metadata,
                    context_packet=context_packet,
                    next_action=next_action,
                    skip_external_rerank=skip_external_rerank,
                    validation_mode=validation_mode,
                    forced_branch=force_branch if validation_mode else None,
                )
                self.trace_collector.record(trace)
                routing_metadata["trace_id"] = trace.trace_id

            return RetrievalResponse(
                context_packet=context_packet,
                next_action=next_action,
                routing_metadata=routing_metadata,
            )

        except Exception as e:
            # Record error trace
            if self.trace_collector is not None:
                duration_ms = (time.perf_counter() - start_time) * 1000
                trace = RetrievalTrace(
                    query=request.query,
                    mode=request.mode,
                    top_k=request.top_k,
                    threshold=request.threshold,
                    provider_override=request.provider_override,
                    selected_provider="unknown",
                    branch_code="ERROR",
                    action="fallback",
                    reason=type(e).__name__,
                    duration_ms=duration_ms,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],
                )
                self.trace_collector.record(trace)
            raise RetrievalError(
                f"Retrieval failed: {str(e)}",
                code="RETRIEVAL_ERROR",
                context={
                    "original_error_type": type(e).__name__,
                    "provider": getattr(request, 'provider_override', 'unknown'),
                    "query_length": len(str(request.query)),
                },
                retry_hint=True
            ) from e

    def _resolve_memory_service_for_provider(
        self,
        provider: str,
    ) -> MemoryService:
        """
        Resolve provider-consistent memory service for retrieval.

        If injected service already matches selected provider, reuse it.
        Otherwise, create provider-specific service instance.

        Args:
            provider: Selected provider from routing decision

        Returns:
            MemoryService instance aligned with selected provider
        """
        if self.memory_service.provider == provider:
            return self.memory_service
        return create_memory_service(provider=provider, config=self.config)

    def _build_routing_metadata(
        self,
        provider: str,
        route_options: dict[str, Any],
        route_options_skip_rerank: bool,
        rerank_metadata: dict[str, Any],
        provider_metadata: dict[str, Any] | None = None,
        mode: str = "conversation",
    ) -> dict[str, Any]:
        """Build rich routing metadata for response."""
        metadata = {
            "selected_provider": provider,
            "mode": mode,
            "skip_external_rerank": route_options_skip_rerank,
            "rerank_type": rerank_metadata.get("rerank_type", "none"),
            "rerank_bypass_reason": rerank_metadata.get("rerank_bypass_reason"),
            "feature_flags_snapshot": dict(self.feature_flags),
            "provider_status_snapshot": dict(self.provider_status),
        }
        if provider_metadata:
            metadata["provider_metadata"] = provider_metadata
        return metadata

    def _build_trace(
        self,
        request: RetrievalRequest,
        duration_ms: float,
        provider: str,
        route_options: dict[str, Any],
        raw_candidate_count: int,
        candidates: list[ContextCandidate],
        rerank_metadata: dict[str, Any],
        context_packet: ContextPacket,
        next_action: NextAction,
        skip_external_rerank: bool,
        validation_mode: bool,
        forced_branch: str | None,
    ) -> RetrievalTrace:
        """Build RetrievalTrace from request, response, and intermediate values."""
        return RetrievalTrace(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k,
            threshold=request.threshold,
            provider_override=request.provider_override,
            selected_provider=provider,
            feature_flags_snapshot=dict(self.feature_flags),
            provider_status_snapshot=dict(self.provider_status),
            raw_candidate_count=raw_candidate_count,
            final_candidate_count=len(candidates),
            top_confidence=context_packet.summary.top_confidence,
            rerank_type=rerank_metadata.get("rerank_type", "none"),
            rerank_bypass_reason=rerank_metadata.get("rerank_bypass_reason"),
            skip_external_rerank=skip_external_rerank,
            branch_code=context_packet.summary.branch,
            action=next_action.action,
            reason=next_action.reason,
            duration_ms=duration_ms,
            validation_mode=validation_mode,
            forced_branch=forced_branch,
        )

    def _force_branch_output(
        self,
        candidates: list[ContextCandidate],
        force_branch: str,
        provider: str,
        skip_external_rerank: bool,
        threshold: float,
    ) -> tuple[ContextPacket, NextAction]:
        """Force specific branch output for validation testing."""
        from second_brain.orchestration.fallbacks import FallbackEmitter

        if force_branch == BranchCodes.EMPTY_SET:
            return FallbackEmitter.emit_empty_set(provider)
        elif force_branch == BranchCodes.LOW_CONFIDENCE:
            low_conf_candidates = (
                [
                    ContextCandidate(
                        id=c.id,
                        content=c.content,
                        source=c.source,
                        confidence=0.4,  # Below threshold
                        metadata=c.metadata,
                    )
                    for c in candidates
                ]
                if candidates
                else []
            )
            return FallbackEmitter.emit_low_confidence(
                low_conf_candidates, 0.4, threshold, provider
            )
        elif force_branch == BranchCodes.CHANNEL_MISMATCH:
            return FallbackEmitter.emit_channel_mismatch(candidates or [], "test_channel", provider)
        elif force_branch == BranchCodes.RERANK_BYPASSED:
            return FallbackEmitter.emit_rerank_bypassed(
                candidates
                or [
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
                candidates
                or [
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
    mode: Literal["fast", "accurate", "conversation"] = "conversation",
    top_k: int = 5,
    threshold: float = 0.6,
    provider_override: Optional[str] = None,
    validation_mode: bool = False,
    force_branch: Optional[str] = None,
    trace_collector: Optional[TraceCollector] = None,
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
        trace_collector: Optional trace collector for observability

    Returns:
        RetrievalResponse with full contract envelope
    """
    request = RetrievalRequest(
        query=query,
        mode=mode,
        top_k=top_k,
        threshold=threshold,
        provider_override=provider_override,
    )

    memory_service = MemoryService(provider="mem0")
    rerank_service = VoyageRerankService(enabled=True)

    orchestrator = RecallOrchestrator(
        memory_service=memory_service,
        rerank_service=rerank_service,
        trace_collector=trace_collector,
    )

    return orchestrator.run(
        request=request,
        validation_mode=validation_mode,
        force_branch=force_branch,
    )
