"""Conversation contracts for multi-turn dialogue management."""

import uuid
from datetime import datetime, timezone
from typing import Literal, Any

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """Single turn in a conversation."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    branch_code: str | None = None
    action_taken: str | None = None


class ConversationState(BaseModel):
    """Multi-turn conversation session."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    turns: list[ConversationTurn] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlannerResponse(BaseModel):
    """Structured response from the planning module."""

    response_text: str
    action_taken: Literal["proceed", "clarify", "fallback", "escalate"]
    branch_code: str
    session_id: str
    suggestions: list[str] = Field(default_factory=list)
    candidates_used: int = 0
    confidence: float = 0.0
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)
