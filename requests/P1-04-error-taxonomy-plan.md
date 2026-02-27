# Feature: P1-04 Error Taxonomy

## Feature Description

Implement a comprehensive error hierarchy for the Second Brain system that replaces generic exceptions with typed errors that convey meaningful information. This includes creating a base SecondBrainError class with specific subclasses (ProviderError, ConfigurationError, IngestionError, RetrievalError, SchemaError). Each error class contains standardized properties like code, context dictionary, and retry hint, enabling more reliable error handling throughout the application without disrupting existing graceful degradation patterns.

## User Story

As a system developer, I want to identify different types of errors through a typed hierarchy so that I can handle specific error categories appropriately, improve debugging and monitoring, and create more resilient recovery mechanisms when different failure modes occur.

## Problem Statement

Currently, the Second Brain system relies on built-in Python exceptions (ValueError, KeyError, etc.) with no custom error types. This creates several problems: lack of error categorization that makes debugging difficult, inconsistent error handling patterns across services (some return error dictionaries while others raise exceptions), services swallowing exceptions without proper logging or classification, and no standardized way to indicate retry hints for transient failures.

## Solution Statement

Create a proper error taxonomy with inheritance hierarchy and standardized interface:

- Decision 1: Establish SecondBrainError as a base class with standard attributes (code, message, context, retry_hint) — to provide consistent error interface for all custom errors
- Decision 2: Create specific subclasses for different error domains (ProviderError, ConfigurationError, etc.) — to enable precise error categorization and handling
- Decision 3: Maintain service-level graceful degradation patterns while adding typed error propagation when appropriate — to preserve system resilience while adding proper error classification
- Decision 4: Implement to_dict() serialization method on all errors — to ensure consistent error reporting and logging

## Feature Metadata

- **Feature Type**: Refactor
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: errors.py(new file), memory.py, voyage.py, supabase.py, llm.py, recall.py, planner.py, markdown.py, conversation.py
- **Dependencies**: Pydantic (for ValidationError), typing

### Slice Guardrails (Required)

- **Single Outcome**: Standardized error hierarchy implemented with proper class relationships
- **Expected Files Touched**: errors.py, services/memory.py, services/voyage.py, services/supabase.py, services/llm.py, agents/recall.py, orchestration/planner.py, ingestion/markdown.py, services/conversation.py
- **Scope Boundary**: Changes are limited to error taxonomy and integration with existing exception handling patterns
- **Split Trigger**: Implementation of error taxonomy without modifying service degradation patterns beyond adding appropriate error types

---
## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `services/memory.py` — Why: Contains the main pattern where services catch broadly and return error dictionaries instead of raising
- `services/voyage.py` — Why: Shows return tuple pattern (result, error_dict) that should remain intact
- `agents/recall.py:208` — Why: Only place that re-raises exceptions, which we'll convert to RetrievalError wrapper
- `orchestration/planner.py:89` — Why: Shows current manually maintained exception catch list that should migrate to SecondBrainError
- `ingestion/markdown.py` — Why: Contains error dictionary returns that should sometimes migrate to IngestionError for unrecoverable cases

### New Files to Create

- `backend/src/second_brain/errors.py` — Defines the entire error taxonomy including base class and all subclasses
- `backend/tests/test_errors.py` — Contains unit tests for error class functionality

### Related Memories (from memory.md)

> Past experiences and lessons relevant to this feature. Populated by `/planning` from memory.md.

- No relevant memories found in memory.md

### Relevant Documentation

> The execution agent SHOULD read these before implementing.

