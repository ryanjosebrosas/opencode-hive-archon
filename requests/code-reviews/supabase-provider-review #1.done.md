# Code Review: supabase-memory-provider (uncommitted changes)

**Date**: 2026-02-26
**Iteration**: 1
**Scope**: Uncommitted changes (Supabase provider, memory service updates)

---

## Type Safety

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Major | voyage.py:53 | `result.embeddings[0]` accessed without bounds check | Add explicit check for empty embeddings |
| Major | supabase.py:18 | `self._client: Any \| None = None` loses type safety | Import `Client` type or create Protocol |
| Major | voyage.py:22 | `self._voyage_client: Any \| None = None` loses type safety | Import type or create Protocol |
| Minor | deps.py:42 | Docstring not updated for new parameters | Update docstring |

## Security

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Minor | supabase.py:111-113 | ✅ Good: Error sanitization correct | No change needed |
| Minor | memory.py:200-203 | ✅ Good: Mem0 error sanitization preserved | No change needed |

## Architecture

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Major | memory.py:216-228 | Creates VoyageRerankService/SupabaseProvider on every call | Cache as instance variables |
| Major | memory.py:128-136 | Re-reads `os.getenv()` on every call for SUPABASE_* | Cache credentials in `__init__` |
| Minor | memory.py:39-46 | Provider routing split across multiple methods | Consider registry pattern |

## Performance

| Severity | File:line | Issue | Recommendation |
|----------|-----------|-------|----------------|
| Major | memory.py:216-219 | VoyageRerankService instantiated every search call | Cache as instance variable |
| Major | memory.py:228 | SupabaseProvider instantiated every search call | Cache as instance variable |
| Minor | supabase.py:51-54 | RPC call doesn't specify timeout | Consider adding timeout |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| Major | 8 |
| Minor | 5 |
| **Total** | **13** |

---

## Priority Recommendations

**P1 (Fix soon):**
1. Instance caching in MemoryService (memory.py:216-228)
2. Bounds check for embeddings (voyage.py:53)
3. Environment variable caching (memory.py:134-136)
4. Type hints for external clients (supabase.py:18, voyage.py:22)