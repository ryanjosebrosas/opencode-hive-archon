"""Tests for SchemaManager service."""
from pathlib import Path
from datetime import datetime, timezone

import pytest

from second_brain.errors import SchemaError
from second_brain.services.schema_manager import DriftItem, MigrationInfo, MigrationRecord, SchemaManager


def test_scan_migrations_finds_and_sorts_sql_files(tmp_path: Path) -> None:
    """Test that scan_migrations finds and sorts .sql files."""
    # Create mock migration files
    (tmp_path / "001_first_migration.sql").write_text("CREATE TABLE a;")
    (tmp_path / "003_third_migration.sql").write_text("ALTER TABLE a ADD COLUMN c;")
    (tmp_path / "002_second_migration.sql").write_text("CREATE TABLE b;")
    
    # Create non-migration files that should be ignored
    (tmp_path / "readme.txt").write_text("This is not a migration")
    (tmp_path / "10_no_underscore").write_text("This has improper naming")
    
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    # Should only include .sql files with proper versioning and be sorted by version
    assert len(migrations) == 3
    assert [m.version for m in migrations] == [1, 2, 3]
    assert migrations[0].filename == "001_first_migration.sql"
    assert migrations[1].filename == "002_second_migration.sql"
    assert migrations[2].filename == "003_third_migration.sql"


def test_scan_migrations_skips_non_sql_files(tmp_path: Path) -> None:
    """Test that scan_migrations skips non-.sql files."""
    (tmp_path / "001_valid.sql").write_text("CREATE TABLE a;")
    (tmp_path / "002_not_sql.txt").write_text("Not a SQL file")
    (tmp_path / "003_also_valid.sql").write_text("CREATE TABLE b;")
    
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    # Should only find the SQL files
    assert len(migrations) == 2
    filenames = {m.filename for m in migrations}
    assert "001_valid.sql" in filenames
    assert "003_also_valid.sql" in filenames
    assert "002_not_sql.txt" not in filenames


def test_scan_migrations_skips_invalid_filename_patterns(tmp_path: Path) -> None:
    """Test that scan_migrations skips invalid filenames (logged as debug)."""
    (tmp_path / "001_valid.sql").write_text("CREATE TABLE a;")
    (tmp_path / "invalid_name.sql").write_text("CREATE TABLE b;")  # lacks numeric prefix
    (tmp_path / "ABC_alpha.sql").write_text("CREATE TABLE c;")    # prefix is not numeric
    (tmp_path / "002_valid_again.sql").write_text("CREATE TABLE d;")
    
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    # Should only find the correctly named files
    assert len(migrations) == 2
    filenames = {m.filename for m in migrations}
    assert "001_valid.sql" in filenames
    assert "002_valid_again.sql" in filenames
    assert "invalid_name.sql" not in filenames
    assert "ABC_alpha.sql" not in filenames


