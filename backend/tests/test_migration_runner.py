"""Tests for MigrationRunner service."""
from pathlib import Path
from datetime import datetime, timezone

import pytest

from second_brain.errors import SchemaError
from second_brain.services.migration_runner import MigrationResult, MigrationRunner, MIGRATION_LOCK_KEY
from second_brain.services.schema_manager import MigrationRecord, SchemaManager


class MockExecutor:
    """Mock executor for testing MigrationRunner."""

    def __init__(self, applied=None, lock_result=True):
        self.applied = applied or []
        self.lock_result = lock_result
        self.executed_sql = []
        self.recorded = []
        self.removed = []
        self.lock_acquired = False
        self.lock_released = False
        self.fail_on_sql = None

    def execute_sql(self, sql):
        if self.fail_on_sql and self.fail_on_sql in sql:
            raise RuntimeError(f"SQL execution failed: {self.fail_on_sql}")
        self.executed_sql.append(sql)

    def get_applied_migrations(self):
        return self.applied

    def record_migration(self, info, execution_time_ms):
        self.recorded.append((info, execution_time_ms))

    def remove_migration_record(self, version):
        self.removed.append(version)

    def acquire_advisory_lock(self, lock_key):
        self.lock_acquired = True
        return self.lock_result

    def release_advisory_lock(self, lock_key):
        self.lock_released = True


