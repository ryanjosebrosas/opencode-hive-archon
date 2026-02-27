# Structured Plan: P1-02 pydantic-settings-config

> Spec: Replace scattered os.getenv() calls in deps.py with centralized Pydantic Settings class
> Complexity: Standard (5-model free review gauntlet)
> Pillar: P1 (Data Infrastructure) — Pillar A: Type Safety & Config

---

# Feature: Pydantic Settings Configuration

## Feature Description

Centralize all environment variable reads from deps.py into a single Pydantic Settings class using pydantic-settings BaseSettings. This provides type-safe configuration with automatic validation, sensible defaults, and structured error messages on startup. All 8 os.getenv calls in deps.py will be replaced with Settings field access. Service files (voyage.py, llm.py, memory.py, supabase.py, ingestion/markdown.py) keep their own os.getenv calls as fallback — this spec only centralizes deps.py.

## User Story

As a **developer**, I want to **have all configuration in one validated Settings class**, so that **I get immediate structured errors when environment variables are misconfigured instead of silent failures or AttributeError deep in the code**.

## Problem Statement

Currently deps.py has 8 scattered os.getenv() calls (lines 53, 57, 62, 137-144) with inconsistent defaults and no validation. If someone sets `VOYAGE_EMBED_ENABLED=invalid`, the code silently treats it as False. If `MEM0_USER_ID` is required but missing, the error only appears when the service tries to use it. There's no single source of truth for what configuration exists.

## Solution Statement

**What approach we chose:** Create `backend/src/second_brain/config.py` with a Pydantic Settings class using `pydantic_settings.BaseSettings`. All fields are optional with sensible defaults — no breaking changes if no .env file exists. deps.py imports Settings and uses it instead of os.getenv.

**Key decisions:**
- Decision 1: **All fields optional** — because existing tests run without .env file, breaking changes block adoption
- Decision 2: **pydantic-settings BaseSettings with no env_prefix** — because existing env var names (MEM0_API_KEY, VOYAGE_EMBED_MODEL, etc.) should stay the same
- Decision 3: **Settings singleton at module level** — because multiple instantiations waste validation overhead, single source of truth
- Decision 4: **Provide get_settings() function for DI/testing** — because tests need to override settings without global mutation
- Decision 5: **Scope: ONLY config.py + deps.py refactor + tests** — because service files have their own fallback patterns, centralizing everything in one spec increases risk

## Feature Metadata

- **Feature Type**: Refactor + New Capability
- **Estimated Complexity**: Medium (standard spec — 5-model free review gauntlet)
- **Primary Systems Affected**: deps.py, config.py (new), tests/test_config.py (new), pyproject.toml
- **Dependencies**: pydantic-settings>=2.0 (already have pydantic>=2.0)

### Slice Guardrails (Required)