def test_scan_migrations_duplicate_version_numbers_raises_schema_error(tmp_path: Path) -> None:
    """Test that scan_migrations detects duplicate version numbers and raises SchemaError."""
    (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
    (tmp_path / "001_second.sql").write_text("CREATE TABLE b;")  # Same version
    
    manager = SchemaManager(tmp_path)
    with pytest.raises(SchemaError) as exc_info:
        manager.scan_migrations()
    
    error = exc_info.value
    assert "Duplicate version detected" in error.message
    assert "001_first.sql" in error.context["conflicting_files"]
    assert "001_second.sql" in error.context["conflicting_files"]


def test_compute_checksum_produces_consistent_sha256(tmp_path: Path) -> None:
    """Test that compute_checksum produces consistent SHA-256 (64-char hex)."""
    test_file = tmp_path / "test_migration.sql"
    test_content = "CREATE TABLE test; ALTER TABLE test ADD COLUMN id SERIAL;"
    test_file.write_text(test_content)
    
    checksum1 = SchemaManager.compute_checksum(test_file)
    checksum2 = SchemaManager.compute_checksum(test_file)
    
    # Same content should produce same checksum
    assert checksum1 == checksum2
    # Should be valid SHA-256 (64 hex characters)
    assert len(checksum1) == 64
    assert all(c in '0123456789abcdef' for c in checksum1)


def test_compute_checksum_returns_different_results_for_different_content(tmp_path: Path) -> None:
    """Test that compute_checksum returns different results for different content."""
    file1 = tmp_path / "first.sql"
    file1.write_text("CREATE TABLE first;")
    
    file2 = tmp_path / "second.sql"
    file2.write_text("CREATE TABLE second;")
    
    checksum1 = SchemaManager.compute_checksum(file1)
    checksum2 = SchemaManager.compute_checksum(file2)
    
    assert checksum1 != checksum2


def test_detect_drift_with_no_drift_returns_empty_list() -> None:
    """Test that detect_drift with no drift returns empty list."""
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="abc123"),
        MigrationInfo(version=2, filename="002_test.sql", checksum="def456")
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="abc123", applied_at=datetime.now(timezone.utc)),
        MigrationRecord(version=2, filename="002_test.sql", checksum="def456", applied_at=datetime.now(timezone.utc))
    ]
    
    manager = SchemaManager(Path("."))
    drift_items = manager.detect_drift(expected, applied)
    
    assert len(drift_items) == 0
    assert drift_items == []


def test_detect_drift_with_modified_checksum_returns_drift_item() -> None:
    """Test that detect_drift with modified checksum returns DriftItem(drift_type='modified')."""
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="new_checksum_here"),
        MigrationInfo(version=2, filename="002_test.sql", checksum="unchanged_checksum")
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="old_checksum_here", applied_at=datetime.now(timezone.utc)),
        MigrationRecord(version=2, filename="002_test.sql", checksum="unchanged_checksum", applied_at=datetime.now(timezone.utc))
    ]
    
    manager = SchemaManager(Path("."))
    drift_items = manager.detect_drift(expected, applied)
    
    assert len(drift_items) == 1
    drift_item = drift_items[0]
    assert drift_item.version == 1
    assert drift_item.drift_type == "modified"
    assert drift_item.expected_checksum == "new_checksum_here"
    assert drift_item.actual_checksum == "old_checksum_here"
    assert drift_item.filename == "001_test.sql"


def test_detect_drift_with_missing_migration_returns_drift_item(tmp_path: Path) -> None:
    """Test that detect_drift with missing migration returns DriftItem(drift_type='missing')."""
    # Note: For this test we simulate a missing migration by having it in expected but NOT applied
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="checksum1"),
        MigrationInfo(version=2, filename="002_missing.sql", checksum="checksum2")  # Present in code, not in DB
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="checksum1", applied_at=datetime.now(timezone.utc))
        # Version 2 not applied - so it's a 'missing' item (pending migration)
    ]
    
    manager = SchemaManager(tmp_path)
    drift_items = manager.detect_drift(expected, applied)
    
    assert len(drift_items) == 1
    drift_item = drift_items[0]
    assert drift_item.version == 2
    assert drift_item.drift_type == "missing"
    assert drift_item.filename == "002_missing.sql"
    assert drift_item.actual_checksum is None  # Doesn't exist in DB


def test_detect_drift_with_unexpected_record_returns_drift_item(tmp_path: Path) -> None:
    """Test that detect_drift with unexpected record returns DriftItem(drift_type='unexpected')."""
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="checksum1")
        # Note: version 2 is not in expected (migrated but file was deleted)
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="checksum1", applied_at=datetime.now(timezone.utc)),
        MigrationRecord(version=2, filename="002_deleted.sql", checksum="deleted_checksum", applied_at=datetime.now(timezone.utc))
        # Version 2 exists in DB but not in code - unexpected
    ]
    
    manager = SchemaManager(tmp_path)
    drift_items = manager.detect_drift(expected, applied)
    
    assert len(drift_items) == 1
    drift_item = drift_items[0]
    assert drift_item.version == 2
    assert drift_item.drift_type == "unexpected"
    assert drift_item.filename == "002_deleted.sql"
    assert drift_item.expected_checksum is None  # Doesn't exist in code
    assert drift_item.actual_checksum == "deleted_checksum"  # Exists in DB


