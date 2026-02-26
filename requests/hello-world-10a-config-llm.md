# Feature: Hello World 10a — Config + LLM Service

The following plan should be complete, but validate documentation, codebase patterns, and task sanity before implementation.

Pay close attention to naming of existing utils, types, and models. Import from the correct files.

## Feature Description

Make the Second Brain configurable via environment variables (replacing hardcoded False flags) and add an Ollama LLM synthesis service. This is the first sub-slice of the "Hello World Personal Knowledge Loop" — it adds no external dependencies to the running system but makes every subsequent slice possible.

## User Story

As a developer deploying Second Brain,
I want to configure retrieval providers and LLM via environment variables,
So that I can switch between mock and real backends without code changes.

## Problem Statement

`deps.py` has `mem0_use_real_provider: False`, `supabase_use_real_provider: False` hardcoded. There is no LLM service — the planner formats f-string templates. There is no way to make the system use real providers or generate intelligent responses without editing source code.

## Solution Statement

- Decision 1: **Env-var config** — replace hardcoded flags in `deps.py` with `os.getenv()` reads. Defaults remain `"false"` so all existing tests pass unchanged.
- Decision 2: **Ollama LLM service** — new `services/llm.py` with direct REST API call to Ollama `/api/chat`. Uses `httpx`. Follows the same lazy-init pattern as `voyage.py`.
- Decision 3: **Add httpx dependency** — the only new package in this sub-slice. `voyageai`, `supabase`, `fastmcp` come in later sub-slices.

## Feature Metadata

- **Feature Type**: Enhancement
- **Estimated Complexity**: Low-Medium
- **Primary Systems Affected**: `deps.py`, new `services/llm.py`
- **Dependencies**: `httpx>=0.27` (new)

### Slice Guardrails (Required)

