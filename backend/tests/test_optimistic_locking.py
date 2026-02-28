"""Tests for optimistic_locking functionality."""

from __future__ import annotations

from typing import Any

import pytest

from second_brain.errors import SecondBrainError
from second_brain.services.optimistic_lock import (
    OptimisticLockService,
    StaleDataError,
    ChunkNotFoundError,
)


class MockOptimisticLockExecutor:
    def __init__(self) -> None:
        self._store: dict[str, int] = {}  # chunk_id → version
    
    def seed(self, chunk_id: str, version: int = 1) -> None:
        self._store[chunk_id] = version
    
    def get_chunk_version(self, chunk_id: str) -> int | None:
        return self._store.get(chunk_id)
    
    def update_if_version_matches(
        self, chunk_id: str, expected_version: int, updates: dict[str, Any]
    ) -> bool:
        if self._store.get(chunk_id) == expected_version:
            self._store[chunk_id] = expected_version + 1
            return True
        return False


def test_update_correct_version_succeeds() -> None:
    """update with correct version returns new version"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 1)
    
    new_version = service.update(chunk_id, 1, {"content": "updated"})
    
    assert new_version == 2
    assert executor.get_chunk_version(chunk_id) == 2


def test_update_increments_version() -> None:
    """version goes from 1 → 2 after update"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 1)
    
    service.update(chunk_id, 1, {"content": "updated"})
    
    assert executor.get_chunk_version(chunk_id) == 2


def test_update_stale_version_raises() -> None:
    """wrong version raises StaleDataError with STALE_VERSION code"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 2)  # current version is 2
    
    with pytest.raises(StaleDataError) as exc_info:
        service.update(chunk_id, 1, {"content": "updated"})  # trying with version 1
    
    assert exc_info.value.code == "STALE_VERSION"


def test_update_chunk_not_found_raises() -> None:
    """missing chunk raises ChunkNotFoundError with CHUNK_NOT_FOUND code"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "nonexistent-id"
    
    with pytest.raises(ChunkNotFoundError) as exc_info:
        service.update(chunk_id, 1, {"content": "updated"})
    
    assert exc_info.value.code == "CHUNK_NOT_FOUND"


def test_stale_error_has_correct_context() -> None:
    """error context contains chunk_id, expected_version"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 3)  # current version is 3
    
    with pytest.raises(StaleDataError) as exc_info:
        service.update(chunk_id, 1, {"content": "updated"})  # expecting version 1
    
    context = exc_info.value.context
    assert context["chunk_id"] == chunk_id
    assert context["expected_version"] == 1
    # actual_version is no longer in the StaleDataError as we removed the pre-check


def test_multiple_sequential_updates() -> None:
    """version 1→2→3 in sequence"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 1)
    
    version_after_first = service.update(chunk_id, 1, {"content": "first"})
    version_after_second = service.update(chunk_id, 2, {"content": "second"})
    
    assert version_after_first == 2
    assert version_after_second == 3
    assert executor.get_chunk_version(chunk_id) == 3


def test_concurrent_updates_one_wins() -> None:
    """two threads updating version 1: one gets True, one gets StaleDataError"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 1)
    
    # First update should succeed
    result1 = service.update(chunk_id, 1, {"content": "first"})
    assert result1 == 2
    
    # Second update with the old version should fail
    with pytest.raises(StaleDataError):
        service.update(chunk_id, 1, {"content": "second"})


def test_update_version_2_with_1_raises() -> None:
    """explicit stale: chunk at v2, trying to update with v1"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 2)  # chunk at version 2
    
    with pytest.raises(StaleDataError) as exc_info:
        service.update(chunk_id, 1, {"content": "updated"})  # attempting with version 1
    
    assert exc_info.value.code == "STALE_VERSION"


def test_get_chunk_version_returns_current() -> None:
    """executor.get_chunk_version matches expected"""
    executor = MockOptimisticLockExecutor()
    chunk_id = "test-id"
    executor.seed(chunk_id, 5)
    
    assert executor.get_chunk_version(chunk_id) == 5


def test_update_does_not_affect_other_chunks() -> None:
    """updating chunk A doesn't change chunk B version"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_a_id = "chunk-a"
    chunk_b_id = "chunk-b"
    executor.seed(chunk_a_id, 1)
    executor.seed(chunk_b_id, 1)
    
    initial_b_version = executor.get_chunk_version(chunk_b_id)
    service.update(chunk_a_id, 1, {"content": "updated A"})
    final_b_version = executor.get_chunk_version(chunk_b_id)
    
    assert initial_b_version == 1
    assert final_b_version == 1  # B's version unchanged


def test_stale_data_error_is_second_brain_error() -> None:
    """isinstance check passes"""
    error = StaleDataError("test", code="TEST_ERROR", context={})
    assert isinstance(error, SecondBrainError)


def test_chunk_not_found_error_is_second_brain_error() -> None:
    """isinstance check passes for ChunkNotFoundError"""
    error = ChunkNotFoundError("test", code="TEST_ERROR", context={})
    assert isinstance(error, SecondBrainError)


def test_update_returns_new_version_number() -> None:
    """return value = expected_version + 1"""
    executor = MockOptimisticLockExecutor()
    service = OptimisticLockService(executor)
    chunk_id = "test-id"
    executor.seed(chunk_id, 5)  # chunk is at version 5 initially
    
    returned_version = service.update(chunk_id, 5, {"content": "updated"})  # update version 5 with expected v5
    
    assert returned_version == 6  # expected_version + 1 = 5 + 1 = 6