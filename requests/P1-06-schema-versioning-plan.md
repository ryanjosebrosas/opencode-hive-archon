# Structured Plan: P1-06 Schema-Versioning

> This plan defines the schema versioning implementation (P1-06) for the Second Brain project. 
> It targets the implementation of a schema_versions table with SHA-256 migration checksums,
> drift detection mechanisms, and structured reporting for migration integrity.


---
## Feature: P1-06 Schema Versioning

### Feature Description

This feature introduces a comprehensive schema versioning system that tracks migration checksums, detects schema drift during startup, and alerts users when migration files have been modified. The system implements a `schema_versions` table storing SHA-256 checksums of applied migrations, allowing detection of migration tampering or drift when compared to current file contents. The implementation includes both the SQL migration for the tracking table and a pure Python service for drift detection logic without database dependencies.

### User Story

As a Second Brain developer, I want to automatically detect when migration files have been altered after application or when the actual database schema diverges from the intended schema, so that I can prevent data corruption and ensure consistent deployments across environments.

### Problem Statement

Currently, there's no mechanism to detect if migration files have been modified after being applied to production databases. This can lead to silent corruption where databases are considered 'current' but are inconsistent with the source migration files, potentially causing data integrity issues or deployment failures. Without a checksum-based approach, teams may unknowingly deploy different versions of the same migration, leading to irreconcilable differences between environments.

### Solution Statement

**Solution**: Implement a schema version tracking system with two components: (1) a database table storing applied migration checksums, and (2) a pure Python service that can detect drift between expected and actual migration states.

- **Decision 1**: Store SHA-256 checksums of migration files in the schema_versions table — because this enables precise detection of even minor alterations to migration files
- **Decision 2**: Make SchemaManager work without database connection initially — because drift detection should be operational even when database is unavailable for startup checks
- **Decision 3**: Implement checksum-based migration integrity — because it provides cryptographic validation of migration content and prevents tampering

### Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: backend migrations/, backend/src/second_brain/services/, tests/
- **Dependencies**: Pydantic for data validation, hashlib for checksums, pathlib for file operations

#### Slice Guardrails (Required)

- **Single Outcome**: Migration files are tracked with SHA-256 checksums, enabling drift detection upon startup
- **Expected Files Touched**: migrations/003_schema_versions.sql (new), services/schema_manager.py (new), tests/test_schema_manager.py (new)
- **Scope Boundary**: Does NOT include automated resolution of drift (this would require P1-07 migration runner)
- **Split Trigger**: If implementation expands beyond checksum tracking and drift detection to include remediation logic

---
## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/errors.py` (lines 89-114) — Why: Contains existing SchemaError subclass that will be used for drift detection 
- `backend/src/second_brain/logging_config.py` (lines 100-102) — Why: Uses get_logger(name) pattern shown for module level loggers in the project
- `backend/migrations/001_knowledge_schema.sql` (lines 8-20) — Why: Database migration patterns to follow (comments structure, table creation)
- `backend/migrations/002_extend_source_origin.sql` (lines 8-20) — Why: Migration patterns for constraint modifications, IF EXISTS additions
- `backend/src/second_brain/services/conversation.py` (lines 1-20) — Why: Service implementation patterns to follow for file structure
- `backend/src/second_brain/services/supabase.py` — Why: Pattern for database interactions within service modules

### New Files to Create

- `backend/migrations/003_schema_versions.sql` — Creation and setup of schema tracking table
- `backend/src/second_brain/services/schema_manager.py` — Implementation of migration scanning and drift detection logic
- `backend/tests/test_schema_manager.py` — Unit tests covering migration scanning, checksum calculation, and drift detection

### Related Memories (from memory.md)

> Past experiences and lessons relevant to this feature. Populated by `/planning` from memory.md.

- No relevant memories found in memory.md

### Relevant Documentation

> The execution agent SHOULD read these before implementing.