- **Single Outcome**: Configurable deps.py + working OllamaLLMService with tests
- **Expected Files Touched**: 4 files (1 new service, 1 new test, 2 modified)
- **Scope Boundary**: Does NOT wire LLM into planner (that's 10c). Does NOT add ingestion. Does NOT add MCP transport.
- **Split Trigger**: N/A — this slice is already minimal

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/deps.py` (lines 1-121) — Why: ALL hardcoded flags live here. `get_default_config()` at line 106 returns `mem0_use_real_provider: False`, `supabase_use_real_provider: False`. `create_voyage_rerank_service()` at line 44 has `embed_enabled: bool = False`. Both must become env-var driven.
- `backend/src/second_brain/services/voyage.py` (lines 13-48) — Why: Pattern reference for lazy service init with graceful degradation. The LLM service must follow this exact pattern.
- `backend/src/second_brain/services/memory.py` (lines 1-30) — Why: Shows how `MemoryService.__init__` reads config. The env-var config from `deps.py` flows into services via `get_default_config()`.
- `backend/pyproject.toml` (lines 1-20) — Why: Must add `httpx` to dependencies.
- `tests/test_supabase_provider.py` (lines 1-30) — Why: Test pattern reference for service tests with mocks.

### New Files to Create

- `backend/src/second_brain/services/llm.py` — Ollama LLM synthesis service
- `tests/test_llm_service.py` — Unit tests for LLM service

### Related Memories (from memory.md)

- Memory: "Python-first with framework-agnostic contracts" — Relevance: LLM service must be a plain Python class, no framework coupling
- Memory: "Incremental-by-default slices with full validation every loop" — Relevance: All 235+ existing tests must pass after this slice

### Relevant Documentation

- [Ollama API — Chat Completion](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion)
  - Specific section: POST /api/chat request/response format
  - Why: The LLM service calls this endpoint

### Patterns to Follow

**Lazy Service Init Pattern** (from `backend/src/second_brain/services/voyage.py:13-48`):
```python
class VoyageRerankService:
    def __init__(self, enabled=True, model="rerank-2", embed_model="voyage-4-large",
                 embed_enabled=False, use_real_rerank=False):
        self.enabled = enabled
        self._voyage_client: Any | None = None

    def _load_voyage_client(self) -> Any | None:
        if self._voyage_client is not None:
            return self._voyage_client
        try:
            import voyageai
            api_key = os.getenv("VOYAGE_API_KEY")
            if api_key:
                self._voyage_client = voyageai.Client(api_key=api_key)
            else:
                self._voyage_client = voyageai.Client()
            return self._voyage_client
        except ImportError:
            logger.debug("voyageai SDK not installed")
        except Exception as e:
            logger.warning("Voyage client init failed: %s", type(e).__name__)
        return None
```
- Why this pattern: All services use lazy loading with ImportError handling for optional deps.
- Common gotchas: Return None on failure, let caller handle gracefully.

**Env Config Pattern** (from `backend/src/second_brain/deps.py:106-121`):
```python
def get_default_config() -> dict[str, Any]:
    return {
        "default_mode": "conversation",
        "mem0_use_real_provider": False,  # HARDCODED — must become env-var
        "supabase_use_real_provider": False,  # HARDCODED — must become env-var
        ...
    }
```
- Why this pattern: Central config factory. All services read from this.
- Common gotchas: `os.getenv()` returns string. Must compare `.lower() == "true"` for bool flags.

---

## IMPLEMENTATION PLAN

### Phase 1: Dependencies

Add `httpx` to project dependencies.

### Phase 2: Config

Update `deps.py` to read env vars.

### Phase 3: LLM Service

Create `services/llm.py` with `OllamaLLMService`.

### Phase 4: Tests

Unit tests for LLM service.

---

## STEP-BY-STEP TASKS

### UPDATE `backend/pyproject.toml` — Add httpx dependency

- **IMPLEMENT**: Change the dependencies list:

  **Current** (line 6-8):
  ```toml
  dependencies = [
      "pydantic>=2.0",
  ]
  ```

  **Replace with**:
  ```toml
  dependencies = [
      "pydantic>=2.0",
      "httpx>=0.27",
  ]
  ```

  Then run: `cd backend && pip install -e .`

- **PATTERN**: `pyproject.toml:6-8`
- **IMPORTS**: N/A
- **GOTCHA**: Only adding `httpx` in this slice. `voyageai`, `supabase`, `fastmcp` come in later sub-slices. Pin minimum version, not exact.
- **VALIDATE**: `cd backend && pip install -e . 2>&1 | tail -3 && python -c "import httpx; print('httpx', httpx.__version__)"`

### UPDATE `backend/src/second_brain/deps.py` — Env-var driven config

- **IMPLEMENT**:

  a) Add `import os` to the top of the file (after `from __future__ import annotations`).

  b) Replace `get_default_config()` (lines 106-121):

  **Current**:
  ```python
  def get_default_config() -> dict[str, Any]:
      """Get default configuration for recall flow."""
      return {
          "default_mode": "conversation",
          "default_top_k": 5,
          "default_threshold": 0.6,
          "mem0_rerank_native": True,
          "mem0_skip_external_rerank": True,
          "mem0_use_real_provider": False,
          "mem0_user_id": None,
          "mem0_api_key": None,
          "supabase_use_real_provider": False,
          "supabase_url": None,
          "supabase_key": None,
          "voyage_embed_model": "voyage-4-large",
      }
  ```

  **Replace with**:
  ```python
  def get_default_config() -> dict[str, Any]:
      """Get configuration from environment variables with safe defaults."""
      return {
          "default_mode": "conversation",
          "default_top_k": 5,
          "default_threshold": 0.6,
          "mem0_rerank_native": True,
          "mem0_skip_external_rerank": True,
          "mem0_use_real_provider": os.getenv("MEM0_USE_REAL_PROVIDER", "false").lower() == "true",
          "mem0_user_id": os.getenv("MEM0_USER_ID"),
          "mem0_api_key": os.getenv("MEM0_API_KEY"),
          "supabase_use_real_provider": os.getenv("SUPABASE_USE_REAL_PROVIDER", "false").lower() == "true",
          "supabase_url": os.getenv("SUPABASE_URL"),
          "supabase_key": os.getenv("SUPABASE_KEY"),
          "voyage_embed_model": os.getenv("VOYAGE_EMBED_MODEL", "voyage-4-large"),
      }
  ```

  c) Replace `create_voyage_rerank_service()` (lines 44-56):

  **Current**:
  ```python
  def create_voyage_rerank_service(
      enabled: bool = True,
      model: str = "rerank-2",
      embed_model: str = "voyage-4-large",
      embed_enabled: bool = False,
  ) -> VoyageRerankService:
      """Create voyage rerank service instance."""
      return VoyageRerankService(
          enabled=enabled,
          model=model,
          embed_model=embed_model,
          embed_enabled=embed_enabled,
      )
  ```

  **Replace with**:
  ```python
  def create_voyage_rerank_service(
      enabled: bool = True,
      model: str = "rerank-2",
      embed_model: str | None = None,
      embed_enabled: bool | None = None,
      use_real_rerank: bool | None = None,
  ) -> VoyageRerankService:
      """Create voyage rerank service instance with env-var defaults."""
      _embed_model = embed_model or os.getenv("VOYAGE_EMBED_MODEL", "voyage-4-large")
      _embed_enabled = (
          embed_enabled
          if embed_enabled is not None
          else os.getenv("VOYAGE_EMBED_ENABLED", "false").lower() == "true"
      )
      _use_real_rerank = (
          use_real_rerank
          if use_real_rerank is not None
          else os.getenv("VOYAGE_USE_REAL_RERANK", "false").lower() == "true"
      )
      return VoyageRerankService(
          enabled=enabled,
          model=model,
          embed_model=_embed_model,
          embed_enabled=_embed_enabled,
          use_real_rerank=_use_real_rerank,
      )
  ```

  d) Add `create_llm_service()` factory function (after `create_conversation_store`, before `create_planner`):
  ```python
  def create_llm_service() -> Any:
      """Create LLM service for synthesis. Returns OllamaLLMService instance."""
      from second_brain.services.llm import OllamaLLMService
      return OllamaLLMService()
  ```

- **PATTERN**: `deps.py:44-56` existing factory functions
- **IMPORTS**: `import os` at top of file
- **GOTCHA**: All env-var defaults are `"false"` — existing tests pass without any env vars set. The `create_llm_service()` uses lazy import to avoid circular imports. The `create_voyage_rerank_service` signature changes (new optional params) but all call sites use positional or defaults, so backward compatible.
- **VALIDATE**: `cd backend && python -m pytest ../tests/ -q 2>&1 | tail -5` (ALL existing tests must still pass)

### CREATE `backend/src/second_brain/services/llm.py` — Ollama LLM service

- **IMPLEMENT**: Create new file:

  ```python
  """LLM synthesis service via Ollama REST API."""

  import logging
  import os
  from typing import Any

  logger = logging.getLogger(__name__)

  DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
  DEFAULT_OLLAMA_MODEL = "qwen3-coder-next"


  class OllamaLLMService:
      """LLM synthesis via Ollama (local or cloud) REST API."""

      def __init__(
          self,
          base_url: str | None = None,
          model: str | None = None,
      ):
          self.base_url = base_url or os.getenv(
              "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL
          )
          self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
          self._client: Any | None = None

      def _load_client(self) -> Any | None:
          """Load httpx client lazily."""
          if self._client is not None:
              return self._client
          try:
              import httpx

              self._client = httpx.Client(
                  base_url=self.base_url, timeout=120.0
              )
              return self._client
          except ImportError:
              logger.debug("httpx not installed")
          except Exception as e:
              logger.warning(
                  "httpx client init failed: %s", type(e).__name__
              )
          return None

      def synthesize(
          self,
          query: str,
          context_candidates: list[dict[str, Any]],
          system_prompt: str | None = None,
      ) -> tuple[str, dict[str, Any]]:
          """
          Generate a synthesis response from retrieved context.

          Args:
              query: The user's original question
              context_candidates: Retrieved context chunks with content and metadata
              system_prompt: Optional custom system prompt

          Returns:
              Tuple of (response_text, metadata)
          """
          metadata: dict[str, Any] = {
              "llm_provider": "ollama",
              "model": self.model,
              "base_url": self.base_url,
          }

          client = self._load_client()
          if client is None:
              return self._fallback_response(query, context_candidates), {
                  **metadata,
                  "fallback": True,
                  "reason": "client_unavailable",
              }

          context_block = self._build_context_block(context_candidates)

          default_system = (
              "You are a personal knowledge assistant. Answer the user's question "
              "using ONLY the provided context from their notes. Be specific, cite "
              "which note the information comes from when possible. If the context "
              "doesn't contain enough information to answer, say so honestly."
          )

          messages = [
              {
                  "role": "system",
                  "content": system_prompt or default_system,
              },
              {
                  "role": "user",
                  "content": (
                      f"Context from your notes:\n\n{context_block}\n\n"
                      f"Question: {query}"
                  ),
              },
          ]

          try:
              response = client.post(
                  "/api/chat",
                  json={
                      "model": self.model,
                      "messages": messages,
                      "stream": False,
                  },
              )
              response.raise_for_status()
              data = response.json()
              answer = data.get("message", {}).get("content", "")
              if not answer:
                  return self._fallback_response(
                      query, context_candidates
                  ), {
                      **metadata,
                      "fallback": True,
                      "reason": "empty_response",
                  }
              metadata["total_duration"] = data.get("total_duration")
              metadata["eval_count"] = data.get("eval_count")
              return answer, metadata
          except Exception as e:
              logger.warning(
                  "Ollama synthesis failed: %s — %s",
                  type(e).__name__,
                  str(e)[:200],
              )
              return self._fallback_response(
                  query, context_candidates
              ), {**metadata, "fallback": True, "reason": type(e).__name__}

      def _build_context_block(
          self, candidates: list[dict[str, Any]]
      ) -> str:
          """Format context candidates into a readable block for the LLM."""
          if not candidates:
              return "(No relevant context found in your notes.)"
          parts = []
          for i, c in enumerate(candidates, 1):
              source = c.get("source", "unknown")
              content = c.get("content", "")
              confidence = c.get("confidence", 0.0)
              doc_id = c.get("metadata", {}).get("document_id", "")
              header = f"[{i}] (source: {source}, confidence: {confidence:.2f}"
              if doc_id:
                  header += f", doc: {doc_id}"
              header += ")"
              parts.append(f"{header}\n{content}")
          return "\n\n---\n\n".join(parts)

      def _fallback_response(
          self,
          query: str,
          candidates: list[dict[str, Any]],
      ) -> str:
          """Generate a non-LLM fallback when Ollama is unavailable."""
          if not candidates:
              return (
                  "I couldn't find relevant context for your query "
                  "and the LLM is unavailable."
              )
          context_parts = []
          for i, c in enumerate(candidates[:3], 1):
              content = c.get("content", "")
              if len(content) > 300:
                  content = content[:300] + "..."
              context_parts.append(f"[{i}] {content}")
          return (
              "(LLM unavailable — showing raw retrieved context)\n\n"
              + "\n\n".join(context_parts)
          )

      def health_check(self) -> bool:
          """Check if Ollama is reachable."""
          client = self._load_client()
          if client is None:
              return False
          try:
              resp = client.get("/api/tags")
              return resp.status_code == 200
          except Exception:
              return False
  ```

- **PATTERN**: `services/voyage.py:13-48` lazy client init
- **IMPORTS**: `logging`, `os` at top; `httpx` imported lazily inside `_load_client()`
- **GOTCHA**: Ollama `/api/chat` with `"stream": False` returns full JSON response. With `"stream": True` it returns NDJSON lines — we MUST use `False`. Timeout is 120s because LLM generation can be slow. The `total_duration` in response is nanoseconds (not ms).
- **VALIDATE**: `cd backend && python -m ruff check src/second_brain/services/llm.py && python -m mypy src/second_brain/services/llm.py --ignore-missing-imports`

### CREATE `tests/test_llm_service.py` — LLM service tests

- **IMPLEMENT**: Create new file:

  ```python
  """Tests for Ollama LLM service."""

  from unittest.mock import MagicMock

  import pytest


  class TestOllamaLLMServiceInit:
      """Test OllamaLLMService initialization."""

      def test_defaults(self):
          from second_brain.services.llm import OllamaLLMService

          svc = OllamaLLMService()
          assert svc.base_url == "http://localhost:11434"
          assert svc.model == "qwen3-coder-next"

      def test_custom_args(self):
          from second_brain.services.llm import OllamaLLMService

          svc = OllamaLLMService(
              base_url="http://custom:1234", model="llama3"
          )
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

          answer, meta = svc.synthesize(
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
                  {"content": "some context", "source": "s", "confidence": 0.8, "metadata": {}}
              ],
          )
          assert "LLM unavailable" in answer or "raw retrieved context" in answer
          assert meta["fallback"] is True

      def test_no_client_triggers_fallback(self):
          from second_brain.services.llm import OllamaLLMService

          svc = OllamaLLMService()
          svc._load_client = MagicMock(return_value=None)

          answer, meta = svc.synthesize(query="test", context_candidates=[])
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

          answer, meta = svc.synthesize(
              query="test",
              context_candidates=[],
              system_prompt="You are a test bot.",
          )
          # Verify custom system prompt was sent
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
  ```

- **PATTERN**: `tests/test_supabase_provider.py` test structure
- **IMPORTS**: `unittest.mock.MagicMock`, `pytest`
- **GOTCHA**: Import inside test methods to avoid issues if module has import errors. Use `monkeypatch.setenv` for env var tests — it auto-restores after each test. Include tests for `deps.py` env-var behavior since we're modifying it.
- **VALIDATE**: `cd backend && python -m pytest ../tests/test_llm_service.py -v`

---

## TESTING STRATEGY

### Unit Tests

- `test_llm_service.py`: 16 tests covering init (defaults, custom, env), synthesize (success, empty response, exception, no client, custom system prompt), helpers (context block, fallback, health check), deps env config (3 tests)

### Integration Tests

Not applicable for this sub-slice — no external service calls.

### Edge Cases

- Edge case 1: No env vars set → all flags default to False, existing behavior unchanged
- Edge case 2: httpx not installed → `_load_client()` returns None, synthesize falls back gracefully
- Edge case 3: Ollama returns empty message content → falls back to raw context display
- Edge case 4: `OLLAMA_BASE_URL` set to unreachable host → synthesize catches exception, falls back

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
cd backend && python -m ruff check src/second_brain/deps.py src/second_brain/services/llm.py ../tests/test_llm_service.py
```

