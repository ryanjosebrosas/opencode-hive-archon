"""Content-addressable deduplication for knowledge chunks."""

from __future__ import annotations

import hashlib
from typing import Any, Protocol

from pydantic import BaseModel

from second_brain.contracts.knowledge import ChunkStatusValue
from second_brain.logging_config import get_logger
from second_brain.errors import SecondBrainError

logger = get_logger(__name__)


class DeduplicationError(SecondBrainError):
    """Deduplication operation failure."""
    pass


class ChunkRecord(BaseModel):
    """Minimal chunk representation for dedup operations."""
    id: str
    content_hash: str
    status: ChunkStatusValue
    metadata: dict[str, Any] = {}


class DeduplicationResult(BaseModel):
    content_hash: str
    chunk_id: str
    is_duplicate: bool           # True if content_hash already existed
    existing_chunk_id: str | None = None  # id of the existing chunk when is_duplicate=True
    metadata_updated: bool = False


class ChunkDeduplicator(Protocol):
    """Protocol for chunk dedup storage operations."""
    def find_by_content_hash(self, content_hash: str) -> ChunkRecord | None: ...
    def insert_chunk(self, content: str, content_hash: str, metadata: dict[str, Any]) -> str: ...
    def update_metadata(self, chunk_id: str, metadata: dict[str, Any]) -> None: ...
    def mark_superseded(self, chunk_id: str) -> None: ...


class DeduplicationService:
    """Deduplicates chunks by SHA-256 hash of content."""

    def __init__(self, deduplicator: ChunkDeduplicator) -> None:
        self._deduplicator = deduplicator

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hex digest of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def upsert_chunk(self, content: str, metadata: dict[str, Any]) -> DeduplicationResult:
        """Insert or update chunk. Duplicate = update metadata, no new row."""
        content_hash = self.compute_hash(content)
        existing = self._deduplicator.find_by_content_hash(content_hash)

        if existing is not None:
            self._deduplicator.update_metadata(existing.id, metadata)
            logger.info("chunk_deduplicated", content_hash=content_hash, chunk_id=existing.id)
            return DeduplicationResult(
                content_hash=content_hash,
                chunk_id=existing.id,
                is_duplicate=True,
                existing_chunk_id=existing.id,
                metadata_updated=True,
            )

        # Attempt insert — may race with concurrent writer on unique constraint
        try:
            chunk_id = self._deduplicator.insert_chunk(content, content_hash, metadata)
            logger.info("chunk_inserted", content_hash=content_hash, chunk_id=chunk_id)
            return DeduplicationResult(
                content_hash=content_hash,
                chunk_id=chunk_id,
                is_duplicate=False,
            )
        except Exception:
            # Concurrent writer won the race — treat as duplicate
            race_existing = self._deduplicator.find_by_content_hash(content_hash)
            if race_existing is not None:
                self._deduplicator.update_metadata(race_existing.id, metadata)
                logger.info("chunk_deduplicated_race", content_hash=content_hash, chunk_id=race_existing.id)
                return DeduplicationResult(
                    content_hash=content_hash,
                    chunk_id=race_existing.id,
                    is_duplicate=True,
                    existing_chunk_id=race_existing.id,
                    metadata_updated=True,
                )
            raise DeduplicationError(
                "Insert failed and chunk not found after race",
                context={"content_hash": content_hash},
            )

    def supersede_chunk(self, chunk_id: str) -> None:
        """Mark a chunk as superseded (replaced by newer content at same location)."""
        self._deduplicator.mark_superseded(chunk_id)
        logger.info("chunk_superseded", chunk_id=chunk_id)