def test_detect_drift_with_multiple_drift_types_simultaneously(tmp_path: Path) -> None:
    """Test that detect_drift with multiple drift types simultaneously works correctly."""
    # Expected includes versions [1, 2, 3, 5]
    expected = [
        MigrationInfo(version=1, filename="001_base.sql", checksum="valid_checksum"),
        MigrationInfo(version=2, filename="002_modified.sql", checksum="new_modified_checksum"),  # Modified from DB
        MigrationInfo(version=3, filename="003_okay.sql", checksum="ok_checksum"),
        MigrationInfo(version=5, filename="005_pending.sql", checksum="future_checksum")  # Missing in DB (pending)
    ]
    
    # Applied includes versions [2, 3, 4] but version 2 has different checksum (modified), and version 4 doesn't exist in expected (unexpected)
    applied = [
        MigrationRecord(version=2, filename="002_modified.sql", checksum="old_modified_checksum", applied_at=datetime.now(timezone.utc)),  # Modified: different checksum than expected
        MigrationRecord(version=3, filename="003_okay.sql", checksum="ok_checksum", applied_at=datetime.now(timezone.utc)),  # Okay: checksum matches
        MigrationRecord(version=4, filename="004_unexpected.sql", checksum="unexpected_checksum", applied_at=datetime.now(timezone.utc))  # Unexpected: not in code
    ]
    
    manager = SchemaManager(tmp_path)
    drift_items = manager.detect_drift(expected, applied)
    
    # Should detect 4 types of issues:
    # 1. Modified: v2 checksums differ
    # 2. Missing: v1 in expected but not in applied
    # 3. Missing: v5 in expected but not in applied  
    # 4. Unexpected: v4 in applied but not in expected
    assert len(drift_items) == 4
    
    drift_types = {item.drift_type for item in drift_items}
    assert drift_types == {"modified", "unexpected", "missing"}
    
    # Count of each type
    modified_items = [item for item in drift_items if item.drift_type == "modified"]
    unexpected_items = [item for item in drift_items if item.drift_type == "unexpected"]
    missing_items = [item for item in drift_items if item.drift_type == "missing"]
    
    assert len(modified_items) == 1
    assert modified_items[0].version == 2
    assert modified_items[0].expected_checksum == "new_modified_checksum"
    assert modified_items[0].actual_checksum == "old_modified_checksum"
    
    assert len(unexpected_items) == 1
    assert unexpected_items[0].version == 4
    assert unexpected_items[0].expected_checksum is None
    assert unexpected_items[0].actual_checksum == "unexpected_checksum"
    
    assert len(missing_items) == 2  # Versions 1 and 5
    
    # Identify the specific missing versions
    missing_versions = {item.version for item in missing_items}
    assert 1 in missing_versions
    assert 5 in missing_versions
    assert missing_versions == {1, 5}


def test_validate_schema_integrity_raises_schema_error_for_modified_drift(tmp_path: Path) -> None:
    """Test that validate_schema_integrity raises SchemaError for modified drift."""
    # Create a migration file in the directory 
    file_content = "CREATE TABLE first_original;"
    (tmp_path / "001_first.sql").write_text(file_content)
    
    # But imagine that in the DB, it was applied with different content/checksum
    manager = SchemaManager(tmp_path)
    applied = [
        MigrationRecord(version=1, filename="001_first.sql", checksum="different_from_current_file", applied_at=datetime.now(timezone.utc))
    ]
    
    with pytest.raises(SchemaError) as exc_info:
        manager.validate_schema_integrity(applied)
    
    error = exc_info.value
    assert "Schema drift detected" in error.message
    assert error.code == "SCHEMA_DRIFT"
    assert error.context["drift_count"] == 1
    assert error.context["drift_items"][0]["drift_type"] == "modified"


