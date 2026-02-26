"""Tests for Ollama LLM service."""

from unittest.mock import MagicMock


class TestOllamaLLMServiceInit:
    """Test OllamaLLMService initialization."""

    def test_defaults(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        assert svc.base_url == "http://localhost:11434"
        assert svc.model == "qwen3-coder-next"

    def test_custom_args(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService(base_url="http://custom:1234", model="llama3")
        assert svc.base_url == "http://custom:1234"
        assert svc.model == "llama3"

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://envhost:5555")
        monkeypatch.setenv("OLLAMA_MODEL", "envmodel")
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        assert svc.base_url == "http://envhost:5555"
        assert svc.model == "envmodel"


class TestOllamaLLMServiceSynthesize:
    """Test synthesize method."""

    def test_success(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Based on your notes, the answer is X."},
            "total_duration": 1_000_000,
            "eval_count": 50,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        svc._client = mock_client

        answer, meta = svc.synthesize(
            query="What is X?",
            context_candidates=[
                {
                    "content": "X is defined as...",
                    "source": "supabase",
                    "confidence": 0.9,
                    "metadata": {},
                }
            ],
        )
        assert "answer is X" in answer
        assert meta["llm_provider"] == "ollama"
        assert meta.get("fallback") is None

    def test_empty_response_triggers_fallback(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": ""}}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        svc._client = mock_client

        _, meta = svc.synthesize(
            query="test",
            context_candidates=[
                {"content": "ctx", "source": "s", "confidence": 0.8, "metadata": {}}
            ],
        )
        assert meta["fallback"] is True
        assert meta["reason"] == "empty_response"

    def test_exception_triggers_fallback(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()

        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("connection refused")
        svc._client = mock_client

        answer, meta = svc.synthesize(
            query="What is X?",
            context_candidates=[
                {
                    "content": "some context",
                    "source": "s",
                    "confidence": 0.8,
                    "metadata": {},
                }
            ],
        )
        assert "LLM unavailable" in answer or "raw retrieved context" in answer
        assert meta["fallback"] is True

    def test_no_client_triggers_fallback(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        svc._load_client = MagicMock(return_value=None)

        _, meta = svc.synthesize(query="test", context_candidates=[])
        assert meta["fallback"] is True
        assert meta["reason"] == "client_unavailable"

    def test_custom_system_prompt(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Custom response."},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        svc._client = mock_client

        svc.synthesize(
            query="test",
            context_candidates=[],
            system_prompt="You are a test bot.",
        )
        call_args = mock_client.post.call_args
        sent_messages = call_args[1]["json"]["messages"]
        assert sent_messages[0]["content"] == "You are a test bot."


class TestOllamaLLMServiceHelpers:
    """Test helper methods."""

    def test_build_context_block_empty(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        block = svc._build_context_block([])
        assert "No relevant context" in block

    def test_build_context_block_with_candidates(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        block = svc._build_context_block(
            [
                {
                    "content": "Note about RAG",
                    "source": "supabase",
                    "confidence": 0.9,
                    "metadata": {},
                },
                {
                    "content": "Note about LLMs",
                    "source": "supabase",
                    "confidence": 0.8,
                    "metadata": {},
                },
            ]
        )
        assert "RAG" in block
        assert "LLMs" in block
        assert "[1]" in block
        assert "[2]" in block

    def test_build_context_block_with_doc_id(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        block = svc._build_context_block(
            [
                {
                    "content": "Test",
                    "source": "supabase",
                    "confidence": 0.9,
                    "metadata": {"document_id": "doc-123"},
                }
            ]
        )
        assert "doc-123" in block

    def test_fallback_response_no_candidates(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        resp = svc._fallback_response("test", [])
        assert "LLM is unavailable" in resp

    def test_fallback_response_with_candidates(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        resp = svc._fallback_response(
            "test",
            [{"content": "Some note content", "source": "s", "confidence": 0.8, "metadata": {}}],
        )
        assert "LLM unavailable" in resp
        assert "Some note content" in resp

    def test_fallback_truncates_long_content(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()
        long_content = "A" * 500
        resp = svc._fallback_response(
            "test",
            [{"content": long_content, "source": "s", "confidence": 0.8, "metadata": {}}],
        )
        assert "..." in resp
        assert len(resp) < len(long_content) + 200

    def test_health_check_success(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        svc._client = mock_client

        assert svc.health_check() is True

    def test_health_check_failure(self):
        from second_brain.services.llm import OllamaLLMService

        svc = OllamaLLMService()

        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("down")
        svc._client = mock_client

        assert svc.health_check() is False


class TestDepsEnvConfig:
    """Test that deps.py config reads env vars."""

    def test_default_config_defaults_to_false(self):
        from second_brain.deps import get_default_config

        config = get_default_config()
        assert config["mem0_use_real_provider"] is False
        assert config["supabase_use_real_provider"] is False

    def test_default_config_reads_env(self, monkeypatch):
        monkeypatch.setenv("MEM0_USE_REAL_PROVIDER", "true")
        monkeypatch.setenv("SUPABASE_USE_REAL_PROVIDER", "TRUE")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        from second_brain.deps import get_default_config

        config = get_default_config()
        assert config["mem0_use_real_provider"] is True
        assert config["supabase_use_real_provider"] is True
        assert config["supabase_url"] == "https://test.supabase.co"

    def test_create_llm_service(self):
        from second_brain.deps import create_llm_service
        from second_brain.services.llm import OllamaLLMService

        svc = create_llm_service()
        assert isinstance(svc, OllamaLLMService)
