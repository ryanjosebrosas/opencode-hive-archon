"""Migration runner with dry-run, rollback, and advisory lock support."""

from __future__ import annotations

import time
from typing import Protocol

from pydantic import BaseModel

from second_brain.errors import SchemaError
from second_brain.logging_config import get_logger
from second_brain.services.schema_manager import MigrationInfo, MigrationRecord, SchemaManager

logger = get_logger(__name__)

MIGRATION_LOCK_KEY = 728349261


class MigrationExecutor(Protocol):
    """Abstract interface for database migration execution."""

    def execute_sql(self, sql: str) -> None: ...
    def get_applied_migrations(self) -> list[MigrationRecord]: ...
    def record_migration(self, info: MigrationInfo, execution_time_ms: int) -> None: ...
    def remove_migration_record(self, version: int) -> None: ...
    def acquire_advisory_lock(self, lock_key: int) -> bool: ...
    def release_advisory_lock(self, lock_key: int) -> None: ...


class MigrationResult(BaseModel):
    """Result of a migration operation."""
    success: bool
    applied: list[MigrationInfo] = []
    rolled_back: list[MigrationInfo] = []
    dry_run: bool = False
    error: str | None = None
    pending_count: int = 0


class MigrationRunner:
    """Runs database migrations with safety features."""

    def __init__(self, schema_manager: SchemaManager, executor: MigrationExecutor) -> None:
        self.schema_manager = schema_manager
        self.executor = executor

    def get_pending(self, applied: list[MigrationRecord]) -> list[MigrationInfo]:
        """Return pending migrations in version order."""
        applied_versions = {r.version for r in applied}
        expected = self.schema_manager.scan_migrations()
        return [m for m in expected if m.version not in applied_versions]

    def apply_pending(self, dry_run: bool = False) -> MigrationResult:
        """Apply all pending migrations in order.
        
        1. Acquire advisory lock
        2. Get applied migrations from DB
        3. Check for schema drift (abort if critical drift)
        4. Compute pending migrations
        5. For each pending: read SQL, execute, record
        6. Release lock
        """
        if dry_run:
            return self._dry_run()

        lock_acquired = False
        try:
            lock_acquired = self.executor.acquire_advisory_lock(MIGRATION_LOCK_KEY)
            if not lock_acquired:
                return MigrationResult(
                    success=False,
                    error="Could not acquire migration lock. Another migration may be running.",
                )

            applied = self.executor.get_applied_migrations()
            
            self.schema_manager.validate_schema_integrity(applied)
            
            pending = self.get_pending(applied)
            if not pending:
                logger.info("no_pending_migrations")
                return MigrationResult(success=True, pending_count=0)

            applied_list: list[MigrationInfo] = []
            for migration in pending:
                filepath = self.schema_manager.migrations_dir / migration.filename
                sql = filepath.read_text(encoding="utf-8")
                
                forward_sql = self._extract_forward_sql(sql)
                
                started = time.monotonic()
                try:
                    self.executor.execute_sql(forward_sql)
                except Exception as exc:
                    return MigrationResult(
                        success=False,
                        applied=applied_list,
                        error=f"Migration {migration.filename} failed: {exc}",
                        pending_count=len(pending) - len(applied_list),
                    )
                
                elapsed_ms = int((time.monotonic() - started) * 1000)
                self.executor.record_migration(migration, elapsed_ms)
                applied_list.append(migration)
                logger.info("migration_applied", filename=migration.filename, version=migration.version, time_ms=elapsed_ms)

            return MigrationResult(
                success=True,
                applied=applied_list,
                pending_count=0,
            )
        finally:
            if lock_acquired:
                self.executor.release_advisory_lock(MIGRATION_LOCK_KEY)

    def rollback_last(self) -> MigrationResult:
        """Rollback the last applied migration."""
        lock_acquired = False
        try:
            lock_acquired = self.executor.acquire_advisory_lock(MIGRATION_LOCK_KEY)
            if not lock_acquired:
                return MigrationResult(
                    success=False,
                    error="Could not acquire migration lock for rollback.",
                )

            applied = self.executor.get_applied_migrations()
            if not applied:
                raise SchemaError(
                    "No applied migrations to rollback",
                    code="NO_MIGRATIONS",
                )

            last = max(applied, key=lambda r: r.version)
            
            expected = self.schema_manager.scan_migrations()
            migration_info = next(
                (m for m in expected if m.version == last.version), None
            )
            if migration_info is None:
                raise SchemaError(
                    f"Migration file for version {last.version} not found",
                    code="MIGRATION_FILE_NOT_FOUND",
                    context={"version": last.version, "filename": last.filename},
                )

            filepath = self.schema_manager.migrations_dir / migration_info.filename
            sql = filepath.read_text(encoding="utf-8")
            rollback_sql = self._extract_rollback_sql(sql)
            
            if not rollback_sql:
                raise SchemaError(
                    f"No rollback section found in {migration_info.filename}",
                    code="NO_ROLLBACK_SQL",
                    context={"filename": migration_info.filename},
                )

            self.executor.execute_sql(rollback_sql)
            self.executor.remove_migration_record(last.version)
            
            logger.info("migration_rolled_back", filename=migration_info.filename, version=migration_info.version)
            
            return MigrationResult(
                success=True,
                rolled_back=[migration_info],
            )
        finally:
            if lock_acquired:
                self.executor.release_advisory_lock(MIGRATION_LOCK_KEY)

    def _dry_run(self) -> MigrationResult:
        """Report pending migrations without executing."""
        applied = self.executor.get_applied_migrations()
        pending = self.get_pending(applied)
        
        for migration in pending:
            logger.info("dry_run_would_apply", filename=migration.filename, version=migration.version)
        
        return MigrationResult(
            success=True,
            applied=pending,
            dry_run=True,
            pending_count=len(pending),
        )

    @staticmethod
    def _extract_forward_sql(sql: str) -> str:
        """Extract forward migration SQL (everything before '-- rollback:')."""
        marker = "-- rollback:"
        idx = sql.lower().find(marker.lower())
        if idx == -1:
            return sql
        return sql[:idx].rstrip()

    @staticmethod
    def _extract_rollback_sql(sql: str) -> str | None:
        """Extract rollback SQL (everything after '-- rollback:')."""
        marker = "-- rollback:"
        idx = sql.lower().find(marker.lower())
        if idx == -1:
            return None
        rollback = sql[idx + len(marker):].strip()
        lines = [line.strip() for line in rollback.split("\n") if line.strip() and not line.strip().startswith("--")]
        if not lines:
            return None
        return rollback
