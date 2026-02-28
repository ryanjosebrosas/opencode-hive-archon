# Structured Plan: P1-07 Migration Runner with Advisory Locking and Rollback Support

---

# Feature: Migration Runner with Advisory Locking and Rollback Support

## Feature Description

Python migration runner service that applies pending database migrations in order, supports dry-run mode for preview, provides rollback capability via embedded rollback sections in migration files, and uses PostgreSQL advisory locks to prevent concurrent migration executions.

## User Story

As a database administrator, I want to apply schema migrations safely with preview and rollback capabilities, so that I can manage database schema changes without risking data loss or corruption from concurrent operations.

## Problem Statement

Existing schema management (SchemaManager) can scan migrations and detect drift but lacks execution capabilities. Without a runner, migrations must be applied manually, increasing risk of human error and concurrent execution conflicts. Rollback support is manual and error-prone.

## Solution Statement

Implement MigrationRunner with:
- Protocol-based executor interface for testability without live database
- Advisory locking using PostgreSQL `pg_try_advisory_lock` with fixed key `b"second_brain_migrations"`
- Dry-run mode that logs intended operations without execution
- Rollback support via `-- rollback:` comment sections in migration files
- Integration with SchemaManager for pending migration detection

Decisions:
- Protocol over abstract class — because Protocols enable easy mocking without inheritance hierarchy
- Fixed advisory lock key — because all migrations share the same namespace, preventing any parallel migrations across the system
- Rollback section extraction with regex line scanning — because simple and reliable, avoids complex AST parsing for comments

## Feature Metadata

- **Feature Type**: New Capability
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: `backend/src/second_brain/services/` (MigrationRunner), `backend/src/second_brain/tests/` (tests)
- **Dependencies**: P1-06 (SchemaManager)

### Slice Guardrails (Required)

