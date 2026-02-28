from __future__ import annotations

import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

from second_brain.services.concurrent_writes import (
    ChunkUpsertData,
    ChunkWriteManager,
    ConflictAuditEntry,
    UpsertResult,
)


class MockChunkWriteExecutor:
    """Thread-safe mock that simulates last-write-wins upsert."""
    
    def __init__(self) -> None:
        self._store: dict[str, ChunkUpsertData] = {}
        self._lock = threading.Lock()
        self._conflict_log: list[ConflictAuditEntry] = []
    
    def upsert_chunk(self, data: ChunkUpsertData) -> UpsertResult:
        with self._lock:
            existing = self._store.get(data.content_hash)
            if existing is None:
                self._store[data.content_hash] = data
                return UpsertResult(
                    content_hash=data.content_hash,
                    was_conflict=False,
                    conflict_resolved=False,
                    job_id=data.job_id,
                )
            # Conflict: last-write-wins by updated_at
            if data.updated_at > existing.updated_at:
                # We win — update
                previous = existing
                self._store[data.content_hash] = data
                return UpsertResult(
                    content_hash=data.content_hash,
                    was_conflict=True,
                    conflict_resolved=True,  # our write won
                    previous_updated_at=previous.updated_at,
                    previous_job_id=previous.job_id,
                    job_id=data.job_id,
                )
            else:
                # We lose — skip
                return UpsertResult(
                    content_hash=data.content_hash,
                    was_conflict=True,
                    conflict_resolved=False,  # existing write won
                    previous_updated_at=existing.updated_at,
                    previous_job_id=existing.job_id,
                    job_id=data.job_id,
                )
    
    def log_conflict(self, entry: ConflictAuditEntry) -> None:
        with self._lock:
            self._conflict_log.append(entry)
    
    def get_conflict_log(self) -> list[ConflictAuditEntry]:
        with self._lock:
            return list(self._conflict_log)


def test_write_chunk_no_conflict():
    """Test that first write works with no conflict."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    chunk_data = ChunkUpsertData(
        content_hash="hash1",
        content="content1",
        metadata={},
        updated_at=datetime.now(ZoneInfo('UTC')),
        job_id="job1"
    )
    
    result = manager.write_chunk(chunk_data)
    
    assert not result.was_conflict
    assert not result.conflict_resolved
    assert result.content_hash == "hash1"
    
    # Check that the chunk was stored
    assert len(executor._store) == 1
    assert "hash1" in executor._store
    assert executor._store["hash1"].content == "content1"


def test_write_chunk_returns_upsert_result():
    """Test that write_chunk returns proper UpsertResult."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    chunk_data = ChunkUpsertData(
        content_hash="hash1",
        content="content1",
        metadata={},
        updated_at=datetime.now(ZoneInfo('UTC')),
        job_id="job1"
    )
    
    result = manager.write_chunk(chunk_data)
    
    assert isinstance(result, UpsertResult)
    assert result.content_hash == "hash1"
    assert result.job_id == "job1"
    assert hasattr(result, 'was_conflict')
    assert hasattr(result, 'conflict_resolved')


def test_conflict_newer_wins():
    """Test that chunk with newer timestamp wins in conflict."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Insert first chunk with older timestamp
    chunk_data_old = ChunkUpsertData(
        content_hash="same_hash",
        content="content_old",
        metadata={},
        updated_at=datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC')),
        job_id="job_old"
    )
    
    manager.write_chunk(chunk_data_old)
    
    # Insert second chunk with newer timestamp
    chunk_data_new = ChunkUpsertData(
        content_hash="same_hash",
        content="content_new",
        metadata={},
        updated_at=datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC')),  # later time
        job_id="job_new"
    )
    
    result = manager.write_chunk(chunk_data_new)
    
    # Newer chunk should win
    assert result.was_conflict
    assert result.conflict_resolved
    assert result.previous_updated_at == datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC'))
    assert result.previous_job_id == "job_old"
    
    # Verify stored content is the newer one
    assert executor._store["same_hash"].content == "content_new"
    assert executor._store["same_hash"].job_id == "job_new"


def test_conflict_older_loses():
    """Test that chunk with older timestamp loses in conflict."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Insert first chunk with newer timestamp
    chunk_data_new = ChunkUpsertData(
        content_hash="same_hash",
        content="content_new",
        metadata={},
        updated_at=datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC')),
        job_id="job_new"
    )
    
    manager.write_chunk(chunk_data_new)
    
    # Try to insert second chunk with older timestamp
    chunk_data_old = ChunkUpsertData(
        content_hash="same_hash",
        content="content_old",
        metadata={},
        updated_at=datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC')),  # earlier time
        job_id="job_old"
    )
    
    result = manager.write_chunk(chunk_data_old)
    
    # Older chunk should lose
    assert result.was_conflict
    assert not result.conflict_resolved  # existing write won
    assert result.previous_updated_at == datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC'))
    assert result.previous_job_id == "job_new"
    
    # Verify stored content is still the newer one
    assert executor._store["same_hash"].content == "content_new"
    assert executor._store["same_hash"].job_id == "job_new"


