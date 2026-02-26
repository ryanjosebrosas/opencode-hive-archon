# Fix Plan: Code Review Findings #1

**Source Review**: `requests/code-reviews/hybrid-retrieval-orchestrator-review #1.md`
**Date**: 2026-02-26

---

## Summary

Fix 2 Major issues from code review. P1 (fix soon) only - MemoryService refactoring is deferred to a future slice.

---

## Issues to Fix

### Major 1: Missing Return Type Annotation

**File**: `backend/src/second_brain/agents/recall.py:313`
**Issue**: `_force_branch_output` returns `tuple` without type parameters
**Fix**: Change `-> tuple:` to `-> tuple[ContextPacket, NextAction]:`

### Major 2: MemoryService Responsibilities (DEFERRED)

**File**: `backend/src/second_brain/services/memory.py:24-359`
**Issue**: `MemoryService` has too many responsibilities (mock, real provider, supabase, fallback)
**Status**: DEFERRED - Requires significant architectural refactoring. Mark as future slice.

---

## Implementation Plan

### Task 1: Fix Return Type Annotation

**ACTION**: Update type annotation
**TARGET**: `backend/src/second_brain/agents/recall.py`
**IMPLEMENT**: 
- Line 313: Change `) -> tuple:` to `) -> tuple[ContextPacket, NextAction]:`

**PATTERN**: Follow existing type annotation patterns in the codebase (e.g., `determine_branch` returns `tuple[ContextPacket, NextAction]`)

**IMPORTS**: None needed (ContextPacket and NextAction already imported)

**GOTCHA**: None - straightforward type annotation fix

**VALIDATE**: Run `mypy backend/src` and `ruff check backend`

---

## Tasks Summary

| # | Task | Status |
|---|------|--------|
| 1 | Fix `_force_branch_output` return type | Pending |
| 2 | MemoryService refactoring | DEFERRED |

---

## Validation Commands

```bash
# Type checking
mypy backend/src

# Linting
ruff check backend

# Unit tests
pytest tests/ -v
```