- **Single Outcome**: Migration runner can apply pending migrations in order, supports dry-run, and rolls back last migration
- **Expected Files Touched**: `backend/src/second_brain/services/migration_runner.py` (exists), `backend/src/second_brain/tests/test_migration_runner.py` (exists)
- **Scope Boundary**: Does NOT include real PostgreSQL executor implementation (that's a separate feature), does NOT include CLI interface
- **Split Trigger**: If >15 test classes or need for complex state management, create separate plan for real executor

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/services/schema_manager.py` (lines 21-47) — Why: Contains `MigrationInfo` and `MigrationRecord` models that MigrationRunner uses
- `backend/src/second_brain/services/schema_manager.py` (lines 71-117) — Why: `scan_migrations()` method used by `get_pending()` to get expected migrations
- `backend/src/second_brain/services/schema_manager.py` (lines 119-179) — Why: `detect_drift()` logic for comparing expected vs applied migrations
- `backend/src/second_brain/errors.py` (lines 103-114) — Why: `SchemaError` exception class used for migration failures and drift detection
- `backend/tests/test_schema_manager.py` (lines 11-47) — Why: Test fixture patterns (tmp_path) to follow for migration runner tests
- `backend/src/second_brain/logging_config.py` — Why: `get_logger()` function for structured logging in MigrationRunner

### New Files to Create

- `backend/src/second_brain/services/migration_runner.py` (exists) — Main service: MigrationRunner, MigrationExecutor Protocol, MigrationResult model, extract_rollback_sql helper
- `backend/src/second_brain/tests/test_migration_runner.py` (exists) — Comprehensive tests with mock executor

### Related Memories (from memory.md)

- Memory: Strict gate workflow enforced for all feature plans — Relevance: Ensures this plan follows established quality gates
- Memory: Python-first with framework-agnostic contracts — Relevance: Protocol-based executor design follows portability guidelines
- Memory: Test fixture patterns from test_schema_manager.py — Relevance: Use tmp_path fixtures for migration file creation

### Relevant Documentation

> The execution agent SHOULD read these before implementing.

- [PostgreSQL Advisory Locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS)
  - Specific section: Advisory Locks
  - Why: Required for implementing `pg_try_advisory_lock` and `pg_advisory_unlock` in executor
- [Python Typing Protocols](https://docs.python.org/3/library/typing.html#typing.Protocol)
  - Specific section: Protocol classes
  - Why: Used for MigrationExecutor interface definition

### Patterns to Follow

> Specific patterns extracted from the codebase — include actual code examples from the project.

**SchemaManager logger binding** (from `backend/src/second_brain/services/schema_manager.py:59`):
```python
def __init__(self, migrations_dir: Path):
    self.migrations_dir = migrations_dir
    self.logger = logger.bind(component="SchemaManager")
```
- Why this pattern: Structured logging with component name for easier log filtering
- Common gotchas: Always bind logger in __init__, not per-call, for consistency

**Migration file pattern regex** (from `backend/src/second_brain/services/schema_manager.py:18`):
```python
MIGRATION_PATTERN = re.compile(r"^(\d+)_[a-z0-9_]+\.sql$")
```
- Why this pattern: Version prefix + snake_case filename + .sql extension, matches scan_migrations behavior
- Common gotchas: Leading zeros in version numbers are preserved as strings in filenames but parsed as integers

**Error context dict pattern** (from `backend/src/second_brain/errors.py:28-32`):
```python
def __init__(
    self,
    message: str,
    *,
    code: str = "UNKNOWN_ERROR",
    context: dict[str, Any] | None = None,
    retry_hint: bool = False,
) -> None:
    super().__init__(message)
    self.code = code
    self.message = message
    self.context = dict(context) if context else {}
    self.retry_hint = retry_hint
```
- Why this pattern: Consistent error handling with code, context dict, and retry hint
- Common gotchas: Always convert None context to empty dict, never modify passed-in context directly

**Test fixture pattern with tmp_path** (from `backend/tests/test_schema_manager.py:11-30`):
```python
def test_scan_migrations_finds_and_sorts_sql_files(tmp_path: Path) -> None:
    # Create mock migration files
    (tmp_path / "001_first_migration.sql").write_text("CREATE TABLE a;")
    (tmp_path / "003_third_migration.sql").write_text("ALTER TABLE a ADD COLUMN c;")
    (tmp_path / "002_second_migration.sql").write_text("CREATE TABLE b;")
```
- Why this pattern: pytest tmp_path fixture creates temporary directories cleaned up automatically
- Common gotchas: Use Path object methods like write_text, not open/write/close

**BaseModel properties pattern** (from `backend/src/second_brain/services/schema_manager.py:21-26`):
```python
class MigrationInfo(BaseModel):
    version: int
    filename: str
    checksum: str
```
- Why this pattern: Pydantic BaseModel provides validation and serialization automatically
- Common gotchas: All fields are required by default, use Optional | None for nullable fields

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

**Tasks:**
- Define MigrationResult model with success, message, applied_migrations, rolled_back_migrations fields and total_applied/total_rolled_back properties
- Define MigrationExecutor Protocol with abstract methods: execute_sql, insert_migration_record, delete_migration_record, get_applied_migrations, acquire_advisory_lock, release_advisory_lock
- Define ADVISORY_LOCK_KEY class variable on MigrationExecutor Protocol
- Implement extract_rollback_sql function using line scanning for `-- rollback:` marker
- Define MigrationRunner class with migrations_dir, executor, schema_manager, logger attributes

### Phase 2: Core Implementation

**Tasks:**
- Implement get_pending() method: scan migrations, get applied from executor, compare versions, return list of MigrationInfo
- Implement apply_pending() method: acquire advisory lock (skip in dry-run), iterate pending migrations, execute SQL and insert records (skip in dry-run), release lock, return MigrationResult
- Implement apply_pending() error handling: halt on first error, return MigrationResult with success=False and list of successfully applied migrations before error
- Implement rollback_last() method: get applied migrations, find max version by version, read file, extract rollback SQL, execute rollback (skip in dry-run), delete record (skip in dry-run), release lock, return MigrationResult

### Phase 3: Integration

**Tasks:**
- Add extract_rollback_sql to module exports (if needed)
- Ensure MigrationExecutor Protocol is imported from correct location
- Verify MigrationRunner uses SchemaManager from services module correctly
- Validate logging statements follow existing pattern with component binding

### Phase 4: Testing & Validation

**Tasks:**
- Create MockMigrationExecutor implementing MigrationExecutor Protocol with in-memory state tracking
- Create temp_migrations_dir fixture with sample migration files
- Write tests for MigrationResult model initialization and properties
- Write tests for extract_rollback_sql: no section, with section, case-insensitive, multiline, with comments
- Write tests for get_pending: all pending, some applied, none pending
- Write tests for apply_pending: no migrations, dry-run mode, execute and insert records, halts on error, lock failure
- Write tests for rollback_last: no applied, extracts and executes rollback SQL, missing file raises exception, no rollback section raises exception, dry-run mode, lock failure
- Write tests for advisory lock behavior: apply_pending acquires/releases lock, rollback_last acquires/releases lock

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.
>
> **Action keywords**: CREATE (new files), UPDATE (modify existing), ADD (insert new functionality),
> REMOVE (delete deprecated code), REFACTOR (restructure without changing behavior), MIRROR (copy pattern from elsewhere)
>
> **Tip**: For text-centric changes (templates, commands, configs), include exact **Current** / **Replace with**
> content blocks in IMPLEMENT. This eliminates ambiguity and achieves higher plan-to-implementation fidelity
> than prose descriptions. See `reference/piv-loop-practice.md` Section 3 for guidance.

### VERIFY backend/src/second_brain/services/migration_runner.py exists and complete

- **IMPLEMENT**: Verify migration_runner.py exists and contains: MigrationResult model (lines 25-39), MigrationExecutor Protocol (lines 42-76), extract_rollback_sql function (lines 79-99), MigrationRunner class (lines 102-355) with methods: __init__, get_pending, apply_pending, rollback_last
- **PATTERN**: Compare with `backend/src/second_brain/services/schema_manager.py:49-59` (SchemaManager class structure)
- **IMPORTS**: Verify imports: `from __future__ import annotations`, `from abc import abstractmethod`, `from pathlib import Path`, `from typing import Protocol, ClassVar`, `import re`, `from pydantic import BaseModel`, `from second_brain.errors import SchemaError`, `from second_brain.logging_config import get_logger`, `from second_brain.services.schema_manager import SchemaManager, MigrationInfo, MigrationRecord`
- **GOTCHA**: Protocol methods must use `@abstractmethod` decorator with `...` ellipsis body, not `pass`
- **VALIDATE**: `python -c "from second_brain.services.migration_runner import MigrationResult, MigrationExecutor, MigrationRunner, extract_rollback_sql; print('All imports successful')"`

### VERIFY MigrationResult model

- **IMPLEMENT**: Verify MigrationResult has fields: success (bool), message (str), applied_migrations (list[MigrationInfo]), rolled_back_migrations (list[MigrationInfo]); properties: total_applied (returns len(applied_migrations)), total_rolled_back (returns len(rolled_back_migrations))
- **PATTERN**: Follow `backend/src/second_brain/services/schema_manager.py:21-26` (MigrationInfo BaseModel pattern)
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Property methods should use `@property` decorator without parentheses when accessed
- **VALIDATE**: `python -c "from second_brain.services.migration_runner import MigrationResult; from second_brain.services.schema_manager import MigrationInfo; r = MigrationResult(success=True, message='test', applied_migrations=[MigrationInfo(version=1, filename='test.sql', checksum='abc')], rolled_back_migrations=[]); print(r.total_applied)"`

### VERIFY MigrationExecutor Protocol

- **IMPLEMENT**: Verify MigrationExecutor is a Protocol with ADVISORY_LOCK_KEY: ClassVar[bytes] = b"second_brain_migrations"; abstract methods: async def execute_sql(self, sql: str) -> None, async def insert_migration_record(self, migration: MigrationInfo) -> MigrationRecord, async def delete_migration_record(self, version: int) -> bool, async def get_applied_migrations(self) -> list[MigrationRecord], async def acquire_advisory_lock(self, lock_key: bytes) -> bool, async def release_advisory_lock(self, lock_key: bytes) -> bool
- **PATTERN**: Follow Python typing Protocol pattern from official docs
- **IMPORTS**: `from abc import abstractmethod`, `from typing import Protocol, ClassVar`
- **GOTCHA**: Protocol methods don't need implementation, use `...` ellipsis; ClassVar for class-level constants
- **VALIDATE**: `python -c "from second_brain.services.migration_runner import MigrationExecutor; print(f'Lock key: {MigrationExecutor.ADVISORY_LOCK_KEY}'); print('Protocol defined successfully')"`

### VERIFY extract_rollback_sql function

- **IMPLEMENT**: Verify function signature: `def extract_rollback_sql(migration_content: str) -> str | None`; implementation: splitlines, find `-- rollback:` (case-insensitive), return all content after marker, return None if not found or empty
- **PATTERN**: Follow `backend/src/second_brain/services/schema_manager.py:71-90` (scan_migrations pattern for file content processing)
- **IMPORTS**: No additional imports needed (re not needed for simple line scanning)
- **GOTCHA**: Case-insensitive check with `lower()`, keep original case for returned SQL; strip whitespace before checking empty
- **VALIDATE**: `python -c "from second_brain.services.migration_runner import extract_rollback_sql; sql = 'CREATE TABLE test;\\n-- rollback:\\nDROP TABLE test;'; print(extract_rollback_sql(sql))"`

### VERIFY MigrationRunner __init__

- **IMPLEMENT**: Verify __init__ signature: `def __init__(self, migrations_dir: Path, executor: MigrationExecutor)`; sets: self.migrations_dir = migrations_dir, self.executor = executor, self.logger = logger.bind(component="MigrationRunner"), self.schema_manager = SchemaManager(migrations_dir)
- **PATTERN**: Follow `backend/src/second_brain/services/schema_manager.py:57-60` (SchemaManager __init__)
- **IMPORTS**: `from second_brain.logging_config import get_logger`
- **GOTCHA**: Always import logger at module level, not inside __init__
- **VALIDATE**: `python -c "from pathlib import Path; from second_brain.services.migration_runner import MigrationRunner; from tests.test_migration_runner import MockMigrationExecutor; runner = MigrationRunner(Path('.'), MockMigrationExecutor()); print(runner.logger)"`

### VERIFY MigrationRunner get_pending method

- **IMPLEMENT**: Verify async method: `async def get_pending(self) -> list[MigrationInfo]`; implementation: expected = schema_manager.scan_migrations(), applied = await executor.get_applied_migrations(), applied_versions = {r.version for r in applied}, return [m for m in expected if m.version not in applied_versions]
- **PATTERN**: Follow `backend/src/second_brain/services/schema_manager.py:119-135` (detect_drift comparison logic)
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Ensure async/await for executor calls, synchronous for schema_manager calls
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestGetPending::test_get_pending_returns_all_for_new_db -v`

### VERIFY MigrationRunner apply_pending method - early return

- **IMPLEMENT**: Verify apply_pending signature: `async def apply_pending(self, *, dry_run: bool = False) -> MigrationResult`; early return when no pending: return MigrationResult(success=True, message="No pending migrations to apply", applied_migrations=[], rolled_back_migrations=[])
- **PATTERN**: Follow error result pattern from `backend/src/second_brain/services/migration_runner.py:206-211`
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Use `*` before dry_run for keyword-only argument
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestApplyPending::test_apply_pending_returns_empty_when_no_migrations -v`

### VERIFY MigrationRunner apply_pending method - advisory lock acquisition

- **IMPLEMENT**: Verify lock acquisition: lock_acquired = await executor.acquire_advisory_lock(MigrationExecutor.ADVISORY_LOCK_KEY); if not dry_run and not lock_acquired: raise SchemaError("Could not acquire advisory lock...", code="CONCURRENT_MIGRATION_LOCK")
- **PATTERN**: Follow SchemaError raising from `backend/src/second_brain/services/schema_manager.py:87-94`
- **IMPORTS**: `from second_brain.errors import SchemaError`
- **GOTCHA**: Skip lock check in dry_run mode; use SchemaError not generic Exception
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestApplyPending::test_apply_pending_fails_on_lock_failure -v`

### VERIFY MigrationRunner apply_pending method - migration execution loop

- **IMPLEMENT**: Verify loop: for migration in pending_migrations: read file content from migrations_dir/migration.filename; if dry_run: log info; else: await executor.execute_sql(migration_sql), await executor.insert_migration_record(migration), log info; append migration to applied_migrations
- **PATTERN**: Follow file reading pattern from `backend/src/second_brain/services/schema_manager.py:96-102`
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Use encoding="utf-8" for read_text; handle exceptions and return error result
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestApplyPending::test_apply_pending_executes_sql_and_inserts_records -v`

### VERIFY MigrationRunner apply_pending method - error handling

- **IMPLEMENT**: Verify error handling: except Exception as e: error_msg = f"Failed to apply migration {migration.version}: ...", logger.error with context, return MigrationResult(success=False, message=error_msg, applied_migrations=applied_migrations if not dry_run else [], rolled_back_migrations=[])
- **PATTERN**: Follow error result pattern from `backend/src/second_brain/services/migration_runner.py:206-211`
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Return empty applied_migrations in dry_run even on error (no actual execution); use applied_migrations if not dry_run for successful before error
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestApplyPending::test_apply_pending_halts_on_error -v`

### VERIFY MigrationRunner apply_pending method - lock release

- **IMPLEMENT**: Verify finally block: if not dry_run: try: await executor.release_advisory_lock(MigrationExecutor.ADVISORY_LOCK_KEY), logger.debug; except Exception as e: logger.warning
- **PATTERN**: Follow try/except pattern from `backend/src/second_brain/services/migration_runner.py:221-230`
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Always release lock even on error; wrap release in try/except to avoid masking original error
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestAdvisoryLockBehavior::test_apply_pending_acquires_and_releases_lock -v`

### VERIFY MigrationRunner rollback_last method - early return

- **IMPLEMENT**: Verify rollback_last signature: `async def rollback_last(self, *, dry_run: bool = False) -> MigrationResult`; early return when no applied: return MigrationResult(success=True, message="No migrations to roll back", applied_migrations=[], rolled_back_migrations=[])
- **PATTERN**: Follow early return pattern from apply_pending
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Use keyword-only argument with `*` before dry_run
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestRollbackLast::test_rollback_last_returns_empty_without_applied_migrations -v`

### VERIFY MigrationRunner rollback_last method - find last migration

- **IMPLEMENT**: Verify finding last: applied = await executor.get_applied_migrations(); last_migration = max(applied, key=lambda r: r.version); last_migration_filepath = migrations_dir / last_migration.filename; check file exists, raise SchemaError if not
- **PATTERN**: Follow max pattern from Python builtins
- **IMPORTS**: No additional imports needed
- **GOTCHA**: max with key function to find highest version; use Path / operator for joining paths
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestRollbackLast::test_rollback_last_uses_rollback_section_from_sql_file -v`

### VERIFY MigrationRunner rollback_last method - extract and execute rollback SQL

- **IMPLEMENT**: Verify rollback execution: migration_content = file.read_text(); rollback_sql = extract_rollback_sql(migration_content); if rollback_sql is None: raise SchemaError("No rollback section found...", code="NO_ROLLBACK_SECTION"); if dry_run: log info; else: await executor.execute_sql(rollback_sql), await executor.delete_migration_record(last_migration.version), log info
- **PATTERN**: Follow extract_rollback_sql usage from line 286
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Raise SchemaError with specific code if no rollback section; skip execution in dry_run
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestRollbackLast::test_rollback_last_without_rollback_section_raises_exception -v`

### VERIFY MigrationRunner rollback_last method - missing file handling

- **IMPLEMENT**: Verify missing file: if not last_migration_filepath.exists(): raise SchemaError(f"Cannot rollback migration {last_migration.version}...", code="MISSING_ROLLBACK_FILE", context={version, filename, filepath})
- **PATTERN**: Follow SchemaError raising from `backend/src/second_brain/services/schema_manager.py:87-94`
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Include full context dict with version, filename, filepath for debugging
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestRollbackLast::test_rollback_last_missing_file_raises_exception -v`

### VERIFY MigrationRunner rollback_last method - lock behavior

- **IMPLEMENT**: Verify lock acquisition in rollback: lock_acquired = await executor.acquire_advisory_lock(MigrationExecutor.ADVISORY_LOCK_KEY); if not dry_run and not lock_acquired: raise SchemaError(...); finally: if not dry_run: try: await executor.release_advisory_lock(...) except: logger.warning
- **PATTERN**: Mirror lock pattern from apply_pending
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Same lock acquisition and release pattern; skip in dry_run
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestAdvisoryLockBehavior::test_rollback_last_acquires_and_releases_lock -v`

### VERIFY MockMigrationExecutor in tests

- **IMPLEMENT**: Verify MockMigrationExecutor implements MigrationExecutor: has __init__ with executed_sqls, inserted_records, deleted_versions, applied_migrations lists, advisory_lock_acquired bool; methods: execute_sql (appends to executed_sqls), insert_migration_record (creates MigrationRecord and appends), delete_migration_record (removes from applied_migrations), get_applied_migrations (returns copy of applied_migrations), acquire_advisory_lock (returns advisory_lock_acquired), release_advisory_lock (returns True)
- **PATTERN**: Follow Mock implementation from `backend/src/second_brain/tests/test_migration_runner.py:16-54`
- **IMPORTS**: `from datetime import datetime`, `from unittest.mock import AsyncMock, MagicMock`
- **GOTCHA**: All methods must be async even in mock; use `copy()` to return lists without exposing internal state
- **VALIDATE**: `python -c "from tests.test_migration_runner import MockMigrationExecutor; import asyncio; async def test(): m = MockMigrationExecutor(); print(await m.acquire_advisory_lock(b'test')); asyncio.run(test())"`

### VERIFY test fixtures

- **IMPLEMENT**: Verify temp_migrations_dir fixture creates temporary directory with migration files: 001_initial_schema.sql, 002_add_name_field.sql, 003_add_rollback_section.sql; mock_executor fixture returns MockMigrationExecutor; migration_runner fixture returns MigrationRunner(temp_migrations_dir, mock_executor)
- **PATTERN**: Follow fixture pattern from `backend/tests/test_schema_manager.py:56-72`
- **IMPORTS**: `import tempfile`, `from pathlib import Path`, `from typing import Generator`
- **GOTCHA**: Use yield in fixtures for cleanup; create files before yielding
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestMigrationRunnerInit::test_init -v`

### VERIFY TestMigrationResult test class

- **IMPLEMENT**: Verify test_init checks basic MigrationResult initialization with success, message, applied_migrations, rolled_back_migrations; test_properties checks total_applied and total_rolled_back properties return correct counts
- **PATTERN**: Follow model test pattern from `backend/tests/test_schema_manager.py:336-368`
- **IMPORTS**: `import pytest`, `from second_brain.services.migration_runner import MigrationResult`
- **GOTCHA**: Use assert statements, not pytest.raises for basic initialization tests
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestMigrationResult -v`

### VERIFY TestExtractRollbackSql test class

- **IMPLEMENT**: Verify tests: test_no_rollback_section (returns None), test_with_rollback_section (extracts SQL after marker), test_different_case_rollback (case-insensitive), test_multiline_rollback (multiline SQL), test_rollback_with_comments (includes comments in result)
- **PATTERN**: Follow extraction test pattern from `backend/tests/test_schema_manager.py:114-131`
- **IMPORTS**: `import pytest`, `from second_brain.services.migration_runner import extract_rollback_sql`
- **GOTCHA**: Test edge cases: empty rollback, only whitespace, case variations, comments
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestExtractRollbackSql -v`

### VERIFY TestGetPending test class

- **IMPLEMENT**: Verify tests: test_get_pending_returns_all_for_new_db (all migrations pending), test_get_pending_filters_applied (filters out already applied migrations)
- **PATTERN**: Follow comparison test pattern from `backend/tests/test_schema_manager.py:133-155`
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Use MockMigrationExecutor.applied_migrations to set initial state
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestGetPending -v`

### VERIFY TestApplyPending test class

- **IMPLEMENT**: Verify tests: test_apply_pending_returns_empty_when_no_migrations (early return), test_apply_pending_dry_run (no execution in dry run), test_apply_pending_executes_sql_and_inserts_records (executes and records), test_apply_pending_halts_on_error (stops on error), test_apply_pending_fails_on_lock_failure (raises SchemaError)
- **PATTERN**: Follow migration test pattern with mock executor
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Test dry_run separately; test error returns partial success; test lock failure raises SchemaError
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestApplyPending -v`

### VERIFY TestRollbackLast test class

- **IMPLEMENT**: Verify tests: test_rollback_last_returns_empty_without_applied_migrations (early return), test_rollback_last_uses_rollback_section_from_sql_file (extracts and executes), test_rollback_last_missing_file_raises_exception (SchemaError on missing file), test_rollback_last_without_rollback_section_raises_exception (SchemaError on no rollback section), test_rollback_last_dry_run (no execution in dry run), test_rollback_last_fails_on_lock_failure (raises SchemaError)
- **PATTERN**: Follow rollback test pattern with error cases
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Test all error paths; verify record deletion; verify rollback SQL execution
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestRollbackLast -v`

### VERIFY TestAdvisoryLockBehavior test class

- **IMPLEMENT**: Verify tests: test_apply_pending_acquires_and_releases_lock (mock executor calls acquire/release), test_rollback_last_acquires_and_releases_lock (same for rollback)
- **PATTERN**: Follow mock call verification pattern
- **IMPORTS**: `from unittest.mock import MagicMock`, `from unittest.mock import AsyncMock`
- **GOTCHA**: Use MagicMock(wraps=Protocol) for Protocol; use assert_called_once_with to verify exact calls
- **VALIDATE**: `python -m pytest backend/src/second_brain/tests/test_migration_runner.py::TestAdvisoryLockBehavior -v`

---

## TESTING STRATEGY

### Unit Tests

All tests use MockMigrationExecutor implementing MigrationExecutor Protocol for full isolation from database. Test coverage includes:
- MigrationResult model: initialization, properties
- extract_rollback_sql function: no section, with section, case-insensitive, multiline, with comments
- get_pending: all pending, some applied, none pending
- apply_pending: no migrations, dry-run mode, execute and insert records, halts on error, lock failure
- rollback_last: no applied, extracts and executes rollback SQL, missing file raises exception, no rollback section raises exception, dry-run mode, lock failure
- advisory lock behavior: apply_pending acquires/releases lock, rollback_last acquires/releases lock

### Integration Tests

Integration tests deferred to real executor implementation (separate feature). Current tests verify protocol contract compliance through MockMigrationExecutor.

### Edge Cases

- Empty migrations directory: get_pending returns empty list, apply_pending returns success message
- Concurrent migration lock failure: SchemaError raised with CONCURRENT_MIGRATION_LOCK code
- Missing rollback section: SchemaError raised with NO_ROLLBACK_SECTION code
- Missing migration file: SchemaError raised with MISSING_ROLLBACK_FILE code
- Dry-run mode with errors: returns MigrationResult with empty applied_migrations (no actual execution)

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.
> Full validation depth is required for every slice; one proof signal is not enough.

### Level 1: Syntax & Style
```bash
cd backend
ruff check src/second_brain/services/migration_runner.py
ruff check src/second_brain/tests/test_migration_runner.py
```

### Level 2: Type Safety
```bash
cd backend
mypy src/second_brain/services/migration_runner.py
mypy src/second_brain/tests/test_migration_runner.py
```

### Level 3: Unit Tests
```bash
cd backend
pytest src/second_brain/tests/test_migration_runner.py -v
```

### Level 4: Integration Tests
```bash
cd backend
pytest src/second_brain/tests/ -k migration -v
```

### Level 5: Manual Validation

Feature-specific manual testing steps:
1. Create temporary migrations directory with files: `001_initial.sql`, `002_add_field.sql` with `-- rollback:` sections
2. Run test suite and verify all tests pass
3. Verify advisory lock key is `b"second_brain_migrations"` constant
4. Verify dry-run mode doesn't execute SQL (check mock executor state in tests)
5. Verify rollback extracts SQL after `-- rollback:` marker correctly

### Level 6: Additional Validation (Optional)

None required for this feature.

---

## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable
> only after running the code). Check off Implementation items during execution.
> Leave Runtime items for manual testing or post-deployment verification.

