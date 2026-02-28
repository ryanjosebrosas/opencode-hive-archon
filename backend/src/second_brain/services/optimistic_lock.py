"""Optimistic locking for knowledge_chunks via version column."""

from __future__ import annotations

from typing import Any, Protocol


from second_brain.errors import SecondBrainError
from second_brain.logging_config import get_logger

logger = get_logger(__name__)


class StaleDataError(SecondBrainError):
    """Raised when an update is attempted with a stale version."""
    pass


class ChunkNotFoundError(SecondBrainError):
    """Raised when the chunk does not exist."""
    pass


class OptimisticLockExecutor(Protocol):
    """Protocol for optimistic lock storage operations."""
    def get_chunk_version(self, chunk_id: str) -> int | None: ...
    def update_if_version_matches(
        self, chunk_id: str, expected_version: int, updates: dict[str, Any]
    ) -> bool: ...  # returns True if updated, False if version mismatch


class OptimisticLockService:
    """Provides optimistic locking for chunk updates."""

    def __init__(self, executor: OptimisticLockExecutor) -> None:
        self._executor = executor

    def update(
        self, chunk_id: str, expected_version: int, updates: dict[str, Any]
    ) -> int:
        """Update chunk with version check. Returns new version. Raises StaleDataError if stale."""
        # First check chunk exists
        current_version = self._executor.get_chunk_version(chunk_id)
        if current_version is None:
            raise ChunkNotFoundError(
                f"Chunk not found: {chunk_id}",
                code="CHUNK_NOT_FOUND",
                context={"chunk_id": chunk_id},
            )
        # Delegate version check to executor (atomic at DB layer)
        updated = self._executor.update_if_version_matches(chunk_id, expected_version, updates)
        if not updated:
            raise StaleDataError(
                f"Stale version for chunk {chunk_id}: provided {expected_version}",
                code="STALE_VERSION",
                context={"chunk_id": chunk_id, "expected_version": expected_version},
            )
        new_version = expected_version + 1
        logger.info("chunk_updated", chunk_id=chunk_id,
                    from_version=expected_version, to_version=new_version)
        return new_version