- **Single Outcome**: All 8 os.getenv calls in deps.py replaced with Settings field access, validated on import
- **Expected Files Touched**: 4 files (config.py new, deps.py refactor, test_config.py new, pyproject.toml dependency)
- **Scope Boundary**: Does NOT modify voyage.py, llm.py, memory.py, supabase.py, ingestion/markdown.py — those keep their own os.getenv fallbacks
- **Split Trigger**: If service file centralization is needed, create follow-up spec P1-XX "centralize-service-config"

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/deps.py` (lines 1-145) — Why: Main file to refactor, contains all 8 os.getenv calls to replace
- `backend/pyproject.toml` (lines 1-24) — Why: Need to add pydantic-settings dependency
- `tests/test_voyage_rerank.py` (lines 1-100) — Why: Test pattern example — fixture helpers, mock patterns, assertion style
- `tests/test_context_packet_contract.py` (lines 1-100) — Why: Pydantic model testing pattern — validation error tests, bounds testing
- `backend/src/second_brain/services/voyage.py` (lines 36-48) — Why: Example of os.getenv with fallback pattern (reference, not modifying)
- `backend/src/second_brain/services/llm.py` (lines 20-25) — Why: Example of os.getenv with default pattern (reference, not modifying)

### New Files to Create

- `backend/src/second_brain/config.py` — Pydantic Settings class with all env var fields, get_settings() function
- `backend/tests/test_config.py` — Comprehensive tests for Settings validation, defaults, overrides, error messages

### Related Memories (from memory.md)

> Past experiences and lessons relevant to this feature.

- Memory: "Embedding dimension alignment: Voyage voyage-4-large outputs 1024 dims; Supabase pgvector column must match" — Relevance: Shows why config validation matters early
- Memory: "Legacy SDK compatibility: When provider SDKs differ on auth args, use temporary env bridging with lock + restore" — Relevance: Testing may need env var manipulation
- Memory: "OpenCode SDK swallows AbortError" / "info.error handling" — Relevance: Error messages must be structured and actionable
- Memory: "All fields optional with sensible defaults — nothing breaks if no .env file exists" — Relevance: Core design decision for this spec

### Relevant Documentation

> The execution agent SHOULD read these before implementing.

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
  - Specific section: "BaseSettings" and "Field values with defaults"
  - Why: Shows recommended approach for optional fields with defaults
- [Pydantic Validation Errors](https://docs.pydantic.dev/latest/concepts/errors/)
  - Specific section: "Error handling" and "ValidationError structure"
  - Why: Understanding error message structure for test assertions

### Patterns to Follow

> Specific patterns extracted from the codebase — include actual code examples from the project.

**Pydantic Model Pattern** (from `backend/src/second_brain/contracts/context_packet.py:1-50`):
```python
from pydantic import BaseModel, Field, field_validator

class ContextCandidate(BaseModel):
    """Candidate for context retrieval."""
    
    id: str
    content: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
```
- Why this pattern: Shows pydantic Field usage with constraints, default_factory for mutable defaults
- Common gotchas: Use Field(default_factory=dict) not default={} for mutable types

**Test Fixture Pattern** (from `tests/test_voyage_rerank.py:9-20`):
```python
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
```
- Why this pattern: Helper function for creating test data, keeps tests DRY
- Common gotchas: Keep helpers simple, avoid complex state in fixtures

**Mock Pattern** (from `tests/test_voyage_rerank.py:28-58`):
```python
def test_real_rerank_success(self):
    """With mocked client, real rerank returns reordered candidates."""
    service = VoyageRerankService(enabled=True, use_real_rerank=True)

    mock_client = MagicMock()
    mock_reranking = MagicMock()
    
    # ... setup mock return values
    mock_client.rerank.return_value = mock_reranking
    service._voyage_client = mock_client
