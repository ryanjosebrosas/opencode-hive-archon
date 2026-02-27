"""Planning module - interprets retrieval results and manages conversation flow."""

import time
import uuid
from typing import Any, Literal

from pydantic import ValidationError

from second_brain.logging_config import get_correlation_id, get_logger, set_correlation_id
from second_brain.contracts.context_packet import (
    RetrievalRequest,
    RetrievalResponse,
    ContextPacket,
)
from second_brain.contracts.conversation import (
    ConversationTurn,
    PlannerResponse,
)
from second_brain.contracts.trace import RetrievalTrace
from second_brain.agents.recall import RecallOrchestrator
from second_brain.services.conversation import ConversationStore
from second_brain.services.trace import TraceCollector
from second_brain.errors import SecondBrainError

logger = get_logger(__name__)

MAX_CANDIDATE_CHARS = 300


class Planner:
    """Planning module - interprets retrieval results and manages conversation flow."""

    def __init__(
        self,
        recall_orchestrator: RecallOrchestrator,
        conversation_store: ConversationStore,
        trace_collector: TraceCollector | None = None,
        llm_service: Any | None = None,
    ):
        self.recall = recall_orchestrator
        self.conversations = conversation_store
        self.trace_collector = trace_collector
        self.llm_service = llm_service

    def chat(
        self,
        query: str,
        session_id: str | None = None,
        mode: Literal["fast", "accurate", "conversation"] = "conversation",
        top_k: int = 5,
        threshold: float = 0.6,
    ) -> PlannerResponse:
        """
        Full chat loop: query → retrieval → interpret → respond.

        1. Get or create conversation session
        2. Record user turn
        3. Build RetrievalRequest
        4. Run recall orchestrator
        5. Interpret NextAction
        6. Record assistant turn
        7. Return PlannerResponse
        """
        correlation_id = f"planner-{uuid.uuid4().hex[:8]}"
        if not get_correlation_id():
            set_correlation_id(correlation_id)
        
        logger.info("planner_chat_start", query=query[:100], session_id=session_id, mode=mode)
        
        state = self.conversations.get_or_create(session_id)

        # 2. Record user turn
        user_turn = ConversationTurn(role="user", content=query)
        self.conversations.add_turn(state.session_id, user_turn)

        # 3-5. Build request, run retrieval, interpret NextAction
        started_at = time.time()
        try:
            request = RetrievalRequest(
                query=query,
                mode=mode,
                top_k=top_k,
                threshold=threshold,
            )
            retrieval_response = self.recall.run(request)
            response = self._interpret_action(
                retrieval_response=retrieval_response,
                session_id=state.session_id,
            )
        except (SecondBrainError, ValidationError) as exc:
            self._record_retrieval_error_trace(
                query=query,
                mode=mode,
                top_k=top_k,
                threshold=threshold,
                started_at=started_at,
                error=exc,
            )
            response = self._format_retrieval_error(
                session_id=state.session_id,
                error=exc,
            )

        # 6. Record assistant turn
        assistant_turn = ConversationTurn(
            role="assistant",
            content=response.response_text,
            branch_code=response.branch_code,
            action_taken=response.action_taken,
        )
        self.conversations.add_turn(state.session_id, assistant_turn)

        return response

    def _interpret_action(
        self,
        retrieval_response: RetrievalResponse,
        session_id: str,
    ) -> PlannerResponse:
        """Interpret NextAction and generate structured response."""
        action = retrieval_response.next_action.action
        branch = retrieval_response.next_action.branch_code
        packet = retrieval_response.context_packet

        base_metadata = {
            "provider": packet.provider,
            "rerank_applied": packet.rerank_applied,
            "routing": retrieval_response.routing_metadata,
        }

        if action == "proceed":
            return self._format_proceed(packet, branch, session_id, base_metadata)
        elif action == "clarify":
            return self._format_clarify(packet, branch, session_id, base_metadata)
        elif action == "fallback":
            return self._format_fallback(packet, branch, session_id, base_metadata)
        elif action == "escalate":
            return self._format_escalate(packet, branch, session_id, base_metadata)
        else:
            # Defensive: unknown action treated as fallback
            return self._format_fallback(packet, branch, session_id, base_metadata)

    def _format_retrieval_error(self, session_id: str, error: Exception) -> PlannerResponse:
        """Return safe fallback response when retrieval execution fails."""
        return PlannerResponse(
            response_text=(
                "I hit a retrieval issue while processing your request. "
                "Please try again or rephrase your query."
            ),
            action_taken="fallback",
            branch_code="RETRIEVAL_ERROR",
            session_id=session_id,
            suggestions=[
                "Retry the same query in a moment",
                "Rephrase with simpler or more specific terms",
                "Try a broader search term",
            ],
            candidates_used=0,
            confidence=0.0,
            retrieval_metadata={
                "provider": "unknown",
                "rerank_applied": False,
                "routing": {},
                "error_type": error.__class__.__name__,
                "error_message": "retrieval_failed",
            },
        )

    def _record_retrieval_error_trace(
        self,
        query: str,
        mode: str,
        top_k: int,
        threshold: float,
        started_at: float,
        error: Exception,
    ) -> None:
        """Record planner-level retrieval error trace when a collector is available."""
        if self.trace_collector is None:
            return

        duration_ms = max(0.0, (time.time() - started_at) * 1000.0)
        trace = RetrievalTrace(
            query=query,
            mode=mode,
            top_k=top_k,
            threshold=threshold,
            selected_provider="unknown",
            branch_code="RETRIEVAL_ERROR",
            action="fallback",
            reason="planner_retrieval_exception",
            status="error",
            error_type=error.__class__.__name__,
            error_message="retrieval_failed",
            duration_ms=duration_ms,
        )
        self.trace_collector.record(trace)

    def _get_last_user_query(self, session_id: str) -> str:
        """Get the last user message from the conversation."""
        state = self.conversations.get_or_create(session_id)
        for turn in reversed(state.turns):
            if turn.role == "user":
                return turn.content
        return ""

    def _format_proceed(
        self,
        packet: ContextPacket,
        branch: str,
        session_id: str,
        metadata: dict[str, Any],
    ) -> PlannerResponse:
        """Format response for proceed action (SUCCESS / RERANK_BYPASSED)."""
        candidates = packet.candidates
        if not candidates:
            return self._format_fallback(packet, branch, session_id, metadata)

        # Try LLM synthesis if service available
        if self.llm_service is not None:
            candidate_dicts = [
                {
                    "content": c.content,
                    "source": c.source,
                    "confidence": c.confidence,
                    "metadata": c.metadata,
                }
                for c in candidates
            ]
            query = self._get_last_user_query(session_id)
            response_text, llm_metadata = self.llm_service.synthesize(
                query=query,
                context_candidates=candidate_dicts,
            )
            metadata["llm"] = llm_metadata
            return PlannerResponse(
                response_text=response_text,
                action_taken="proceed",
                branch_code=branch,
                session_id=session_id,
                candidates_used=len(candidates),
                confidence=packet.summary.top_confidence,
                retrieval_metadata=metadata,
            )

        # Fallback: f-string formatting (no LLM)
        context_parts = []
        for i, c in enumerate(candidates[:3], 1):
            content = c.content
            if len(content) > MAX_CANDIDATE_CHARS:
                content = f"{content[:MAX_CANDIDATE_CHARS]}..."
            context_parts.append(f"[{i}] {content}")

        response_text = (
            f"Based on {len(candidates)} retrieved context(s) "
            f"(top confidence: {packet.summary.top_confidence:.2f}):\n\n"
            + "\n\n".join(context_parts)
        )

        return PlannerResponse(
            response_text=response_text,
            action_taken="proceed",
            branch_code=branch,
            session_id=session_id,
            candidates_used=len(candidates),
            confidence=packet.summary.top_confidence,
            retrieval_metadata=metadata,
        )

    def _format_clarify(
        self,
        packet: ContextPacket,
        branch: str,
        session_id: str,
        metadata: dict[str, Any],
    ) -> PlannerResponse:
        """Format response for clarify action (LOW_CONFIDENCE)."""
        response_text = (
            f"I found some results but confidence is low "
            f"({packet.summary.top_confidence:.2f}). "
            f"Could you provide more detail about what you're looking for?"
        )
        suggestions = [
            "Try being more specific about the topic",
            "Include keywords from the content you're looking for",
            "Narrow the scope to a particular source or time period",
        ]

        return PlannerResponse(
            response_text=response_text,
            action_taken="clarify",
            branch_code=branch,
            session_id=session_id,
            suggestions=suggestions,
            candidates_used=packet.summary.candidate_count,
            confidence=packet.summary.top_confidence,
            retrieval_metadata=metadata,
        )

    def _format_fallback(
        self,
        packet: ContextPacket,
        branch: str,
        session_id: str,
        metadata: dict[str, Any],
    ) -> PlannerResponse:
        """Format response for fallback action (EMPTY_SET)."""
        response_text = (
            "I couldn't find relevant context for your query. "
            "Try rephrasing or providing more context."
        )

        return PlannerResponse(
            response_text=response_text,
            action_taken="fallback",
            branch_code=branch,
            session_id=session_id,
            suggestions=[
                "Rephrase your question with different keywords",
                "Provide more context about what you need",
                "Try a broader search term",
            ],
            candidates_used=0,
            confidence=0.0,
            retrieval_metadata=metadata,
        )

    def _format_escalate(
        self,
        packet: ContextPacket,
        branch: str,
        session_id: str,
        metadata: dict[str, Any],
    ) -> PlannerResponse:
        """Format response for escalate action (CHANNEL_MISMATCH)."""
        response_text = (
            "The retrieved context doesn't seem to match your query intent. "
            "This may require manual review or a different approach."
        )

        return PlannerResponse(
            response_text=response_text,
            action_taken="escalate",
            branch_code=branch,
            session_id=session_id,
            suggestions=[
                "Try specifying the exact topic or domain",
                "Check if the content has been ingested into the system",
            ],
            candidates_used=packet.summary.candidate_count,
            confidence=packet.summary.top_confidence,
            retrieval_metadata=metadata,
        )