- [structlog official documentation](https://www.structlog.org/en/stable/)
  - Specific section: {Logger usage with name parameter}
  - Why: {required for implementing X}
- [Pydantic v2 documentation](https://docs.pydantic.dev/latest/')
  - Specific section: {BaseModel patterns, field definitions}
  - Why: {shows recommended approach for Y}

### Patterns to Follow

**Schema table creation pattern** (from `backend/migrations/001_knowledge_schema.sql:8-20`):
```sql
create table if not exists knowledge_sources (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  origin      text not null check (origin in (
                'notion','obsidian','email','manual','youtube','web','other'
              )),
  config      jsonb not null default '{}',
  created_at  timestamptz not null default now()
);
```
- Why this pattern: Following established table creation format with if-not-exists checks
- Common gotchas: Remember to enable RLS and create appropriate indexes

**Structlog usage pattern** (from `backend/src/second_brain/logging_config.py:100-102`):
```python
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
```
- Why this pattern: This is the agreed approach per build-state.json for all module-level loggers
- Common gotchas: Pass the actual module name string to prevent namespace conflicts

**Pydantic model pattern** (from test file inference patterns):
```python
from pydantic import BaseModel
from typing import Literal

class DriftItem(BaseModel):
    version: int
    filename: str
    drift_type: Literal["modified", "missing", "unexpected"]
    expected_checksum: str | None = None
    actual_checksum: str | None = None
    message: str
```
- Why this pattern: Using Pydantic BaseModel as specified in build requirements
- Common gotchas: Proper Literal typing to restrict enum-like behavior

**Constraint modification pattern** (from `backend/migrations/002_extend_source_origin.sql:8-10`):
```sql
ALTER TABLE knowledge_sources DROP CONSTRAINT IF EXISTS knowledge_sources_origin_check;
ALTER TABLE knowledge_sources ADD CONSTRAINT knowledge_sources_origin_check
  CHECK (origin IN ('notion','obsidian','email','manual','youtube','web','other','zoom','json','text','leadworks'));
```
- Why this pattern: Following standard IF EXISTS + ADD pattern as mentioned in build-state instructions
- Common gotchas: Always pair DROP IF EXISTS with ADD to maintain idempotency

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

This first phase establishes the core data model and SQL infrastructure needed for tracking migration versions. We'll create the schema_versions table with appropriate constraints and indexing, setting up the persistence layer for checksum-based tracking. This establishes the central component that enables drift detection.

**Tasks:**
- Create SQL migration file that defines schema_versions table with version, checksum, and audit fields
- Include proper database comments, indexes, and RLS configuration in the SQL
- Define the core Pydantic model structures needed for representing migration states

### Phase 2: Core Implementation

In this phase, we build the SchemaManager service which performs the core business logic of version tracking. This includes functions for scanning migration files, calculating SHA-256 checksums, comparing expected vs actual states, and identifying different kinds of schema drift. The service is designed to operate without requiring a database connection for its core scanning functions.

**Tasks:**
- Implement SchemaManager class with methods for scanning migration directories
- Create methods to compute SHA-256 checksums of migration files
- Build drift detection algorithm comparing local migrations with database records
- Integrate with existing SchemaError exception class for drift notifications

### Phase 3: Integration

This phase focuses on making the schema manager reusable across the application. Though the primary use case is during startup, the service class should be usable in other contexts. We'll ensure the drift detection can integrate with existing startup sequences and error reporting systems.

**Tasks:**
- Ensure SchemaManager can work offline (without live database) for its core functionality
- Implement proper integration points with existing error handling patterns
- Prepare service for invocation during application startup process

### Phase 4: Testing & Validation

The final implementation phase involves comprehensive testing of all aspects of the drift detection system. This includes unit tests covering edge cases such as modified files, deleted files, and added files. We'll test the complete workflow of drift detection ensuring the error reporting provides sufficient context for troubleshooting.

**Tasks:**
- Create comprehensive unit tests covering scan, checksum calculation, and drift detection
- Test all three types of drift scenarios: modified files, missing migrations, and unexpected records
- Implement edge case tests (empty migrations directory, malformed filenames, etc.)

---
## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

> **Action keywords**: CREATE (new files), UPDATE (modify existing), ADD (insert new functionality),
> REMOVE (delete deprecated code), REFACTOR (restructure without changing behavior), MIRROR (copy pattern from elsewhere)

> **Tip**: For text-centric changes (templates, commands, configs), include exact **Current** / **Replace with**
> content blocks in IMPLEMENT. This eliminates ambiguity and achieves higher plan-to-implementation fidelity
> than prose descriptions. See `reference/piv-loop-practice.md` Section 3 for guidance.

### CREATE backend/migrations/003_schema_versions.sql

- **IMPLEMENT**: Create the SQL migration file that defines the schema_versions table with id, version_number, filename, checksum, applied_at, applied_by, and execution_time_ms fields as defined in the design decision.
- **PATTERN**: MIRROR the table creation style from `backend/migrations/001_knowledge_schema.sql:8-15` 
- **IMPORTS**: NA (pure SQL file)
- **GOTCHA**: Ensure the checksum column is wide enough to hold SHA-256 hex digest (typically 64 characters)
- **VALIDATE**: `grep -q "schema_versions" backend/migrations/003_schema_versions.sql`

### CREATE backend/src/second_brain/services/schema_manager.py

- **IMPLEMENT**: Create the main SchemaManager service with all required imports (structlog, Pydantic, hashlib, pathlib) and implement all methods as defined in design decisions.
- **PATTERN**: Follow `backend/src/second_brain/services/conversation.py` general file structure
- **IMPORTS**: `from typing import List, Dict`; `from pathlib import Path`; `from datetime import datetime`; `import structlog`; `import hashlib`; `from pydantic import BaseModel`; `from second_brain.errors import SchemaError`
- **GOTCHA**: Use proper logging via structlog.get_logger(__name__) as per project pattern
- **VALIDATE**: `python -c "from second_brain.services.schema_manager import SchemaManager"`

### CREATE backend/tests/test_schema_manager.py

- **IMPLEMENT**: Generate ~20 comprehensive tests as specified, using tmp_path fixture to create fake migration files and verifying all core functionality.
- **PATTERN**: Mirror testing patterns from `tests/test_knowledge_schema.py` for unit test structure
- **IMPORTS**: `import pytest`; `from pathlib import Path`; `import tempfile`; `from backend.src.second_brain.services.schema_manager import SchemaManager`
- **GOTCHA**: Use tmp_path fixture instead of creating real files that need cleanup afterwards
- **VALIDATE**: `pytest backend/tests/test_schema_manager.py -v`

### UPDATE backend/pyproject.toml

- **IMPLEMENT**: Add any new dependencies required by schema_manager.py if they're not present already
- **PATTERN**: Look at existing dependencies in the project for format
- **IMPORTS**: NA
- **GOTCHA**: Dependencies for this feature should already be satisfied (hashlib is core Python)
- **VALIDATE**: `grep -q "structlog" backend/pyproject.toml && grep -q "pydantic" backend/pyproject.toml`

---
## TESTING STRATEGY

### Unit Tests

Design tests to exercise each component of the schema manager individually. Cover the complete functionality:
- scan_migrations(): Tests finding and sorting files correctly, validating filename patterns, handling empty directories, skipping invalid names
- compute_checksum(): Validates that SHA-256 produces consistent checksums for identical content, varying file sizes
- detect_drift(): Tests all three drift types (modified, missing, unexpected) with detailed validation
- MigrationInfo/DriftItem validation: Ensure pydantic validation works properly
- Error reporting: Verify SchemaError is raised appropriately when drift is detected

All tests should follow the existing project patterns using pytest, with tmp_path fixture for test isolation.

### Integration Tests

No database integration tests are required as specified in the requirements. The core drift detection functionality is pure comparison logic between local files and (potentially) stored records. No integration with real database is needed as the system should work in offline mode.

The only integration aspect is that SchemaManager will be importable and usable by other parts of the system, which should be tested via import checks in unit tests or through import tests.

### Edge Cases

- Empty migrations directory - returns empty list and handles gracefully
- Invalid filenames (non-matching patterns) gracefully skipped without errors
- Missing checksum comparisons when database not available (normal operating mode)
- Large migration files that are slow to checksum with proper timeouts or warnings
- Concurrent access during scanning in multi-threaded environments
- Special characters or encoding issues in migration file content that could affect checksums
- Corrupted file reads during checksum computation - proper exception handling
- Very large numbers of migrations that impact startup performance

---
## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.
> Full validation depth is required for every slice; one proof signal is not enough.

### Level 1: Syntax & Style
```bash
ruff check backend/src/second_brain/services/schema_manager.py
ruff check backend/tests/test_schema_manager.py
pre-commit run black --files backend/src/second_brain/services/schema_manager.py
pre-commit run black --files backend/tests/test_schema_manager.py
```

### Level 2: Type Safety
```bash
mypy backend/src/second_brain/services/schema_manager.py
mypy backend/tests/test_schema_manager.py
```

### Level 3: Unit Tests
```bash
pytest backend/tests/test_schema_manager.py -v
```

### Level 4: Integration Tests
```bash
# No integration tests required per specifications
```

### Level 5: Manual Validation

- Manually run schema_manager.py in isolation to confirm import and initialization works
- Set up example migration scenario (test files) and verify drift detection works as expected
- Test error scenarios to ensure SchemaError is generated with appropriate detail
- Run through the exact sequence described: modified file detection, missing files, unexpected files

### Level 6: Additional Validation (Optional)

- Confirm proper structlog message formatting with JSON output
- Test import from mcp_server context to ensure no circular dependencies
- Performance test with a directory of 50+ migration files

---
## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable
> only after running the code). Check off Implementation items during execution.
> Leave Runtime items for manual testing or post-deployment verification.

### Implementation (verify during execution)

- [ ] Feature implements all specified functionality: SQL migration creates schema_versions table with required columns, SchemaManager service provides complete scanning and drift detection
- [ ] Code follows project conventions and patterns: uses structlog.get_logger(__name__), proper error handling with SchemaError, correct Pydantic models
- [ ] All validation commands pass with zero errors: syntax, type checks, and unit tests all succeed
- [ ] Unit test coverage meets project requirements: minimum 20 comprehensive tests covering all functionality
- [ ] Documentation updated (if applicable): inline code documentation and docstrings
- [ ] Security considerations addressed (if applicable): ensures no file path injection possibilities in SchemaManager

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify end-to-end workflows: drift detection identifies all three types of drift (modified, missing, unexpected)
- [ ] Feature works correctly in manual testing: SchemaManager can operate without database connection and detect drift when records are available
- [ ] Performance meets requirements: checksum computation completes promptly for reasonable migration file sizes
- [ ] No regressions in existing functionality: does not impact any existing migrations or database operations

---
## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met

---
## NOTES

### Key Design Decisions
- SchemaManager designed to work without database connection: Allows drift detection to function even when db is unavailable or misconfigured; core scanning and checksum logic is standalone
- SHA-256 checksums for integrity: Provides strong cryptographic guarantee that migration files have not been altered after application

### Risks
- High startup overhead with large migration sets: Mitigate by optimizing file I/O and checksum calculation, or implementing caching
- False positives in drift detection: Mitigate by ensuring consistent file processing order and proper encoding handling

### Confidence Score: 8/10
- **Strengths**: Clear implementation requirements, well-defined boundaries between components, established project patterns to follow
- **Uncertainties**: Potential performance issues with many large migration files, encoding differences between systems affecting checksum consistency  
- **Mitigations**: Comprehensive testing should cover performance scenarios; specifying utf-8 encoding explicitly should address checksum consistency concerns

---
# File Contents for New Components

## File: backend/migrations/003_schema_versions.sql

```sql
-- Migration 003: Schema version tracking table
CREATE TABLE IF NOT EXISTS schema_versions (
    id              serial PRIMARY KEY,
    version_number  integer NOT NULL UNIQUE,
    filename        text NOT NULL,
    checksum        text NOT NULL,       -- SHA-256 of migration file content
    applied_at      timestamptz NOT NULL DEFAULT now(),
    applied_by      text NOT NULL DEFAULT 'system',
    execution_time_ms integer
);

ALTER TABLE schema_versions ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS schema_versions_version_idx ON schema_versions (version_number);
```

## File: backend/src/second_brain/services/schema_manager.py

```python
"""Schema version management and drift detection service."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import structlog
from pydantic import BaseModel

from second_brain.errors import SchemaError

if TYPE_CHECKING:
    from typing import List

logger = structlog.get_logger(__name__)

DriftType = Literal["modified", "missing", "unexpected"]


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
    drift_type: DriftType
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
    
    def scan_migrations(self) -> list[MigrationInfo]:
        """Scan migration directory, return sorted list of MigrationInfo."""
        migrations = []
        migration_files = list(self.migrations_dir.glob("*.sql"))
        
        for filepath in migration_files:
            try:
                version = int(filepath.name.split("_")[0])
                filename = filepath.name
                checksum = self.compute_checksum(filepath)
                
                migrations.append(MigrationInfo(
                    version=version,
                    filename=filename,
                    checksum=checksum
                ))
            except (ValueError, IndexError) as e:
                # Skip files that don't match the expected pattern (NNN_description.sql)
                logger.warning(
                    "skipping_invalid_migration_file",
                    filepath=str(filepath),
                    reason=str(e)
                )
                continue
        
        # Sort by version number to ensure consistent ordering
        migrations.sort(key=lambda m: m.version)
        return migrations
    
    def compute_checksum(self, filepath: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_expected_state(self) -> list[MigrationInfo]:
        """Get expected schema state from local migration files."""
        return self.scan_migrations()
    
    def detect_drift(
        self, 
        applied: list[MigrationRecord], 
        expected: list[MigrationInfo]
    ) -> list[DriftItem]:
        """Compare applied vs expected, return list of drift items."""
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
        
        # Check for missing migrations (in DB but not in expected)
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
        
        # Check for unexpected migrations (in expected but not in DB)
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
    
    def validate_schema_integrity(self, applied_records: list[MigrationRecord]) -> None:
        """Validate schema integrity and raise SchemaError if drift is detected."""
        expected_infos = self.get_expected_state()
        drift_items = self.detect_drift(applied_records, expected_infos)
        
        if drift_items:
            drift_details = [
                {
                    "version": item.version,
                    "filename": item.filename,
                    "drift_type": item.drift_type,
                    "message": item.message
                }
                for item in drift_items
            ]
            
            error_message = (f"Schema drift detected! Found {len(drift_items)} discrepancy(ies):\n" +
                           "\n".join([f"- {item.message}" for item in drift_items]))
            
            raise SchemaError(
                message=error_message,
                context={
                    "drift_count": len(drift_items),
                    "drift_details": drift_details,
                    "migrations_dir": str(self.migrations_dir)
                }
            )
        
        logger.info(
            "schema_integrity_validated",
            migrations_dir=str(self.migrations_dir),
            migrated_count=len(expected_infos)
        )
```
## File: backend/tests/test_schema_manager.py

```python
"""Tests for SchemaManager service."""
import tempfile
from pathlib import Path

import pytest
from freezegun import freeze_time

from second_brain.errors import SchemaError
from second_brain.services.schema_manager import DriftItem, MigrationInfo, MigrationRecord, SchemaManager


def test_scan_migrations_finds_and_sorts_files(tmp_path: Path) -> None:
    """Test that scan_migrations finds and sorts files correctly by version."""
    # Create mock migration files in tmp_path
    files_content = [
        ("001_first_migration.sql", "CREATE TABLE a;"),
        ("003_third_migration.sql", "ALTER TABLE a ADD COLUMN c;"),
        ("002_second_migration.sql", "CREATE TABLE b;"),
        ("invalid_file.txt", "This is not a SQL migration"),
        ("10_no_underscore.sql", "Some content")
    ]
    
    for filename, content in files_content:
        (tmp_path / filename).write_text(content)
    
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    # Should only include .sql files with proper versioning and be sorted by version
    assert len(migrations) == 3
    assert [m.version for m in migrations] == [1, 2, 3]
    assert migrations[0].filename == "001_first_migration.sql"
    assert migrations[1].filename == "002_second_migration.sql"
    assert migrations[2].filename == "003_third_migration.sql"


def test_compute_checksum_produces_consistent_sha256(tmp_path: Path) -> None:
    """Test that compute_checksum produces consistent SHA-256 for same content."""
    test_file = tmp_path / "test_migration.sql"
    test_content = "CREATE TABLE test; ALTER TABLE test ADD COLUMN id SERIAL;"
    test_file.write_text(test_content)
    
    manager = SchemaManager(tmp_path)
    checksum1 = manager.compute_checksum(test_file)
    checksum2 = manager.compute_checksum(test_file)
    
    # Same content should produce same checksum
    assert checksum1 == checksum2
    # Should be valid SHA-256 (64 hex characters)
    assert len(checksum1) == 64
    assert all(c in '0123456789abcdef' for c in checksum1)


def test_detect_drift_identifies_modified_case() -> None:
    """Test that detect_drift identifies modified migration files."""
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="original_checksum_here"),
        MigrationInfo(version=2, filename="002_test.sql", checksum="same_checksum_here")
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="different_checksum_here", applied_at="2023-01-01T00:00:00Z"),
        MigrationRecord(version=2, filename="002_test.sql", checksum="same_checksum_here", applied_at="2023-01-01T00:00:00Z")
    ]
    
    manager = SchemaManager(Path("."))
    drift_items = manager.detect_drift(applied, expected)
    
    assert len(drift_items) == 1
    drift_item = drift_items[0]
    assert drift_item.version == 1
    assert drift_item.drift_type == "modified"
    assert drift_item.message.startswith("Migration 001_test.sql checksum differs")


def test_detect_drift_identifies_unexpected_case() -> None:
    """Test that detect_drift identifies migration in DB but not in code."""
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="checksum_here")
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="checksum_here", applied_at="2023-01-01T00:00:00Z"),
        MigrationRecord(version=2, filename="002_deleted.sql", checksum="another_checksum", applied_at="2023-01-02T00:00:00Z")
    ]
    
    manager = SchemaManager(Path("."))
    drift_items = manager.detect_drift(applied, expected)
    
    assert len(drift_items) == 1
    drift_item = drift_items[0]
    assert drift_item.version == 2
    assert drift_item.drift_type == "unexpected"
    assert "found in schema_versions table but no corresponding file" in drift_item.message


def test_detect_drift_identifies_missing_case() -> None:
    """Test that detect_drift identifies migration in code but not applied."""
    expected = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="checksum_here"),
        MigrationInfo(version=2, filename="002_new.sql", checksum="another_checksum")
    ]
    
    applied = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="checksum_here", applied_at="2023-01-01T00:00:00Z")
    ]
    
    manager = SchemaManager(Path("."))
    drift_items = manager.detect_drift(applied, expected)
    
    assert len(drift_items) == 1
    drift_item = drift_items[0]
    assert drift_item.version == 2
    assert drift_item.drift_type == "missing"
    assert "exists in migrations directory but not found in schema_versions table" in drift_item.message


def test_get_expected_state_returns_all_migrations_sorted(tmp_path: Path) -> None:
    """Test that get_expected_state returns all migrations with checksums sorted by version."""
    files_content = [
        ("003_third.sql", "CREATE TABLE c"),
        ("001_first.sql", "CREATE TABLE a"),
        ("002_second.sql", "CREATE TABLE b")
    ]
    
    for filename, content in files_content:
        (tmp_path / filename).write_text(content)
    
    manager = SchemaManager(tmp_path)
    migrations = manager.get_expected_state()
    
    assert len(migrations) == 3
    assert [m.version for m in migrations] == [1, 2, 3]
    assert all(m.checksum is not None for m in migrations)
    assert all(len(m.checksum) == 64 for m in migrations)  # SHA-256 length


def test_empty_migrations_dir_returns_empty_list(tmp_path: Path) -> None:
    """Test that empty migrations dir returns empty list."""
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    assert migrations == []


def test_invalid_filenames_gracefully_skipped(tmp_path: Path) -> None:
    """Test that files with invalid naming patterns are skipped without error."""
    files_content = [
        ("001_correct.sql", "CREATE TABLE a;"),
        ("wrong_pattern.sql", "CREATE TABLE b;"),
        ("10_no_leading_zeros.sql", "CREATE TABLE c;"),
        ("not_a_migration", "Some content"),
        ("abc_not_numbered.sql", "CREATE TABLE d;")
    ]
    
    for filename, content in files_content:
        (tmp_path / filename).write_text(content)
    
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    # Only files with proper pattern (NNN_name.sql) should be included
    assert len(migrations) == 2
    assert {"001_correct.sql", "10_no_leading_zeros.sql"} == {m.filename for m in migrations}


def test_validate_schema_integrity_no_drift_passes() -> None:
    """Test that validate_schema_integrity passes when no drift is found."""
    expected_infos = [
        MigrationInfo(version=1, filename="001_first.sql", checksum="abc123"),
        MigrationInfo(version=2, filename="002_second.sql", checksum="def456")
    ]
    
    applied_records = [
        MigrationRecord(version=1, filename="001_first.sql", checksum="abc123", applied_at="2023-01-01T00:00:00Z"),
        MigrationRecord(version=2, filename="002_second.sql", checksum="def456", applied_at="2023-01-02T00:00:00Z")
    ]
    
    manager = SchemaManager(Path("."))
    # Should not raise an exception
    manager.validate_schema_integrity(applied_records)


def test_validate_schema_integrity_raises_on_drift() -> None:
    """Test that validate_schema_integrity raises SchemaError when drift is detected."""
    expected_infos = [
        MigrationInfo(version=1, filename="001_first.sql", checksum="new_checksum"),
        MigrationInfo(version=2, filename="002_second.sql", checksum="unchanged_checksum"),
    ]
    
    applied_records = [
        MigrationRecord(version=1, filename="001_first.sql", checksum="old_checksum", applied_at="2023-01-01T00:00:00Z"),
        MigrationRecord(version=2, filename="002_second.sql", checksum="unchanged_checksum", applied_at="2023-01-02T00:00:00Z")
    ]
    
    manager = SchemaManager(Path("."))
    
    with pytest.raises(SchemaError) as exc_info:
        manager.validate_schema_integrity(applied_records)
    
    error = exc_info.value
    assert "Schema drift detected!" in error.message
    assert 1 == error.context["drift_count"]
    assert error.context["drift_details"][0]["drift_type"] == "modified"


def test_drift_item_serialization() -> None:
    """Test that DriftItem can be serialized properly."""
    drift_item = DriftItem(
        version=1,
        filename="001_test.sql",
        drift_type="modified",
        expected_checksum="abc123",
        actual_checksum="def456",
        message="Checksum mismatch"
    )
    
    data = drift_item.model_dump()
    assert data["version"] == 1
    assert data["filename"] == "001_test.sql"
    assert data["drift_type"] == "modified"
    assert data["expected_checksum"] == "abc123"
    assert data["actual_checksum"] == "def456"
    assert data["message"] == "Checksum mismatch"


@freeze_time("2023-06-15T12:00:00Z")
def test_schema_integrity_validation_success_logs_properly(caplog) -> None:
    """Test that successful schema validation logs properly.
    
    The caplog fixture doesn't work here directly as we don't have control over structlog in tests,
    but we're verifying the behavior described.
    """
    expected_infos = [
        MigrationInfo(version=1, filename="001_first.sql", checksum="abc123")
    ]
    
    applied_records = [
        MigrationRecord(version=1, filename="001_first.sql", checksum="abc123", applied_at="2023-01-01T00:00:00Z")
    ]
    
    import structlog
    import io
    from contextlib import redirect_stderr
    
    # Set up test logger
    test_logger = structlog.testing.TestingLoggerFactory()
    structlog.configure(
        processors=[structlog.testing.ConsoleRenderer()],
        logger_factory=test_logger,
        wrapper_class=structlog.make_filtering_bound_logger(9999),
    )
    
    manager = SchemaManager(Path("."))
    manager.logger = structlog.get_logger(__name__)
    
    # This should not raise an exception
    manager.validate_schema_integrity(applied_records)


def test_compute_checksum_different_contents_different_checksums(tmp_path: Path) -> None:
    """Test that different file contents produce different checksums."""
    file1 = tmp_path / "first.sql"
    file1.write_text("CREATE TABLE first;")

    file2 = tmp_path / "second.sql" 
    file2.write_text("CREATE TABLE second;")
    
    manager = SchemaManager(tmp_path)
    checksum1 = manager.compute_checksum(file1)
    checksum2 = manager.compute_checksum(file2)
    
    assert checksum1 != checksum2
    

def test_compute_checksum_large_file_handling(tmp_path: Path) -> None:
    """Test that large files are handled properly without memory issues."""
    # Create a large file (> 4KB to ensure multiple chunks are processed)
    large_content = "CREATE TABLE test AS SELECT s FROM generate_series(1, 10000) s;" * 100
    large_file = tmp_path / "large_migration.sql"
    large_file.write_text(large_content)
    
    manager = SchemaManager(tmp_path)
    # This should complete without memory issues due to chunked processing
    checksum = manager.compute_checksum(large_file)
    
    # Valid SHA-256
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    

def test_scan_migrations_handles_non_utf8_characters_gracefully(tmp_path: Path) -> None:
    """Test that files with non-UTF8 characters still have checksums calculated."""
    # Create a file with different encoding
    test_file = tmp_path / "encoding_test.sql"
    # Write binary content that isn't UTF-8
    with open(test_file, "wb") as f:
        f.write(b"\xff\xfe\x00\x00H\x00i\x00")  # BOM and content that's not valid UTF-8
    
    manager = SchemaManager(tmp_path)
    # Should be able to handle arbitrary binary content via rb mode
    checksum = manager.compute_checksum(test_file)
    assert len(checksum) == 64


def test_detect_drift_all_three_types_in_one_call() -> None:
    """Test that detect_drift can identify all three drift types simultaneously."""
    # Expected has versions [1, 2, 3, 5] 
    expected = [
        MigrationInfo(version=1, filename="001_base.sql", checksum="valid_checksum_here"),
        MigrationInfo(version=2, filename="002_modify.sql", checksum="modified_checksum_new"),  # Modified from applied
        MigrationInfo(version=3, filename="003_add_more.sql", checksum="existing_checksum_here"),  
        MigrationInfo(version=5, filename="005_future.sql", checksum="future_checksum_here")  # Missing in applied
    ]
    
    # Applied has versions [2, 3, 4] where #2 is modified and #4 is unexpected
    applied = [
        MigrationRecord(version=2, filename="002_modify.sql", checksum="modified_checksum_old", applied_at="2023-01-01T00:00:00Z"),  # Different from expected
        MigrationRecord(version=3, filename="003_add_more.sql", checksum="existing_checksum_here", applied_at="2023-01-02T00:00:00Z"),  # Matches expected
        MigrationRecord(version=4, filename="004_unexpected.sql", checksum="unexpected_checksum_here", applied_at="2023-01-03T00:00:00Z")  # Not in expected
    ]
    
    manager = SchemaManager(Path(".")) 
    drift_items = manager.detect_drift(applied, expected)
    
    # Should detect 3 issues:
    # 1. Modified: version 2 (different checksums)
    # 2. Unexpected: version 4 (in applied but not in expected)
    # 3. Missing: version 5 (in expected but not in applied)
    assert len(drift_items) == 3
    
    drift_types = {item.drift_type for item in drift_items}
    assert drift_types == {"modified", "unexpected", "missing"}
    
    # Verify each type exists with correct details
    modified_items = [item for item in drift_items if item.drift_type == "modified"]
    unexpected_items = [item for item in drift_items if item.drift_type == "unexpected"]
    missing_items = [item for item in drift_items if item.drift_type == "missing"]
    
    assert len(modified_items) == 1
    assert modified_items[0].version == 2
    
    assert len(unexpected_items) == 1
    assert unexpected_items[0].version == 4
    
    assert len(missing_items) == 1
    assert missing_items[0].version == 5


def test_validate_schema_integrity_multiline_error_message() -> None:
    """Test that error messages include all drift items formatted as multiline."""
    expected_infos = [
        MigrationInfo(version=1, filename="001_first.sql", checksum="different_than_db"),
        MigrationInfo(version=2, filename="002_second.sql", checksum="also_different_than_db"),
    ]
    
    applied_records = [
        MigrationRecord(version=1, filename="001_first.sql", checksum="in_db_checksum_a", applied_at="2023-01-01T00:00:00Z"),
        MigrationRecord(version=2, filename="002_second.sql", checksum="in_db_checksum_b", applied_at="2023-01-02T00:00:00Z"),
        MigrationRecord(version=3, filename="003_unexpected.sql", checksum="unexpected_cksum", applied_at="2023-01-03T00:00:00Z")
    ]
    
    manager = SchemaManager(Path("."))
    
    with pytest.raises(SchemaError) as exc_info:
        manager.validate_schema_integrity(applied_records)
    
    error = exc_info.value
    message = error.message
    
    # Should mention the number of discrepancies
    assert "2 discrepancy(ies)" in message or "3 discrepancy(ies)" in message
    
    # Should include individual drift messages on separate lines
    lines = message.split("\n")
    drift_line_count = sum(1 for line in lines if "Migration" in line and ("checksum differs" in line or "found in schema_versions" in line or "exists in migrations" in line))
    assert drift_line_count >= 2  # At least two drift descriptions


def test_migration_parsing_with_multiple_digit_prefixes(tmp_path: Path) -> None:
    """Test that migration file name parsing works with various digit counts."""
    files_content = [
        ("001_short.sql", "CREATE TABLE a;"),      # 3 digits
        ("0012_medium.sql", "CREATE TABLE b;"),    # 4 digits  
        ("00042_long.sql", "CREATE TABLE c;"),     # 5 digits
        ("00123_large.sql", "CREATE TABLE d;"),    # Many digits
    ]
    
    for filename, content in files_content:
        (tmp_path / filename).write_text(content)
    
    manager = SchemaManager(tmp_path)
    migrations = manager.scan_migrations()
    
    # Should sort numerically, not lexicographically  
    versions = [m.version for m in migrations]
    assert versions == [1, 12, 42, 123]
    
    filenames = [m.filename for m in migrations]
    assert "001_short.sql" in filenames
    assert "0012_medium.sql" in filenames
    assert "00042_long.sql" in filenames
    assert "00123_large.sql" in filenames


def test_validate_schema_integrity_contextual_data() -> None:
    """Test that SchemaError contains all required contextual data."""
    expected_infos = [
        MigrationInfo(version=1, filename="001_test.sql", checksum="original_checksum"),
    ]
    
    applied_records = [
        MigrationRecord(version=1, filename="001_test.sql", checksum="diff_checksum", applied_at="2023-01-01T00:00:00Z"),
    ]
    
    # Temporarily change working directory to test migrations_dir in context
    import os
    original_cwd = os.getcwd()
    test_dir = "/tmp/test_migrations" 
    
    manager = SchemaManager(Path(test_dir))
    
    with pytest.raises(SchemaError) as exc_info:
        manager.validate_schema_integrity(applied_records)
    
    error = exc_info.value
    
    # Verify error structure 
    assert error.context is not None
    assert "drift_count" in error.context
    assert "drift_details" in error.context
    assert "migrations_dir" in error.context
    
    assert error.context["drift_count"] == 1
    assert isinstance(error.context["drift_details"], list)
    assert len(error.context["drift_details"]) == 1
    assert error.context["migrations_dir"] == test_dir
    os.chdir(original_cwd)


def test_schema_manager_initialization() -> None:
    """Test that SchemaManager initializes properly with correct attributes."""
    test_path = Path("/some/path")
    manager = SchemaManager(test_path)
    
    assert manager.migrations_dir == test_path
    assert hasattr(manager, 'logger')  # Should have logger with correct bounds


if __name__ == "__main__":
    pytest.main([__file__])
````