### Level 2: Type Safety
```
cd backend && python -m mypy src/second_brain/deps.py src/second_brain/services/llm.py --ignore-missing-imports
```

### Level 3: Unit Tests
```
cd backend && python -m pytest ../tests/test_llm_service.py -v
```

### Level 4: Full Regression
```
cd backend && python -m pytest ../tests/ -q
```

### Level 5: Manual Validation

1. `python -c "from second_brain.services.llm import OllamaLLMService; print('OK')"` — import check
2. `python -c "from second_brain.deps import get_default_config; c = get_default_config(); print(c['supabase_use_real_provider'])"` — should print `False`
3. `SUPABASE_USE_REAL_PROVIDER=true python -c "from second_brain.deps import get_default_config; c = get_default_config(); print(c['supabase_use_real_provider'])"` — should print `True`

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `pyproject.toml` has `httpx>=0.27` in dependencies
- [ ] `deps.py` imports `os` and reads all config from env vars
- [ ] `deps.py` `get_default_config()` defaults to `False` for all real-provider flags
- [ ] `deps.py` has `create_llm_service()` factory
- [ ] `deps.py` `create_voyage_rerank_service()` accepts env-var-driven defaults
- [ ] `services/llm.py` exists with `OllamaLLMService` class
- [ ] LLM service follows lazy-init pattern (same as voyage.py)
- [ ] LLM service has `synthesize()`, `health_check()`, `_build_context_block()`, `_fallback_response()`
- [ ] All 235+ existing tests still pass
- [ ] 16+ new tests pass in `test_llm_service.py`
- [ ] Ruff clean, mypy clean

