"""Unit tests for MemoryService mock data lifecycle."""

import logging

from second_brain.services.memory import MemoryService, MemorySearchResult


class TestMockDataLifecycle:
    """Test mock data set/clear behavior for deterministic testing."""

    def test_set_mock_data_uses_mock_results(self):
        """With set_mock_data([...]) service uses mock results."""
        service = MemoryService(provider="mem0")

        mock_results = [
            MemorySearchResult(
                id="test-1",
                content="Test content",
                source="mem0",
                confidence=0.9,
                metadata={"mock": True},
            ),
        ]
        service.set_mock_data(mock_results)

        candidates, metadata = service.search_memories(
            query="any query",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) == 1
        assert candidates[0].id == "test-1"
        assert candidates[0].content == "Test content"

    def test_set_mock_data_empty_list_stays_in_mock_mode(self):
        """With set_mock_data([]) service stays in mock mode and returns empty."""
        service = MemoryService(provider="mem0")

        service.set_mock_data([])

        candidates, metadata = service.search_memories(
            query="any query",
            top_k=5,
            threshold=0.6,
        )

        assert candidates == []
        assert metadata["raw_count"] == 0

    def test_clear_mock_data_restores_fallback_mode(self):
        """After clear_mock_data() service uses fallback deterministic path again."""
        service = MemoryService(provider="mem0")

        mock_results = [
            MemorySearchResult(
                id="test-1",
                content="Mocked content",
                source="mem0",
                confidence=0.9,
                metadata={},
            ),
        ]
        service.set_mock_data(mock_results)

        candidates, _ = service.search_memories(query="test", top_k=5, threshold=0.6)
        assert len(candidates) == 1
        assert candidates[0].id == "test-1"

        service.clear_mock_data()

        candidates, metadata = service.search_memories(
            query="high confidence test",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) >= 1
        assert candidates[0].id != "test-1"
        assert (
            "mock-1" in candidates[0].id or "High confidence" in candidates[0].content
        )

    def test_clear_after_empty_mock_restores_fallback(self):
        """
        set_mock_data([]) followed by clear_mock_data() restores fallback,
        not stuck on empty results.
        """
        service = MemoryService(provider="mem0")

        service.set_mock_data([])
        candidates_empty, _ = service.search_memories(
            query="test query",
            top_k=5,
            threshold=0.6,
        )
        assert candidates_empty == []

        service.clear_mock_data()

        candidates_after_clear, _ = service.search_memories(
            query="test query",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates_after_clear) >= 1


class TestMockDataSemantics:
    """Test semantic distinction between None and [] for mock data."""

    def test_none_means_fallback_mode(self):
        """_mock_data = None means fallback mode (use deterministic fallback)."""
        service = MemoryService(provider="mem0")

        assert service._mock_data is None

        candidates, metadata = service.search_memories(
            query="high confidence",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) >= 1

    def test_empty_list_means_mock_mode_zero_results(self):
        """_mock_data = [] means mock mode with zero results (not disabled)."""
        service = MemoryService(provider="mem0")

        service.set_mock_data([])

        assert service._mock_data is not None
        assert service._mock_data == []

        candidates, _ = service.search_memories(
            query="any query",
            top_k=5,
            threshold=0.6,
        )

        assert candidates == []

    def test_clear_sets_none_not_empty_list(self):
        """clear_mock_data() sets _mock_data to None, not []."""
        service = MemoryService(provider="mem0")

        service.set_mock_data(
            [
                MemorySearchResult(
                    id="test",
                    content="test",
                    source="mem0",
                    confidence=0.9,
                    metadata={},
                ),
            ]
        )

        assert service._mock_data is not None

        service.clear_mock_data()

        assert service._mock_data is None


class TestMockDataProviderPreservation:
    """Test that mock mode preserves provider identity."""

    def test_mock_results_use_service_provider(self):
        """Mock results should use the service's configured provider."""
        service = MemoryService(provider="supabase")

        mock_results = [
            MemorySearchResult(
                id="test-1",
                content="Test",
                source="supabase",
                confidence=0.85,
                metadata={},
            ),
        ]
        service.set_mock_data(mock_results)

        candidates, metadata = service.search_memories(
            query="test",
            top_k=5,
            threshold=0.6,
        )

        assert metadata["provider"] == "supabase"
        if candidates:
            assert candidates[0].source == "supabase"


