from __future__ import annotations
from pathlib import Path
from typing import Any
from importlib.util import spec_from_file_location, module_from_spec
import subprocess
import sys


def load_script_as_module(filepath: str) -> Any:
    """Load a Python script as a module."""
    spec = spec_from_file_location("mig_check", filepath)
    if spec is None:
        raise ValueError(f"Could not load spec from file {filepath}")
    module = module_from_spec(spec)
    if spec.loader is None:
        raise ValueError(f"Specification {spec} has no loader") 
    spec.loader.exec_module(module)
    return module


def test_additive_migration_passes(tmp_path: Path) -> None:
    """Test that additive migrations (CREATE TABLE, ADD COLUMN) pass the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    # Create a temporary migration with additive changes
    migration_path = tmp_path / "test_additive.sql"
    migration_content = """
    CREATE TABLE test_table (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL
    );
    
    INSERT INTO test_table (name) VALUES ('test');
    
    ALTER TABLE test_table ADD COLUMN email TEXT;
    CREATE INDEX idx_test_email ON test_table(email);
    """
    migration_path.write_text(migration_content)
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert len(failures) == 0, f"Expected no failures, got: {failures}"
    # No warnings expected for pure additive changes
    # (Some might appear based on the implementation, adjust as needed)


def test_drop_table_fails(tmp_path: Path) -> None:
    """Test that DROP TABLE fails the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_drop_table.sql"
    migration_path.write_text("DROP TABLE users;")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert any("DROP TABLE" in failure for failure in failures), f"Expected DROP TABLE failure, got: {failures}"


def test_drop_column_fails(tmp_path: Path) -> None:
    """Test that DROP COLUMN fails the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_drop_column.sql"
    migration_path.write_text("ALTER TABLE users DROP COLUMN email;")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert any("DROP COLUMN" in failure for failure in failures), f"Expected DROP COLUMN failure, got: {failures}"


def test_alter_type_narrowing_fails(tmp_path: Path) -> None:
    """Test that ALTER TYPE narrowing fails (text -> varchar)."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_alter_type.sql"
    migration_path.write_text("ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(100);")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert len(failures) > 0, f"Expected ALTER TYPE failure, got: {failures}"
    assert any("ALTER COLUMN ... TYPE" in failure for failure in failures), f"Expected ALTER TYPE failure, got: {failures}"


def test_drop_constraint_add_constraint_allowed(tmp_path: Path) -> None:
    """Test that DROP CONSTRAINT followed by ADD CONSTRAINT is allowed."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_constraint_update.sql"
    migration_content = """
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_check;
    ALTER TABLE users ADD CONSTRAINT users_email_check CHECK (email LIKE '%@%');
    """
    migration_path.write_text(migration_content)
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    # Should pass despite having "DROP" operations as long as they're paired with ADD
    # The current implementation doesn't have fine-grained control for this, but should not trigger for constraints
    assert len(failures) == 0, f"Expected no failures for allowed constraint pattern, got: {failures}"


def test_truncate_fails(tmp_path: Path) -> None:
    """Test that TRUNCATE fails the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_truncate.sql"
    migration_path.write_text("TRUNCATE users;")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert any("TRUNCATE" in failure for failure in failures), f"Expected TRUNCATE failure, got: {failures}"


def test_delete_without_where_fails(tmp_path: Path) -> None:
    """Test that DELETE FROM without WHERE fails."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_delete_no_where.sql"
    migration_path.write_text("DELETE FROM users;")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert len(failures) > 0, f"Expected DELETE failure, got: {failures}"
    

def test_add_index_passes(tmp_path: Path) -> None:
    """Test that ADD INDEX passes the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_add_index.sql"
    migration_path.write_text("CREATE INDEX idx_users_email ON users(email);")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert len(failures) == 0, f"Expected no failures for CREATE INDEX, got: {failures}"


def test_existing_migrations_pass():
    """Test that existing migration files all pass the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migrations_dir = Path("backend/migrations")
    assert migrations_dir.exists(), f"Migrations directory does not exist: {migrations_dir}"
    
    migration_files = list(migrations_dir.glob("*.sql"))
    assert len(migration_files) > 0, f"No migration files found in: {migrations_dir}"
    
    for migration_file in migration_files:
        try:
            failures, warnings = mig_check.check_file_for_destructive_sql(migration_file)
            assert len(failures) == 0, f"Existing migration {migration_file.name} failed policy check: {failures}"
        except FileNotFoundError:
            # If the file doesn't exist, skip the test
            continue


def test_empty_file_passes(tmp_path: Path) -> None:
    """Test that an empty file passes the check."""
    script_path = Path("backend/scripts/check_migrations.py")
    mig_check = load_script_as_module(str(script_path))
    
    migration_path = tmp_path / "test_empty.sql"
    migration_path.write_text("")
    
    failures, warnings = mig_check.check_file_for_destructive_sql(migration_path)
    assert len(failures) == 0, f"Expected no failures for empty file, got: {failures}"


def test_command_line_single_file():
    """Test that the command line interface works for a single file."""
    script_path = Path("backend/scripts/check_migrations.py")
    
    # Test that the script can be run with --file flag on an existing legal migration
    result = subprocess.run([
        sys.executable, str(script_path), "--file", "backend/migrations/001_knowledge_schema.sql"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, f"Command failed with return code {result.returncode}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
