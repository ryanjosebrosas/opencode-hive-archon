"""Tests for content-addressable deduplication logic."""

from __future__ import annotations

import hashlib
from typing import Any

from second_brain.services.dedup import (
    DeduplicationService,
    ChunkRecord,
)


class MockChunkDeduplicator:
    """Test double that satisfies ChunkDeduplicator protocol."""

    def __init__(self) -> None:
        # Two indexes: by hash for finding content duplicates, by ID for updating
        self.chunks_by_hash: dict[str, ChunkRecord] = {}
        self.chunks_by_id: dict[str, ChunkRecord] = {}
        self.metadata_updates: dict[str, dict[str, Any]] = {}
        self.superseded_ids: list[str] = []
        self.fail_on_insert: bool = False  # added for race condition testing

    def find_by_content_hash(self, content_hash: str) -> ChunkRecord | None:
        return self.chunks_by_hash.get(content_hash)

    def insert_chunk(self, content: str, content_hash: str, metadata: dict[str, Any]) -> str:
        if self.fail_on_insert:
            raise RuntimeError("simulated unique violation") 
        chunk_id = f"chunk-{len(self.chunks_by_hash)}"
        record = ChunkRecord(id=chunk_id, content_hash=content_hash, status="active", metadata=metadata.copy())
        self.chunks_by_hash[content_hash] = record
        self.chunks_by_id[chunk_id] = record
        return chunk_id

    def update_metadata(self, chunk_id: str, metadata: dict[str, Any]) -> None:
        if chunk_id in self.chunks_by_id:
            # Update record in the hash index
            old_record = self.chunks_by_id[chunk_id]
            updated_record = ChunkRecord(
                id=old_record.id,
                content_hash=old_record.content_hash,
                status=old_record.status,
                metadata=metadata.copy()
            )
            
            # Update both indexes
            self.chunks_by_id[chunk_id] = updated_record
            # Find and update the corresponding hash-keyed record
            for hash_key, rec in self.chunks_by_hash.items():
                if rec.id == chunk_id:
                    self.chunks_by_hash[hash_key] = updated_record
                    break
        self.metadata_updates[chunk_id] = metadata.copy()

    def mark_superseded(self, chunk_id: str) -> None:
        if chunk_id in self.chunks_by_id:
            old_record = self.chunks_by_id[chunk_id]
            updated_record = ChunkRecord(
                id=old_record.id,
                content_hash=old_record.content_hash,
                status="superseded",  # Update status to superseded
                metadata=old_record.metadata.copy()
            )
            
            # Update both indexes
            self.chunks_by_id[chunk_id] = updated_record
            # Find and update the corresponding hash-keyed record
            for hash_key, rec in self.chunks_by_hash.items():
                if rec.id == chunk_id:
                    self.chunks_by_hash[hash_key] = updated_record
                    break
        self.superseded_ids.append(chunk_id)


def test_compute_hash_is_sha256() -> None:
    """Test that DeduplicationService.compute_hash produces the same SHA-256 as hashlib.sha256."""
    content = "test content for hashing"

    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    actual_hash = DeduplicationService.compute_hash(content)

    assert actual_hash == expected_hash


def test_compute_hash_deterministic() -> None:
    """Test that same input always produces same hash."""
    content = "consistent content for testing"

    hash1 = DeduplicationService.compute_hash(content)
    hash2 = DeduplicationService.compute_hash(content)

    assert hash1 == hash2


def test_compute_hash_different_content() -> None:
    """Test that different content produces different hash."""
    content1 = "content one"
    content2 = "content two"

    hash1 = DeduplicationService.compute_hash(content1)
    hash2 = DeduplicationService.compute_hash(content2)

    assert hash1 != hash2


def test_upsert_new_chunk_returns_not_duplicate() -> None:
    """Test that first insert returns is_duplicate=False."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = "unique content"
    result = service.upsert_chunk(content, {"source": "test"})
    
    assert result.is_duplicate is False


def test_upsert_new_chunk_stored() -> None:
    """Test that after insert, find_by_content_hash can return the chunk."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = "content to store"
    metadata = {"source": "test", "category": "example"}
    
    result = service.upsert_chunk(content, metadata)
    retrieved = mock_dedup.chunks_by_hash.get(result.content_hash)
    
    assert retrieved is not None
    assert retrieved.id == result.chunk_id
    assert retrieved.content_hash == result.content_hash


def test_upsert_duplicate_returns_is_duplicate_true() -> None:
    """Test that second insert with same content returns is_duplicate=True."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = "duplicate test content"
    
    # Insert first time
    service.upsert_chunk(content, {"source": "test1"})
    
    # Insert same content second time (should be duplicate)
    result = service.upsert_chunk(content, {"source": "test2"})
    
    assert result.is_duplicate is True


def test_upsert_duplicate_updates_metadata() -> None:
    """Test that duplicate upsert updates metadata on existing row."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = "content to update"
    initial_metadata = {"source": "initial", "version": "1"}
    update_metadata = {"source": "updated", "version": "2", "extra": "data"}
    
    # Insert first with initial metadata
    first_result = service.upsert_chunk(content, initial_metadata)
    
    # Insert duplicate with updated metadata 
    service.upsert_chunk(content, update_metadata)
    
    # Check that metadata was updated
    expected_record = mock_dedup.chunks_by_hash[first_result.content_hash]
    assert expected_record.metadata == update_metadata
    

