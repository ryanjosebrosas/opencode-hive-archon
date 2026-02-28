from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from typing_extensions import Protocol

from ..logging_config import get_logger
from ..errors import SecondBrainError


logger = get_logger(__name__)


class ConcurrentWriteError(SecondBrainError):
    """Custom error raised during concurrent write operations."""
    pass


class ChunkUpsertData(BaseModel):
    content_hash: str          # unique key for dedup/conflict detection
    content: str
    metadata: dict[str, Any] = {}
    updated_at: datetime       # used for last-write-wins comparison
    job_id: str                # ingestion job identifier for audit trail


class UpsertResult(BaseModel):
    content_hash: str
    was_conflict: bool         # True if row already existed
    conflict_resolved: bool    # True if last-write-wins applied (our update won)
    previous_updated_at: datetime | None = None  # only set if was_conflict=True
    previous_job_id: str | None = None  # only set if was_conflict=True
    job_id: str


class ConflictAuditEntry(BaseModel):
    content_hash: str
    winner_job_id: str
    loser_job_id: str
    winner_updated_at: datetime
    loser_updated_at: datetime
    resolved_at: datetime


class ChunkWriteExecutor(Protocol):
    def upsert_chunk(self, data: ChunkUpsertData) -> UpsertResult:
        ...
    
    def log_conflict(self, entry: ConflictAuditEntry) -> None:
        ...
    
    def get_conflict_log(self) -> list[ConflictAuditEntry]:
        ...





class ChunkWriteManager:
    def __init__(self, executor: ChunkWriteExecutor) -> None:
        self._executor = executor

    def write_chunk(self, data: ChunkUpsertData) -> UpsertResult:
        """Upsert chunk with last-write-wins conflict resolution and audit trail."""
        result = self._executor.upsert_chunk(data)
        
        if result.was_conflict and result.conflict_resolved and result.previous_job_id and result.previous_updated_at:
            # We won — log the previous as loser
            entry = ConflictAuditEntry(
                content_hash=result.content_hash,
                winner_job_id=data.job_id,
                loser_job_id=result.previous_job_id,
                winner_updated_at=data.updated_at,
                loser_updated_at=result.previous_updated_at,
                resolved_at=datetime.now(ZoneInfo('UTC')),
            )
            self._executor.log_conflict(entry)
        elif result.was_conflict and not result.conflict_resolved and result.previous_job_id and result.previous_updated_at:
            # We lost — log us as loser
            entry = ConflictAuditEntry(
                content_hash=result.content_hash,
                winner_job_id=result.previous_job_id,
                loser_job_id=data.job_id,
                winner_updated_at=result.previous_updated_at,
                loser_updated_at=data.updated_at,
                resolved_at=datetime.now(ZoneInfo('UTC')),
            )
            self._executor.log_conflict(entry)
        
        return result
    
    def get_audit_log(self) -> list[ConflictAuditEntry]:
        return self._executor.get_conflict_log()