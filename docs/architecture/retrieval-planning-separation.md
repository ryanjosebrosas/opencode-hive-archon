# Retrieval-Planning Separation

## Overview

This document defines the responsibility boundary between retrieval and planning modules, ensuring clear separation of concerns while maintaining contract-aligned data flow.

## Responsibility Boundaries

### Retrieval Module

**Owns**:
- Provider selection and routing
- Context candidate gathering
- Confidence scoring
- Reranking (provider-native or external)
- Contract-compliant output emission

**Does NOT own**:
- Query reformulation
- Multi-turn conversation state
- User intent interpretation
- Action planning

### Planning Module

**Owns**:
- Query understanding and reformulation
- Multi-turn conversation state management
- User intent classification
- Action sequencing and orchestration
- Next action determination (business logic)

**Does NOT own**:
- Raw context retrieval
- Provider-specific operations
- Confidence calculation
- Reranking execution

## Data Flow

### Request Path

```
User Query
    ↓
Planning Module (intent classification, query refinement)
    ↓
Retrieval Module (provider selection, context gathering)
    ↓
ContextPacket + NextAction
    ↓
Planning Module (action sequencing)
    ↓
Response Generation
```

### Message Flow

1. **Planning → Retrieval**: Retrieval request with query + mode
2. **Retrieval → Planning**: ContextPacket + NextAction
3. **Planning → Orchestrator**: Final action plan

## Interface Contract

### Retrieval Request

```python
class RetrievalRequest(BaseModel):
    query: str
    mode: Literal["fast", "accurate", "conversation"]
    top_k: int = 5
    threshold: float = 0.6
    provider_override: str | None = None
```

### Retrieval Response

```python
class RetrievalResponse(BaseModel):
    context_packet: ContextPacket
    next_action: NextAction
    routing_metadata: dict[str, Any] = Field(default_factory=dict)
```

## Separation Benefits

1. **Testability**: Retrieval tested independently of planning logic
2. **Provider Swapping**: Change providers without affecting planning
3. **Debugability**: Clear boundaries for issue isolation
4. **Parallel Development**: Teams can work on modules independently

## Common Pitfalls

### ❌ Planning Logic in Retrieval

```python
# WRONG: Retrieval module deciding user intent
if query.contains("how"):
    branch = "tutorial"  # Don't do this
```

### ✅ Retrieval Module Stays Neutral

```python
# CORRECT: Retrieval only scores confidence
confidence = calculate_similarity(query, candidate)
branch = determine_branch(confidence)  # Based on score only
```

## Exception Handling

### Retrieval Failures

Retrieval module MUST always return valid ContextPacket + NextAction, even on failure:

```python
# Provider unavailable → EMPTY_SET branch
# Timeout → EMPTY_SET branch with metadata
# Schema error → LOW_CONFIDENCE branch
```

### Planning Failures

Planning module handles NextAction interpretation:

```python
match next_action.action:
    case "proceed": generate_response(context_packet)
    case "clarify": request_user_clarification()
    case "fallback": trigger_fallback_sequence()
    case "escalate": escalate_to_human()
```

## Integration Points

### MCP Tool Exposure

Retrieval tools expose contract fields without breaking compatibility:

```python
@mcp_tool()
async def search_memory(query: str) -> dict:
    response = await retrieval_router.retrieve(query=query, mode="conversation")
    return {
        **response.context_packet.model_dump(),
        "next_action": response.next_action.model_dump()
    }
```

### Service Layer

Memory service applies policy hooks:

```python
async def retrieve_with_rerank(query: str, use_mem0: bool):
    if use_mem0:
        # Provider-native rerank only
        return await mem0_provider.search(query, rerank=True)
    else:
        # External rerank if needed
        results = await storage.search(query)
        return await voyage_rerank(results) if config.rerank_enabled else results
```

## Testing Strategy

### Unit Tests

- Retrieval: Provider selection, confidence scoring, branch determination
- Planning: Intent classification, action sequencing, NextAction interpretation

### Integration Tests

- Full request → retrieval → response flow
- Contract compliance validation
- Feature flag behavior

### Contract Tests

- Schema validation for all branch types
- Deterministic output verification
- Provider swap compatibility
