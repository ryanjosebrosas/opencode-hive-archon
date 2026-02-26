"""Unit tests for Supabase provider and Voyage embedding service."""

from unittest.mock import MagicMock
from second_brain.services.supabase import SupabaseProvider
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService


class TestSupabaseProviderSearch:
    """Test SupabaseProvider.search() with mocked Supabase client."""

    def test_search_returns_normalized_results(self):
        """Successful RPC returns normalized MemorySearchResult list."""
        provider = SupabaseProvider(
            config={
                "supabase_url": "https://test.supabase.co",
                "supabase_key": "test-key",
            }
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": "doc-1",
                "similarity": 0.92,
                "content": "Test document 1",
                "knowledge_type": "document",
                "document_id": "doc-parent-1",
                "chunk_index": 0,
                "source_origin": "manual",
                "metadata": {"topic": "ai"},
            },
            {
                "id": "doc-2",
                "similarity": 0.78,
                "content": "Test document 2",
                "knowledge_type": "note",
                "document_id": "doc-parent-2",
                "chunk_index": 1,
                "source_origin": "notion",
                "metadata": {"topic": "ml"},
            },
        ]
        mock_client.rpc.return_value.execute.return_value = mock_response
        provider._client = mock_client

        results, metadata = provider.search(
            query_embedding=[0.1] * 1024,
            top_k=5,
            threshold=0.6,
        )

        assert len(results) == 2
        assert results[0].id == "doc-1"
        assert results[0].content == "Test document 1"
        assert results[0].source == "supabase"
        assert results[0].confidence == 0.92
        assert results[0].metadata["knowledge_type"] == "document"
        assert results[0].metadata["document_id"] == "doc-parent-1"
        assert results[0].metadata["chunk_index"] == 0
        assert results[0].metadata["source_origin"] == "manual"
        assert metadata.get("real_provider") is True

    def test_search_client_unavailable_returns_empty(self):
        """When client can't load, returns empty with fallback_reason."""
        provider = SupabaseProvider(config={})
        results, metadata = provider.search([0.1] * 1024, top_k=5)
        assert results == []
        assert metadata["fallback_reason"] == "client_unavailable"

    def test_search_rpc_error_returns_empty_with_metadata(self):
        """When RPC throws, returns empty with sanitized error."""
        provider = SupabaseProvider(
            config={
                "supabase_url": "https://secret.supabase.co",
                "supabase_key": "secret-key",
            }
        )
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.side_effect = RuntimeError(
            "connection to https://secret.supabase.co failed"
        )
        provider._client = mock_client

        results, metadata = provider.search([0.1] * 1024, top_k=5)

        assert results == []
        assert metadata["fallback_reason"] == "provider_error"
        assert "secret.supabase.co" not in metadata["error_message"]
        assert "[REDACTED]" in metadata["error_message"]

    def test_normalize_clamps_confidence(self):
        """Similarity values outside 0-1 are clamped."""
        provider = SupabaseProvider()
        results = provider._normalize_results(
            [{"id": "x", "similarity": 1.5, "content": "test"}],
            top_k=5,
        )
        assert results[0].confidence == 1.0

    def test_normalize_handles_missing_fields(self):
        """Missing id/similarity/metadata are handled gracefully."""
        provider = SupabaseProvider()
        results = provider._normalize_results(
            [{"similarity": 0.8}],
            top_k=5,
        )
        assert results[0].id == "supa-0"
        assert results[0].content == ""
        assert results[0].confidence == 0.8

    def test_search_respects_top_k(self):
        """Results are capped at top_k."""
        provider = SupabaseProvider()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": f"doc-{i}",
                "similarity": 0.9 - i * 0.1,
                "metadata": {"content": f"doc {i}"},
            }
            for i in range(10)
        ]
        mock_client.rpc.return_value.execute.return_value = mock_response
        provider._client = mock_client

        results, _ = provider.search([0.1] * 1024, top_k=3)
        assert len(results) == 3