### Runtime (verify after testing/deployment)

- [ ] Setting `SUPABASE_USE_REAL_PROVIDER=true` activates real Supabase provider
- [ ] Setting `OLLAMA_BASE_URL` + `OLLAMA_MODEL` configures LLM service
- [ ] LLM service falls back gracefully when Ollama is unreachable

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **httpx over requests**: httpx is modern, async-capable (for future), and has better timeout handling. It's also the standard for modern Python HTTP.
- **Lazy import of httpx**: Even though we add it as a dependency, the import is lazy inside `_load_client()` to match the established pattern and avoid breaking tests that don't need HTTP.
- **LLM service not wired in yet**: This slice creates the service but doesn't inject it into the planner. That's sub-slice 10c. This keeps 10a testable independently.
- **No changes to planner or mcp_server**: Intentionally isolated. Only deps.py config and new service file.

### Risks

- Risk 1: **Env-var config breaks existing tests** — Mitigation: Defaults are identical to current hardcoded values. Tests run without env vars set.
- Risk 2: **httpx version conflict** — Mitigation: `>=0.27` is widely compatible. No known conflicts with pydantic.

### Confidence Score: 9/10
- **Strengths**: Small scope, clear patterns to follow, no external service calls, all existing tests preserved
- **Uncertainties**: None significant — this is straightforward
- **Mitigations**: Full test suite runs before and after
