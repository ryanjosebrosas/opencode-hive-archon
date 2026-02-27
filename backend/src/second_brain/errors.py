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
from __future__ import annotations
from typing import Any


class SecondBrainError(Exception):
    """Base exception for all Second Brain errors."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "UNKNOWN_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = dict(context) if context else {}
        self.retry_hint = retry_hint
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to structured dict."""
        return {
            "code": self.code,
            "message": self.message,
            "context": dict(self.context),
            "retry_hint": self.retry_hint,
        }


class ProviderError(SecondBrainError):
    """External API/provider failure (mem0, voyage, supabase, ollama)."""
    
    def __init__(
        self,
        message: str,
        *,
        provider: str = "unknown",
        code: str = "PROVIDER_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = True,
    ) -> None:
        ctx = dict(context) if context else {}
        ctx["provider"] = provider
        super().__init__(message, code=code, context=ctx, retry_hint=retry_hint)


class ConfigurationError(SecondBrainError):
    """Missing or invalid configuration."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "CONFIGURATION_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = False,
    ) -> None:
        super().__init__(message, code=code, context=context, retry_hint=retry_hint)


class IngestionError(SecondBrainError):
    """Ingestion pipeline failure."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "INGESTION_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = False,
    ) -> None:
        super().__init__(message, code=code, context=context, retry_hint=retry_hint)


class RetrievalError(SecondBrainError):
    """Retrieval/search failure."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "RETRIEVAL_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = True,
    ) -> None:
        super().__init__(message, code=code, context=context, retry_hint=retry_hint)


class SchemaError(SecondBrainError):
    """Data validation/schema failure."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "SCHEMA_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = False,
    ) -> None:
        super().__init__(message, code=code, context=context, retry_hint=retry_hint)