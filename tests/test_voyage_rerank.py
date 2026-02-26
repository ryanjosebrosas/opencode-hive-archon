"""Unit tests for VoyageRerankService rerank functionality."""

from unittest.mock import MagicMock

from second_brain.contracts.context_packet import ContextCandidate
from second_brain.services.voyage import VoyageRerankService


def _make_candidates(n: int = 3) -> list[ContextCandidate]:
    """Create test candidates."""
    return [
        ContextCandidate(
            id=f"doc-{i}",
            content=f"Test document {i} about topic {chr(65 + i)}",
            source="supabase",
            confidence=0.7 + i * 0.05,
            metadata={"index": i},
        )
        for i in range(n)
    ]


class TestRealRerank:
    """Test real Voyage rerank API path."""

    def test_real_rerank_success(self):
        """With mocked client, real rerank returns reordered candidates."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()

        # Voyage returns results sorted by relevance (index refers to original position)
        mock_result_0 = MagicMock()
        mock_result_0.index = 2  # originally 3rd doc is most relevant
        mock_result_0.document = "Test document 2 about topic C"
        mock_result_0.relevance_score = 0.95

        mock_result_1 = MagicMock()
        mock_result_1.index = 0  # originally 1st doc is 2nd most relevant
        mock_result_1.document = "Test document 0 about topic A"
        mock_result_1.relevance_score = 0.72

        mock_reranking.results = [mock_result_0, mock_result_1]
        mock_reranking.total_tokens = 100
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = _make_candidates(3)
        reranked, metadata = service.rerank("test query", candidates, top_k=2)

        assert len(reranked) == 2
        assert reranked[0].id == "doc-2"  # highest relevance
        assert reranked[0].confidence == 0.95
        assert reranked[1].id == "doc-0"
        assert reranked[1].confidence == 0.72
        assert metadata["rerank_type"] == "external"
        assert metadata["real_rerank"] is True

        # Verify Voyage API was called correctly
        mock_client.rerank.assert_called_once_with(
            query="test query",
            documents=[c.content for c in candidates],
            model="rerank-2",
            top_k=2,
        )

    def test_real_rerank_preserves_original_metadata(self):
        """Real rerank preserves original candidate metadata plus adds rerank fields."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()
        mock_result = MagicMock()
        mock_result.index = 0
        mock_result.document = "doc content"
        mock_result.relevance_score = 0.88
        mock_reranking.results = [mock_result]
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = [
            ContextCandidate(
                id="doc-0",
                content="doc content",
                source="supabase",
                confidence=0.7,
                metadata={"custom_field": "preserved"},
            )
        ]

        # Single candidate normally bypasses rerank, so use 2
        candidates.append(
            ContextCandidate(
                id="doc-1",
                content="other",
                source="supabase",
                confidence=0.5,
                metadata={},
            )
        )
        mock_result_1 = MagicMock()
        mock_result_1.index = 1
        mock_result_1.document = "other"
        mock_result_1.relevance_score = 0.3
        mock_reranking.results = [mock_result, mock_result_1]

        reranked, _ = service.rerank("query", candidates, top_k=2)

        assert reranked[0].metadata["custom_field"] == "preserved"
        assert reranked[0].metadata["rerank_adjusted"] is True
        assert reranked[0].metadata["original_confidence"] == 0.7

    def test_real_rerank_clamps_relevance_score(self):
        """Relevance scores outside 0-1 are clamped."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()

        mock_r0 = MagicMock()
        mock_r0.index = 0
        mock_r0.relevance_score = 1.5  # over 1.0
        mock_r0.document = "doc"

        mock_r1 = MagicMock()
        mock_r1.index = 1
        mock_r1.relevance_score = -0.1  # below 0.0
        mock_r1.document = "doc2"

        mock_reranking.results = [mock_r0, mock_r1]
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = _make_candidates(2)
        reranked, _ = service.rerank("q", candidates, top_k=2)

        assert reranked[0].confidence == 1.0
        assert reranked[1].confidence == 0.0


class TestRealRerankFallback:
    """Test fallback from real rerank to mock."""

    def test_real_rerank_disabled_uses_mock(self):
        """When use_real_rerank=False, uses mock rerank."""
        service = VoyageRerankService(enabled=True, use_real_rerank=False)
        candidates = _make_candidates(3)

        reranked, metadata = service.rerank("test", candidates, top_k=3)

        assert len(reranked) == 3
        assert metadata["rerank_type"] == "external"
        assert metadata.get("real_rerank") is False

    def test_real_rerank_client_unavailable_falls_back(self):
        """When Voyage client can't load, falls back to mock."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)
        # Don't set _voyage_client — client loading will fail (no SDK)

        candidates = _make_candidates(3)
        reranked, metadata = service.rerank("test", candidates, top_k=3)

        assert len(reranked) == 3
        assert metadata["rerank_type"] == "external"
        assert metadata.get("real_rerank") is False

    def test_real_rerank_api_error_falls_back(self):
        """When Voyage API throws, falls back to mock."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_client.rerank.side_effect = RuntimeError("API timeout")
        service._voyage_client = mock_client

        candidates = _make_candidates(3)
        reranked, metadata = service.rerank("test", candidates, top_k=3)

        assert len(reranked) == 3
        assert metadata["rerank_type"] == "external"
        assert metadata.get("real_rerank") is False

    def test_real_rerank_empty_results_falls_back(self):
        """When Voyage API returns empty results, falls back to mock."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()
        mock_reranking.results = []
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = _make_candidates(3)
        reranked, metadata = service.rerank("test", candidates, top_k=3)

        assert len(reranked) == 3
        assert metadata.get("real_rerank") is False


