# Retrieval Overlap Policy

## Overview

This policy defines capability overlap checks and default-on/default-off rules to prevent redundant operations across retrieval providers.

## Decision Table: Rerank Policy

| Provider | Native Rerank | External Rerank | Default |
|----------|--------------|-----------------|---------|
| Mem0 | YES | Optional | Native ON, External OFF |
| Supabase | NO | Optional | External configurable |
| Graphiti | NO | Optional | External configurable |

## Mem0 Rerank Policy

### Rule

**Mem0 path MUST apply provider-native rerank and skip external rerank by default.**

### Rationale

1. **Redundancy**: Mem0's managed memory includes built-in reranking
2. **Performance**: External rerank adds latency without proven benefit
3. **Cost**: Duplicate rerank consumes API quota unnecessarily

### Implementation

```python
# CORRECT: Mem0 path
async def mem0_retrieve(query: str):
    results = await mem0.search(query, rerank=True)  # Native only
    # Do NOT call external rerank
    return results

# CORRECT: Non-Mem0 path  
async def storage_retrieve(query: str, use_rerank: bool):
    results = await storage.search(query)
    if use_rerank and config.external_rerank_enabled:
        results = await voyage_rerank(results)
    return results
```

### Feature Flag

```python
# Environment variable
MEM0_EXTERNAL_RERANK=false  # Default: OFF
```

## Duplicate Rerank Prevention

### Guard Condition

External rerank skipped when ANY of:
1. Provider has native rerank AND `skip_external_rerank=True`
2. Feature flag explicitly disables external rerank
3. Rerank service unavailable (degraded mode)

### Metadata Tracking

All retrieval responses MUST include rerank metadata:

```python
{
    "rerank_applied": True,
    "rerank_type": "provider-native",  # or "external" or "none"
    "rerank_bypass_reason": "mem0-default-policy"  # if skipped
}
```

## Capability Overlap Checks

### Before Enabling New Provider

Check against existing providers:

| Capability | Mem0 | Supabase | Graphiti | Overlap Risk |
|-----------|------|----------|----------|--------------|
| Semantic search | YES | YES | NO | Medium |
| Reranking | YES | NO | NO | Low |
| Graph traversal | NO | NO | YES | None |
| Session memory | YES | NO | NO | Low |

### Mitigation

1. **Feature flags** gate each provider independently
2. **Router policy** selects best provider for mode
3. **Metadata** tracks which provider served request

## Default-On/Default-Off Rules

### Default-On (Stable)

- Mem0 provider for conversation mode
- Native rerank on Mem0 path
- Contract-aligned output for all branches

### Default-Off (Opt-In)

- Graphiti provider (requires feature flag)
- External rerank on Mem0 path (requires explicit override)
- Multi-provider merge (requires accurate mode)

### Configuration Example

```python
# config.py
RETRIEVAL_CONFIG = {
    "mem0": {
        "enabled": True,
        "native_rerank": True,
        "external_rerank": False,  # Explicit override needed
    },
    "graphiti": {
        "enabled": False,  # Feature flag required
        "external_rerank": True,
    },
    "supabase": {
        "enabled": True,
        "external_rerank": True,  # Configurable
    }
}
```

## Policy Enforcement

### Router-Level Guard

```python
async def select_provider(mode: str, providers: list[str], config: dict):
    if mode == "conversation" and "mem0" in providers:
        # Enforce mem0 policy
        return "mem0", {"skip_external_rerank": True}
    
    # Other providers use standard rerank policy
    return select_best_available(providers), {"skip_external_rerank": False}
```

### Service-Level Guard

```python
async def retrieve(query: str, provider: str, options: dict):
    if provider == "mem0" and options.get("external_rerank", False):
        # Log warning but allow explicit override
        logger.warning("External rerank on Mem0 path - override in effect")
    
    # Apply standard policy
    skip_rerank = provider == "mem0" and not options.get("external_rerank")
    return await provider.search(query, skip_rerank=skip_rerank)
```

## Testing Requirements

### Unit Tests

- Mem0 path skips external rerank by default
- Non-Mem0 paths apply external rerank per config
- Explicit override bypasses default policy

### Regression Tests

- Mem0 duplicate-rerank prevention (must always pass)
- Feature flag behavior for Graphiti path
- Policy metadata present in all responses

### Integration Tests

- End-to-end retrieval with policy enforcement
- Contract compliance with rerank metadata

## Policy Violations

### Detected Patterns

❌ **Violation**: External rerank called on Mem0 results without explicit override
❌ **Violation**: Graphiti enabled without feature flag
❌ **Violation**: Rerank metadata missing from response

### Resolution

1. Add policy guard at call site
2. Add test case for violation scenario
3. Update this policy if exception justified

## Version History

- **1.0.0** (2026-02-25): Initial policy with Mem0 duplicate-rerank prevention
