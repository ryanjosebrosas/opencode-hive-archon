# Code Review: hybrid-retrieval-orchestrator

**Date**: 2026-02-26
**Iteration**: 1

---

## Type Safety

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Minor | context_packet.py:13 | `metadata: dict[str, Any]` uses Any type | Consider defining a TypedDict for known metadata fields with `Extra: Any` for extensibility |
| Minor | retrieval_router.py:75 | Return type `tuple[str, dict]` is underspecified | Use `tuple[str, dict[str, Any]]` or define a `RouteOptions` TypedDict |
| Major | recall.py:313 | `_force_branch_output` returns `tuple` without type parameters | Specify return type: `-> tuple[ContextPacket, NextAction]` |
| Minor | recall.py:406 | `# type: ignore` comment for mode parameter | Use `Literal` type narrowing or validate with `if mode not in ("fast", "accurate", "conversation")` |
| Minor | memory.py:32 | `_mem0_client: Any \| None = None` uses Any for external library type | Add inline comment explaining Any usage is intentional for optional external dependency |
| Minor | voyage.py:27 | `_voyage_client: Any \| None = None` uses Any for external library type | Same as above - acceptable but document intent |
| Minor | schemas.py:58 | `**legacy_fields,  # type: ignore` bypasses type checking | Consider using `model_construct()` or explicit field assignment instead of kwargs spread |
| Minor | mcp_server.py:58 | Uses `cast()` for mode parameter instead of validation | Validate input string against allowed Literal values before casting |

## Security

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Minor | memory.py:200-204 | `_sanitize_error_message` only redacts known API keys, may miss others | Add logging for potential key exposure, consider regex pattern matching for key-like strings |
| Minor | voyage.py:35-39 | Creates client without explicit key if env var unset, no warning logged | Log warning when falling back to implicit credentials |
| Minor | deps.py:69-73 | Default config contains `None` for API keys with no validation | Add runtime validation in production path that warns if keys are None when real provider enabled |

## Architecture

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Minor | recall.py:76-77 | Late import of `FallbackEmitter` inside `run()` method | Move to top-level imports for consistency |
| Minor | recall.py:315 | Duplicate late import of `FallbackEmitter` | Remove, already imported at top of fallbacks module |
| Minor | memory.py:213-214 | Late imports inside `_search_with_supabase` for dependencies | Consider dependency injection or top-level imports with try/except |
| Minor | mcp_server.py:53-54 | Late imports inside `recall_search` method | Move imports to module level |
| Minor | mcp_server.py:99 | Late import inside `validate_branch` for validation module | Move to module level with conditional import if needed |
| Minor | retrieval_router.py:59 | `ProviderStatus` class defined after functions that use it | Move class definition to top of module |
| Major | memory.py:24-359 | `MemoryService` has too many responsibilities (mock, real provider, supabase, fallback) | Extract provider-specific implementations behind a `MemoryProvider` protocol |
| Minor | recall.py:412-418 | `run_recall` creates new service instances each call without caching | Document this is convenience-only, not production-use |

## Performance

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Minor | trace.py:47-50 | `get_by_id` uses O(n) linear search | Add a `dict[str, RetrievalTrace]` index for O(1) lookup if frequently called |
| Minor | trace.py:35-36 | `pop(0)` on list is O(n), inefficient eviction | Use `collections.deque(maxlen=max_traces)` for O(1) append/pop |
| Minor | memory.py:291 | Sorts mock data on every `_search_mock` call | Pre-sort when `set_mock_data()` is called |
| Minor | recall.py:85-86, 263-264, 290-291 | Multiple `dict(self.feature_flags)` copies create unnecessary allocations | Store immutable copies or reference directly if mutation not a concern |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Major | 2 |
| Minor | 21 |
| **Total** | **23** |

---

## Priority Recommendations

**P0 (Fix before commit):**
- None - No critical issues found

**P1 (Fix soon):**
1. `recall.py:313` - Add proper return type annotation to `_force_branch_output`
2. `memory.py:24-359` - Consider refactoring `MemoryService` to separate provider implementations

**P2 (Consider):**
1. Replace `trace.py:35-36` list with `deque` for O(1) eviction
2. Add type narrowing for `mode` parameter in `run_recall()` and `recall_search()`
3. Move late imports to module level for better import graph visibility
4. Add logging when API keys are missing and fallback paths are used
5. Pre-sort mock data in `set_mock_data()` to avoid repeated sorting
6. Add `_id_index: dict[str, int]` to `TraceCollector` for O(1) ID lookup