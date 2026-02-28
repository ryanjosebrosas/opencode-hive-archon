"""Tests for P1-18: hybrid search RPC (RRF fusion of vector + full-text)."""
from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch


from second_brain.services.supabase import SupabaseProvider


# ---------------------------------------------------------------------------
# SQL structure tests (migration content assertions)
# ---------------------------------------------------------------------------

MIGRATION = pathlib.Path("migrations/009_hybrid_search.sql")


def test_migration_file_exists() -> None:
    assert MIGRATION.exists()


def _sql() -> str:
    return MIGRATION.read_text()


def test_rpc_function_name() -> None:
    assert "hybrid_search_knowledge_chunks" in _sql()


def test_rrf_formula_present() -> None:
    # RRF k=60 constant must appear
    assert "60.0 +" in _sql()


def test_vector_cte_present() -> None:
    assert "vector_results" in _sql()


def test_text_cte_present() -> None:
    assert "text_results" in _sql()


def test_combined_cte_uses_full_outer_join() -> None:
    assert "FULL OUTER JOIN" in _sql()


def test_rrf_score_column_returned() -> None:
    assert "rrf_score" in _sql()


def test_vector_rank_column_returned() -> None:
    assert "vector_rank" in _sql()


def test_text_rank_column_returned() -> None:
    assert "text_rank" in _sql()


def test_active_status_filter() -> None:
    assert "status = 'active'" in _sql()


def test_security_definer_set() -> None:
    assert "SECURITY DEFINER" in _sql()


def test_revoke_all_from_public() -> None:
    assert "REVOKE ALL" in _sql()


def test_grant_to_service_role() -> None:
    sql = _sql()
    assert "GRANT EXECUTE" in sql
    assert "service_role" in sql


def test_configurable_weights_in_signature() -> None:
    sql = _sql()
    assert "vector_weight" in sql
    assert "text_weight" in sql


def test_pool_size_parameter() -> None:
    assert "pool_size" in _sql()


def test_match_threshold_parameter() -> None:
    assert "match_threshold" in _sql()


def test_search_mode_branches() -> None:
    sql = _sql()
    assert "phraseto_tsquery" in sql
    assert "plainto_tsquery" in sql
    assert "websearch_to_tsquery" in sql


def test_subquery_order_before_limit() -> None:
    # Ensure subqueries have ORDER BY before LIMIT (Codex review requirement)
    sql = _sql()
    assert "ORDER BY dist" in sql or "ORDER BY kc.embedding" in sql
    assert "ORDER BY trank_raw DESC" in sql


# ---------------------------------------------------------------------------
# Python method tests (mock Supabase client)
# ---------------------------------------------------------------------------


def _make_provider() -> SupabaseProvider:
    return SupabaseProvider(config={"supabase_url": "http://test", "supabase_key": "test-key"})


def _make_mock_client(data: list[dict]) -> MagicMock:  # type: ignore[type-arg]
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = data
    return mock_client


def _make_row(
    i: int = 0,
    rrf_score: float = 0.015,
    vrank: int | None = 1,
    trank: int | None = 2,
) -> dict:  # type: ignore[type-arg]
    return {
        "id": f"chunk-{i}",
        "content": f"content {i}",
        "rrf_score": rrf_score,
        "knowledge_type": "document",
        "document_id": None,
        "chunk_index": i,
        "source_origin": "manual",
        "metadata": {},
        "vector_rank": vrank,
        "text_rank": trank,
    }


def test_hybrid_search_returns_tuple() -> None:
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        result = provider.hybrid_search([0.0] * 1024, "machine learning")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_hybrid_search_no_client_returns_empty() -> None:
    provider = _make_provider()
    with patch.object(provider, "_load_client", return_value=None):
        results, meta = provider.hybrid_search([0.0] * 1024, "test")
    assert results == []
    assert meta["fallback_reason"] == "client_unavailable"


def test_hybrid_search_calls_correct_rpc() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.hybrid_search([0.0] * 1024, "machine learning")
    mock_client.rpc.assert_called_once()
    assert mock_client.rpc.call_args[0][0] == "hybrid_search_knowledge_chunks"


def test_hybrid_search_passes_weights() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([])
    with patch.object(provider, "_load_client", return_value=mock_client):
        provider.hybrid_search([0.0] * 1024, "test", vector_weight=0.7, text_weight=0.3)
    params = mock_client.rpc.call_args[0][1]
    assert params["vector_weight"] == 0.7
    assert params["text_weight"] == 0.3


def test_hybrid_search_normalizes_rrf_score_to_confidence() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([_make_row(rrf_score=0.015)])
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.hybrid_search([0.0] * 1024, "ML")
    assert len(results) == 1
    assert results[0].confidence == 0.015


def test_hybrid_search_includes_rank_metadata() -> None:
    provider = _make_provider()
    mock_client = _make_mock_client([_make_row(vrank=3, trank=5)])
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.hybrid_search([0.0] * 1024, "test")
    assert results[0].metadata["vector_rank"] == 3
    assert results[0].metadata["text_rank"] == 5


def test_hybrid_search_exception_returns_fallback() -> None:
    provider = _make_provider()
    mock_client = MagicMock()
    mock_client.rpc.side_effect = RuntimeError("connection failed")
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, meta = provider.hybrid_search([0.0] * 1024, "test")
    assert results == []
    assert meta["fallback_reason"] == "provider_error"


def test_hybrid_search_respects_top_k() -> None:
    provider = _make_provider()
    rows = [_make_row(i, rrf_score=0.01 * (10 - i)) for i in range(10)]
    mock_client = _make_mock_client(rows)
    with patch.object(provider, "_load_client", return_value=mock_client):
        results, _ = provider.hybrid_search([0.0] * 1024, "test", top_k=3)
    assert len(results) == 3
