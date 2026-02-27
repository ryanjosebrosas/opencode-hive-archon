"""Schema version management and drift detection service."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from second_brain.errors import SchemaError
from second_brain.logging_config import get_logger

logger = get_logger(__name__)

MIGRATION_PATTERN = re.compile(r"^(\d+)_[a-z0-9_]+\.sql$")


class MigrationInfo(BaseModel):
    """Represents expected migration information from local files."""

    version: int
    filename: str
    checksum: str  # SHA-256 hex digest


class MigrationRecord(BaseModel):
    """Represents actual migration information stored in database."""

    version: int
    filename: str
    checksum: str
    applied_at: datetime


class DriftItem(BaseModel):
    """Represents a detected schema drift item."""

    version: int
    filename: str
    drift_type: Literal["modified", "missing", "unexpected"]
    expected_checksum: str | None = None
    actual_checksum: str | None = None
    message: str


class SchemaManager:
    """Pure Python service for managing schema versions and detecting drift.

    This service can operate WITHOUT a live database connection. It scans migration
    files and computes checksums, and only compares with DB records when database
    connection is available.
    """

    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.logger = logger.bind(component="SchemaManager")

    @staticmethod
    def compute_checksum(filepath: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def scan_migrations(self) -> list[MigrationInfo]:
        """Scan migration directory, return sorted list of MigrationInfo."""
        migrations = []
        migration_files = list(self.migrations_dir.glob("*.sql"))

        # Dictionary to track version numbers for duplicate detection
        version_map: dict[int, str] = {}

        for filepath in migration_files:
            match = MIGRATION_PATTERN.match(filepath.name)
            if match:
                version = int(match.group(1))
                filename = filepath.name

                # Check for duplicate version numbers
                if version in version_map:
                    raise SchemaError(
                        f"Duplicate version detected: both '{version_map[version]}' and '{filename}' map to version {version}",
                        code="DUPLICATE_VERSION",
                        context={
                            "duplicate_version": version,
                            "conflicting_files": [version_map[version], filename]
                        }
                    )

                checksum = self.compute_checksum(filepath)
                
                migrations.append(MigrationInfo(
                    version=version,
                    filename=filename,
                    checksum=checksum
                ))
                
                # Record that we've seen this version number
                version_map[version] = filename
            else:
                # Skip non-matching files silently (with debug log)
                logger.debug(
                    "skipping_invalid_migration_file",
                    filepath=str(filepath),
                    reason="doesn't match migration filename pattern"
                )
                continue

        # Sort by version number to ensure consistent ordering
        migrations.sort(key=lambda m: m.version)
        return migrations

    def detect_drift(
        self, 
        expected: list[MigrationInfo], 
        applied: list[MigrationRecord]
    ) -> list[DriftItem]:
        """Compare applied vs expected, return list of drift items.
        
        Returns all types of items:
        - "missing" = file exists locally but NOT in applied records (is a pending migration)
        - "modified" = file exists locally AND in applied, checksums differ (is drift)
        - "unexpected" = record in applied, file NOT found locally (is drift)
        """
        drift_items = []
        
        # Convert lists to dictionaries for easier comparison
        applied_by_version = {record.version: record for record in applied}
        expected_by_version = {info.version: info for info in expected}
        
        # Check for modified migrations (exist in both but differ in checksum)
        for version, expected_info in expected_by_version.items():
            if version in applied_by_version:
                applied_record = applied_by_version[version]
                if expected_info.checksum != applied_record.checksum:
                    drift_items.append(DriftItem(
                        version=version,
                        filename=expected_info.filename,
                        drift_type="modified",
                        expected_checksum=expected_info.checksum,
                        actual_checksum=applied_record.checksum,
                        message=f"Migration {expected_info.filename} checksum differs. "
                                f"Expected: {expected_info.checksum}, "
                                f"found in DB: {applied_record.checksum}"
                    ))

        # Check for unexpected migrations (in applied but not in expected)
        for version, applied_record in applied_by_version.items():
            if version not in expected_by_version:
                drift_items.append(DriftItem(
                    version=version,
                    filename=applied_record.filename,
                    drift_type="unexpected",
                    expected_checksum=None,
                    actual_checksum=applied_record.checksum,
                    message=f"Migration {applied_record.filename} found in schema_versions table "
                            f"but no corresponding file in migrations directory"
                ))

        # Check for missing migrations (in expected but not in applied) -- these are pending migrations
        for version, expected_info in expected_by_version.items():
            if version not in applied_by_version:
                drift_items.append(DriftItem(
                    version=version,
                    filename=expected_info.filename,
                    drift_type="missing",
                    expected_checksum=expected_info.checksum,
                    actual_checksum=None,
                    message=f"Migration {expected_info.filename} exists in migrations directory "
                            f"but not found in schema_versions table (pending migration)"
                ))

        return drift_items

    def validate_schema_integrity(self, applied: list[MigrationRecord]) -> None:
        """Validate schema integrity and raise SchemaError if critical drift is detected.
        
        Critical drift includes:
        - "modified" migrations (files changed after application)
        - "unexpected" records (migrations applied but no longer exist in code)
        
        Does NOT raise for "missing" migrations (pending migrations).
        """
        expected = self.scan_migrations()
        drift_items = self.detect_drift(expected, applied)
        
        # Separate critical drift items from non-critical (pending) items
        critical_items = [item for item in drift_items if item.drift_type in ("modified", "unexpected")]
        
        if critical_items:
            raise SchemaError(
                f"Schema drift detected: {len(critical_items)} issue(s)",
                code="SCHEMA_DRIFT",
                context={
                    "drift_count": len(critical_items),
                    "drift_items": [item.model_dump() for item in critical_items],
                    "total_drift_count": len(drift_items),
                    "pending_migrations": [item.model_dump() for item in drift_items if item.drift_type == "missing"],
                    "migrations_dir": str(self.migrations_dir)
                },
            )
        
        # Log if there are pending migrations (non-critical)
        pending_migrations = [item for item in drift_items if item.drift_type == "missing"]
        if pending_migrations:
            self.logger.info(
                "pending_migrations_detected",
                migrations_dir=str(self.migrations_dir),
                pending_count=len(pending_migrations),
                pending_migrations=[item.filename for item in pending_migrations]
            )
        
        self.logger.info(
            "schema_integrity_validated",
            migrations_dir=str(self.migrations_dir),
            migrated_count=len(expected)
        )