- [Python Exception Handling Best Practices](https://docs.python.org/3/library/exceptions.html)
  - Specific section: Base classes for exception hierarchies
  - Why: required for implementing X
- [Pydantic Error Handling Patterns](https://docs.pydantic.dev/latest/concepts/errors/)
  - Specific section: Custom errors and inheritance
  - Why: shows recommended approach for Y

### Patterns to Follow

> Specific patterns extracted from the codebase — include actual code examples from the project.

**Logger pattern** (from `services/memory.py:lines 1-20`):
```
import structlog
logger = structlog.get_logger(__name__)
```
- Why this pattern: Consistent logging approach across the codebase
- Common gotchas: Need to maintain logger name based on location

**Type annotation pattern** (from `services/voyage.py:lines 30-60`):
```
from typing import Tuple, Optional, Dict, Any
EmbeddingResult = Tuple[Optional[list], Optional[Dict[str, Any]]]
```
- Why this pattern: Maintains typing consistency across files
- Common gotchas: Use Optional consistently for return types

**Sanitize error message pattern** (from `services/memory.py:lines 400-410`):
```
def _sanitize_error_message(error_str: str) -> str:
    """Redact sensitive information from error messages."""
    # Remove potential API keys
    sanitized = re.sub(r'["\']*sk-[a-zA-Z0-9_-]+["\']*', '[REDACTED]', error_str)
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + "..."
    return sanitized
```
- Why this pattern: Ensures API keys and sensitive info are never leaked in errors
- Common gotchas: Applied consistently to prevent security breaches

---
## IMPLEMENTATION PLAN

### Phase 1: Foundation

Create the base error hierarchy in a new file that establishes the foundation for the entire error taxonomy. This phase includes implementation of the base SecondBrainError class and all its subclasses with the required attributes and serialization methods.

**Tasks:**
- Create base error class with all required standard attributes
- Define inheritance hierarchy with five specialized subclasses
- Implement serialization method for JSON output
- Create initialization and string representation methods

### Phase 2: Core Implementation

Integrate the new error classes into services that should throw specialized errors when their functions encounter unrecoverable conditions. This phase focuses on converting some places where generic exceptions would bubble up into properly typed ones.

**Tasks:**
- Update recall.py to catch generic exceptions and re-raise as RetrievalError
- Modify planner.py to catch SecondBrainError instead of individual built-in exceptions  
- Enhance markdown.py ingestion to use IngestionError for specific failure conditions
- Update conversation.py KeyError handling to use appropriate error type

### Phase 3: Integration

Update other services to optionally use new error types when they encounter unrecoverable conditions that they want to allow to propagate to higher-level handlers. Keep service-level graceful degradation patterns intact but allow for typed error propagation when appropriate.

**Tasks:**
- Update imports across services to include new error classes
- Adjust service exception catching where it makes sense to propagate certain errors
- Update error handling in key areas to use new typed errors
- Verify consistency in error attribute usage

### Phase 4: Testing & Validation

Create comprehensive unit tests for the error hierarchy functionality including class instantiation, inheritance, serialization, and attribute access. Test that error objects behave correctly when used with their expected use cases.

**Tasks:**
- Implement unit tests for each error type with different initialization scenarios
- Create fixture and test serialization methods
- Test inheritance and polymorphism properties
- Test retry hint logic and default values
- Validate all error attributes are set correctly

---
## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.

> **Action keywords**: CREATE (new files), UPDATE (modify existing), ADD (insert new functionality),
> REMOVE (delete deprecated code), REFACTOR (restructure without changing behavior), MIRROR (copy pattern from elsewhere)

### CREATE backend/src/second_brain/errors.py

- **IMPLEMENT**: Create the complete error hierarchy with SecondBrainError base class and all subclasses with standard attributes
- **PATTERN**: Mirror structlog import structure as seen in other files
- **IMPORTS**: import structlog, typing
- **GOTCHA**: Be consistent with docstrings and attribute initialization
- **VALIDATE**: `python -c "from backend.src.second_brain.errors import SecondBrainError, ProviderError; e = SecondBrainError('test', 'Test'); assert hasattr(e, 'code')"`

```
"""
Error taxonomy for Second Brain system.

Defines hierarchical exceptions with standardized attributes for consistent
error handling, logging, and client communication throughout the application.

Each error class implements:
- code: String identifier for the error type 
- message: Human-readable description
- context: Dict containing additional contextual information
- retry_hint: Boolean indicating if retry might succeed
"""

import structlog
from typing import Dict, Any, Optional


logger = structlog.get_logger(__name__)


class SecondBrainError(Exception):
    """
    Base error class for the Second Brain system.
    
    All specific errors inherit from this class to maintain consistency
    in error attributes and behavior across the application.
    """
    
    def __init__(self, code: str, message: str, context: Optional[Dict[str, Any]] = None, retry_hint: bool = False):
        """
        Initialize a SecondBrainError.
        
        Args:
            code: String identifier for the error (e.g., 'PROVIDER_CONNECTION_ERROR')
            message: Human-readable error description
            context: Optional dictionary with additional contextual details
            retry_hint: Whether retrying the operation is recommended
        """
        self.code = code
        self.message = message
        self.context = context or {}
        self.retry_hint = retry_hint
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the error to a dictionary for response bodies or logging.
        
        Returns:
            Dict with error information structured as: {code, message, context, retry_hint}
        """
        return {
            "code": self.code,
            "message": self.message,
            "context": self.context,
            "retry_hint": self.retry_hint
        }
    
    def __str__(self):
        """Represent the error as a string for logging/debugging."""
        return f"[{self.code}] {self.message}"


class ProviderError(SecondBrainError):
    """Error encountered when operating with external providers (Mem0, Voyage, Supabase, Ollama)."""
    
    def __init__(self, provider_name: str, message: str, context: Optional[Dict[str, Any]] = None, 
                 retry_hint: bool = False, http_status: Optional[int] = None):
        """
        Initialize a ProviderError.
        
        Args:
            provider_name: Name of the provider (e.g., 'mem0', 'voyage', 'supabase')
            message: Human-readable error description
            context: Optional context dictionary
            retry_hint: Whether retrying is recommended
            http_status: HTTP status code if this was an HTTP error
        """
        error_context = context or {}
        error_context.update({'provider': provider_name})
        if http_status is not None:
            error_context['http_status'] = http_status
            
        code = f"{provider_name.upper()}_ERROR".replace(" ", "_")
        super().__init__(
            code,
            f"{provider_name.title()} provider error: {message}",
            error_context,
            retry_hint
        )


class ConfigurationError(SecondBrainError):
    """Error encountered when configuration is invalid or missing."""
    
    def __init__(self, config_item: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize a ConfigurationError.
        
        Args:
            config_item: Name of the configuration item that failed validation
            message: Human-readable error description
            context: Optional context dictionary
        """
        error_context = context or {}
        error_context.update({'config_item': config_item})
        
        super().__init__(
            f"CONFIG_{config_item.upper()}_ERROR",
            f"Configuration error ({config_item}): {message}",
            error_context
        )


class IngestionError(SecondBrainError):
    """Error encountered during the content ingestion pipeline."""
    
    def __init__(self, stage: str, message: str, context: Optional[Dict[str, Any]] = None, 
                 retry_hint: bool = False, file_path: Optional[str] = None):
        """
        Initialize an IngestionError.
        
        Args:
            stage: Name of the ingestion stage where error occurred ('parsing', 'chunking', etc.)
            message: Human-readable error description  
            context: Optional context dictionary
            retry_hint: Whether retrying is recommended
            file_path: Path to the file causing the error if applicable
        """
        error_context = context or {}
        error_context.update({'stage': stage})
        if file_path is not None:
            error_context['file_path'] = file_path
            
        super().__init__(
            f"INGESTION_{stage.upper()}_ERROR", 
            f"Ingestion error at {stage} stage: {message}",
            error_context,
            retry_hint
        )


class RetrievalError(SecondBrainError):
    """Error encountered during content search or retrieval operations."""
    
    def __init__(self, operation: str, message: str, context: Optional[Dict[str, Any]] = None, 
                 retry_hint: bool = False, query: Optional[str] = None):
        """
        Initialize a RetrievalError.
        
        Args:
            operation: Name of the retrieval operation that failed
            message: Human-readable error description
            context: Optional context dictionary
            retry_hint: Whether retrying is recommended
            query: The search/query string if applicable
        """
        error_context = context or {}
        error_context.update({'operation': operation})
        if query is not None:
            error_context['query'] = query
            
        super().__init__(
            f"RETRIEVAL_{operation.upper()}_ERROR",
            f"Retrieval error during {operation} operation: {message}",
            error_context,
            retry_hint
        )


class SchemaError(SecondBrainError):
    """Error encountered when data fails to conform to expected schema/format."""
    
    def __init__(self, schema_name: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize a SchemaError.
        
        Args:
            schema_name: Name of the schema that validation failed against
            message: Human-readable error description
            context: Optional context dictionary
        """
        error_context = context or {}
        error_context.update({'schema': schema_name})
        
        super().__init__(
            f"SCHEMA_{schema_name.upper()}_ERROR",
            f"Schema validation error for {schema_name}: {message}",
            error_context
        )
```


### UPDATE agents/recall.py

- **IMPLEMENT**: Wrap the existing Exception catch to re-raise as RetrievalError
- **PATTERN**: Mirror current error handling pattern while adding typed exception wrapper 
- **IMPORTS**: from backend.src.second_brain.errors import RetrievalError
- **GOTCHA**: Preserve the original error in the context
- **VALIDATE**: `python -c "exec(open('agents/recall.py').read())"`


```
# At the top with imports
from backend.src.second_brain.errors import RetrievalError

# Update the exception handling in line 208 (or similar location where exceptions are currently re-raised)
```

### UPDATE orchestration/planner.py

- **IMPLEMENT**: Replace manual caught exception list with custom SecondBrainError catch
- **PATTERN**: Mirror current catch and error response pattern 
- **IMPORTS**: from backend.src.second_brain.errors import SecondBrainError, ProviderError, IngestionError, RetrievalError, SchemaError
- **GOTCHA**: Maintain backward compatibility for now, just enhance with new error types
- **VALIDATE**: `python -c "exec(open('orchestration/planner.py').read())"`

```
# At the top with imports
from backend.src.second_brain.errors import (
    SecondBrainError, 
    ProviderError, 
    IngestionError, 
    RetrievalError, 
    SchemaError
)

# Update the exception handling around line 89 (or similar location of exception handling)
```

### UPDATE ingestion/markdown.py

- **IMPLEMENT**: Add import for IngestionError for future use
- **PATTERN**: Keep existing error dictionary patterns but allow for typed errors in critical failures
- **IMPORTS**: from backend.src.second_brain.errors import IngestionError
- **GOTCHA**: Don't break existing graceful degradation pattern
- **VALIDATE**: `python -c "python -c \"exec(open('\\ingestion\\markdown.py\').read())\"`

```
# At the top with imports
from backend.src.second_brain.errors import IngestionError
```

### UPDATE services/conversation.py

- **IMPLEMENT**: Handle KeyError that originates from get_session and could propagate
- **PATTERN**: Follow the graceful degradation pattern used throughout the service files
- **IMPORTS**: from ..errors import SchemaError
- **GOTCHA**: Don't break the existing constructor validation pattern
- **VALIDATE**: `python -c "exec(open('services/conversation.py').read())"`

```
# At the top with imports near other imports
from ..errors import SchemaError

# For ValueError lines in constructor, consider converting to SchemaError where appropriate:
# FROM:
# raise ValueError(f"max_turns must be positive, got {max_turns}")

# TO:
# raise SchemaError("configuration", f"max_turns must be positive, got {max_turns}", context={"max_turns": max_turns, "expected": "positive integer"})
```

### UPDATE services/memory.py

- **IMPLEMENT**: Add optional typed error propagation while maintaining graceful degradation
- **PATTERN**: Mirror existing graceful degradation pattern but allow ProviderError to surface when appropriate
- **IMPORTS**: from ..errors import ProviderError, RetrievalError
- **GOTCHA**: Don't break the established service-level error handling
- **VALIDATE**: `python -c "exec(open('services/memory.py').read())"`

```
# At the top with imports  
from ..errors import ProviderError, RetrievalError
```

### UPDATE services/voyage.py

- **IMPLEMENT**: Integrate error types where appropriate while keeping service-level patterns
- **PATTERN**: Mirror existing tuple return error pattern (None, error_dict) 
- **IMPORTS**: from ..errors import ProviderError
- **GOTCHA**: Maintain the established error return tuple pattern
- **VALIDATE**: `python -c "exec(open('services/voyage.py').read())"`

```
# At the top with imports
from ..errors import ProviderError
```

### UPDATE services/supabase.py

- **IMPLEMENT**: Integrate error types for supabase operations when appropriate
- **PATTERN**: Mirror existing fallback result + error metadata pattern
- **IMPORTS**: from ..errors import ProviderError
- **GOTCHA**: Maintain graceful degradation with fallback results for search failures
- **VALIDATE**: `python -c "exec(open('services/supabase.py').read())"`

```
# At the top with imports
from ..errors import ProviderError
```

### UPDATE services/llm.py

- **IMPLEMENT**: Integrate error types for LLM service operations
- **PATTERN**: Mirror existing graceful degradation pattern
- **IMPORTS**: from ..errors import ProviderError
- **GOTCHA**: Maintain fallback text return pattern for synthesis operations
- **VALIDATE**: `python -c "exec(open('services/llm.py').read())"`

```
# At the top with imports
from ..errors import ProviderError
```

### CREATE backend/tests/test_errors.py

- **IMPLEMENT**: Create comprehensive test suite for error hierarchy, classes, and functionality
- **PATTERN**: Mirror existing testing patterns in the codebase
- **IMPORTS**: from backend.src.second_brain.errors import *
- **GOTCHA**: Test inheritance and all subclass-specific functionality thoroughly
- **VALIDATE**: `pytest backend/tests/test_errors.py`

```
"""
Unit tests for the SecondBrainError hierarchy and related functionality.
"""
import pytest
import json
from backend.src.second_brain.errors import (
    SecondBrainError,
    ProviderError, 
    ConfigurationError,
    IngestionError,
    RetrievalError,
    SchemaError
)


class TestSecondBrainErrorBase:
    """Test the base SecondBrainError class functionality."""
    
    def test_initialization_minimal(self):
        """Test initializing with minimal parameters."""
        error = SecondBrainError("TEST_CODE", "Test message")
        assert error.code == "TEST_CODE"
        assert error.message == "Test message"
        assert error.context == {}
        assert not error.retry_hint
    
    def test_initialization_with_all_params(self):
        """Test initializing with all parameters."""
        context = {"key": "value"}
        error = SecondBrainError("TEST_CODE", "Test message", context, True)
        assert error.code == "TEST_CODE"
        assert error.message == "Test message"
        assert error.context == context
        assert error.retry_hint is True
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary format."""
        context = {"param1": "val1", "param2": "val2"}
        error = SecondBrainError("TEST_CODE", "Test message", context, False)
        
        result_dict = error.to_dict()
        
        expected = {
            "code": "TEST_CODE",
            "message": "Test message",
            "context": context,
            "retry_hint": False
        }
        assert result_dict == expected
    
    def test_string_representation(self):
        """Test string representation format."""
        error = SecondBrainError("TEST_CODE", "Test message")
        assert str(error) == "[TEST_CODE] Test message"
    
    def test_inheritance(self):
        """Test that SecondBrainError inherits from Exception."""
        error = SecondBrainError("TEST_CODE", "Test message")
        assert isinstance(error, Exception)


class TestProviderError:
    """Test ProviderError and its specific functionality."""
    
    def test_initialization(self):
        """Test ProviderError initialization."""
        error = ProviderError("voyage", "API Key rejected", None, True)
        assert error.code == "VOYAGE_ERROR"
        assert "voyage" in error.message.lower()
        assert error.context.get("provider") == "voyage"
        assert error.retry_hint is True
    
    def test_provider_error_with_http_status(self):
        """Test ProviderError with HTTP status code."""
        error = ProviderError("supabase", "Database unavailable", None, True, 503)
        assert error.context.get("http_status") == 503  
    
    def test_provider_error_with_context(self):
        """Test ProviderError preserves additional context."""
        initial_context = {"request_id": "abc-123"}
        error = ProviderError("mem0", "Connection failed", initial_context, False)
        assert error.context.get("provider") == "mem0"
        assert error.context.get("request_id") == "abc-123"


class TestConfigurationError:
    """Test ConfigurationError and its specific functionality."""
    
    def test_initialization(self):
        """Test ConfigurationError initialization."""
        error = ConfigurationError("api_key", "Missing required field")
        assert error.code == "CONFIG_API_KEY_ERROR"
        assert "api_key" in error.message.lower()
        assert error.context.get("config_item") == "api_key"
    
    def test_configuration_error_with_context(self):
        """Test ConfigurationError with additional context."""
        initial_context = {"expected_type": "string", "received_value": 123}
        error = ConfigurationError("max_tokens", "Invalid type", initial_context)
        assert error.context.get("config_item") == "max_tokens"
        assert error.context.get("expected_type") == "string"


class TestIngestionError:
    """Test IngestionError and its specific functionality."""
    
    def test_initialization(self):
        """Test IngestionError initialization."""
        error = IngestionError("parsing", "Invalid markdown syntax")
        assert error.code == "INGESTION_PARSING_ERROR"
        assert "parsing" in error.message.lower()
        assert error.context.get("stage") == "parsing"
    
    def test_ingestion_error_with_file_path(self):
        """Test IngestionError with file path."""
        error = IngestionError("chunking", "File too large", None, False, "/path/to/file.md")
        assert error.context.get("file_path") == "/path/to/file.md"

    def test_ingestion_error_retry_hint(self):
        """Test IngestionError with retry hint."""
        error = IngestionError("upload", "Network issue", None, True)
        assert error.retry_hint is True


class TestRetrievalError:
    """Test RetrievalError and its specific functionality."""
    
    def test_initialization(self):
        """Test RetrievalError initialization."""
        error = RetrievalError("semantic", "Index not ready")
        assert error.code == "RETRIEVAL_SEMANTIC_ERROR"
        assert "semantic" in error.message.lower()
        assert error.context.get("operation") == "semantic"
    
    def test_retrieval_error_with_query(self):
        """Test RetrievalError with query in context."""
        error = RetrievalError("search", "No results found", None, True, "sample query")
        assert error.context.get("query") == "sample query"
    
    def test_retrieval_error_retry_hint(self):
        """Test RetrievalError with retry hint.""" 
        error = RetrievalError("db_lookup", "Temporary outage", None, True)
        assert error.retry_hint is True


class TestSchemaError:
    """Test SchemaError and its specific functionality."""
    
    def test_initialization(self):
        """Test SchemaError initialization."""
        error = SchemaError("conversation", "Malformed session object")
        assert error.code == "SCHEMA_CONVERSATION_ERROR"
        assert "conversation" in error.message.lower()
        assert error.context.get("schema") == "conversation"


class TestErrorInheritanceHierarchy:
    """Test the complete inheritance hierarchy."""
    
    def test_all_subclasses_inherit_from_second_brain_error(self):
        """All custom errors should inherit from SecondBrainError."""
        errors = [
            ProviderError("test_provider", "test msg"),
            ConfigurationError("config", "test msg"),
            IngestionError("stage", "test msg"),
            RetrievalError("op", "test msg"),
            SchemaError("schema_name", "test msg")
        ]
        
        for error_obj in errors:
            assert isinstance(error_obj, SecondBrainError)
            assert isinstance(error_obj, Exception)


class TestErrorMessageStructure:
    """Test that error messages follow proper structure."""
    
    def test_error_message_contains_identifying_info(self):
        """Error messages should clearly identify the type/source."""
        # Test provider errors mention provider type
        provider_error = ProviderError("voyage", "connection failed")
        assert "voyage" in provider_error.message.lower()
        
        # Test config errors mention config property
        config_error = ConfigurationError("api_key", "invalid format")
        assert "api_key" in config_error.message.lower()
        
        # Similar for other error types
        ingestion_error = IngestionError("parse", "syntax error") 
        assert "parse" in ingestion_error.message.lower()


def test_error_json_serializable():
    """Test that errors can be serialized to JSON properly."""
    error = SecondBrainError("UNICODE_TEST", "Test with unicode émojis! 🚀", {"key": "val"})
    error_dict = error.to_dict()
    
    # Should be JSON serializable
    json_str = json.dumps(error_dict)
    result_dict = json.loads(json_str)
    
    assert result_dict == error_dict
    assert result_dict["code"] == "UNICODE_TEST"
    assert "🚀" in result_dict["message"]
```

---
## TESTING STRATEGY

### Unit Tests

Create comprehensive test coverage for each error class with parameter combinations, edge cases, inheritance, serialization, and attribute access. Test all constructors and methods for correct behavior.

### Integration Tests

Verify error classes work correctly when integrated into services. Test that the error propagation happens as expected while preserving graceful degradation patterns where required.

### Edge Cases

- Test initialization with None values
- Test invalid input types for parameters
- Test deep nesting of error contexts
- Test exception chaining with 'from' keyword
- Test behavior of error methods after initialization

---
## VALIDATION COMMANDS

### Level 1: Syntax & Style
```
ruff check backend/src/second_brain/errors.py
```

### Level 2: Type Safety
```
mypy backend/src/second_brain/errors.py
```

### Level 3: Unit Tests
```
pytest backend/tests/test_errors.py
```

### Level 4: Integration Tests
```
pytest tests/
```

### Level 5: Manual Validation

- Test error creation and serialization manually
- Verify imports work from various modules
- Check that exception handling works in integration contexts

---
## ACCEPTANCE CRITERIA

### Implementation (verify during execution)

- [ ] Error hierarchy created with all specified classes
- [ ] All classes have required attributes (code, message, context, retry_hint)
- [ ] to_dict method returns proper format on all classes
- [ ] Inheritance chain works properly
- [ ] Error handling is integrated into services without breaking existing patterns
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage meets project requirements

### Runtime (verify after testing/deployment)

- [ ] Error objects serialize correctly to JSON
- [ ] Service graceful degradation patterns remain intact
- [ ] Typed errors properly integrate where appropriate
- [ ] No regressions in existing functionality

---
## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met

---
## NOTES

### Key Design Decisions
- Preserve existing service degradation patterns while adding error taxonomy where beneficial
- Implement consistent interface across all error types
- Use structured error information for better debugging

### Risks
- Risk 1: Breaking existing error handling patterns - Mitigation: Thorough testing with existing flows
- Risk 2: Service degradation behavior changes unexpectedly - Mitigation: Careful implementation following current patterns

### Confidence Score: 8/10
- **Strengths**: Clear requirements, well-defined error hierarchy structure
- **Uncertainties**: Exact integration points may need minor adjustments during implementation
- **Mitigations**: Comprehensive testing to catch any integration issues

(End of plan - total approximately 780 lines)