import tempfile
from pathlib import Path
import importlib.util


# Import the script using importlib since direct import doesn't work properly
def get_script_module():
    """Get the schema docs script module via importlib."""
    script_path = Path(__file__).parent.parent / "scripts" / "generate_schema_docs.py"
    spec = importlib.util.spec_from_file_location("generate_schema_docs", script_path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_import():
    """Test that the script module can be imported."""
    mod = get_script_module()
    assert hasattr(mod, 'parse_sql_file')
    assert hasattr(mod, 'generate_markdown_docs')
    print("✓ Script module can be imported successfully")


def test_parse_create_table(tmp_path):
    """Test parse_create_table extracts table name and columns from simple DDL."""
    # Create a test migration file
    test_sql = '''CREATE TABLE test_table (
      id    serial primary key,
      name  text not null,
      age   integer check(age > 0)
    );
    
    ALTER TABLE test_table ENABLE ROW LEVEL SECURITY;'''
    
    migration_file = tmp_path / "test_migration.sql"
    migration_file.write_text(test_sql)
    
    # Get module instance
    mod = get_script_module()
    result = mod.parse_sql_file(migration_file)
    
    tables = result['tables']
    assert len(tables) == 1
    assert tables[0]['name'] == 'test_table'
    
    # Test column parsing separately
    columns = mod.parse_table_columns(tables[0]['definition'])
    assert len(columns) == 3
    assert any(c['name'] == 'id' and 'serial' in c['type'].lower() for c in columns)
    assert any(c['name'] == 'name' and 'text' in c['type'].lower() for c in columns)
    print("✓ parse_create_table function works correctly")


def test_parse_create_index(tmp_path):
    """Test parse_create_index extracts index info."""
    test_sql = '''
    CREATE TABLE test_table (
      id    serial primary key,
      name  text
    );
    
    CREATE INDEX IF NOT EXISTS test_idx ON test_table (name);'''
    
    migration_file = tmp_path / "test_migration.sql"
    migration_file.write_text(test_sql)
    
    # Get module instance
    mod = get_script_module()
    result = mod.parse_sql_file(migration_file)
    
    indexes = result['indexes']
    assert len(indexes) == 1
    assert indexes[0]['name'] == 'test_idx'
    print("✓ parse_create_index function works correctly")


def test_generate_docs(tmp_path):
    """Test generate_docs produces non-empty output for migration files."""
    # Create a temp migration file
    test_sql = '''-- Test migration
    CREATE TABLE test_users (
      id    serial primary key,
      email text not null
    );
    
    CREATE INDEX IF NOT EXISTS users_email_idx ON test_users (email);
    
    ALTER TABLE test_users ENABLE ROW LEVEL SECURITY;'''
    
    migration_file = tmp_path / "001_test.sql"
    migration_file.write_text(test_sql)
    
    # Get module instance
    mod = get_script_module()
    
    # Parse the file
    result = mod.parse_sql_file(migration_file)
    
    # Generate docs from the parsed result
    markdown = mod.generate_markdown_docs([result])
    
    assert len(markdown) > 0
    assert 'Table: `test_users`' in markdown
    assert '`users_email_idx`' in markdown
    assert 'Row Level Security enabled' in markdown
    print("✓ generate_docs function produces expected output")


def test_generated_output_contains_expected_tables(tmp_path):
    """Test generated output contains all expected table names."""
    test_sql = '''-- Test migration
    CREATE TABLE test_one (
      id    serial primary key
    );
    
    CREATE TABLE test_two (
      id    serial primary key
    );
    
    ALTER TABLE test_one ENABLE ROW LEVEL SECURITY;'''
    
    migration_file = tmp_path / "001_test.sql"
    migration_file.write_text(test_sql)
    
    # Get module instance
    mod = get_script_module()
    
    # Parse the file
    result = mod.parse_sql_file(migration_file)
    
    # Generate docs
    markdown = mod.generate_markdown_docs([result])
    
    assert 'Table: `test_one`' in markdown
    assert 'Table: `test_two`' in markdown
    assert 'Row Level Security enabled' in markdown
    print("✓ Generated output contains expected table names")


def run_tests():
    """Run all tests."""
    print("Running schema documentation generation tests...")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_script_import()
        test_parse_create_table(tmp_path)
        test_parse_create_index(tmp_path)
        test_generate_docs(tmp_path)
        test_generated_output_contains_expected_tables(tmp_path)
    
    print("\n✓ All tests passed!")


if __name__ == '__main__':
    run_tests()