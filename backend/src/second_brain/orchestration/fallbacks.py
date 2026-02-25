from second_brain.contracts.context_packet import (
    ContextPacket,
    ContextCandidate,
    ConfidenceSummary,
    NextAction,
)


class BranchCodes:
    """Stable branch code constants."""
    EMPTY_SET = "EMPTY_SET"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    RERANK_BYPASSED = "RERANK_BYPASSED"
    SUCCESS = "SUCCESS"


class FallbackEmitter:
    """Deterministic branch emitters."""
    
    @staticmethod
    def emit_empty_set(provider: str = "unknown") -> tuple[ContextPacket, NextAction]:
        """Emit EMPTY_SET branch for no candidates."""
        packet = ContextPacket(
            candidates=[],
            summary=ConfidenceSummary(
                top_confidence=0.0,
                candidate_count=0,
                threshold_met=False,
                branch=BranchCodes.EMPTY_SET,
            ),
            provider=provider,
            rerank_applied=False,
        )
        
        next_action = NextAction(
            action="fallback",
            reason="No context candidates retrieved from any provider",
            branch_code=BranchCodes.EMPTY_SET,
            suggestion="Ask user to rephrase query or provide more context",
        )
        
        return packet, next_action
    
    @staticmethod
    def emit_low_confidence(
        candidates: list[ContextCandidate],
        top_confidence: float,
        threshold: float,
        provider: str = "unknown"
    ) -> tuple[ContextPacket, NextAction]:
        """Emit LOW_CONFIDENCE branch for below-threshold results."""
        packet = ContextPacket(
            candidates=candidates,
            summary=ConfidenceSummary(
                top_confidence=top_confidence,
                candidate_count=len(candidates),
                threshold_met=False,
                branch=BranchCodes.LOW_CONFIDENCE,
            ),
            provider=provider,
            rerank_applied=False,
        )
        
        next_action = NextAction(
            action="clarify",
            reason=f"Top confidence {top_confidence:.2f} below threshold {threshold:.2f}",
            branch_code=BranchCodes.LOW_CONFIDENCE,
            suggestion="Request clarification on query intent or narrow scope",
        )
        
        return packet, next_action
    
    @staticmethod
    def emit_channel_mismatch(
        candidates: list[ContextCandidate],
        expected_channel: str,
        provider: str = "unknown"
    ) -> tuple[ContextPacket, NextAction]:
        """Emit CHANNEL_MISMATCH branch for intent mismatch."""
        packet = ContextPacket(
            candidates=candidates,
            summary=ConfidenceSummary(
                top_confidence=candidates[0].confidence if candidates else 0.0,
                candidate_count=len(candidates),
                threshold_met=False,
                branch=BranchCodes.CHANNEL_MISMATCH,
            ),
            provider=provider,
            rerank_applied=False,
        )
        
        next_action = NextAction(
            action="escalate",
            reason=f"Retrieved context doesn't match expected channel: {expected_channel}",
            branch_code=BranchCodes.CHANNEL_MISMATCH,
            suggestion="Escalate to human or trigger intent reclassification",
        )
        
        return packet, next_action
    
    @staticmethod
    def emit_rerank_bypassed(
        candidates: list[ContextCandidate],
        provider: str = "mem0"
    ) -> tuple[ContextPacket, NextAction]:
        """Emit RERANK_BYPASSED branch when external rerank skipped."""
        top_confidence = candidates[0].confidence if candidates else 0.0
        
        packet = ContextPacket(
            candidates=candidates,
            summary=ConfidenceSummary(
                top_confidence=top_confidence,
                candidate_count=len(candidates),
                threshold_met=top_confidence >= 0.6,
                branch=BranchCodes.RERANK_BYPASSED,
            ),
            provider=provider,
            rerank_applied=True,  # Provider-native applied
        )
        
        next_action = NextAction(
            action="proceed",
            reason="Provider-native rerank applied, external rerank bypassed per policy",
            branch_code=BranchCodes.RERANK_BYPASSED,
            suggestion=None,
        )
        
        return packet, next_action
    
    @staticmethod
    def emit_success(
        candidates: list[ContextCandidate],
        provider: str = "unknown",
        rerank_applied: bool = False
    ) -> tuple[ContextPacket, NextAction]:
        """Emit SUCCESS branch for high-confidence results."""
        top_confidence = candidates[0].confidence if candidates else 0.0
        
        packet = ContextPacket(
            candidates=candidates,
            summary=ConfidenceSummary(
                top_confidence=top_confidence,
                candidate_count=len(candidates),
                threshold_met=True,
                branch=BranchCodes.SUCCESS,
            ),
            provider=provider,
            rerank_applied=rerank_applied,
        )
        
        next_action = NextAction(
            action="proceed",
            reason=f"Retrieved {len(candidates)} high-confidence candidates",
            branch_code=BranchCodes.SUCCESS,
            suggestion=None,
        )
        
        return packet, next_action


def determine_branch(
    candidates: list[ContextCandidate],
    threshold: float = 0.6,
    rerank_bypassed: bool = False,
    provider: str = "unknown"
) -> tuple[ContextPacket, NextAction]:
    """
    Determine appropriate branch and emit corresponding output.
    
    Args:
        candidates: Retrieved context candidates
        threshold: Confidence threshold
        rerank_bypassed: Whether external rerank was skipped
        provider: Provider that served request
    
    Returns:
        Tuple of (ContextPacket, NextAction) for determined branch
    """
    # EMPTY_SET: No candidates
    if not candidates:
        return FallbackEmitter.emit_empty_set(provider)
    
    top_confidence = candidates[0].confidence
    
    # LOW_CONFIDENCE: Below threshold (check before rerank bypass)
    if top_confidence < threshold:
        return FallbackEmitter.emit_low_confidence(
            candidates, top_confidence, threshold, provider
        )
    
    # RERANK_BYPASSED: Mem0 path with native rerank (only if confidence is good)
    if rerank_bypassed and provider == "mem0":
        return FallbackEmitter.emit_rerank_bypassed(candidates, provider)
    
    # SUCCESS: High confidence
    return FallbackEmitter.emit_success(
        candidates, provider, rerank_applied=rerank_bypassed
    )