class TestGetPending:
    """Tests for get_pending method."""

    def test_get_pending_returns_correct_pending_list(self, tmp_path: Path) -> None:
        """Test get_pending returns correct pending migrations."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        (tmp_path / "003_third.sql").write_text("CREATE TABLE c;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum1 = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(
                version=1,
                filename="001_first.sql",
                checksum=checksum1,
                applied_at=datetime.now(timezone.utc)
            )
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        pending = runner.get_pending(executor.applied)
        
        assert len(pending) == 2
        assert [p.version for p in pending] == [2, 3]
        assert pending[0].filename == "002_second.sql"
        assert pending[1].filename == "003_third.sql"

    def test_get_pending_with_no_pending_returns_empty(self, tmp_path: Path) -> None:
        """Test get_pending with all migrations applied returns empty."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum1 = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        checksum2 = SchemaManager.compute_checksum(tmp_path / "002_second.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum1, applied_at=datetime.now(timezone.utc)),
            MigrationRecord(version=2, filename="002_second.sql", checksum=checksum2, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        pending = runner.get_pending(executor.applied)
        
        assert pending == []

    def test_get_pending_with_all_applied_returns_empty(self, tmp_path: Path) -> None:
        """Test get_pending when everything is applied."""
        (tmp_path / "001_only.sql").write_text("CREATE TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_only.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_only.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        pending = runner.get_pending(executor.applied)
        
        assert pending == []


class TestApplyPending:
    """Tests for apply_pending method."""

    def test_apply_pending_executes_migrations_in_version_order(self, tmp_path: Path) -> None:
        """Test apply_pending executes migrations in correct order."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        (tmp_path / "003_third.sql").write_text("CREATE TABLE c;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is True
        assert len(executor.executed_sql) == 3
        assert "CREATE TABLE a;" in executor.executed_sql[0]
        assert "CREATE TABLE b;" in executor.executed_sql[1]
        assert "CREATE TABLE c;" in executor.executed_sql[2]

    def test_apply_pending_records_each_migration_with_time(self, tmp_path: Path) -> None:
        """Test apply_pending records migrations with execution time."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is True
        assert len(executor.recorded) == 2
        assert executor.recorded[0][0].version == 1
        assert executor.recorded[1][0].version == 2
        assert all(isinstance(rec[1], int) for rec in executor.recorded)

    def test_apply_pending_dry_run_doesnt_execute_sql(self, tmp_path: Path) -> None:
        """Test dry_run mode doesn't execute SQL."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending(dry_run=True)
        
        assert result.success is True
        assert result.dry_run is True
        assert executor.executed_sql == []
        assert executor.recorded == []

    def test_apply_pending_dry_run_returns_pending_list(self, tmp_path: Path) -> None:
        """Test dry_run returns list of what would be applied."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending(dry_run=True)
        
        assert len(result.applied) == 2
        assert result.applied[0].version == 1
        assert result.applied[1].version == 2
        assert result.pending_count == 2

    def test_apply_pending_acquires_and_releases_lock(self, tmp_path: Path) -> None:
        """Test apply_pending acquires and releases advisory lock."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is True
        assert executor.lock_acquired is True
        assert executor.lock_released is True

    def test_apply_pending_releases_lock_on_error(self, tmp_path: Path) -> None:
        """Test apply_pending releases lock even on SQL error."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        executor.fail_on_sql = "CREATE TABLE b;"
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is False
        assert executor.lock_released is True

    def test_apply_pending_stops_on_first_sql_error(self, tmp_path: Path) -> None:
        """Test apply_pending stops on first error and returns partial result."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        (tmp_path / "003_third.sql").write_text("CREATE TABLE c;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        executor.fail_on_sql = "CREATE TABLE b;"
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is False
        assert len(result.applied) == 1
        assert result.applied[0].version == 1
        assert "002_second.sql" in result.error

    def test_apply_pending_with_no_pending_returns_success(self, tmp_path: Path) -> None:
        """Test apply_pending with no pending migrations returns success."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is True
        assert result.pending_count == 0

    def test_apply_pending_fails_if_lock_not_acquired(self, tmp_path: Path) -> None:
        """Test apply_pending fails when lock cannot be acquired."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor(lock_result=False)
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.apply_pending()
        
        assert result.success is False
        assert "Could not acquire migration lock" in result.error

    def test_apply_pending_checks_drift_before_applying(self, tmp_path: Path) -> None:
        """Test apply_pending validates schema integrity before applying."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        (tmp_path / "002_second.sql").write_text("CREATE TABLE b;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum="different_checksum", applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        with pytest.raises(SchemaError) as exc_info:
            runner.apply_pending()
        
        assert exc_info.value.code == "SCHEMA_DRIFT"


class TestRollbackLast:
    """Tests for rollback_last method."""

    def test_rollback_last_with_rollback_section_works(self, tmp_path: Path) -> None:
        """Test rollback_last successfully rolls back with rollback section."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;\n-- rollback:\nDROP TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.rollback_last()
        
        assert result.success is True
        assert len(result.rolled_back) == 1
        assert result.rolled_back[0].version == 1
        assert len(executor.executed_sql) == 1
        assert "DROP TABLE a;" in executor.executed_sql[0]
        assert executor.removed == [1]

    def test_rollback_last_without_rollback_section_raises_schema_error(self, tmp_path: Path) -> None:
        """Test rollback_last raises SchemaError when no rollback section."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        with pytest.raises(SchemaError) as exc_info:
            runner.rollback_last()
        
        assert exc_info.value.code == "NO_ROLLBACK_SQL"

    def test_rollback_last_with_empty_rollback_section_raises_schema_error(self, tmp_path: Path) -> None:
        """Test rollback_last raises SchemaError when rollback section is empty."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;\n-- rollback:\n-- just a comment")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        with pytest.raises(SchemaError) as exc_info:
            runner.rollback_last()
        
        assert exc_info.value.code == "NO_ROLLBACK_SQL"

    def test_rollback_last_with_no_applied_migrations_raises_schema_error(self, tmp_path: Path) -> None:
        """Test rollback_last raises SchemaError when no migrations applied."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;\n-- rollback:\nDROP TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor(applied=[])
        runner = MigrationRunner(schema_manager, executor)
        
        with pytest.raises(SchemaError) as exc_info:
            runner.rollback_last()
        
        assert exc_info.value.code == "NO_MIGRATIONS"

    def test_rollback_last_acquires_and_releases_lock(self, tmp_path: Path) -> None:
        """Test rollback_last acquires and releases advisory lock."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;\n-- rollback:\nDROP TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ])
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.rollback_last()
        
        assert result.success is True
        assert executor.lock_acquired is True
        assert executor.lock_released is True

    def test_rollback_last_fails_if_lock_not_acquired(self, tmp_path: Path) -> None:
        """Test rollback_last fails when lock cannot be acquired."""
        (tmp_path / "001_first.sql").write_text("CREATE TABLE a;\n-- rollback:\nDROP TABLE a;")
        
        schema_manager = SchemaManager(tmp_path)
        checksum = SchemaManager.compute_checksum(tmp_path / "001_first.sql")
        executor = MockExecutor(applied=[
            MigrationRecord(version=1, filename="001_first.sql", checksum=checksum, applied_at=datetime.now(timezone.utc)),
        ], lock_result=False)
        runner = MigrationRunner(schema_manager, executor)
        
        result = runner.rollback_last()
        
        assert result.success is False
        assert "Could not acquire migration lock for rollback" in result.error


class TestMigrationResult:
    """Tests for MigrationResult model."""

    def test_migration_result_serialization(self) -> None:
        """Test MigrationResult can be serialized."""
        result = MigrationResult(
            success=True,
            applied=[],
            rolled_back=[],
            dry_run=False,
            error=None,
            pending_count=0
        )
        
        data = result.model_dump()
        assert data["success"] is True
        assert data["dry_run"] is False
        assert data["error"] is None


class TestExtractForwardSql:
    """Tests for _extract_forward_sql static method."""

    def test_extract_forward_sql_without_rollback(self) -> None:
        """Test extract forward SQL when no rollback section."""
        sql = "CREATE TABLE test;"
        result = MigrationRunner._extract_forward_sql(sql)
        assert result == "CREATE TABLE test;"

    def test_extract_forward_sql_with_rollback(self) -> None:
        """Test extract forward SQL with rollback section."""
        sql = "CREATE TABLE test;\n-- rollback:\nDROP TABLE test;"
        result = MigrationRunner._extract_forward_sql(sql)
        assert result == "CREATE TABLE test;"

    def test_extract_forward_sql_case_insensitive(self) -> None:
        """Test extract forward SQL is case insensitive."""
        sql = "CREATE TABLE test;\n-- ROLLBACK:\nDROP TABLE test;"
        result = MigrationRunner._extract_forward_sql(sql)
        assert result == "CREATE TABLE test;"


class TestExtractRollbackSql:
    """Tests for _extract_rollback_sql static method."""

    def test_extract_rollback_sql_without_rollback(self) -> None:
        """Test extract rollback SQL when no rollback section."""
        sql = "CREATE TABLE test;"
        result = MigrationRunner._extract_rollback_sql(sql)
        assert result is None

    def test_extract_rollback_sql_with_rollback(self) -> None:
        """Test extract rollback SQL with rollback section."""
        sql = "CREATE TABLE test;\n-- rollback:\nDROP TABLE test;"
        result = MigrationRunner._extract_rollback_sql(sql)
        assert result is not None
        assert "DROP TABLE test;" in result

    def test_extract_rollback_sql_case_insensitive(self) -> None:
        """Test extract rollback SQL is case insensitive."""
        sql = "CREATE TABLE test;\n-- ROLLBACK:\nDROP TABLE test;"
        result = MigrationRunner._extract_rollback_sql(sql)
        assert result is not None
        assert "DROP TABLE test;" in result

    def test_extract_rollback_sql_returns_none_for_empty_rollback(self) -> None:
        """Test extract rollback SQL returns None for empty rollback section."""
        sql = "CREATE TABLE test;\n-- rollback:\n-- just a comment"
        result = MigrationRunner._extract_rollback_sql(sql)
        assert result is None

    def test_extract_rollback_sql_returns_none_for_whitespace_only_rollback(self) -> None:
        """Test extract rollback SQL returns None for whitespace-only rollback."""
        sql = "CREATE TABLE test;\n-- rollback:\n   \n  "
        result = MigrationRunner._extract_rollback_sql(sql)
        assert result is None


class TestMigrationRunnerInit:
    """Tests for MigrationRunner initialization."""

    def test_init_stores_schema_manager_and_executor(self, tmp_path: Path) -> None:
        """Test MigrationRunner stores schema_manager and executor."""
        schema_manager = SchemaManager(tmp_path)
        executor = MockExecutor()
        runner = MigrationRunner(schema_manager, executor)
        
        assert runner.schema_manager is schema_manager
        assert runner.executor is executor


class TestMigrationLockKey:
    """Tests for migration lock key constant."""

    def test_migration_lock_key_is_integer(self) -> None:
        """Test MIGRATION_LOCK_KEY is an integer."""
        assert isinstance(MIGRATION_LOCK_KEY, int)
        assert MIGRATION_LOCK_KEY == 728349261
