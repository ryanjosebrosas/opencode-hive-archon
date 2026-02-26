# Fix Plan: Code Review Findings #1

**Source Review**: `requests/code-reviews/real-voyage-rerank-review #1.md`
**Date**: 2026-02-26

---

## Summary

Fix 1 Major issue from code review of uncommitted voyage rerank changes.

---

## Issues to Fix

### Major 1: IndexError Risk (voyage.py:102-103)

**Issue**: `candidates_list[r.index]` accessed without bounds check. Voyage API could return invalid index.

**Fix**: Add bounds check before accessing list.

**PATTERN**: Follow existing defensive patterns in codebase.

**VALIDATE**: `pytest tests/test_voyage_rerank.py -v`

---

## Additional Minor Fixes

### Minor 1: TypeError Risk (voyage.py:109)

**Issue**: `float(r.relevance_score)` could raise TypeError if None/string.

**Fix**: Wrap in try/except.

### Minor 2: Misleading rerank_type (voyage.py:169)

**Issue**: Mock rerank sets `rerank_type="external"` which is misleading.

**Fix**: Change to `"mock"` for clarity.

---

## Implementation

### Task 1: Add bounds check for Voyage API index

**ACTION**: Add defensive check
**TARGET**: `backend/src/second_brain/services/voyage.py`
**IMPLEMENT**:
```python
for r in reranking.results:
    if r.index >= len(candidates_list):
        logger.warning("Voyage returned invalid index %d for %d candidates", r.index, len(candidates_list))
        continue
    original = candidates_list[r.index]
    try:
        score = float(r.relevance_score)
    except (TypeError, ValueError):
        logger.warning("Invalid relevance_score: %r", r.relevance_score)
        continue
    confidence = max(0.0, min(1.0, score))
```

**VALIDATE**: `pytest tests/test_voyage_rerank.py -v`