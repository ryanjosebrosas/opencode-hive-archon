from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

from second_brain.services.supabase import SupabaseProvider


# ---------------------------------------------------------------------------
# SQL structure tests (migration content assertions)
# ---------------------------------------------------------------------------

MIGRATION = pathlib.Path("migrations/010_trigram_search.sql")


def test_migration_file_exists() -> None:
    assert MIGRATION.exists()


def _sql() -> str:
    return MIGRATION.read_text()


def test_pg_trgm_extension_enabled() -> None:
    assert "pg_trgm" in _sql()


def test_gin_trigram_index_created() -> None:
    sql = _sql()
    assert "USING GIN" in sql
    assert "gin_trgm_ops" in sql


def test_index_name_follows_convention() -> None:
    assert "knowledge_entities_name_trgm_idx" in _sql()


def test_rpc_function_created() -> None:
    assert "search_knowledge_entities_fuzzy" in _sql()


def test_rpc_has_search_term_parameter() -> None:
    assert "search_term" in _sql()


def test_rpc_has_similarity_threshold_parameter() -> None:
    sql = _sql()
    assert "similarity_threshold" in sql
    assert "DEFAULT 0.3" in sql


def test_rpc_has_match_count_parameter() -> None:
    sql = _sql()
    assert "match_count" in sql
    assert "DEFAULT 10" in sql


def test_rpc_has_filter_type_parameter() -> None:
    assert "filter_type" in _sql()


def test_rpc_returns_similarity_column() -> None:
    sql = _sql()
    assert "similarity" in sql
    assert "float" in sql


def test_rpc_uses_similarity_function() -> None:
    assert "extensions.similarity" in _sql()


def test_rpc_uses_set_config_for_threshold() -> None:
    assert "set_config('pg_trgm.similarity_threshold'" in _sql()


def test_rpc_uses_trigram_operator() -> None:
    assert "ke.name % search_term" in _sql()


def test_rpc_orders_by_similarity() -> None:
    sql = _sql()
    assert "ORDER BY" in sql
    assert "similarity" in sql


def test_rpc_has_security_definer() -> None:
    assert "SECURITY DEFINER" in _sql()


def test_rpc_granted_to_service_role() -> None:
    sql = _sql()
    assert "GRANT EXECUTE" in sql
    assert "service_role" in sql


def test_rpc_revoked_from_public() -> None:
    sql = _sql()
    assert "REVOKE ALL" in sql


def test_rpc_filters_by_entity_type() -> None:
    sql = _sql()
    assert "ke.entity_type = filter_type" in sql


def test_rpc_returns_entity_type() -> None:
    assert "entity_type" in _sql()


def test_rpc_returns_description() -> None:
    assert "description" in _sql()


def test_rpc_has_search_path() -> None:
    sql = _sql()
    assert "SET search_path = public, extensions" in sql


def test_empty_search_term_handled() -> None:
    sql = _sql()
    assert "length(trim(search_term)) = 0" in sql


# ---------------------------------------------------------------------------
# Python method tests (mock Supabase client)
# ---------------------------------------------------------------------------

def _make_provider() -> SupabaseProvider:
    return SupabaseProvider(config={"supabase_url": "http://test", "supabase_key": "test-key"})


def _make_mock_client(data: list[dict]) -> MagicMock:
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = data
    return mock_client


def _make_entity_row(
    i: int = 0,
    similarity: float = 0.85,
) -> dict:
    return {
        "id": f"entity-{i}",
        "name": f"Entity {i}",
        "entity_type": "concept",
        "description": f"Description {i}",
        "similarity": similarity,
    }


def test_fuzzy_search_returns_tuple() -> None:
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        result = provider.fuzzy_search_entities("test")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_fuzzy_search_no_client_returns_empty() -> None:
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        results, meta = provider.fuzzy_search_entities("test")
    assert results == []
    assert meta["fallback_reason"] == "client_unavailable"


def test_fuzzy_search_calls_correct_rpc() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.fuzzy_search_entities("machine learning")
    mock_client.rpc.assert_called_once()
    assert mock_client.rpc.call_args[0][0] == "search_knowledge_entities_fuzzy"


def test_fuzzy_search_passes_parameters() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.fuzzy_search_entities(
            "test",
            top_k=5,
            threshold=0.5,
            filter_type="person",
        )
    params = mock_client.rpc.call_args[0][1]
    assert params["search_term"] == "test"
    assert params["similarity_threshold"] == 0.5
    assert params["match_count"] == 5
    assert params["filter_type"] == "person"


def test_fuzzy_search_strips_search_term() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.fuzzy_search_entities("  test  ")
    params = mock_client.rpc.call_args[0][1]
    assert params["search_term"] == "test"


def test_fuzzy_search_clamps_threshold() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.fuzzy_search_entities("test", threshold=1.5)
    params = mock_client.rpc.call_args[0][1]
    assert params["similarity_threshold"] == 1.0


def test_fuzzy_search_clamps_threshold_low() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.fuzzy_search_entities("test", threshold=-0.5)
    params = mock_client.rpc.call_args[0][1]
    assert params["similarity_threshold"] == 0.0


def test_fuzzy_search_exception_returns_fallback() -> None:
    provider = _make_provider()
    mock_client = MagicMock()
    mock_client.rpc.side_effect = RuntimeError("connection failed")
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, meta = provider.fuzzy_search_entities("test")
    assert results == []
    assert meta["fallback_reason"] == "provider_error"
    assert meta["error_type"] == "RuntimeError"


def test_fuzzy_search_respects_top_k() -> None:
    provider = _make_provider()
    rows = [_make_entity_row(i, similarity=0.9 - i * 0.1) for i in range(10)]
    mock_client = _make_mock_client(rows)
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.fuzzy_search_entities("test", top_k=3)
    # RPC returns results, server-side LIMIT applies top_k
    # Test verifies match_count parameter is passed correctly
    params = mock_client.rpc.call_args[0][1]
    assert params["match_count"] == 3


def test_fuzzy_search_returns_raw_dicts() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([_make_entity_row()])
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.fuzzy_search_entities("test")
    assert len(results) == 1
    assert isinstance(results[0], dict)
    assert "id" in results[0]
    assert "name" in results[0]
    assert "entity_type" in results[0]
    assert "similarity" in results[0]


def test_fuzzy_search_metadata_mode() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        _, meta = provider.fuzzy_search_entities("test")
    assert meta["mode"] == "fuzzy_entity"
    assert meta["provider"] == "supabase"


def test_fuzzy_search_match_count_minimum() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.fuzzy_search_entities("test", top_k=0)
    params = mock_client.rpc.call_args[0][1]
    assert params["match_count"] >= 1


def test_fuzzy_search_empty_after_strip_returns_empty() -> None:
    """Whitespace-only search_term short-circuits — no RPC call, empty results."""
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, meta = provider.fuzzy_search_entities("   ")
    mock_client.rpc.assert_not_called()
    assert results == []
    assert meta.get("fallback_reason") == "empty_query"
