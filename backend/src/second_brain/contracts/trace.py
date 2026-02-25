"""Structured trace records for retrieval pipeline observability."""

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class RetrievalTrace(BaseModel):
    """Structured trace record for a single retrieval pipeline call."""

    # Identity
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Timing
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = Field(default=0.0, ge=0.0)

    # Request snapshot
    query: str
    mode: str
    top_k: int
    threshold: float
    provider_override: str | None = None

    # Routing decision
    selected_provider: str
    feature_flags_snapshot: dict[str, bool] = Field(default_factory=dict)
    provider_status_snapshot: dict[str, str] = Field(default_factory=dict)

    # Retrieval statistics
    raw_candidate_count: int = Field(default=0, ge=0)
    final_candidate_count: int = Field(default=0, ge=0)
    top_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Rerank
    rerank_type: str = "none"
    rerank_bypass_reason: str | None = None
    skip_external_rerank: bool = False

    # Branch outcome
    branch_code: str
    action: str
    reason: str

    # Validation mode
    validation_mode: bool = False
    forced_branch: str | None = None

    # Error tracking
    status: Literal["ok", "error"] = "ok"
    error_type: str | None = None
    error_message: str | None = None
