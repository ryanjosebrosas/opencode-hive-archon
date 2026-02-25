from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime, timezone


class ContextCandidate(BaseModel):
    """Represents a single retrieval candidate."""

    id: str
    content: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfidenceSummary(BaseModel):
    """Aggregated confidence assessment."""

    top_confidence: float = Field(ge=0.0, le=1.0)
    candidate_count: int = Field(ge=0)
    threshold_met: bool
    branch: str


class ContextPacket(BaseModel):
    """Complete retrieval result envelope."""

    candidates: list[ContextCandidate]
    summary: ConfidenceSummary
    provider: str
    rerank_applied: bool
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NextAction(BaseModel):
    """Explicit actionability indicator."""

    action: Literal["proceed", "clarify", "fallback", "escalate"]
    reason: str
    branch_code: str
    suggestion: str | None = None


class RetrievalRequest(BaseModel):
    """Request to retrieval module."""

    query: str
    mode: Literal["fast", "accurate", "conversation"] = "conversation"
    top_k: int = Field(default=5, ge=1)
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    provider_override: str | None = None


class RetrievalResponse(BaseModel):
    """Response from retrieval module."""

    context_packet: ContextPacket
    next_action: NextAction
    routing_metadata: dict[str, Any] = Field(default_factory=dict)