def test_conflict_logged_when_newer_wins():
    """Test that conflict audit log entry is created when newer chunk wins."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Insert first chunk
    chunk_data_old = ChunkUpsertData(
        content_hash="same_hash",
        content="content_old",
        metadata={},
        updated_at=datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC')),
        job_id="job_old"
    )
    
    manager.write_chunk(chunk_data_old)
    
    # Insert newer chunk (should win)
    chunk_data_new = ChunkUpsertData(
        content_hash="same_hash",
        content="content_new",
        metadata={},
        updated_at=datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC')),
        job_id="job_new"
    )
    
    manager.write_chunk(chunk_data_new)
    
    # Check that conflict audit was logged
    audit_log = manager.get_audit_log()
    assert len(audit_log) == 1
    
    entry = audit_log[0]
    assert entry.content_hash == "same_hash"
    assert entry.winner_job_id == "job_new"
    assert entry.loser_job_id == "job_old"
    assert entry.winner_updated_at == datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC'))
    assert entry.loser_updated_at == datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC'))


def test_conflict_logged_when_older_loses():
    """Test that conflict audit log entry is created when older chunk loses."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Insert newer first
    chunk_data_new = ChunkUpsertData(
        content_hash="same_hash",
        content="content_new",
        metadata={},
        updated_at=datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC')),
        job_id="job_new"
    )
    
    manager.write_chunk(chunk_data_new)
    
    # Try older chunk (should lose)
    chunk_data_old = ChunkUpsertData(
        content_hash="same_hash",
        content="content_old",
        metadata={},
        updated_at=datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC')),
        job_id="job_old"
    )
    
    manager.write_chunk(chunk_data_old)
    
    # Check that conflict audit was logged (from losing perspective)
    audit_log = manager.get_audit_log()
    assert len(audit_log) == 1
    
    entry = audit_log[0]
    assert entry.content_hash == "same_hash"
    assert entry.winner_job_id == "job_new"
    assert entry.loser_job_id == "job_old"
    assert entry.winner_updated_at == datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC'))
    assert entry.loser_updated_at == datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC'))


def test_audit_log_empty_on_no_conflicts():
    """Test that audit log stays empty when there are no conflicts."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    chunk_data = ChunkUpsertData(
        content_hash="hash1",
        content="content1",
        metadata={},
        updated_at=datetime.now(ZoneInfo('UTC')),
        job_id="job1"
    )
    
    manager.write_chunk(chunk_data)
    
    audit_log = manager.get_audit_log()
    assert len(audit_log) == 0


def test_audit_log_has_timestamps():
    """Test that audit log entries have proper timestamps."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Create a conflict scenario
    chunk_data1 = ChunkUpsertData(
        content_hash="hash",
        content="content1",
        metadata={},
        updated_at=datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC')),
        job_id="job1"
    )
    
    manager.write_chunk(chunk_data1)
    
    chunk_data2 = ChunkUpsertData(
        content_hash="hash",
        content="content2", 
        metadata={},
        updated_at=datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC')),
        job_id="job2"
    )
    
    manager.write_chunk(chunk_data2)
    
    audit_log = manager.get_audit_log()
    assert len(audit_log) == 1
    
    entry = audit_log[0]
    assert isinstance(entry.resolved_at, datetime)
    # Verify that the timestamp is indeed a timezone-aware UTC datetime
    assert entry.resolved_at.tzinfo is not None
    # Compare against a known UTC time to ensure the zoneinfo works correctly
    utc_example = datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC'))
    assert str(entry.resolved_at.tzinfo) == str(utc_example.tzinfo)


