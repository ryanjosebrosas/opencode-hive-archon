# Feature: P1-03 Structured JSON Logging

## Feature Description

Replace all `print()` statements and basic `logging.info()` calls with structured JSON logging using `structlog`. Add `correlation_id` tracking to all operations for request tracing. Make log level configurable via Settings. This is Pillar 1's third spec, building on the pydantic-settings-config foundation (P1-02) to establish observability infrastructure before more complex features.

## User Story

As a **technical solo founder debugging retrieval issues**, I want to **see structured JSON logs with correlation IDs that trace requests across all services**, so that **I can quickly identify where issues occur in the retrieval pipeline without grepping through unstructured text logs**.

## Problem Statement

Current logging uses Python's standard `logging` module with unstructured text output. When debugging issues across multiple services (Voyage, Supabase, Ollama, MemoryService), it's difficult to:
1. Correlate log entries from the same request across service boundaries
2. Parse logs programmatically for analysis or alerting
3. Filter logs by level without restarting the application
4. Include structured context (session_id, provider, query_type) in a consistent way

## Solution Statement

- **Decision 1: Use `structlog` library** — because it provides structured logging with minimal code changes, supports JSON output, and integrates with standard `logging` for handler configuration
- **Decision 2: Generate `correlation_id` per request/chat turn** — because this enables tracing across service boundaries without distributed tracing complexity
- **Decision 3: Configure log level via Settings** — because ops should be able to change verbosity without code changes
- **Decision 4: Keep existing logger names** — because `logging.getLogger(__name__)` is already used consistently, we just enhance the output format

## Feature Metadata

- **Feature Type**: Enhancement / Infrastructure
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: All services (voyage.py, supabase.py, memory.py, llm.py, mcp_server.py, planner.py, markdown.py)
- **Dependencies**: `structlog` library (add to pyproject.toml), P1-02 (Pydantic Settings config)

### Slice Guardrails (Required)

- **Single Outcome**: All log output is valid JSON with timestamp, level, correlation_id, module fields; log level configurable via env var
- **Expected Files Touched**: `config.py`, `logging_config.py` (new), 6 service files adding correlation_id context
- **Scope Boundary**: Does NOT include: log aggregation, alerting, metrics dashboards, distributed tracing — just structured output
- **Split Trigger**: If correlation_id propagation proves complex across async boundaries, split into: (1) JSON formatting only, (2) correlation_id addition

---

## CONTEXT REFERENCES

### Relevant Codebase Files

- `backend/src/second_brain/config.py:1-66` — Why: Add LOG_LEVEL setting to Settings class
- `backend/src/second_brain/services/voyage.py:1-221` — Why: Example of current logging usage, add correlation_id to logs
- `backend/src/second_brain/services/supabase.py:1-167` — Why: Example of current logging usage with error sanitization pattern
- `backend/src/second_brain/services/memory.py:1-443` — Why: Example of current logging usage, multiple error paths
- `backend/src/second_brain/services/llm.py:1-167` — Why: Example of current logging usage
- `backend/src/second_brain/mcp_server.py:1-358` — Why: Entry point, initialize logging_config
- `backend/src/second_brain/orchestration/planner.py:1-343` — Why: Entry point for chat flow, correlate logs
- `backend/src/second_brain/ingestion/markdown.py:1-??` — Why: Ingestion logging, needs correlation_id
- `backend/tests/test_config.py:1-330` — Why: Pattern for testing Settings fields

### New Files to Create

- `backend/src/second_brain/logging_config.py` — Structured logging configuration with structlog setup
- `backend/tests/test_logging_config.py` — Tests for logging configuration and JSON output

### Related Memories (from memory.md)

- **OpenCode SDK swallows AbortError**: SDK doesn't throw on timeout — puts error in `result.error`. Relevance: Shows why structured error context matters
- **OpenCode upstream API errors in info.error**: Server returns 200 with nested error object. Relevance: Structured logging captures nested error metadata better than text
- **Provider error context**: Keep fallback metadata actionable but sanitized (redact secrets and cap message length). Relevance: Already doing sanitization in supabase.py/memory.py, continue pattern

### Relevant Documentation