class TestProviderPath:
    """Test real provider adapter path with safe fallback."""

    def test_provider_path_disabled_uses_fallback(self):
        """When mem0_use_real_provider=False, use fallback path."""
        service = MemoryService(
            provider="mem0",
            config={"mem0_use_real_provider": False},
        )

        candidates, metadata = service.search_memories(
            query="test query",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) >= 1
        assert metadata.get("fallback_reason") == "real_provider_disabled"
        assert metadata.get("real_provider") is None

    def test_provider_sdk_unavailable_uses_fallback(self):
        """When Mem0 SDK not installed, fall back gracefully."""
        service = MemoryService(
            provider="mem0",
            config={
                "mem0_use_real_provider": True,
                "mem0_api_key": "test-key",
            },
        )

        candidates, metadata = service.search_memories(
            query="test query",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) >= 1
        assert metadata.get("fallback_reason") in [
            "client_unavailable",
            "provider_error",
        ]

    def test_provider_exception_uses_fallback(self):
        """When provider throws exception, use fallback path."""
        service = MemoryService(
            provider="mem0",
            config={
                "mem0_use_real_provider": True,
                "mem0_api_key": "invalid-key",
            },
        )

        candidates, metadata = service.search_memories(
            query="test query",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) >= 1
        assert metadata.get("fallback_reason") in [
            "provider_error",
            "client_unavailable",
        ]
        if metadata.get("fallback_reason") == "provider_error":
            assert "error_type" in metadata

    def test_non_mem0_provider_ignores_real_provider_config(self):
        """Non-Mem0 providers ignore mem0_use_real_provider config."""
        service = MemoryService(
            provider="supabase",
            config={"mem0_use_real_provider": True},
        )

        candidates, metadata = service.search_memories(
            query="test query",
            top_k=5,
            threshold=0.6,
        )

        assert len(candidates) >= 1
        assert metadata.get("fallback_reason") == "real_provider_disabled"


class TestMajorFindingsFollowup:
    """Regression tests for deferred major code-review findings."""

    def test_input_validation_clamps_top_k_and_threshold(self, monkeypatch):
        """search_memories clamps invalid numeric parameters before provider path."""
        service = MemoryService(
            provider="mem0",
            config={"mem0_use_real_provider": True, "mem0_api_key": "test-key"},
        )

        captured: dict[str, float | int | str] = {}

        def fake_provider_search(query: str, top_k: int, threshold: float):
            captured["query"] = query
            captured["top_k"] = top_k
            captured["threshold"] = threshold
            return [], {"provider": "mem0", "real_provider": True}

        monkeypatch.setattr(service, "_search_with_provider", fake_provider_search)

        service.search_memories(query="  normalized query  ", top_k=0, threshold=1.9)

        assert captured["query"] == "normalized query"
        assert captured["top_k"] == 1
        assert captured["threshold"] == 1.0

    def test_input_validation_uses_defaults_for_unparseable_values(self, monkeypatch):
        """search_memories falls back to safe defaults when inputs are unparseable."""
        service = MemoryService(
            provider="mem0",
            config={"mem0_use_real_provider": True, "mem0_api_key": "test-key"},
        )

        captured: dict[str, float | int] = {}

        def fake_provider_search(query: str, top_k: int, threshold: float):
            captured["top_k"] = top_k
            captured["threshold"] = threshold
            return [], {"provider": "mem0", "real_provider": True}

        monkeypatch.setattr(service, "_search_with_provider", fake_provider_search)

        service.search_memories(query="x", top_k="bad", threshold="bad")  # type: ignore[arg-type]

        assert captured["top_k"] == 1
        assert captured["threshold"] == 0.6

    def test_provider_error_metadata_includes_sanitized_message(
        self, monkeypatch, caplog
    ):
        """Provider errors include redacted message context and warning logs."""
        secret = "secret-key-123"
        service = MemoryService(
            provider="mem0",
            config={"mem0_use_real_provider": True, "mem0_api_key": secret},
        )

        class FailingClient:
            def search(self, query: str, limit: int):
                raise RuntimeError(f"auth failed using {secret}")

        monkeypatch.setattr(service, "_load_mem0_client", lambda: FailingClient())

        with caplog.at_level(logging.WARNING):
            _, metadata = service.search_memories(
                query="normal query", top_k=3, threshold=0.6
            )

        assert metadata["fallback_reason"] == "provider_error"
        assert metadata["error_type"] == "RuntimeError"
        assert "error_message" in metadata
        assert secret not in metadata["error_message"]
        assert len(metadata["error_message"]) <= 200
        assert any(
            "Mem0 provider search failed" in message for message in caplog.messages
        )
