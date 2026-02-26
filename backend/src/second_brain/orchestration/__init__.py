"""Orchestration package - export routing and fallbacks."""

from second_brain.orchestration.retrieval_router import (
    route_retrieval,
    RouteDecision,
    ProviderStatus,
)
from second_brain.orchestration.fallbacks import (
    determine_branch,
    FallbackEmitter,
    BranchCodes,
)

__all__ = [
    "BranchCodes",
    "determine_branch",
    "FallbackEmitter",
    "ProviderStatus",
    "RouteDecision",
    "route_retrieval",
]
