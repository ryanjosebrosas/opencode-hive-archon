"""Chunk status lifecycle management with enforced state transitions."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from second_brain.contracts.knowledge import ChunkStatusValue
from second_brain.errors import SecondBrainError
from second_brain.logging_config import get_logger

logger = get_logger(__name__)

# Valid transitions: (from_status, to_status)
_VALID_TRANSITIONS: frozenset[tuple[ChunkStatusValue, ChunkStatusValue]] = frozenset({
    ("active", "superseded"),
    ("active", "archived"),
    ("active", "deleted"),
    ("superseded", "deleted"),
    ("archived", "active"),
    ("archived", "deleted"),
    ("deleted", "active"),
})


class ChunkLifecycleError(SecondBrainError):
    """Invalid chunk status transition."""
    pass


class ChunkStatusRecord(BaseModel):
    """Minimal chunk record for lifecycle operations."""
    id: str
    status: ChunkStatusValue


class ChunkLifecycleExecutor(Protocol):
    """Protocol for chunk lifecycle storage operations."""
    def get_chunk_status(self, chunk_id: str) -> ChunkStatusRecord | None: ...
    def update_chunk_status(self, chunk_id: str, new_status: ChunkStatusValue) -> None: ...
    def get_active_chunks(self) -> list[ChunkStatusRecord]: ...


class ChunkLifecycleService:
    """Enforces valid chunk status transitions."""

    def __init__(self, executor: ChunkLifecycleExecutor) -> None:
        self._executor = executor

    def transition(self, chunk_id: str, new_status: ChunkStatusValue) -> None:
        """Transition chunk to new status. Raises if invalid."""
        record = self._executor.get_chunk_status(chunk_id)
        if record is None:
            raise ChunkLifecycleError(
                f"Chunk not found: {chunk_id}",
                code="CHUNK_NOT_FOUND",
                context={"chunk_id": chunk_id},
            )
        from_status = record.status
        if from_status == new_status:
            raise ChunkLifecycleError(
                f"Chunk already has status: {new_status}",
                code="NO_OP_TRANSITION",
                context={"chunk_id": chunk_id, "status": from_status},
            )
        if (from_status, new_status) not in _VALID_TRANSITIONS:
            raise ChunkLifecycleError(
                f"Invalid transition: {from_status} → {new_status}",
                code="INVALID_TRANSITION",
                context={"chunk_id": chunk_id, "from": from_status, "to": new_status},
            )
        self._executor.update_chunk_status(chunk_id, new_status)
        logger.info("chunk_status_transitioned",
                    chunk_id=chunk_id, from_status=from_status, to_status=new_status)

    def archive(self, chunk_id: str) -> None:
        self.transition(chunk_id, "archived")

    def delete(self, chunk_id: str) -> None:
        self.transition(chunk_id, "deleted")

    def restore(self, chunk_id: str) -> None:
        self.transition(chunk_id, "active")

    def supersede(self, chunk_id: str) -> None:
        self.transition(chunk_id, "superseded")

    def get_active_chunks(self) -> list[ChunkStatusRecord]:
        """Return only active chunks (search-eligible)."""
        return self._executor.get_active_chunks()