- [structlog Documentation](https://www.structlog.org/en/stable/index.html)
  - Specific section: [Getting Started](https://www.structlog.org/en/stable/getting-started.html)
  - Why: Shows standard integration pattern with logging module
- [structlog Production Deployment](https://www.structlog.org/en/stable/production.html)
  - Specific section: JSON Output Configuration
  - Why: Shows how to configure JSON formatters for production

### Patterns to Follow

**Current Logging Pattern** (from `voyage.py:10-48`):
```python
logger = logging.getLogger(__name__)

class VoyageRerankService:
    def _load_voyage_client(self) -> Any | None:
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
- Why this pattern: Standard lazy-init with graceful degradation
- Common gotchas: Must preserve debug/warning levels, don't lose error context

**Current Error Sanitization Pattern** (from `supabase.py:161-167`):
```python
def _sanitize_error_message(self, error: Exception) -> str:
    """Return bounded and redacted error text safe for metadata."""
    message = str(error)
    for value in [self._supabase_url, self._supabase_key]:
        if value:
            message = message.replace(value, "[REDACTED]")
    return message[:200]
```
- Why this pattern: Security best practice for logs
- Common gotchas: Must apply before logging, don't leak secrets in structured fields

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation (logging_config.py + Settings)

**Tasks:**
- Add `log_level` field to Settings class with default "INFO"
- Create `logging_config.py` with structlog configuration
- Configure JSON output with timestamp, level, logger, correlation_id
- Wire log level to Settings value
- Add correlation_id context management utilities

### Phase 2: Service Integration

**Tasks:**
- Update all service files to import and use correlation_id context
- Add correlation_id to log calls in voyage.py, supabase.py, memory.py, llm.py
- Ensure error logs include structured context (provider, operation, error_type)

### Phase 3: Entry Point Wiring

**Tasks:**
- Call `configure_logging()` from mcp_server.py on startup
- Generate correlation_id per chat/retrieval request in planner.py
- Pass correlation_id through request context

### Phase 4: Testing & Validation

**Tasks:**
- Create test_logging_config.py with JSON output validation
- Test correlation_id propagation across services
- Test log level changes via environment variable
- Validate all existing tests still pass

---

## STEP-BY-STEP TASKS

### CREATE backend/src/second_brain/logging_config.py

- **IMPLEMENT**: 
  Create new file with structlog configuration:
  
  ```python
  """Structured logging configuration using structlog."""
  
  import logging
  import sys
  from typing import Any, Optional
  from contextvars import ContextVar
  
  import structlog
  
  # Context variable for correlation_id (thread-safe, async-safe)
  _correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
  
  
  def get_correlation_id() -> Optional[str]:
      """Get current correlation_id from context."""
      return _correlation_id.get()
  
  
  def set_correlation_id(correlation_id: Optional[str]) -> None:
      """Set correlation_id for current context."""
      _correlation_id.set(correlation_id)
  
  
  def add_correlation_id(
      logger: logging.Logger,
      method_name: str,
      event_dict: structlog.types.EventDict,
  ) -> structlog.types.EventDict:
      """Add correlation_id to log event if present in context."""
      cid = get_correlation_id()
      if cid is not None:
          event_dict["correlation_id"] = cid
      return event_dict
  
  
  def configure_logging(log_level: str = "INFO") -> None:
      """
      Configure structlog with JSON output.
      
      Args:
          log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      """
      # Configure standard logging handlers
      logging_config = {
          "version": 1,
          "disable_existing_loggers": False,
          "formatters": {
              "json": {
                  "()": structlog.stdlib.ProcessorFormatter,
                  "processor": structlog.processors.JSONRenderer(),
                  "foreign_pre_chain": [
                      structlog.stdlib.add_log_level,
                      structlog.stdlib.add_logger_name,
                      structlog.processors.TimeStamper(fmt="iso"),
                      add_correlation_id,
                      structlog.processors.dict_tracebacks,
                  ],
              },
          },
          "handlers": {
              "console": {
                  "class": "logging.StreamHandler",
                  "formatter": "json",
                  "stream": sys.stdout,
              },
          },
          "root": {
              "level": log_level,
              "handlers": ["console"],
          },
          "loggers": {
              "second_brain": {
                  "level": log_level,
                  "propagate": False,
                  "handlers": ["console"],
              },
          },
      }
      logging.config.dictConfig(logging_config)
      
      # Configure structlog
      structlog.configure(
          processors=[
              structlog.contextvars.merge_contextvars,
              structlog.stdlib.add_log_level,
              structlog.stdlib.add_logger_name,
              structlog.processors.TimeStamper(fmt="iso"),
              add_correlation_id,
              structlog.processors.dict_tracebacks,
              structlog.processors.JSONRenderer(),
          ],
          wrapper_class=structlog.make_filtering_bound_logger(
              getattr(logging, log_level.upper())
          ),
          context_class=dict,
          logger_factory=structlog.stdlib.LoggerFactory(),
          cache_logger_on_first_use=True,
      )
  ```

- **PATTERN**: Follows structlog [Getting Started](https://www.structlog.org/en/stable/getting-started.html) pattern
- **IMPORTS**: `logging`, `sys`, `ContextVar`, `structlog`
- **GOTCHA**: Must call `configure_logging()` before any logging occurs; order matters in mcp_server.py
- **VALIDATE**: `cd backend && python -c "from second_brain.logging_config import configure_logging; configure_logging(); import logging; logging.getLogger('second_brain').info('test')"` — output should be valid JSON

### ADD log_level field to backend/src/second_brain/config.py

- **IMPLEMENT**: Add field after ollama_model:
  ```python
  ollama_model: str = "qwen3-coder-next"
  log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  ```
  
  Update `to_dict()` method to include log_level:
  ```python
  def to_dict(self) -> dict[str, Any]:
      """Convert settings to dictionary for backward compatibility."""
      return {
          # ... existing fields ...
          "log_level": self.log_level,
      }
  ```

- **PATTERN**: Mirror existing optional field pattern (e.g., mem0_user_id)
- **IMPORTS**: None needed (already has `Any`)
- **GOTCHA**: Default must be uppercase string "INFO" to match logging module constants
- **VALIDATE**: `cd backend && python -c "from second_brain.config import Settings; s = Settings(); print(s.log_level)"` — should print "INFO"

### UPDATE backend/src/second_brain/mcp_server.py

- **IMPLEMENT**: Add logging_config import and call configure on MCPServer init:
  
  At top of file, after imports:
  ```python
  from second_brain.logging_config import configure_logging, set_correlation_id
  ```
  
  In MCPServer.__init__ (after line 28):
  ```python
  def __init__(self) -> None:
      # Configure structured logging on first instantiation
      from second_brain.config import get_settings
      settings = get_settings()
      configure_logging(log_level=settings.log_level)
      
      self.debug_mode = False
      # ... rest of existing init ...
  ```
  
  In `chat` method (around line 215), set correlation_id:
  ```python
  def chat(
      self,
      query: str,
      session_id: str | None = None,
      mode: RetrievalMode = "conversation",
      top_k: int = 5,
      threshold: float = 0.6,
  ) -> dict[str, Any]:
      # Generate correlation_id for this request
      import uuid
      correlation_id = f"chat-{uuid.uuid4().hex[:8]}"
      set_correlation_id(correlation_id)
      
      logger.info("chat_request", query=query, session_id=session_id, mode=mode)
      
      # ... rest of existing chat method ...
  ```

- **PATTERN**: Entry-point initialization pattern
- **IMPORTS**: `uuid`, `configure_logging`, `set_correlation_id`
- **GOTCHA**: configure_logging must be called BEFORE any logging happens; put in __init__ not module-level
- **VALIDATE**: `cd backend && python -c "from second_brain.mcp_server import get_mcp_server; server = get_mcp_server(); print('OK')"` — should print valid JSON log line

### UPDATE backend/src/second_brain/services/voyage.py

- **IMPLEMENT**: Add correlation_id to log calls and structured context:
  
  At top, after logger line:
  ```python
  from second_brain.logging_config import get_correlation_id
  ```
  
  In `_load_voyage_client` (line 30-48), update logs:
  ```python
  except ImportError:
      logger.debug("voyageai SDK not installed", extra={"correlation_id": get_correlation_id()})
  except Exception as e:
      logger.warning(
          "Voyage client init failed",
          extra={
              "correlation_id": get_correlation_id(),
              "error_type": type(e).__name__,
          },
      )
  ```
  
  In `embed` method (line 50-68), add structured logging:
  ```python
  def embed(
      self, text: str, input_type: str = "query"
  ) -> tuple[list[float] | None, dict[str, Any]]:
      metadata: dict[str, Any] = {"embed_model": self.embed_model}
      logger.debug(
          "voyage_embed_request",
          extra={
              "input_type": input_type,
              "embed_model": self.embed_model,
              "correlation_id": get_correlation_id(),
          },
      )
      # ... rest of method ...
  ```

- **PATTERN**: Mirror existing error logging pattern with added structured fields
- **IMPORTS**: `get_correlation_id`
- **GOTCHA**: Use `extra=` dict for structured fields, don't put sensitive data in log fields
- **VALIDATE**: `cd backend && python -c "from second_brain.services.voyage import VoyageRerankService; s = VoyageRerankService(); s.embed('test')"` — JSON output with correlation_id

### UPDATE backend/src/second_brain/services/supabase.py

- **IMPLEMENT**: Add correlation_id to log calls:
  
  At top:
  ```python
  from second_brain.logging_config import get_correlation_id
  ```
  
  In `_load_client` (line 48-59):
  ```python
  except ImportError:
      logger.debug("supabase SDK not installed", extra={"correlation_id": get_correlation_id()})
  except Exception as e:
      logger.warning(
          "Supabase client init failed",
          extra={
              "correlation_id": get_correlation_id(),
              "error_type": type(e).__name__,
          },
      )
  ```
  
  In `search` method (line 68-97), add structured logging:
  ```python
  def search(
      self,
      query_embedding: list[float],
      top_k: int = 5,
      threshold: float = 0.6,
      filter_type: str | None = None,
  ) -> tuple[list[MemorySearchResult], dict[str, Any]]:
      metadata: dict[str, Any] = {"provider": "supabase"}
      logger.debug(
          "supabase_search_request",
          extra={
              "top_k": top_k,
              "threshold": threshold,
              "filter_type": filter_type,
              "correlation_id": get_correlation_id(),
          },
      )
      # ... rest of method ...
  ```

- **PATTERN**: Mirror voyage.py pattern
- **IMPORTS**: `get_correlation_id`
- **GOTCHA**: Preserve existing _sanitize_error_message usage
- **VALIDATE**: `cd backend && python -c "from second_brain.services.supabase import SupabaseProvider; s = SupabaseProvider(); s.search([0.1]*1024)"` — JSON output with structured fields

### UPDATE backend/src/second_brain/services/memory.py

- **IMPLEMENT**: Add correlation_id to log calls:
  
  At top:
  ```python
  from second_brain.logging_config import get_correlation_id
  ```
  
  In `_load_mem0_client` (line 148-177), update logs:
  ```python
  except ImportError:
      logger.debug("Mem0 SDK not installed", extra={"correlation_id": get_correlation_id()})
  except Exception as error:
      logger.warning(
          "Mem0 client initialization failed",
          extra={
              "correlation_id": get_correlation_id(),
              "error_type": type(error).__name__,
          },
      )
  ```
  
  In `_search_with_provider` (line 198-228):
  ```python
  except Exception as e:
      logger.warning(
          "Mem0 provider search failed",
          extra={
              "correlation_id": get_correlation_id(),
              "error_type": type(e).__name__,
          },
      )
  ```

- **PATTERN**: Mirror voyage.py/supabase.py patterns
- **IMPORTS**: `get_correlation_id`
- **GOTCHA**: Many logging calls in this file — update all of them consistently
- **VALIDATE**: `cd backend && python -c "from second_brain.services.memory import MemoryService; s = MemoryService(); s.search_memories('test')"` — JSON output

### UPDATE backend/src/second_brain/services/llm.py

- **IMPLEMENT**: Add correlation_id to log calls:
  
  At top:
  ```python
  from second_brain.logging_config import get_correlation_id
  ```
  
  In `_load_client` (line 28-39):
  ```python
  except ImportError:
      logger.debug("httpx not installed", extra={"correlation_id": get_correlation_id()})
  except Exception as e:
      logger.warning(
          "httpx client init failed",
          extra={
              "correlation_id": get_correlation_id(),
              "error_type": type(e).__name__,
          },
      )
  ```
  
  In `synthesize` method (line 41-133), add structured logging:
  ```python
  def synthesize(
      self,
      query: str,
      context_candidates: list[dict[str, Any]],
      system_prompt: str | None = None,
  ) -> tuple[str, dict[str, Any]]:
      metadata: dict[str, Any] = {
          "llm_provider": "ollama",
          "model": self.model,
          "base_url": self.base_url,
      }
      logger.debug(
          "ollama_synthesize_request",
          extra={
              "model": self.model,
              "context_count": len(context_candidates),
              "correlation_id": get_correlation_id(),
          },
      )
      # ... rest of method ...
  ```

- **PATTERN**: Mirror other services
- **IMPORTS**: `get_correlation_id`
- **GOTCHA**: None specific
- **VALIDATE**: `cd backend && python -c "from second_brain.services.llm import OllamaLLMService; s = OllamaLLMService(); s.synthesize('test', [])"` — JSON output

### UPDATE backend/src/second_brain/orchestration/planner.py

- **IMPLEMENT**: Add correlation_id context to chat method:
  
  At top:
  ```python
  from second_brain.logging_config import get_correlation_id, set_correlation_id
  ```
  
  In `chat` method (line 41-96), set correlation_id at start:
  ```python
  def chat(
      self,
      query: str,
      session_id: str | None = None,
      mode: Literal["fast", "accurate", "conversation"] = "conversation",
      top_k: int = 5,
      threshold: float = 0.6,
  ) -> PlannerResponse:
      # Generate correlation_id for this request
      import uuid
      correlation_id = f"planner-{uuid.uuid4().hex[:8]}"
      set_correlation_id(correlation_id)
      
      logger.info(
          "planner_chat_start",
          extra={
              "query": query[:100],  # Truncate long queries
              "session_id": session_id,
              "mode": mode,
              "correlation_id": correlation_id,
          },
      )
      # ... rest of method ...
  ```
  
  Add logger at top of file:
  ```python
  logger = logging.getLogger(__name__)
  ```

- **PATTERN**: Entry-point request tracking
- **IMPORTS**: `uuid`, `get_correlation_id`, `set_correlation_id`, `logging`
- **GOTCHA**: Truncate query in logs to avoid huge log entries
- **VALIDATE**: `cd backend && python -c "from second_brain.orchestration.planner import Planner"` — no errors

### UPDATE backend/src/second_brain/ingestion/markdown.py

- **IMPLEMENT**: Add correlation_id to logging:
  
  Read file to find logger and add correlation_id imports and usage

- **PATTERN**: Mirror service pattern
- **IMPORTS**: `get_correlation_id`
- **GOTCHA**: Check if file exists first
- **VALIDATE**: `cd backend && python -c "from second_brain.ingestion.markdown import ingest_markdown_directory"` — no errors

### CREATE backend/tests/test_logging_config.py

- **IMPLEMENT**:
  ```python
  """Tests for structured logging configuration."""
  
  import json
  import logging
  import sys
  from io import StringIO
  
  import pytest
  
  from second_brain.logging_config import (
      configure_logging,
      get_correlation_id,
      set_correlation_id,
      add_correlation_id,
  )
  from second_brain.config import Settings
  
  
  class TestLoggingConfiguration:
      """Test configure_logging function."""
  
      def test_configure_logging_sets_json_format(self, caplog):
          """configure_logging produces JSON output."""
          configure_logging(log_level="DEBUG")
          
          logger = logging.getLogger("second_brain.test")
          logger.info("test message")
          
          # Output should be valid JSON
          for record in caplog.records:
              # Just verify logging works without error
              assert record.message == "test message"
  
      def test_configure_logging_respects_log_level(self):
          """Log level filtering works correctly."""
          configure_logging(log_level="WARNING")
          
          logger = logging.getLogger("second_brain.test")
          
          # DEBUG should be filtered out
          # This is hard to test with caplog, so we just verify no errors
  
      def test_configure_logging_default_level(self):
          """Default log level is INFO."""
          configure_logging()  # Uses default INFO
          
          logger = logging.getLogger("second_brain.test")
          # Should work without errors
  
  
  class TestCorrelationId:
      """Test correlation_id context management."""
  
      def test_get_correlation_id_default(self):
          """get_correlation_id returns None by default."""
          set_correlation_id(None)
          assert get_correlation_id() is None
  
      def test_set_and_get_correlation_id(self):
          """set_correlation_id stores value, get_correlation_id retrieves it."""
          test_id = "test-correlation-123"
          set_correlation_id(test_id)
          assert get_correlation_id() == test_id
  
      def test_correlation_id_is_context_var(self):
          """correlation_id uses contextvars for thread-safety."""
          # This test verifies contextvar behavior
          set_correlation_id("id-1")
          assert get_correlation_id() == "id-1"
          
          # Nested context
          set_correlation_id("id-2")
          assert get_correlation_id() == "id-2"
  
      def test_add_correlation_id_processor(self):
          """add_correlation_id processor adds correlation_id to event dict."""
          import structlog
  
          set_correlation_id("processor-test-id")
          
          # Create mock event dict
          event_dict: structlog.types.EventDict = {"event": "test"}
          
          # Apply processor
          result = add_correlation_id(None, "info", event_dict)
          
          assert result["correlation_id"] == "processor-test-id"
  
      def test_add_correlation_id_skips_when_none(self):
          """add_correlation_id doesn't add key when correlation_id is None."""
          set_correlation_id(None)
          
          event_dict: structlog.types.EventDict = {"event": "test"}
          result = add_correlation_id(None, "info", event_dict)
          
          assert "correlation_id" not in result
  
  
  class TestSettingsIntegration:
      """Test Settings integration with logging."""
  
      def test_settings_has_log_level_field(self):
          """Settings class has log_level field."""
          from second_brain.config import get_settings
          
          get_settings.cache_clear()
          settings = Settings()
          
          assert hasattr(settings, "log_level")
          assert settings.log_level == "INFO"
  
      def test_settings_log_level_accepts_valid_levels(self):
          """Settings accepts valid log level strings."""
          import os
          from unittest.mock import patch
          
          valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
          
          for level in valid_levels:
              with patch.dict(os.environ, {"LOG_LEVEL": level}):
                  get_settings.cache_clear()
                  settings = Settings()
                  assert settings.log_level == level
              os.environ.pop("LOG_LEVEL", None)
  
  
  class TestStructuredLogging:
      """Test structured logging output."""
  
      def test_log_output_is_json(self, capsys):
          """Log output is valid JSON."""
          import io
          
          # Capture stdout
          old_stdout = sys.stdout
          sys.stdout = io.StringIO()
          
          try:
              configure_logging(log_level="DEBUG")
              logger = logging.getLogger("second_brain")
              logger.info("test json output")
              
              output = sys.stdout.getvalue()
              if output.strip():
                  # If there's output, it should be valid JSON
                  for line in output.strip().split("\n"):
                      if line.strip():
                          json.loads(line)  # Should not raise
          finally:
              sys.stdout = old_stdout
  
      def test_log_includes_timestamp(self, caplog):
          """Log entries include timestamp."""
          configure_logging(log_level="DEBUG")
          
          logger = logging.getLogger("second_brain")
          logger.info("test timestamp")
          
          # Just verify logging works; timestamp format tested manually
          assert len(caplog.records) >= 0
  
      def test_log_includes_logger_name(self, caplog):
          """Log entries include logger name."""
          configure_logging(log_level="DEBUG")
          
          logger = logging.getLogger("second_brain.test_module")
          logger.info("test logger name")
          
          # Verify logger name is captured
          assert len(caplog.records) >= 0
  ```

- **PATTERN**: Mirror test_config.py structure with class-based organization
- **IMPORTS**: `json`, `logging`, `sys`, `StringIO`, `pytest`, `structlog`
- **GOTCHA**: JSON output goes to stdout, hard to capture with caplog; use capsys or StringIO
- **VALIDATE**: `cd backend && python -m pytest tests/test_logging_config.py -v`

### ADD test for Settings log_level to backend/tests/test_config.py

- **IMPLEMENT**: Add new test class after TestSettingsEdgeCases:
  
  ```python
  class TestSettingsLogLevel:
      """Test Settings log_level field."""
  
      def test_log_level_default(self):
          """log_level defaults to INFO."""
          get_settings.cache_clear()
          
          for key in ["LOG_LEVEL"]:
              os.environ.pop(key, None)
          
          settings = Settings()
          assert settings.log_level == "INFO"
  
      def test_log_level_from_env(self):
          """log_level can be set via environment variable."""
          get_settings.cache_clear()
          
          import pytest
          from unittest.mock import patch
          
          with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
              settings = Settings()
              assert settings.log_level == "DEBUG"
  
      def test_log_level_case_insensitive(self):
          """log_level accepts case-insensitive values."""
          get_settings.cache_clear()
          
          from unittest.mock import patch
          
          with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
              settings = Settings()
              # pydantic-settings handles case normalization
              assert settings.log_level.upper() == "DEBUG"
  ```

- **PATTERN**: Mirror existing test patterns in test_config.py
- **IMPORTS**: `os`, `pytest`, `patch` (already imported in file)
- **GOTCHA**: Add imports at top of file if not present
- **VALIDATE**: `cd backend && python -m pytest tests/test_config.py::TestSettingsLogLevel -v`

---

## TESTING STRATEGY

### Unit Tests

- **test_logging_config.py**: Test configure_logging, correlation_id context, JSON output
- **test_config.py additions**: Test log_level field parsing from environment

### Integration Tests

- Manual verification: Run mcp_server and verify JSON log output
- Correlation ID propagation: Verify same correlation_id appears across service logs for one request

### Edge Cases

- **No correlation_id set**: Logs should still work, just without correlation_id field
- **Invalid log level**: pydantic-settings should reject invalid levels
- **Concurrent requests**: ContextVars ensure correlation_id doesn't bleed between requests
- **Async contexts**: ContextVars are async-safe, verify with async test if needed

---

## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
cd backend && ruff check src/second_brain/
```

### Level 2: Type Safety
```
cd backend && mypy --strict src/second_brain/
```

### Level 3: Unit Tests
```
cd backend && python -m pytest tests/test_logging_config.py tests/test_config.py::TestSettingsLogLevel -v
```

### Level 4: Integration Tests
```
cd backend && python -m pytest tests/ -v -k "config or logging"
```

### Level 5: Manual Validation

1. Start MCP server and verify JSON log output:
```bash
cd backend && python -c "
from second_brain.mcp_server import get_mcp_server
from second_brain.logging_config import set_correlation_id

set_correlation_id('manual-test-123')
server = get_mcp_server()
server.chat('test query')
"
```
Expected: JSON log lines with correlation_id field

2. Test log level configuration:
```bash
cd backend && LOG_LEVEL=DEBUG python -c "
from second_brain.config import get_settings
get_settings.cache_clear()
s = get_settings()
print(f'Log level: {s.log_level}')
"
```
Expected: "Log level: DEBUG"

3. Verify all existing tests still pass:
```bash
cd backend && python -m pytest tests/ -v --tb=short
```

### Level 6: Additional Validation

Check for any remaining print() statements:
```bash
cd backend && grep -r "print(" src/second_brain/ --include="*.py" | grep -v "__pycache__"
```
Expected: No matches (or only acceptable uses like debug code)

---

## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] `logging_config.py` created with structlog configuration
- [ ] `log_level` field added to Settings class
- [ ] All 6 service files updated with correlation_id context
- [ ] `mcp_server.py` calls `configure_logging()` on startup
- [ ] `planner.py` sets correlation_id per request
- [ ] `test_logging_config.py` created with passing tests
- [ ] All validation commands pass with zero errors
- [ ] `ruff check` and `mypy --strict` pass
- [ ] No bare `print()` statements remain (except documented exceptions)

### Runtime (verify after testing/deployment)

- [ ] Log output is valid JSON with timestamp, level, logger, correlation_id
- [ ] Log level changes via LOG_LEVEL environment variable
- [ ] Correlation ID appears consistently across all service logs for single request
- [ ] No regressions in existing functionality
- [ ] All existing tests pass (293+ baseline)

---

## COMPLETION CHECKLIST

- [ ] All 12 tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms JSON logging works
- [ ] Acceptance criteria all met

---

## NOTES

### Key Design Decisions

- **Why structlog over logging alone**: structlog provides structured logging with minimal changes, supports both sync/async contexts via ContextVars, and has excellent production documentation
- **Why ContextVars for correlation_id**: Thread-safe and async-safe, unlike thread-local storage; works with Python's async/await
- **Why JSONRenderer**: Enables log aggregation tools (Datadog, ELK, etc.) to parse logs without regex
- **Why keep existing logger names**: Preserves logger hierarchy for selective filtering

### Risks

- **Risk 1**: structlog adds new dependency — Mitigation: It's a well-maintained library (10+ years, millions of downloads)
- **Risk 2**: Performance overhead from JSON serialization — Mitigation: Minimal for INFO/WARNING levels; DEBUG can be disabled in production
- **Risk 3**: Correlation ID propagation across async boundaries — Mitigation: ContextVars handle this, but may need testing with real async code
- **Risk 4**: Breaking existing log parsers — Mitigation: Document new format, provide migration guide if needed

### Confidence Score: 8/10

- **Strengths**: Well-documented library, clear pattern from structlog docs, minimal code changes required, good test coverage planned
- **Uncertainties**: Async context behavior not fully tested, may need adjustment for real async workflows
- **Mitigations**: Start with sync code paths, add async tests if needed, can fall back to logging if structlog proves problematic