def test_two_jobs_same_chunk_concurrent():
    """Test two threads writing same chunk, ensure exactly one wins."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Prepare two chunk data objects with slightly different timestamps
    chunk_data_early = ChunkUpsertData(
        content_hash="same_hash",
        content="content_early",
        metadata={},
        updated_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=ZoneInfo('UTC')),
        job_id="job_early"
    )
    
    chunk_data_late = ChunkUpsertData(
        content_hash="same_hash",
        content="content_late",
        metadata={},
        updated_at=datetime(2023, 1, 1, 0, 0, 1, tzinfo=ZoneInfo('UTC')),  # slight advantage
        job_id="job_late"
    )
    
    results = []
    def worker(chunk_data):
        result = manager.write_chunk(chunk_data)
        results.append(result)
    
    # Run both writes concurrently
    with ThreadPoolExecutor(max_workers=2) as executor_pool:
        futures = [
            executor_pool.submit(worker, chunk_data_early),
            executor_pool.submit(worker, chunk_data_late),
        ]
        for future in futures:
            future.result()  # wait for completion
    
    # Verify exactly one result shows conflict_resolved=True and one shows False
    resolved_results = [r for r in results if r.conflict_resolved]
    non_resolved_results = [r for r in results if not r.conflict_resolved]
    
    assert len(resolved_results) == 1
    assert len(non_resolved_results) == 1
    
    # Verify the later timestamp wins
    assert executor._store["same_hash"].content == "content_late"
    
    # Verify audit log has one entry
    audit_log = manager.get_audit_log()
    assert len(audit_log) == 1
    

def test_ten_jobs_same_chunk_concurrent():
    """Test 10 threads writing same chunk with staggered timestamps."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    results = []
    timestamps_and_ids = [(datetime(2023, 1, 1, 0, 0, i, tzinfo=ZoneInfo('UTC')), f"job_{i}") for i in range(10)]
    
    def worker(data_tuple):
        ts, job_id = data_tuple
        chunk_data = ChunkUpsertData(
            content_hash="same_hash",
            content=f"content_{job_id}",
            metadata={},
            updated_at=ts,
            job_id=job_id
        )
        result = manager.write_chunk(chunk_data)
        results.append(result)
    
    # Run all 10 writers concurrently
    with ThreadPoolExecutor(max_workers=10) as executor_pool:
        futures = [
            executor_pool.submit(worker, data_tuple)
            for data_tuple in timestamps_and_ids
        ]
        for future in futures:
            future.result()  # wait for completion
    
    # The latest timestamp (job_9) should win
    assert executor._store["same_hash"].content == "content_job_9"
    
    # Should have 9 conflict audit entries (since one job initiated the conflictless insert)
    audit_log = manager.get_audit_log()
    
    # Filter out the initial no-conflict insert, then we should have 9 conflicts
    conflictful_results = [r for r in results if r.was_conflict]
    assert len(conflictful_results) == 9
    assert len(audit_log) == 9
    
    # All entries should be for the same content_hash
    for entry in audit_log:
        assert entry.content_hash == "same_hash"


def test_independent_chunks_no_conflicts():
    """Test multiple threads writing different chunks - no conflicts."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    results = []
    
    def worker(i):
        chunk_data = ChunkUpsertData(
            content_hash=f"hash_{i}",
            content=f"content_{i}",
            metadata={"index": i},
            updated_at=datetime.now(ZoneInfo('UTC')),
            job_id=f"job_{i}"
        )
        result = manager.write_chunk(chunk_data)
        results.append(result)
    
    # Run 10 writers for different chunks
    with ThreadPoolExecutor(max_workers=10) as executor_pool:
        futures = [executor_pool.submit(worker, i) for i in range(10)]
        for future in futures:
            future.result()  # wait for completion
    
    # No conflicts should occur
    conflictful_results = [r for r in results if r.was_conflict]
    assert len(conflictful_results) == 0
    
    # All 10 chunks should be stored
    assert len(executor._store) == 10
    for i in range(10):
        assert f"hash_{i}" in executor._store
    
    # No audit log entries
    audit_log = manager.get_audit_log()
    assert len(audit_log) == 0


def test_get_audit_log_returns_copy():
    """Test that audit log manipulation doesn't affect internal log."""
    executor = MockChunkWriteExecutor()
    manager = ChunkWriteManager(executor)
    
    # Create one conflict to get an audit entry
    chunk_data1 = ChunkUpsertData(
        content_hash="hash",
        content="content1",
        metadata={},
        updated_at=datetime(2023, 1, 1, tzinfo=ZoneInfo('UTC')),
        job_id="job1"
    )
    
    manager.write_chunk(chunk_data1)
    
    chunk_data2 = ChunkUpsertData(
        content_hash="hash",
        content="content2",
        metadata={},
        updated_at=datetime(2023, 1, 2, tzinfo=ZoneInfo('UTC')),
        job_id="job2"
    )
    
    manager.write_chunk(chunk_data2)
    
    # Get the original audit log
    original_log = manager.get_audit_log()
    assert len(original_log) == 1
    
    # Modify the returned list
    original_log.clear()
    assert len(original_log) == 0
    
    # Internal log should remain unchanged
    internal_log = manager.get_audit_log()
    assert len(internal_log) == 1
    assert internal_log[0].winner_job_id == "job2"