```
- Why this pattern: Direct attribute assignment for mocks, clear setup
- Common gotchas: Use MagicMock for complex nested objects, verify calls with assert_called_once_with

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

Add pydantic-settings dependency to pyproject.toml and create the Settings class in config.py.

**Tasks:**
- Add `pydantic-settings>=2.0` to pyproject.toml dependencies
- Create `backend/src/second_brain/config.py` with Settings class
- Define all 11 env var fields with types and defaults
- Create get_settings() function for DI/testing

### Phase 2: Core Implementation

Refactor deps.py to use Settings instead of os.getenv.

**Tasks:**
- Remove `import os` from deps.py
- Import Settings from config module
- Replace all 8 os.getenv calls with Settings field access
- Update create_voyage_rerank_service() to use Settings
- Update get_default_config() to use Settings

### Phase 3: Integration

Ensure settings are validated on startup and integrate with existing code.

**Tasks:**
- Verify Settings instantiates on module import (eager validation)
- Ensure no circular imports between config.py and deps.py
- Run existing tests to verify no regressions

### Phase 4: Testing & Validation

Create comprehensive test suite for Settings class.

**Tasks:**
- Create `backend/tests/test_config.py`
- Test Settings default values (no .env file)
- Test Settings with environment variable overrides
- Test validation error messages for invalid types
- Test get_settings() function returns singleton
- Test Settings can be overridden for testing

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE backend/src/second_brain/config.py

- **IMPLEMENT**: Create new file with Pydantic Settings class. All fields optional with defaults. See full code in Appendix A.
- **PATTERN**: Follows pydantic-settings BaseSettings pattern from documentation
- **IMPORTS**: `from pydantic_settings import BaseSettings, SettingsConfigDict`
- **GOTCHA**: 
  - Use `model_config` not `Config` (Pydantic v2 syntax)
  - Use `SettingsConfigDict` not inner `Config` class
  - `extra="ignore"` prevents errors from unrelated env vars in environment
  - `@lru_cache` ensures singleton pattern for testing
  - Eager validation on import means bad config = immediate startup error
- **VALIDATE**: `python -c "from second_brain.config import Settings, get_settings; s = get_settings(); print('Settings loaded:', type(s).__name__)"`

### UPDATE backend/pyproject.toml

- **IMPLEMENT**: Add pydantic-settings to dependencies list (line 7, after pydantic)
- **PATTERN**: Standard dependency addition pattern
- **IMPORTS**: N/A
- **GOTCHA**: 
  - Keep alphabetical-ish order (pydantic-settings right after pydantic)
  - Use >=2.0 to match pydantic major version
- **VALIDATE**: `pip install -e backend && python -c "import pydantic_settings; print('pydantic-settings version:', pydantic_settings.__version__)"`

### UPDATE backend/src/second_brain/deps.py

- **IMPLEMENT**: Refactor to use Settings instead of os.getenv. Full file content in Appendix B.
- **PATTERN**: Mirrors existing function signatures, only changes internal implementation
- **IMPORTS**: 
  - Remove: `import os`
  - Add: `from second_brain.config import get_settings`
- **GOTCHA**: 
  - Keep function signatures identical for backward compatibility
  - Explicit function args (embed_model, embed_enabled, use_real_rerank) still take precedence over settings
  - `get_settings()` returns cached singleton, safe to call multiple times
  - No circular import: config.py has no imports from second_brain submodules
- **VALIDATE**: `python -c "from second_brain.deps import get_default_config; cfg = get_default_config(); print('Config keys:', list(cfg.keys()))"`

### CREATE backend/tests/test_config.py

- **IMPLEMENT**: Comprehensive test file (~200+ lines). Full code in Appendix C.
- **PATTERN**: Follows pytest class-based test organization from test_voyage_rerank.py
- **IMPORTS**: 
  ```python
  import os
  from unittest.mock import patch
  
  import pytest
  from pydantic import ValidationError
  
  from second_brain.config import Settings, get_settings
  ```
- **GOTCHA**: 
  - Always call `get_settings.cache_clear()` before tests that need fresh settings
  - Use `patch.dict(os.environ, ...)` for env var manipulation
  - Clean up env vars after tests to prevent test pollution
  - Boolean parsing: pydantic-settings parses "true", "1", "yes" as True; "false", "0", "no", "" as False
  - Extra env vars are ignored (extra="ignore"), won't cause errors
- **VALIDATE**: `pytest tests/test_config.py -v`

---

## TESTING STRATEGY

### Unit Tests

Test Settings class in isolation:
- Default values when no env vars set
- Environment variable overrides for all field types (bool, str)
- Boolean parsing (various true/false string representations)
- get_settings() singleton behavior and cache
- to_dict() method returns all fields
- Extra env vars are ignored

### Integration Tests

Test Settings with deps.py:
- get_default_config() uses Settings values
- create_voyage_rerank_service() uses Settings defaults
- Explicit function args override Settings
- Full flow: Settings → deps.py → service creation

### Edge Cases

- Empty string for optional string fields (valid, not None)
- Whitespace preservation in string values
- Case sensitivity for env var names (case_sensitive=False in config)
- Invalid boolean values (should raise ValidationError or parse conservatively)
- Cache clearing for test isolation
- Concurrent access to get_settings() (lru_cache is thread-safe)

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style
```
ruff check backend/src/second_brain/config.py backend/src/second_brain/deps.py tests/test_config.py
```
```
ruff format backend/src/second_brain/config.py backend/src/second_brain/deps.py tests/test_config.py --check
```

### Level 2: Type Safety
```
mypy --strict backend/src/second_brain/config.py backend/src/second_brain/deps.py
```

### Level 3: Unit Tests
```
pytest tests/test_config.py -v
```

### Level 4: Integration Tests (Full Suite)
```
pytest tests/ -v --tb=short
```

### Level 5: Manual Validation

**Test 1: Settings loads with defaults**
```
python -c "from second_brain.config import get_settings; s = get_settings(); print('mem0_user_id:', s.mem0_user_id); print('voyage_embed_model:', s.voyage_embed_model)"
```
Expected: No errors, shows default values

**Test 2: Settings with env override**
```
set VOYAGE_EMBED_MODEL=test-model-override && python -c "from second_brain.config import get_settings; get_settings.cache_clear(); s = get_settings(); print('voyage_embed_model:', s.voyage_embed_model)"
```
Expected: voyage_embed_model shows test-model-override

**Test 3: deps.py uses Settings**
```
python -c "from second_brain.deps import get_default_config; cfg = get_default_config(); print('Config keys:', sorted(cfg.keys()))"
```
Expected: Shows all config keys including mem0_*, supabase_*, voyage_*

**Test 4: All existing tests pass**
```
pytest tests/ -x -v 2>&1 | tail -20
```
Expected: 293+ tests pass, 0 failures

### Level 6: Additional Validation

**Import test — no circular imports**
```
python -c "import second_brain.config; import second_brain.deps; print('No circular import errors')"
```

**Startup validation test**
```
python -c "from second_brain.config import _settings_instance; print('Settings validated on import:', type(_settings_instance).__name__)"
```

---

## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable only after running the code).

### Implementation (verify during execution)

- [ ] config.py created with Settings class using BaseSettings
- [ ] All 11 config fields defined with correct types and defaults
- [ ] get_settings() function with @lru_cache for singleton pattern
- [ ] Eager validation: _settings_instance created on module import
- [ ] deps.py refactored: import os removed, get_settings imported
- [ ] All 8 os.getenv calls in deps.py replaced with Settings field access
- [ ] pyproject.toml updated with pydantic-settings>=2.0 dependency
- [ ] test_config.py created with 20+ test cases
- [ ] mypy --strict passes on config.py and deps.py with zero errors
- [ ] ruff check passes with zero errors
- [ ] ruff format passes with zero formatting changes needed
- [ ] All 293+ existing tests pass
- [ ] All new test_config.py tests pass

### Runtime (verify after testing/deployment)

- [ ] Settings loads without .env file (uses defaults)
- [ ] Settings picks up environment variable overrides
- [ ] Boolean fields parse "true"/"false" strings correctly
- [ ] get_settings() returns same instance on repeated calls (singleton)
- [ ] Bad env var values raise ValidationError on startup (not silent failure)
- [ ] No circular import errors between config.py and deps.py
- [ ] deps.py functions work with Settings-based config
- [ ] Explicit function args override Settings defaults

---

## COMPLETION CHECKLIST

- [ ] All 4 tasks completed in order
- [ ] Each task validation command passed
- [ ] Full validation suite executed (lint, types, unit, integration)
- [ ] Manual validation confirms feature works
- [ ] All acceptance criteria met

---

## NOTES

### Key Design Decisions
- All fields optional to avoid breaking existing tests
- Singleton pattern via lru_cache for efficiency
- Eager validation on import for immediate error detection
- Scope limited to deps.py only (not service files)

### Risks
- Risk: Circular imports between config.py and other modules — Mitigation: config.py has no imports from second_brain submodules
- Risk: Tests pollute global settings state — Mitigation: get_settings.cache_clear() before each test

### Confidence Score: 9/10
- **Strengths**: Well-defined scope, clear patterns from existing code, comprehensive test plan
- **Uncertainties**: pydantic-settings boolean parsing edge cases
- **Mitigations**: Tests cover various boolean string representations

---

## APPENDIX A: Full config.py Code

```python
"""Centralized configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables.
    
    All fields are optional with sensible defaults.
    Missing or invalid env vars raise ValidationError on import.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars not defined here
    )
    
    # Mem0 settings
    mem0_use_real_provider: bool = False
    mem0_user_id: str | None = None
    mem0_api_key: str | None = None
    
    # Supabase settings
    supabase_use_real_provider: bool = False
    supabase_url: str | None = None
    supabase_key: str | None = None
    
    # Voyage settings
    voyage_embed_model: str = "voyage-4-large"
    voyage_embed_enabled: bool = False
    voyage_use_real_rerank: bool = False
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3-coder-next"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for backward compatibility."""
        return {
            "mem0_use_real_provider": self.mem0_use_real_provider,
            "mem0_user_id": self.mem0_user_id,
            "mem0_api_key": self.mem0_api_key,
            "supabase_use_real_provider": self.supabase_use_real_provider,
            "supabase_url": self.supabase_url,
            "supabase_key": self.supabase_key,
            "voyage_embed_model": self.voyage_embed_model,
            "voyage_embed_enabled": self.voyage_embed_enabled,
            "voyage_use_real_rerank": self.voyage_use_real_rerank,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached Settings singleton.
    
    Use this function for dependency injection and testing overrides.
    The cache ensures only one Settings instance exists per process.
    
    For testing: override with get_settings.cache_clear() then set env vars.
    """
    return Settings()


# Eager validation: instantiate on import to catch errors early
_settings_instance = get_settings()
```

---

## APPENDIX B: Full Refactored deps.py Code

```python
"""Dependency injection helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from second_brain.config import get_settings
from second_brain.services.memory import MemoryService
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.trace import TraceCollector
from second_brain.services.conversation import ConversationStore

if TYPE_CHECKING:
    from second_brain.orchestration.planner import Planner


def get_feature_flags() -> dict[str, bool]:
    """Get default feature flags for provider gating."""
    return {
        "mem0_enabled": True,
        "supabase_enabled": True,
        "graphiti_enabled": False,
        "external_rerank_enabled": True,
    }


def get_provider_status() -> dict[str, str]:
    """Get provider health status snapshot."""
    # In production, this would check actual provider health
    # For testing, return deterministic defaults
    return {
        "mem0": "available",
        "supabase": "available",
        "graphiti": "unavailable",
    }


def create_memory_service(
    provider: str = "mem0",
    config: dict[str, Any] | None = None,
) -> MemoryService:
    """Create memory service instance."""
    return MemoryService(provider=provider, config=config)


def create_voyage_rerank_service(
    enabled: bool = True,
    model: str = "rerank-2",
    embed_model: str | None = None,
    embed_enabled: bool | None = None,
    use_real_rerank: bool | None = None,
) -> VoyageRerankService:
    """Create voyage rerank service instance with settings defaults."""
    settings = get_settings()
    
    # Use provided args if explicit, otherwise fall back to settings
    _embed_model = embed_model or settings.voyage_embed_model
    _embed_enabled = (
        embed_enabled
        if embed_enabled is not None
        else settings.voyage_embed_enabled
    )
    _use_real_rerank = (
        use_real_rerank
        if use_real_rerank is not None
        else settings.voyage_use_real_rerank
    )
    
    return VoyageRerankService(
        enabled=enabled,
        model=model,
        embed_model=_embed_model,
        embed_enabled=_embed_enabled,
        use_real_rerank=_use_real_rerank,
    )


def create_trace_collector(
    max_traces: int = 1000,
) -> TraceCollector:
    """Create trace collector instance."""
    return TraceCollector(max_traces=max_traces)


def create_conversation_store(
    max_turns: int = 50,
    max_sessions: int = 100,
) -> ConversationStore:
    """Create conversation store instance."""
    return ConversationStore(
        max_turns_per_session=max_turns,
        max_sessions=max_sessions,
    )


def create_llm_service() -> Any:
    """Create LLM service for synthesis. Returns OllamaLLMService instance."""
    from second_brain.services.llm import OllamaLLMService

    return OllamaLLMService()


def create_planner(
    memory_service: MemoryService | None = None,
    rerank_service: VoyageRerankService | None = None,
    conversation_store: ConversationStore | None = None,
    trace_collector: TraceCollector | None = None,
    llm_service: Any | None = None,
) -> Planner:
    """Create planner with default dependencies."""
    from second_brain.orchestration.planner import Planner
    from second_brain.agents.recall import RecallOrchestrator

    _memory = memory_service or create_memory_service()
    _rerank = rerank_service or create_voyage_rerank_service()
    _conversations = conversation_store or create_conversation_store()

    orchestrator = RecallOrchestrator(
        memory_service=_memory,
        rerank_service=_rerank,
        feature_flags=get_feature_flags(),
        provider_status=get_provider_status(),
        trace_collector=trace_collector,
    )

    return Planner(
        recall_orchestrator=orchestrator,
        conversation_store=_conversations,
        trace_collector=trace_collector,
        llm_service=llm_service,
    )


def get_default_config() -> dict[str, Any]:
    """Get configuration from settings with safe defaults."""
    settings = get_settings()
    
    return {
        "default_mode": "conversation",
        "default_top_k": 5,
        "default_threshold": 0.6,
        "mem0_rerank_native": True,
        "mem0_skip_external_rerank": True,
        "mem0_use_real_provider": settings.mem0_use_real_provider,
        "mem0_user_id": settings.mem0_user_id,
        "mem0_api_key": settings.mem0_api_key,
        "supabase_use_real_provider": settings.supabase_use_real_provider,
        "supabase_url": settings.supabase_url,
        "supabase_key": settings.supabase_key,
        "voyage_embed_model": settings.voyage_embed_model,
    }
```

---

## APPENDIX C: Full test_config.py Code

```python
"""Tests for Pydantic Settings configuration."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from second_brain.config import Settings, get_settings


class TestSettingsDefaults:
    """Test Settings with no environment variables (default values)."""

    def test_all_defaults(self):
        """Settings loads with all default values when no env vars set."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {}, clear=False):
            for key in [
                "MEM0_USE_REAL_PROVIDER",
                "MEM0_USER_ID",
                "MEM0_API_KEY",
                "SUPABASE_USE_REAL_PROVIDER",
                "SUPABASE_URL",
                "SUPABASE_KEY",
                "VOYAGE_EMBED_MODEL",
                "VOYAGE_EMBED_ENABLED",
                "VOYAGE_USE_REAL_RERANK",
                "OLLAMA_BASE_URL",
                "OLLAMA_MODEL",
            ]:
                os.environ.pop(key, None)
            
            settings = Settings()
            
            assert settings.mem0_use_real_provider is False
            assert settings.mem0_user_id is None
            assert settings.mem0_api_key is None
            assert settings.supabase_use_real_provider is False
            assert settings.supabase_url is None
            assert settings.supabase_key is None
            assert settings.voyage_embed_model == "voyage-4-large"
            assert settings.voyage_embed_enabled is False
            assert settings.voyage_use_real_rerank is False
            assert settings.ollama_base_url == "http://localhost:11434"
            assert settings.ollama_model == "qwen3-coder-next"

    def test_to_dict(self):
        """Settings.to_dict() returns all fields as dictionary."""
        get_settings.cache_clear()
        settings = Settings()
        
        config_dict = settings.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "mem0_use_real_provider" in config_dict
        assert "mem0_user_id" in config_dict
        assert "mem0_api_key" in config_dict
        assert "supabase_use_real_provider" in config_dict
        assert "supabase_url" in config_dict
        assert "supabase_key" in config_dict
        assert "voyage_embed_model" in config_dict
        assert "voyage_embed_enabled" in config_dict
        assert "voyage_use_real_rerank" in config_dict
        assert "ollama_base_url" in config_dict
        assert "ollama_model" in config_dict


class TestSettingsEnvOverrides:
    """Test Settings with environment variable overrides."""

    def test_bool_parsing_true_values(self):
        """Boolean fields parse various true string values."""
        get_settings.cache_clear()
        
        true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "on"]
        
        for true_val in true_values:
            with patch.dict(os.environ, {"MEM0_USE_REAL_PROVIDER": true_val}):
                settings = Settings()
                assert settings.mem0_use_real_provider is True, f"Failed for {true_val}"
            os.environ.pop("MEM0_USE_REAL_PROVIDER", None)

    def test_bool_parsing_false_values(self):
        """Boolean fields parse various false string values."""
        get_settings.cache_clear()
        
        false_values = ["false", "False", "FALSE", "0", "no", "No", "off", ""]
        
        for false_val in false_values:
            with patch.dict(os.environ, {"MEM0_USE_REAL_PROVIDER": false_val}):
                settings = Settings()
                assert settings.mem0_use_real_provider is False, f"Failed for {false_val}"
            os.environ.pop("MEM0_USE_REAL_PROVIDER", None)

    def test_string_env_vars(self):
        """String fields accept environment variable values."""
        get_settings.cache_clear()
        
        with patch.dict(
            os.environ,
            {
                "MEM0_USER_ID": "test-user-123",
                "MEM0_API_KEY": "sk-test-key",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                "VOYAGE_EMBED_MODEL": "voyage-3-lite",
                "OLLAMA_BASE_URL": "http://remote-ollama:11434",
                "OLLAMA_MODEL": "qwen3-coder-plus",
            },
        ):
            settings = Settings()
            
            assert settings.mem0_user_id == "test-user-123"
            assert settings.mem0_api_key == "sk-test-key"
            assert settings.supabase_url == "https://test.supabase.co"
            assert settings.supabase_key == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            assert settings.voyage_embed_model == "voyage-3-lite"
            assert settings.ollama_base_url == "http://remote-ollama:11434"
            assert settings.ollama_model == "qwen3-coder-plus"

    def test_voyage_embed_enabled_parsing(self):
        """VOYAGE_EMBED_ENABLED parses boolean correctly."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"VOYAGE_EMBED_ENABLED": "true"}):
            settings = Settings()
            assert settings.voyage_embed_enabled is True
        
        with patch.dict(os.environ, {"VOYAGE_EMBED_ENABLED": "false"}):
            settings = Settings()
            assert settings.voyage_embed_enabled is False

    def test_voyage_use_real_rerank_parsing(self):
        """VOYAGE_USE_REAL_RERANK parses boolean correctly."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"VOYAGE_USE_REAL_RERANK": "true"}):
            settings = Settings()
            assert settings.voyage_use_real_rerank is True
        
        with patch.dict(os.environ, {"VOYAGE_USE_REAL_RERANK": "false"}):
            settings = Settings()
            assert settings.voyage_use_real_rerank is False


