"""Test chunk lifecycle transitions and status management."""

import pytest

from second_brain.contracts.knowledge import ChunkStatusValue
from second_brain.services.lifecycle import (
    ChunkLifecycleError, ChunkLifecycleService, 
    ChunkStatusRecord
)


def _assert_error_has_code(error: Exception, expected_code: str) -> None:
    assert hasattr(error, "code"), f"Expected error to have 'code' attribute. Got: {error}"
    assert error.code == expected_code, f"Expected code '{expected_code}', got '{error.code}'"


class MockChunkLifecycleExecutor:
    def __init__(self) -> None:
        self._store: dict[str, ChunkStatusRecord] = {}

    def seed(self, chunk_id: str, status: ChunkStatusValue) -> None:
        self._store[chunk_id] = ChunkStatusRecord(id=chunk_id, status=status)

    def get_chunk_status(self, chunk_id: str) -> ChunkStatusRecord | None:
        return self._store.get(chunk_id)

    def update_chunk_status(self, chunk_id: str, new_status: ChunkStatusValue) -> None:
        if chunk_id in self._store:
            self._store[chunk_id] = ChunkStatusRecord(id=chunk_id, status=new_status)

    def get_active_chunks(self) -> list[ChunkStatusRecord]:
        return [r for r in self._store.values() if r.status == "active"]


class TestChunkLifecycleService:
    def _make_service(self, executor: MockChunkLifecycleExecutor | None = None) -> ChunkLifecycleService:
        if executor is None:
            executor = MockChunkLifecycleExecutor()
        return ChunkLifecycleService(executor=executor)

    def test_transition_active_to_superseded(self) -> None:
        """Valid transition: active to superseded."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "active")
        service = self._make_service(executor)

        service.transition("chunk_1", "superseded")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "superseded"

    def test_transition_active_to_archived(self) -> None:
        """Valid transition: active to archived."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "active")
        service = self._make_service(executor)

        service.transition("chunk_1", "archived")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "archived"

    def test_transition_active_to_deleted(self) -> None:
        """Valid transition: active to deleted."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "active")
        service = self._make_service(executor)

        service.transition("chunk_1", "deleted")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "deleted"

    def test_transition_archived_to_active(self) -> None:
        """Valid transition: archived to active."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "archived")
        service = self._make_service(executor)

        service.transition("chunk_1", "active")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "active"

    def test_transition_archived_to_deleted(self) -> None:
        """Valid transition: archived to deleted."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "archived")
        service = self._make_service(executor)

        service.transition("chunk_1", "deleted")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "deleted"

    def test_transition_deleted_to_active(self) -> None:
        """Valid transition: deleted to active."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "deleted")
        service = self._make_service(executor)

        service.transition("chunk_1", "active")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "active"

    def test_transition_superseded_to_deleted(self) -> None:
        """Valid transition: superseded to deleted."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "superseded")
        service = self._make_service(executor)

        service.transition("chunk_1", "deleted")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "deleted"

    def test_transition_superseded_to_active_raises(self) -> None:
        """Invalid transition: superseded to active raises error."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "superseded")
        service = self._make_service(executor)

        with pytest.raises(ChunkLifecycleError) as exc_info:
            service.transition("chunk_1", "active")
        
        assert "Invalid transition: superseded → active" in str(exc_info.value)
        _assert_error_has_code(exc_info.value, "INVALID_TRANSITION")

    def test_transition_superseded_to_archived_raises(self) -> None:
        """Invalid transition: superseded to archived raises error."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "superseded")
        service = self._make_service(executor)

        with pytest.raises(ChunkLifecycleError) as exc_info:
            service.transition("chunk_1", "archived")
        
        assert "Invalid transition: superseded → archived" in str(exc_info.value)
        _assert_error_has_code(exc_info.value, "INVALID_TRANSITION")

    def test_transition_deleted_to_superseded_raises(self) -> None:
        """Invalid transition: deleted to superseded raises error."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "deleted")
        service = self._make_service(executor)

        with pytest.raises(ChunkLifecycleError) as exc_info:
            service.transition("chunk_1", "superseded")
        
        assert "Invalid transition: deleted → superseded" in str(exc_info.value)
        _assert_error_has_code(exc_info.value, "INVALID_TRANSITION")

    def test_transition_deleted_to_archived_raises(self) -> None:
        """Invalid transition: deleted to archived raises error."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "deleted")
        service = self._make_service(executor)

        with pytest.raises(ChunkLifecycleError) as exc_info:
            service.transition("chunk_1", "archived")
        
        assert "Invalid transition: deleted → archived" in str(exc_info.value)
        _assert_error_has_code(exc_info.value, "INVALID_TRANSITION")

    def test_same_status_transition_raises(self) -> None:
        """Same status transition raises error."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "active")
        service = self._make_service(executor)

        with pytest.raises(ChunkLifecycleError) as exc_info:
            service.transition("chunk_1", "active")
        
        assert "Chunk already has status: active" in str(exc_info.value)
        _assert_error_has_code(exc_info.value, "NO_OP_TRANSITION")

    def test_chunk_not_found_raises(self) -> None:
        """Missing chunk raises error with code CHUNK_NOT_FOUND."""
        executor = MockChunkLifecycleExecutor()
        service = self._make_service(executor)

        with pytest.raises(ChunkLifecycleError) as exc_info:
            service.transition("nonexistent", "active")
        
        assert "Chunk not found: nonexistent" in str(exc_info.value)
        _assert_error_has_code(exc_info.value, "CHUNK_NOT_FOUND")

    def test_get_active_chunks_excludes_non_active(self) -> None:
        """Only active chunks returned by get_active_chunks."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("active_1", "active")
        executor.seed("archived_1", "archived")
        executor.seed("superseded_1", "superseded")
        executor.seed("deleted_1", "deleted")
        executor.seed("active_2", "active")
        service = self._make_service(executor)

        active_chunks = service.get_active_chunks()
        active_ids = {chunk.id for chunk in active_chunks}
        
        assert active_ids == {"active_1", "active_2"}
        # Check the actual statuses match too
        for chunk in active_chunks:
            assert chunk.status == "active"

    def test_convenience_methods_archive_delete_restore(self) -> None:
        """Convenience methods archive, delete, restore work."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("test_chunk", "active")
        service = self._make_service(executor)

        # Archive chunk
        service.archive("test_chunk")
        record = executor.get_chunk_status("test_chunk")
        assert record is not None and record.status == "archived"

        # Restore chunk
        service.restore("test_chunk")
        record = executor.get_chunk_status("test_chunk")
        assert record is not None and record.status == "active"

        # Delete chunk
        service.delete("test_chunk")
        record = executor.get_chunk_status("test_chunk")
        assert record is not None and record.status == "deleted"

    def test_supersede_convenience_method(self) -> None:
        """Supersede convenience method works."""
        executor = MockChunkLifecycleExecutor()
        executor.seed("chunk_1", "active")
        service = self._make_service(executor)

        service.supersede("chunk_1")
        record = executor.get_chunk_status("chunk_1")
        assert record is not None
        assert record.status == "superseded"