def test_upsert_duplicate_no_new_row() -> None:
    """Test that duplicate upsert keeps exactly one entry for that hash."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = "deduplicate test"
    
    # Insert first time
    first_result = service.upsert_chunk(content, {"first": "meta"})
    
    # Insert duplicate
    service.upsert_chunk(content, {"dup": "meta"})
    
    # Only one record with the content hash should exist 
    assert len([h for h in mock_dedup.chunks_by_hash.keys() if h == first_result.content_hash]) == 1
    assert len(mock_dedup.chunks_by_hash) == 1


def test_upsert_duplicate_returns_same_chunk_id() -> None:
    """Test that duplicate returns original chunk_id."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = "same content to match ids"
    
    # First insertion
    first_result = service.upsert_chunk(content, {"source": "original"})
    
    # Duplicate insertion
    second_result = service.upsert_chunk(content, {"source": "duplicate"})
    
    assert first_result.chunk_id == second_result.chunk_id


def test_supersede_chunk_marks_status() -> None:
    """Test that after supersede_chunk, chunk status is 'superseded'."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    # Simulate inserting a chunk
    content = "content that will be superseded"
    result = service.upsert_chunk(content, {"source": "test"})
    
    # Supersede it
    service.supersede_chunk(result.chunk_id)
    
    # Check that mock was called with the right parameters
    assert result.chunk_id in mock_dedup.superseded_ids


def test_independent_content_no_conflicts() -> None:
    """Test 10 different contents produce 10 different hashes, no dedup."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    contents = [f"content {i}" for i in range(10)]
    results = []
    
    for i, content in enumerate(contents):
        metadata = {"index": i}
        result = service.upsert_chunk(content, metadata)
        results.append(result)
    
    # Should have created 10 different chunks
    assert len(results) == 10
    
    # All should have unique hashes
    hash_set = {result.content_hash for result in results}
    assert len(hash_set) == 10
    
    # All should be new chunks (not duplicates)
    duplicate_results = [r for r in results if r.is_duplicate]
    assert len(duplicate_results) == 0


def test_upsert_empty_content_has_hash() -> None:
    """Test that empty string has a valid SHA-256 hash."""
    mock_dedup = MockChunkDeduplicator()
    service = DeduplicationService(mock_dedup)
    
    content = ""
    result = service.upsert_chunk(content, {"empty": True})
    
    # Should have a valid hash (SHA-256 of empty string)
    expected_empty_hash = hashlib.sha256(b"").hexdigest()
    assert result.content_hash == expected_empty_hash
    assert len(result.content_hash) == 64  # SHA-256 produces 64 hex chars


class RaceConditionMockChunkDeduplicator(MockChunkDeduplicator):
    """Mock for testing race conditions: first find returns None, but later finds return a value."""
    
    def __init__(self) -> None:
        super().__init__()
        self.first_find_call = True
        self.simulate_concurrent_insert = False
        self.concurrent_chunk_id = None
        self.concurrent_chunk_hash = ""
        self.concurrent_chunk_metadata = {}
        self.call_sequence = []
    
    def find_by_content_hash(self, content_hash: str) -> ChunkRecord | None:
        self.call_sequence.append(f"find:{content_hash}")
        if self.first_find_call:
            self.concurrent_chunk_hash = content_hash
            self.first_find_call = False
            return None  # Initially nothing exists (before race)
        else:
            # After insert failure - simulate that another process added it in the meantime
            if self.simulate_concurrent_insert and self.concurrent_chunk_id:
                # Return the chunk that concurrent process created
                concurrent_chunk = ChunkRecord(
                    id=self.concurrent_chunk_id, 
                    content_hash=self.concurrent_chunk_hash,
                    status="active",
                    metadata=self.concurrent_chunk_metadata
                )
                return concurrent_chunk
            return super().find_by_content_hash(content_hash)
    
    def insert_chunk(self, content: str, content_hash: str, metadata: dict[str, Any]) -> str:
        # In race condition test, we want insert to fail
        self.call_sequence.append(f"insert:{content_hash}")
        if self.simulate_concurrent_insert:
            # Simulate the concurrent chunk as if created elsewhere during the race period
            self.concurrent_chunk_id = f"concurrent-{len(self.chunks_by_hash)}"
            self.concurrent_chunk_metadata = metadata.copy()
            
            # Create the entry that was inserted "concurrently"  
            record = ChunkRecord(
                id=self.concurrent_chunk_id,
                content_hash=content_hash,
                status="active", 
                metadata=self.concurrent_chunk_metadata.copy()
            )
            
            # Update internal indexes as if it was actually added
            self.chunks_by_hash[content_hash] = record
            self.chunks_by_id[self.concurrent_chunk_id] = record
            
            # Now throw the exception to simulate constraint violation
            raise RuntimeError("simulated unique violation")
        
        return super().insert_chunk(content, content_hash, metadata)


def test_upsert_race_condition_handled() -> None:
    """If insert fails (simulated unique violation), service falls back to find-then-update."""
    executor = RaceConditionMockChunkDeduplicator()
    service = DeduplicationService(executor)
    
    content = "race content"
    # Turn on race condition simulation: first find=None, then insert fails with existing value
    executor.simulate_concurrent_insert = True
    
    result = service.upsert_chunk(content, {"new": "metadata"})
    
    assert result.is_duplicate is True
    assert result.existing_chunk_id is not None
    assert result.metadata_updated is True