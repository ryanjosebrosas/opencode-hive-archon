from __future__ import annotations

import pathlib


def test_migration_file_exists():
    """Test that the fulltext search migration file exists."""
    migration_file = pathlib.Path("migrations/008_fulltext_search.sql")
    assert migration_file.exists()


def test_tsvector_column_added():
    """Test that tsvector column is added to the migration SQL."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "content_tsv tsvector" in sql_content


def test_gin_index_created():
    """Test that GIN index is created in the migration SQL."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "USING GIN" in sql_content
    assert "content_tsv" in sql_content


def test_trigger_function_created():
    """Test that the trigger function is created in the migration SQL."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "knowledge_chunks_tsvector_update" in sql_content


def test_trigger_attached_to_table():
    """Test that the trigger is attached to the knowledge_chunks table."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "CREATE TRIGGER" in sql_content
    assert "knowledge_chunks" in sql_content


def test_trigger_fires_on_insert():
    """Test that the trigger fires on INSERT operations."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "BEFORE INSERT" in sql_content


def test_trigger_fires_on_update():
    """Test that the trigger fires on UPDATE operations."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "BEFORE INSERT OR UPDATE" in sql_content


def test_rpc_function_created():
    """Test that the RPC search function is created."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "search_knowledge_chunks_fulltext" in sql_content


def test_rpc_supports_websearch_mode():
    """Test that the RPC function supports websearch mode."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "websearch_to_tsquery" in sql_content


def test_rpc_supports_phrase_mode():
    """Test that the RPC function supports phrase search mode."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "phraseto_tsquery" in sql_content


def test_rpc_supports_simple_mode():
    """Test that the RPC function supports simple search mode."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "plainto_tsquery" in sql_content


def test_rpc_filters_active_status():
    """Test that the RPC function filters for active chunks."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "kc.status = 'active'" in sql_content


def test_rpc_returns_rank_column():
    """Test that the RPC function returns a rank column."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "ts_rank_cd" in sql_content


def test_rpc_granted_to_service_role():
    """Test that the RPC function is granted to service_role."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "GRANT EXECUTE" in sql_content
    assert "service_role" in sql_content


def test_trigger_uses_english_language():
    """Test that the trigger function uses English language for text processing."""
    sql_content = pathlib.Path("migrations/008_fulltext_search.sql").read_text()
    assert "to_tsvector('english'" in sql_content