def test_validate_schema_integrity_raises_schema_error_for_unexpected_drift(tmp_path: Path) -> None:
    """Test that validate_schema_integrity raises SchemaError for unexpected drift."""
    # Create a migration file in the directory to match the applied state
    file_content = "CREATE TABLE first;"
    (tmp_path / "001_first.sql").write_text(file_content)
    
    # Compute the actual checksum of the created file
    actual_checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
    
    # Now apply the state where the checksums match (no modified drift), but v2 is unexpected (no file)
    applied = [
        MigrationRecord(version=1, filename="001_first.sql", checksum=actual_checksum, applied_at=datetime.now(timezone.utc)),
        MigrationRecord(version=2, filename="002_deleted.sql", checksum="deleted_checksum", applied_at=datetime.now(timezone.utc))  # Unexpected: no file exists
    ]
    
    manager = SchemaManager(tmp_path)
    with pytest.raises(SchemaError) as exc_info:
        manager.validate_schema_integrity(applied)
    
    error = exc_info.value
    assert "Schema drift detected" in error.message
    assert error.code == "SCHEMA_DRIFT"
    # There should be only the unexpected drift issue (v2 exists in DB but no file in code)
    assert error.context["drift_count"] == 1  # Only the unexpected drift
    assert error.context["drift_items"][0]["drift_type"] == "unexpected"
    assert error.context["drift_items"][0]["version"] == 2


def test_validate_schema_integrity_does_not_raise_for_missing_only_pending_drift(tmp_path: Path) -> None:
    """Test that validate_schema_integrity does NOT raise for missing-only (pending) drift."""
    # Create migration files that include versions not in applied (pending migrations)  
    (tmp_path / "001_first.sql").write_text("CREATE TABLE first;")
    (tmp_path / "002_pending.sql").write_text("CREATE TABLE pending;")  # This is a pending migration
    
    # Compute the actual checksum of the first file to match what scan_migrations will find
    actual_checksum_1 = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
    
    applied = [
        MigrationRecord(version=1, filename="001_first.sql", checksum=actual_checksum_1, applied_at=datetime.now(timezone.utc))
        # Version 2 not applied - will be treated as pending migration
    ]
    
    manager = SchemaManager(tmp_path)
    # This should NOT raise an error - only "missing" items are pending migrations
    manager.validate_schema_integrity(applied)


def test_validate_schema_integrity_passes_with_empty_lists(tmp_path: Path) -> None:
    """Test that validate_schema_integrity passes with empty lists."""
    manager = SchemaManager(tmp_path)
    # Should not raise any error
    manager.validate_schema_integrity([])


def test_migration_info_model_serialization() -> None:
    """Test MigrationInfo model serialization."""
    migration_info = MigrationInfo(
        version=1,
        filename="001_test.sql",
        checksum="abc123"
    )
    
    data = migration_info.model_dump()
    assert data["version"] == 1
    assert data["filename"] == "001_test.sql"
    assert data["checksum"] == "abc123"


def test_drift_item_model_serialization() -> None:
    """Test DriftItem model serialization."""
    drift_item = DriftItem(
        version=1,
        filename="001_test.sql",
        drift_type="modified",
        expected_checksum="new_checksum",
        actual_checksum="old_checksum",
        message="Checksum mismatch"
    )
    
    data = drift_item.model_dump()
    assert data["version"] == 1
    assert data["filename"] == "001_test.sql"
    assert data["drift_type"] == "modified"
    assert data["expected_checksum"] == "new_checksum"
    assert data["actual_checksum"] == "old_checksum"
    assert data["message"] == "Checksum mismatch"


def test_empty_migrations_directory_returns_empty_list(tmp_path: Path) -> None:
    """Test empty migrations directory returns empty list."""
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    assert migrations == []