### Implementation (verify during execution)

- [ ] MigrationResult model exists with required fields and properties
- [ ] MigrationExecutor Protocol defined with all abstract methods and ADVISORY_LOCK_KEY
- [ ] extract_rollback_sql function correctly extracts rollback sections
- [ ] MigrationRunner class implements get_pending, apply_pending, rollback_last
- [ ] apply_pending acquires advisory lock, executes migrations in order, releases lock
- [ ] apply_pending supports dry-run mode (no execution)
- [ ] apply_pending halts on error and returns partial results
- [ ] rollback_last extracts and executes rollback SQL from file
- [ ] rollback_last supports dry-run mode (no execution)
- [ ] rollback_last raises SchemaError for missing file or no rollback section
- [ ] Advisory lock key is `b"second_brain_migrations"`
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage includes all public methods and edge cases

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify end-to-end workflows
- [ ] MockMigrationExecutor correctly implements MigrationExecutor Protocol
- [ ] Tests verify lock acquisition and release in both apply_pending and rollback_last
- [ ] Tests verify dry-run mode doesn't execute actual SQL
- [ ] Tests verify rollback SQL is extracted and executed correctly
- [ ] No regressions in existing functionality

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

- Protocol over abstract class: Enables easy mocking without inheritance hierarchy. MockMigrationExecutor can implement methods directly without subclassing constraints.
- Fixed advisory lock key: All migrations share namespace `b"second_brain_migrations"` to prevent any concurrent migrations across the system.
- Dry-run skips lock acquisition: Dry-run is read-only preview, no actual database state changes, so lock not needed.
- Extract rollback SQL via line scanning: Simple regex or line-by-line scanning is sufficient for comment extraction. Avoids complex SQL parsing.
- Error returns partial success: When migration fails mid-sequence, return MigrationResult with successfully applied migrations before error. Caller can decide what to do.

### Risks

- Risk 1: Real executor implementation (not in this slice) must correctly implement advisory locks using PostgreSQL `pg_try_advisory_lock` and `pg_advisory_unlock`. Mitigation: Protocol interface is explicit; implementation must follow contract.
- Risk 2: Rollback sections can be malformed (no actual SQL, only comments). Mitigation: extract_rollback_sql strips whitespace but doesn't validate SQL syntax. Executor will handle SQL errors.
- Risk 3: Concurrent processes may attempt migrations simultaneously before lock acquisition. Mitigation: Advisory lock is PostgreSQL-level, not Python-level, so works across processes.

### Confidence Score: 9/10

- **Strengths**: Protocol-based design is testable and clean. Mock executor enables comprehensive tests without database. Lock contract is explicit. Dry-run and rollback logic is straightforward.
- **Uncertainties**: None significant. Real executor implementation (separate feature) will verify Protocol contract in practice.
- **Mitigations**: Comprehensive test coverage with mock executor validates all logic paths. Protocol documentation clear for future executor implementation.
