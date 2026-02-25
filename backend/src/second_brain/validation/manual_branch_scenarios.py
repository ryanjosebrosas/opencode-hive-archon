"""Manual branch validation scenarios for testing and operator validation."""
from dataclasses import dataclass, field
from typing import Optional
from second_brain.contracts.context_packet import RetrievalRequest
from second_brain.orchestration.fallbacks import BranchCodes


@dataclass
class BranchScenario:
    """Deterministic branch scenario definition."""
    id: str
    description: str
    request: RetrievalRequest
    provider_status: dict[str, str]
    feature_flags: dict[str, bool]
    expected_branch: str
    expected_action: str
    expected_rerank_type: str
    tags: list[str] = field(default_factory=list)
    notes: str = ""


def get_all_scenarios() -> list[BranchScenario]:
    """Get all validation scenarios."""
    return [
        # Smoke scenarios
        BranchScenario(
            id="S001",
            description="Conversation Mem0 high confidence",
            request=RetrievalRequest(
                query="test high confidence query",
                mode="conversation",
                top_k=5,
                threshold=0.6,
            ),
            provider_status={"mem0": "available", "supabase": "available"},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True, "graphiti_enabled": False},
            expected_branch=BranchCodes.RERANK_BYPASSED,
            expected_action="proceed",
            expected_rerank_type="provider-native",
            tags=["smoke", "policy"],
        ),
        BranchScenario(
            id="S002",
            description="Conversation Mem0 no candidates",
            request=RetrievalRequest(
                query="empty set query",
                mode="conversation",
                top_k=5,
                threshold=0.6,
            ),
            provider_status={"mem0": "available"},
            feature_flags={"mem0_enabled": True, "supabase_enabled": False},
            expected_branch=BranchCodes.EMPTY_SET,
            expected_action="fallback",
            expected_rerank_type="none",
            tags=["smoke", "edge"],
        ),
        BranchScenario(
            id="S003",
            description="Conversation Mem0 low confidence",
            request=RetrievalRequest(
                query="low confidence query",
                mode="conversation",
                top_k=5,
                threshold=0.6,
            ),
            provider_status={"mem0": "available"},
            feature_flags={"mem0_enabled": True},
            expected_branch=BranchCodes.LOW_CONFIDENCE,
            expected_action="clarify",
            expected_rerank_type="provider-native",
            tags=["smoke", "edge"],
        ),
        BranchScenario(
            id="S004",
            description="Conversation Supabase high confidence",
            request=RetrievalRequest(
                query="supabase query",
                mode="conversation",
                top_k=5,
                threshold=0.6,
            ),
            provider_status={"mem0": "unavailable", "supabase": "available"},
            feature_flags={"mem0_enabled": False, "supabase_enabled": True},
            expected_branch=BranchCodes.SUCCESS,
            expected_action="proceed",
            expected_rerank_type="external",
            tags=["smoke"],
        ),
        
        # Policy scenarios
        BranchScenario(
            id="S022",
            description="Rerank service disabled",
            request=RetrievalRequest(
                query="rerank disabled query",
                mode="fast",
                top_k=5,
            ),
            provider_status={"mem0": "unavailable", "supabase": "available"},
            feature_flags={
                "mem0_enabled": False,
                "supabase_enabled": True,
                "external_rerank_enabled": False,
            },
            expected_branch=BranchCodes.SUCCESS,
            expected_action="proceed",
            expected_rerank_type="none",
            tags=["policy"],
        ),
        BranchScenario(
            id="S025",
            description="Mem0 external override on",
            request=RetrievalRequest(
                query="mem0 override query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "available"},
            feature_flags={
                "mem0_enabled": True,
                "supabase_enabled": True,
                "mem0_external_override": True,
            },
            expected_branch=BranchCodes.RERANK_BYPASSED,
            expected_action="proceed",
            expected_rerank_type="provider-native",
            tags=["policy"],
            notes="Mem0 policy still skips external even with override flag",
        ),
        BranchScenario(
            id="S026",
            description="Mem0 external override off default",
            request=RetrievalRequest(
                query="mem0 default query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "available"},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
            expected_branch=BranchCodes.RERANK_BYPASSED,
            expected_action="proceed",
            expected_rerank_type="provider-native",
            tags=["policy"],
        ),
        
        # Degraded scenarios
        BranchScenario(
            id="S015",
            description="Mem0 degraded, Supabase available fallback",
            request=RetrievalRequest(
                query="degraded mem0 query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "degraded", "supabase": "available"},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
            expected_branch=BranchCodes.LOW_CONFIDENCE,
            expected_action="clarify",
            expected_rerank_type="none",
            tags=["degraded"],
            notes="Falls back to supabase when mem0 degraded, returns low confidence",
        ),
        BranchScenario(
            id="S016",
            description="Mem0 available, Supabase degraded",
            request=RetrievalRequest(
                query="mem0 primary query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "available", "supabase": "degraded"},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
            expected_branch=BranchCodes.RERANK_BYPASSED,
            expected_action="proceed",
            expected_rerank_type="provider-native",
            tags=["degraded"],
        ),
        
        # Edge scenarios
        BranchScenario(
            id="S013",
            description="All providers disabled",
            request=RetrievalRequest(
                query="no providers query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={},
            feature_flags={"mem0_enabled": False, "supabase_enabled": False},
            expected_branch=BranchCodes.EMPTY_SET,
            expected_action="fallback",
            expected_rerank_type="none",
            tags=["edge"],
        ),
        BranchScenario(
            id="S014",
            description="All providers unavailable",
            request=RetrievalRequest(
                query="all unavailable query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "unavailable", "supabase": "unavailable"},
            feature_flags={"mem0_enabled": True, "supabase_enabled": True},
            expected_branch=BranchCodes.EMPTY_SET,
            expected_action="fallback",
            expected_rerank_type="none",
            tags=["edge"],
        ),
        
        # Channel mismatch (validation mode only)
        BranchScenario(
            id="S027",
            description="Channel mismatch forced validation",
            request=RetrievalRequest(
                query="channel mismatch query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "available"},
            feature_flags={"mem0_enabled": True},
            expected_branch=BranchCodes.CHANNEL_MISMATCH,
            expected_action="escalate",
            expected_rerank_type="none",
            tags=["edge", "validation"],
            notes="Requires validation_mode=True and force_branch",
        ),
        
        # Deterministic replay
        BranchScenario(
            id="S048",
            description="Deterministic replay test 1",
            request=RetrievalRequest(
                query="deterministic test query",
                mode="conversation",
                top_k=5,
            ),
            provider_status={"mem0": "available"},
            feature_flags={"mem0_enabled": True},
            expected_branch=BranchCodes.RERANK_BYPASSED,
            expected_action="proceed",
            expected_rerank_type="provider-native",
            tags=["policy", "deterministic"],
        ),
    ]


def get_scenario_by_id(scenario_id: str) -> Optional[BranchScenario]:
    """Get scenario by ID."""
    for scenario in get_all_scenarios():
        if scenario.id == scenario_id:
            return scenario
    return None


def get_scenarios_by_tag(tag: str) -> list[BranchScenario]:
    """Get all scenarios with specified tag."""
    return [s for s in get_all_scenarios() if tag in s.tags]


def get_smoke_scenarios() -> list[BranchScenario]:
    """Get smoke test scenarios."""
    return get_scenarios_by_tag("smoke")


def get_policy_scenarios() -> list[BranchScenario]:
    """Get policy test scenarios."""
    return get_scenarios_by_tag("policy")


def get_edge_scenarios() -> list[BranchScenario]:
    """Get edge case scenarios."""
    return get_scenarios_by_tag("edge")


def get_degraded_scenarios() -> list[BranchScenario]:
    """Get degraded provider scenarios."""
    return get_scenarios_by_tag("degraded")
