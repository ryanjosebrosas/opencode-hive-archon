"""Schema definitions for MCP compatibility."""

from pydantic import BaseModel, Field
from second_brain.contracts.context_packet import RetrievalResponse


class MCPCompatibilityResponse(BaseModel):
    """
    Compatibility wrapper for MCP tool responses.

    Includes both contract envelope and optional legacy fields
    for backward compatibility.
    """

    # Contract envelope (canonical)
    context_packet: dict = Field(..., description="Context packet with candidates and summary")
    next_action: dict = Field(..., description="Next action with branch code")

    # Legacy compatibility fields (optional, additive only)
    candidates: list[dict] = Field(default_factory=list, description="Legacy flat candidates list")
    branch: str = Field(default="", description="Legacy branch code")
    confidence: float = Field(default=0.0, description="Legacy top confidence")

    # Routing metadata
    routing_metadata: dict = Field(default_factory=dict, description="Route decision metadata")

    @classmethod
    def from_retrieval_response(
        cls,
        response: RetrievalResponse,
        include_legacy: bool = True,
    ) -> "MCPCompatibilityResponse":
        """
        Create compatibility response from RetrievalResponse.

        Args:
            response: Canonical retrieval response
            include_legacy: Whether to include legacy fields

        Returns:
            Compatibility response with nested contract + optional legacy
        """
        context_packet_dump = response.context_packet.model_dump()
        next_action_dump = response.next_action.model_dump()

        legacy_fields = {}
        if include_legacy:
            legacy_fields = {
                "candidates": [c.model_dump() for c in response.context_packet.candidates],
                "branch": response.context_packet.summary.branch,
                "confidence": response.context_packet.summary.top_confidence,
            }

        return cls(
            context_packet=context_packet_dump,
            next_action=next_action_dump,
            routing_metadata=response.routing_metadata,
            **legacy_fields,  # type: ignore
        )
