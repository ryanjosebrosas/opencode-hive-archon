"""Test context packet contract validation."""
import pytest

from second_brain.contracts.context_packet import (
    ContextCandidate,
    ConfidenceSummary,
    ContextPacket,
    NextAction,
)
from second_brain.orchestration.fallbacks import (
    FallbackEmitter,
    BranchCodes,
    determine_branch,
)


class TestContextCandidate:
    """Test ContextCandidate model."""
    
    def test_valid_candidate(self):
        candidate = ContextCandidate(
            id="test-1",
            content="Test content",
            source="mem0",
            confidence=0.85,
        )
        assert candidate.id == "test-1"
        assert candidate.confidence == 0.85
        assert candidate.metadata == {}
    
    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            ContextCandidate(
                id="test-2",
                content="Test",
                source="mem0",
                confidence=1.5,  # Out of bounds
            )
    
    def test_with_metadata(self):
        candidate = ContextCandidate(
            id="test-3",
            content="Test",
            source="supabase",
            confidence=0.75,
            metadata={"key": "value"},
        )
        assert candidate.metadata["key"] == "value"


class TestConfidenceSummary:
    """Test ConfidenceSummary model."""
    
    def test_valid_summary(self):
        summary = ConfidenceSummary(
            top_confidence=0.85,
            candidate_count=5,
            threshold_met=True,
            branch=BranchCodes.SUCCESS,
        )
        assert summary.top_confidence == 0.85
        assert summary.candidate_count == 5
        assert summary.threshold_met is True
    
    def test_empty_set_summary(self):
        summary = ConfidenceSummary(
            top_confidence=0.0,
            candidate_count=0,
            threshold_met=False,
            branch=BranchCodes.EMPTY_SET,
        )
        assert summary.top_confidence == 0.0
        assert summary.candidate_count == 0


class TestContextPacket:
    """Test ContextPacket model."""
    
    def test_valid_packet(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="Content 1",
                source="mem0",
                confidence=0.9,
            )
        ]
        packet = ContextPacket(
            candidates=candidates,
            summary=ConfidenceSummary(
                top_confidence=0.9,
                candidate_count=1,
                threshold_met=True,
                branch=BranchCodes.SUCCESS,
            ),
            provider="mem0",
            rerank_applied=True,
        )
        assert len(packet.candidates) == 1
        assert packet.provider == "mem0"
        assert packet.rerank_applied is True
        assert isinstance(packet.timestamp, str)
    
    def test_empty_packet(self):
        packet = ContextPacket(
            candidates=[],
            summary=ConfidenceSummary(
                top_confidence=0.0,
                candidate_count=0,
                threshold_met=False,
                branch=BranchCodes.EMPTY_SET,
            ),
            provider="unknown",
            rerank_applied=False,
        )
        assert len(packet.candidates) == 0
        assert packet.summary.branch == BranchCodes.EMPTY_SET


class TestNextAction:
    """Test NextAction model."""
    
    def test_proceed_action(self):
        action = NextAction(
            action="proceed",
            reason="High confidence results",
            branch_code=BranchCodes.SUCCESS,
        )
        assert action.action == "proceed"
        assert action.suggestion is None
    
    def test_clarify_action(self):
        action = NextAction(
            action="clarify",
            reason="Low confidence",
            branch_code=BranchCodes.LOW_CONFIDENCE,
            suggestion="Ask for more details",
        )
        assert action.action == "clarify"
        assert action.suggestion == "Ask for more details"
    
    def test_fallback_action(self):
        action = NextAction(
            action="fallback",
            reason="No results",
            branch_code=BranchCodes.EMPTY_SET,
            suggestion="Rephrase query",
        )
        assert action.action == "fallback"
    
    def test_escalate_action(self):
        action = NextAction(
            action="escalate",
            reason="Channel mismatch",
            branch_code=BranchCodes.CHANNEL_MISMATCH,
        )
        assert action.action == "escalate"


class TestFallbackEmitter:
    """Test FallbackEmitter branch emitters."""
    
    def test_emit_empty_set(self):
        packet, action = FallbackEmitter.emit_empty_set("mem0")
        
        assert packet.summary.branch == BranchCodes.EMPTY_SET
        assert packet.candidates == []
        assert packet.summary.top_confidence == 0.0
        assert action.action == "fallback"
        assert action.branch_code == BranchCodes.EMPTY_SET
    
    def test_emit_low_confidence(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="Low confidence",
                source="mem0",
                confidence=0.4,
            )
        ]
        packet, action = FallbackEmitter.emit_low_confidence(
            candidates, 0.4, 0.6, "mem0"
        )
        
        assert packet.summary.branch == BranchCodes.LOW_CONFIDENCE
        assert packet.summary.top_confidence == 0.4
        assert packet.summary.threshold_met is False
        assert action.action == "clarify"
        assert action.branch_code == BranchCodes.LOW_CONFIDENCE
    
    def test_emit_success(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="High confidence",
                source="mem0",
                confidence=0.9,
            )
        ]
        packet, action = FallbackEmitter.emit_success(candidates, "mem0", True)
        
        assert packet.summary.branch == BranchCodes.SUCCESS
        assert packet.summary.threshold_met is True
        assert packet.rerank_applied is True
        assert action.action == "proceed"
    
    def test_emit_rerank_bypassed(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="Mem0 result",
                source="mem0",
                confidence=0.85,
            )
        ]
        packet, action = FallbackEmitter.emit_rerank_bypassed(candidates, "mem0")
        
        assert packet.summary.branch == BranchCodes.RERANK_BYPASSED
        assert packet.rerank_applied is True
        assert packet.provider == "mem0"
        assert action.action == "proceed"


class TestDetermineBranch:
    """Test determine_branch function."""
    
    def test_empty_candidates(self):
        packet, action = determine_branch([], 0.6, False, "unknown")
        assert packet.summary.branch == BranchCodes.EMPTY_SET
        assert action.action == "fallback"
    
    def test_low_confidence(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="Low confidence",
                source="mem0",
                confidence=0.3,
            )
        ]
        packet, action = determine_branch(candidates, 0.6, False, "supabase")
        assert packet.summary.branch == BranchCodes.LOW_CONFIDENCE
        assert action.action == "clarify"
    
    def test_high_confidence(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="High confidence",
                source="mem0",
                confidence=0.85,
            )
        ]
        packet, action = determine_branch(candidates, 0.6, False, "mem0")
        assert packet.summary.branch == BranchCodes.SUCCESS
        assert action.action == "proceed"
    
    def test_mem0_rerank_bypass(self):
        candidates = [
            ContextCandidate(
                id="c1",
                content="Mem0 with native rerank",
                source="mem0",
                confidence=0.85,
            )
        ]
        packet, action = determine_branch(candidates, 0.6, True, "mem0")
        assert packet.summary.branch == BranchCodes.RERANK_BYPASSED
        assert packet.rerank_applied is True


class TestBranchCodes:
    """Test BranchCodes constants."""
    
    def test_branch_codes_are_stable(self):
        assert BranchCodes.EMPTY_SET == "EMPTY_SET"
        assert BranchCodes.LOW_CONFIDENCE == "LOW_CONFIDENCE"
        assert BranchCodes.CHANNEL_MISMATCH == "CHANNEL_MISMATCH"
        assert BranchCodes.RERANK_BYPASSED == "RERANK_BYPASSED"
        assert BranchCodes.SUCCESS == "SUCCESS"