class TestExistingBehaviorPreserved:
    """Regression tests: existing rerank behavior must not change."""

    def test_disabled_returns_unchanged(self):
        """Disabled service returns candidates unchanged."""
        service = VoyageRerankService(enabled=False)
        candidates = _make_candidates(2)

        reranked, metadata = service.rerank("test", candidates, top_k=5)

        assert reranked == list(candidates)
        assert metadata["rerank_type"] == "none"
        assert metadata["bypass_reason"] == "disabled"

    def test_empty_candidates_returns_empty(self):
        """Empty candidates returns empty list."""
        service = VoyageRerankService(enabled=True)

        reranked, metadata = service.rerank("test", [], top_k=5)

        assert reranked == []
        assert metadata["bypass_reason"] == "no_candidates"

    def test_single_candidate_bypasses(self):
        """Single candidate bypasses rerank."""
        service = VoyageRerankService(enabled=True)
        candidates = _make_candidates(1)

        reranked, metadata = service.rerank("test", candidates, top_k=5)

        assert len(reranked) == 1
        assert metadata["bypass_reason"] == "single_candidate"

    def test_mock_rerank_still_works(self):
        """Mock rerank produces deterministic results."""
        service = VoyageRerankService(enabled=True, use_real_rerank=False)
        candidates = _make_candidates(3)

        reranked, metadata = service.rerank("document topic", candidates, top_k=3)

        assert len(reranked) == 3
        assert metadata["rerank_type"] == "external"
        assert metadata["real_rerank"] is False
        # Mock adjusts confidence based on term overlap
        for c in reranked:
            assert c.metadata.get("rerank_adjusted") is True

    def test_embed_not_affected_by_rerank_flag(self):
        """use_real_rerank does not affect embed behavior."""
        service = VoyageRerankService(
            enabled=True,
            use_real_rerank=True,
            embed_enabled=False,
        )
        embedding, metadata = service.embed("test")
        assert embedding is None
        assert metadata["embed_error"] == "embedding_disabled"


class TestRealRerankEdgeCases:
    """Test edge cases for real rerank API responses."""

    def test_real_rerank_invalid_index_skipped(self):
        """Voyage returning invalid index is skipped gracefully."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()

        mock_result_valid = MagicMock()
        mock_result_valid.index = 0
        mock_result_valid.relevance_score = 0.9
        mock_result_valid.document = "valid doc"

        mock_result_invalid = MagicMock()
        mock_result_invalid.index = 99  # out of bounds
        mock_result_invalid.relevance_score = 0.8
        mock_result_invalid.document = "invalid doc"

        mock_reranking.results = [mock_result_valid, mock_result_invalid]
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = _make_candidates(2)
        reranked, metadata = service.rerank("test", candidates, top_k=2)

        assert len(reranked) == 1  # only valid result
        assert reranked[0].id == "doc-0"
        assert metadata["rerank_type"] == "external"
        assert metadata["real_rerank"] is True

    def test_real_rerank_invalid_relevance_score_skipped(self):
        """Voyage returning non-numeric relevance_score is skipped gracefully."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()

        mock_result_valid = MagicMock()
        mock_result_valid.index = 0
        mock_result_valid.relevance_score = 0.9
        mock_result_valid.document = "valid doc"

        mock_result_invalid = MagicMock()
        mock_result_invalid.index = 1
        mock_result_invalid.relevance_score = "not a number"
        mock_result_invalid.document = "invalid doc"

        mock_reranking.results = [mock_result_valid, mock_result_invalid]
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = _make_candidates(2)
        reranked, metadata = service.rerank("test", candidates, top_k=2)

        assert len(reranked) == 1
        assert reranked[0].id == "doc-0"

    def test_real_rerank_none_relevance_score_skipped(self):
        """Voyage returning None relevance_score is skipped gracefully."""
        service = VoyageRerankService(enabled=True, use_real_rerank=True)

        mock_client = MagicMock()
        mock_reranking = MagicMock()

        mock_result_valid = MagicMock()
        mock_result_valid.index = 0
        mock_result_valid.relevance_score = 0.85
        mock_result_valid.document = "valid doc"

        mock_result_none = MagicMock()
        mock_result_none.index = 1
        mock_result_none.relevance_score = None
        mock_result_none.document = "none score doc"

        mock_reranking.results = [mock_result_valid, mock_result_none]
        mock_client.rerank.return_value = mock_reranking
        service._voyage_client = mock_client

        candidates = _make_candidates(2)
        reranked, metadata = service.rerank("test", candidates, top_k=2)

        assert len(reranked) == 1
        assert reranked[0].confidence == 0.85
