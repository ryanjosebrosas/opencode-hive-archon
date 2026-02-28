"""Centralized configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables.
    
    All fields are optional with sensible defaults.
    Validation occurs on first get_settings() call.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    mem0_use_real_provider: bool = False
    mem0_user_id: str | None = None
    mem0_api_key: str | None = None
    
    supabase_use_real_provider: bool = False
    supabase_url: str | None = None
    supabase_key: str | None = None
    
    # Pool configuration
    supabase_max_retries: int = 3
    supabase_retry_delay: float = 1.0
    supabase_retry_backoff: float = 2.0
    supabase_circuit_failure_threshold: int = 5
    supabase_circuit_recovery_timeout: float = 30.0
    
    voyage_embed_model: str = "voyage-4-large"
    voyage_embed_enabled: bool = False
    voyage_use_real_rerank: bool = False
    
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3-coder-next"
    log_level: str = "INFO"
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log_level '{v}'. Must be one of: {', '.join(sorted(valid_levels))}")
        return upper
    
    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for backward compatibility."""
        return {
            "mem0_use_real_provider": self.mem0_use_real_provider,
            "mem0_user_id": self.mem0_user_id,
            "mem0_api_key": self.mem0_api_key,
            "supabase_use_real_provider": self.supabase_use_real_provider,
            "supabase_url": self.supabase_url,
            "supabase_key": self.supabase_key,
            "supabase_max_retries": self.supabase_max_retries,
            "supabase_retry_delay": self.supabase_retry_delay,
            "supabase_retry_backoff": self.supabase_retry_backoff,
            "supabase_circuit_failure_threshold": self.supabase_circuit_failure_threshold,
            "supabase_circuit_recovery_timeout": self.supabase_circuit_recovery_timeout,
            "voyage_embed_model": self.voyage_embed_model,
            "voyage_embed_enabled": self.voyage_embed_enabled,
            "voyage_use_real_rerank": self.voyage_use_real_rerank,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "log_level": self.log_level,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached Settings singleton.
    
    Use this function for dependency injection and testing overrides.
    The cache ensures only one Settings instance exists per process.
    
    For testing: override with get_settings.cache_clear() then set env vars.
    """
    return Settings()