class TestVoyageEmbedding:
    """Test VoyageRerankService.embed() method."""

    def test_embed_disabled_returns_none(self):
        """When embed_enabled=False, returns None with error metadata."""
        service = VoyageRerankService(embed_enabled=False)
        embedding, metadata = service.embed("test query")
        assert embedding is None
        assert metadata["embed_error"] == "embedding_disabled"

    def test_embed_client_unavailable_returns_none(self):
        """When voyageai SDK not available, returns None."""
        service = VoyageRerankService(embed_enabled=True)
        embedding, metadata = service.embed("test query")
        assert embedding is None
        assert "embed_error" in metadata

    def test_embed_success_with_mocked_client(self):
        """With mocked client, returns embedding vector."""
        service = VoyageRerankService(embed_enabled=True, embed_model="voyage-4-large")
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.embeddings = [[0.1, 0.2, 0.3] * 341 + [0.1]]
        mock_result.total_tokens = 5
        mock_client.embed.return_value = mock_result
        service._voyage_client = mock_client

        embedding, metadata = service.embed("test query", input_type="query")

        assert embedding is not None
        assert len(embedding) == 1024
        assert metadata["total_tokens"] == 5
        mock_client.embed.assert_called_once_with(
            ["test query"], model="voyage-4-large", input_type="query"
        )

    def test_embed_preserves_existing_rerank(self):
        """Adding embed doesn't break existing rerank functionality."""
        service = VoyageRerankService(enabled=True, embed_enabled=False)
        from second_brain.contracts.context_packet import ContextCandidate

        candidates = [
            ContextCandidate(
                id="1", content="test a", source="s", confidence=0.8, metadata={}
            ),
            ContextCandidate(
                id="2", content="test b", source="s", confidence=0.7, metadata={}
            ),
        ]
        reranked, meta = service.rerank("test", candidates, top_k=5)
        assert len(reranked) == 2
        assert meta["rerank_type"] == "external"


class TestMemoryServiceSupabasePath:
    """Test MemoryService dispatch to Supabase provider."""

    def test_supabase_disabled_uses_fallback(self):
        """When supabase_use_real_provider=False, uses keyword fallback."""
        service = MemoryService(
            provider="supabase",
            config={"supabase_use_real_provider": False},
        )
        candidates, metadata = service.search_memories("test query", top_k=5)
        assert len(candidates) >= 1
        assert metadata.get("fallback_reason") == "real_provider_disabled"

    def test_supabase_no_credentials_uses_fallback(self):
        """When credentials missing, uses fallback."""
        service = MemoryService(
            provider="supabase",
            config={"supabase_use_real_provider": True},
        )
        candidates, metadata = service.search_memories("test query", top_k=5)
        assert len(candidates) >= 1

    def test_supabase_embed_failure_uses_fallback(self):
        """When embedding fails, falls back to keyword search."""
        service = MemoryService(
            provider="supabase",
            config={
                "supabase_use_real_provider": True,
                "supabase_url": "https://test.supabase.co",
                "supabase_key": "test-key",
            },
        )
        candidates, metadata = service.search_memories("test query", top_k=5)
        assert len(candidates) >= 1

    def test_supabase_embedding_dimension_mismatch_uses_fallback(self):
        """When embedding size is not 1024, falls back before Supabase RPC."""
        service = MemoryService(
            provider="supabase",
            config={
                "supabase_use_real_provider": True,
                "supabase_url": "https://test.supabase.co",
                "supabase_key": "test-key",
            },
        )
        mock_voyage = MagicMock()
        mock_voyage.embed.return_value = ([0.1] * 512, {"embed_model": "voyage-3-large"})
        service._voyage_service = mock_voyage

        candidates, metadata = service.search_memories("test query", top_k=5)

        assert len(candidates) >= 1
        assert metadata.get("fallback_reason") == "embedding_dimension_mismatch"
        assert metadata.get("expected_dimension") == 1024
        assert metadata.get("actual_dimension") == 512

    def test_existing_mem0_path_unchanged(self):
        """Mem0 provider path is not affected by Supabase changes."""
        service = MemoryService(
            provider="mem0",
            config={"mem0_use_real_provider": False},
        )
        candidates, metadata = service.search_memories("test query", top_k=5)
        assert len(candidates) >= 1
        assert metadata["provider"] == "mem0"
        assert metadata.get("fallback_reason") == "real_provider_disabled"
