"""Unit tests for MemoryService mock data lifecycle."""

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
        assert "mock-1" in candidates[0].id or "High confidence" in candidates[0].content
    
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
        
        service.set_mock_data([
            MemorySearchResult(
                id="test",
                content="test",
                source="mem0",
                confidence=0.9,
                metadata={},
            ),
        ])
        
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
