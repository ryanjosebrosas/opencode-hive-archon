# Conversational Retrieval Contract

## Overview

This document defines the canonical runtime contract for conversation-first retrieval orchestration. The contract ensures deterministic behavior across all retrieval branches while maintaining provider agnosticism.

## Core Principles

1. **Conversation-First Runtime**: Markdown documents behavior; agents execute runtime
2. **Contract-Aligned Outputs**: All paths emit `context_packet` + `next_action`
3. **Deterministic Fallbacks**: Branch codes are stable constants
4. **Provider Agnosticism**: Contract excludes provider-specific fields

## Contract Schema

### ContextCandidate

Represents a single retrieval candidate:

```python
class ContextCandidate(BaseModel):
    id: str
    content: str
    source: str
    confidence: float  # 0.0-1.0
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### ConfidenceSummary

Aggregated confidence assessment:

```python
class ConfidenceSummary(BaseModel):
    top_confidence: float
    candidate_count: int
    threshold_met: bool
    branch: str  # Branch code
```

### ContextPacket

Complete retrieval result envelope:

```python
class ContextPacket(BaseModel):
    candidates: list[ContextCandidate]
    summary: ConfidenceSummary
    provider: str
    rerank_applied: bool
    timestamp: str
```

### NextAction

Explicit actionability indicator:

```python
class NextAction(BaseModel):
    action: Literal["proceed", "clarify", "fallback", "escalate"]
    reason: str
    branch_code: str
    suggestion: str | None = None
```

## Branch Semantics

### EMPTY_SET

**Condition**: No candidates retrieved from any provider

**Output**:
- `candidates`: []
- `summary.top_confidence`: 0.0
- `summary.branch`: "EMPTY_SET"
- `next_action.action`: "fallback"

### LOW_CONFIDENCE

**Condition**: Top candidate below confidence threshold (default: 0.6)

**Output**:
- `candidates`: [low_confidence_results]
- `summary.threshold_met`: False
- `summary.branch`: "LOW_CONFIDENCE"
- `next_action.action`: "clarify"

### CHANNEL_MISMATCH

**Condition**: Retrieved context doesn't match query channel/intent

**Output**:
- `candidates`: [mismatched_results]
- `summary.branch`: "CHANNEL_MISMATCH"
- `next_action.action`: "escalate"

### RERANK_BYPASSED

**Condition**: Provider-native rerank applied, external skipped

**Output**:
- `rerank_applied`: True
- `summary.branch`: "RERANK_BYPASSED"
- `next_action.action`: "proceed"

### SUCCESS

**Condition**: High-confidence candidates retrieved

**Output**:
- `summary.threshold_met`: True
- `summary.branch`: "SUCCESS"
- `next_action.action`: "proceed"

## Required Output Guarantees

1. **Deterministic**: Same inputs → same branch + same output structure
2. **Complete**: `context_packet` + `next_action` always present
3. **Stable Codes**: Branch codes never change without major version
4. **Provider Neutral**: Contract fields work across all providers

## Mode Policy

### Retrieval Modes

| Mode | Provider Selection | Rerank Default |
|------|-------------------|----------------|
| `fast` | Single best available | External OFF |
| `accurate` | Multi-provider merge | External ON |
| `conversation` | Mem0 preferred | Provider-native ON |

### Provider Selection Order

1. Check feature flags for enabled providers
2. Check provider availability (connection health)
3. Apply mode-based selection policy
4. Return deterministic provider choice

## Implementation Requirements

- All retrieval agents MUST emit contract-aligned output
- Fallback emitters MUST use stable branch codes
- Router MUST be deterministic for same inputs
- Feature flags MUST gate optional paths (e.g., Graphiti)

## Versioning

- Contract version: 1.0.0
- Breaking changes require major version increment
- Provider-specific extensions go in `metadata` field only
