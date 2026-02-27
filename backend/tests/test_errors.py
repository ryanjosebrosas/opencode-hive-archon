"""
Unit tests for the SecondBrainError hierarchy and related functionality.
"""
from second_brain.errors import (
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
        error = SecondBrainError("Test message")
        assert error.code == "UNKNOWN_ERROR"
        assert error.message == "Test message"
        assert error.context == {}
        assert not error.retry_hint
    
    def test_initialization_with_all_params(self):
        """Test initializing with all parameters."""
        context = {"key": "value"}
        error = SecondBrainError("Test message", code="CUSTOM_CODE", context=context, retry_hint=True)
        assert error.code == "CUSTOM_CODE"
        assert error.message == "Test message"
        assert error.context == context
        assert error.retry_hint is True
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary format."""
        context = {"param1": "val1", "param2": "val2"}
        error = SecondBrainError("Test message", code="SERIALIZE_TEST", context=context, retry_hint=False)
        
        result_dict = error.to_dict()
        
        expected = {
            "code": "SERIALIZE_TEST",
            "message": "Test message",
            "context": context,
            "retry_hint": False
        }
        assert result_dict == expected
    
    def test_inheritance(self):
        """Test that SecondBrainError inherits from Exception."""
        error = SecondBrainError("Test message")
        assert isinstance(error, Exception)
        
    def test_str_representation(self):
        """Test the exception's string representation."""
        error = SecondBrainError("Test message")
        assert str(error) == "Test message"


class TestProviderError:
    """Test ProviderError and its specific functionality."""
    
    def test_initialization_defaults(self):
        """Test ProviderError initialization with defaults."""
        error = ProviderError("API connection failed")
        assert error.code == "PROVIDER_ERROR"
        assert "API connection failed" in error.message
        assert error.context.get("provider") == "unknown"
        assert error.retry_hint is True
    
    def test_initialization_with_provider(self):
        """Test ProviderError initialization with provider."""
        error = ProviderError("Connection failed", provider="voyage", retry_hint=False)
        assert error.code == "PROVIDER_ERROR"
        assert error.message == "Connection failed"
        assert error.context.get("provider") == "voyage"
        assert error.retry_hint is False
    
    def test_provider_error_correct_default_code(self):
        """Test ProviderError has correct default code."""
        error = ProviderError("Some error")
        assert error.code == "PROVIDER_ERROR"
        
    def test_provider_error_correct_default_retry_hint(self):
        """Test ProviderError has correct default retry hint."""
        error = ProviderError("Some error")
        assert error.retry_hint is True
    
    def test_to_dict_includes_provider(self):
        """Test provider key is in context via to_dict()."""
        error = ProviderError("Error", provider="supabase")
        result = error.to_dict()
        assert result["context"]["provider"] == "supabase"
    
    def test_inheritance_from_second_brain_error(self):
        """Test that ProviderError inherits from SecondBrainError."""
        error = ProviderError("test")
        assert isinstance(error, SecondBrainError)


class TestConfigurationError:
    """Test ConfigurationError and its specific functionality."""
    
    def test_initialization_defaults(self):
        """Test ConfigurationError initialization with defaults."""
        error = ConfigurationError("API key missing")
        assert error.code == "CONFIGURATION_ERROR"
        assert error.message == "API key missing"
        assert not error.retry_hint
    
    def test_initialization_with_custom_code(self):
        """Test ConfigurationError initialization with custom code."""
        error = ConfigurationError("Config validation failed", code="CUSTOM_CONFIG_ERROR")
        assert error.code == "CUSTOM_CONFIG_ERROR"
        assert "Config validation failed" in error.message
    
    def test_configuration_error_correct_default_code(self):
        """Test ConfigurationError has correct default code."""
        error = ConfigurationError("test error")
        assert error.code == "CONFIGURATION_ERROR"
        
    def test_configuration_error_correct_default_retry_hint(self):
        """Test ConfigurationError has correct default retry hint."""
        error = ConfigurationError("test error")
        assert error.retry_hint is False


class TestIngestionError:
    """Test IngestionError and its specific functionality."""
    
    def test_initialization_defaults(self):
        """Test IngestionError initialization with defaults."""
        error = IngestionError("Markdown parsing failed")
        assert error.code == "INGESTION_ERROR"
        assert "Markdown parsing failed" in error.message
        assert not error.retry_hint
        
    def test_initialization_with_code(self):
        """Test IngestionError initialization with custom code."""
        error = IngestionError("Chunking error", code="CHUNKING_FAILED")
        assert error.code == "CHUNKING_FAILED"
    
    def test_ingestion_error_correct_default_code(self):
        """Test IngestionError has correct default code."""
        error = IngestionError("test error")
        assert error.code == "INGESTION_ERROR"
        
    def test_ingestion_error_correct_default_retry_hint(self):
        """Test IngestionError has correct default retry hint."""
        error = IngestionError("test error")
        assert error.retry_hint is False 


class TestRetrievalError:
    """Test RetrievalError and its specific functionality."""
    
    def test_initialization_defaults(self):
        """Test RetrievalError initialization with defaults."""
        error = RetrievalError("Search failed")
        assert error.code == "RETRIEVAL_ERROR"
        assert "Search failed" in error.message
        assert error.retry_hint is True
    
    def test_initialization_with_custom_params(self):
        """Test RetrievalError with custom parameters."""
        error = RetrievalError("Query timeout", code="QUERY_TIMEOUT", retry_hint=False)
        assert error.code == "QUERY_TIMEOUT"
        assert error.retry_hint is False
    
    def test_retrieval_error_correct_default_code(self):
        """Test RetrievalError has correct default code."""
        error = RetrievalError("test error")
        assert error.code == "RETRIEVAL_ERROR"
        
    def test_retrieval_error_correct_default_retry_hint(self):
        """Test RetrievalError has correct default retry hint."""
        error = RetrievalError("test error")
        assert error.retry_hint is True


class TestSchemaError:
    """Test SchemaError and its specific functionality."""
    
    def test_initialization_defaults(self):
        """Test SchemaError initialization with defaults."""
        error = SchemaError("Validation failed")
        assert error.code == "SCHEMA_ERROR"
        assert "Validation failed" in error.message
        assert not error.retry_hint
        
    def test_initialization_with_custom_params(self):
        """Test SchemaError with custom parameters."""
        error = SchemaError("Schema mismatch", code="SCHEMA_MISMATCH", retry_hint=False)
        assert error.code == "SCHEMA_MISMATCH"
        assert error.retry_hint is False
    
    def test_schema_error_correct_default_code(self):
        """Test SchemaError has correct default code."""
        error = SchemaError("test error")
        assert error.code == "SCHEMA_ERROR"
        
    def test_schema_error_correct_default_retry_hint(self):
        """Test SchemaError has correct default retry hint."""
        error = SchemaError("test error")
        assert error.retry_hint is False


class TestErrorInheritanceHierachy:
    """Test the complete inheritance hierarchy."""
    
    def test_all_subclasses_inherit_from_second_brain_error(self):
        """All custom errors should inherit from SecondBrainError."""
        errors = [
            ProviderError("test msg"),
            ConfigurationError("test msg"),
            IngestionError("test msg"),
            RetrievalError("test msg"),
            SchemaError("test msg")
        ]
        
        for error_obj in errors:
            assert isinstance(error_obj, SecondBrainError)
            assert isinstance(error_obj, Exception)
    
    def test_exceptions_are_catchable_via_second_brain_error(self):
        """Test that all error types are catchable via SecondBrainError."""
        errors = [
            ProviderError("test"),
            ConfigurationError("test"),
            IngestionError("test"),
            RetrievalError("test"),
            SchemaError("test")
        ]
        
        for error in errors:
            try:
                raise error
            except SecondBrainError:
                pass  # Success - error was caught as SecondBrainError
    

class TestErrorSerialization:
    """Test serialization and context preservation."""
    
    def test_to_dict_with_custom_context_preserved(self):
        """Test to_dict includes custom context."""
        custom_context = {"query": "test", "timestamp": "12345"}
        error = SecondBrainError(
            "Test message", 
            code="CONTEXT_TEST", 
            context=custom_context
        )
        result = error.to_dict()
        assert result["context"] == custom_context
    
    def test_error_message_accessible_via_str(self):
        """Test that error message is accessible via str()."""
        error = SecondBrainError("This is my test message")
        assert str(error) == "This is my test message"
    
    def test_provider_specific_context_field_exists(self):
        """Test ProviderError adds provider to context."""
        error = ProviderError("API error", provider="voyage")
        assert "provider" in error.context
        assert error.context["provider"] == "voyage"
        
    def test_provider_error_to_dict_includes_context(self):
        """Test ProviderError.to_dict() includes provider in context."""
        error = ProviderError("API error", provider="supabase")
        result = error.to_dict()
        assert result["context"]["provider"] == "supabase"
        assert result["code"] == "PROVIDER_ERROR"
        assert "API error" in result["message"]