class TestSettingsValidation:
    """Test Settings validation error handling."""

    def test_extra_env_vars_ignored(self):
        """Settings ignores extra environment variables not in model."""
        get_settings.cache_clear()
        
        with patch.dict(
            os.environ,
            {
                "RANDOM_VAR": "should_be_ignored",
                "ANOTHER_VAR": "also_ignored",
            },
            clear=False,
        ):
            settings = Settings()
            assert hasattr(settings, "random_var") is False

    def test_case_insensitive_env_vars(self):
        """Settings accepts case-insensitive environment variable names."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"mem0_user_id": "lowercase-key"}):
            settings = Settings()
            assert settings.mem0_user_id == "lowercase-key"


class TestGetSettingsFunction:
    """Test get_settings() singleton function."""

    def test_returns_singleton(self):
        """get_settings() returns cached singleton instance."""
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_cache_can_be_cleared(self):
        """get_settings.cache_clear() allows re-initialization."""
        get_settings.cache_clear()
        
        settings1 = get_settings()
        
        get_settings.cache_clear()
        
        settings2 = get_settings()
        
        assert settings1 is not settings2

    def test_cache_info(self):
        """get_settings has LRU cache info."""
        get_settings.cache_clear()
        
        get_settings()
        
        info = get_settings.cache_info()
        assert info.hits == 0
        assert info.misses == 1
        
        get_settings()
        
        info = get_settings.cache_info()
        assert info.hits == 1
        assert info.misses == 1


class TestSettingsWithDeps:
    """Test Settings integration with deps.py functions."""

    def test_get_default_config_uses_settings(self):
        """get_default_config() returns settings-based values."""
        from second_brain.deps import get_default_config
        
        get_settings.cache_clear()
        
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert config["mem0_use_real_provider"] is False
        assert config["mem0_user_id"] is None
        assert config["mem0_api_key"] is None
        assert config["supabase_use_real_provider"] is False
        assert config["supabase_url"] is None
        assert config["supabase_key"] is None
        assert config["voyage_embed_model"] == "voyage-4-large"

    def test_get_default_config_with_env_overrides(self):
        """get_default_config() reflects environment variable overrides."""
        from second_brain.deps import get_default_config
        
        get_settings.cache_clear()
        
        with patch.dict(
            os.environ,
            {
                "MEM0_USE_REAL_PROVIDER": "true",
                "MEM0_USER_ID": "test-user",
                "SUPABASE_URL": "https://test.supabase.co",
                "VOYAGE_EMBED_MODEL": "voyage-3",
            },
        ):
            get_settings.cache_clear()
            
            config = get_default_config()
            
            assert config["mem0_use_real_provider"] is True
            assert config["mem0_user_id"] == "test-user"
            assert config["supabase_url"] == "https://test.supabase.co"
            assert config["voyage_embed_model"] == "voyage-3"

    def test_create_voyage_rerank_service_uses_settings(self):
        """create_voyage_rerank_service() uses settings defaults."""
        from second_brain.deps import create_voyage_rerank_service
        
        get_settings.cache_clear()
        
        for key in ["VOYAGE_EMBED_MODEL", "VOYAGE_EMBED_ENABLED", "VOYAGE_USE_REAL_RERANK"]:
            os.environ.pop(key, None)
        
        service = create_voyage_rerank_service()
        
        assert service.embed_model == "voyage-4-large"
        assert service.embed_enabled is False
        assert service.use_real_rerank is False

    def test_create_voyage_rerank_service_explicit_args_override_settings(self):
        """Explicit args to create_voyage_rerank_service() override settings."""
        from second_brain.deps import create_voyage_rerank_service
        
        get_settings.cache_clear()
        
        with patch.dict(
            os.environ,
            {
                "VOYAGE_EMBED_MODEL": "voyage-from-env",
                "VOYAGE_EMBED_ENABLED": "true",
                "VOYAGE_USE_REAL_RERANK": "true",
            },
        ):
            get_settings.cache_clear()
            
            service = create_voyage_rerank_service(
                embed_model="explicit-model",
                embed_enabled=False,
                use_real_rerank=False,
            )
            
            assert service.embed_model == "explicit-model"
            assert service.embed_enabled is False
            assert service.use_real_rerank is False


class TestSettingsEdgeCases:
    """Test Settings edge cases and error conditions."""

    def test_none_string_not_parsed_as_bool(self):
        """String 'none' or 'None' is not parsed as boolean True."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"MEM0_USE_REAL_PROVIDER": "none"}):
            settings = Settings()
            assert settings.mem0_use_real_provider is False

    def test_empty_string_for_optional_string_is_empty(self):
        """Empty string for optional string field is valid empty string."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"MEM0_USER_ID": ""}):
            settings = Settings()
            assert settings.mem0_user_id == ""

    def test_whitespace_in_string_values_preserved(self):
        """Whitespace in string values is preserved."""
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {"MEM0_USER_ID": "user with spaces"}):
            settings = Settings()
            assert settings.mem0_user_id == "user with spaces"
```

---

END OF PLAN
