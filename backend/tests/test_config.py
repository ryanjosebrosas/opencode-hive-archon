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
        
        false_values = ["false", "False", "FALSE", "0", "no", "No", "off"]
        
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

    def test_invalid_bool_raises_validation_error(self):
        """Invalid boolean strings raise ValidationError."""
        get_settings.cache_clear()
        
        invalid_values = ["none", "None", "invalid", "2"]
        
        for invalid_val in invalid_values:
            with patch.dict(os.environ, {"MEM0_USE_REAL_PROVIDER": invalid_val}):
                with pytest.raises(ValidationError):
                    Settings()
            os.environ.pop("MEM0_USE_REAL_PROVIDER", None)

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
        
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_log_level_to_dict(self):
        """log_level is included in to_dict() output."""
        get_settings.cache_clear()
        
        settings = Settings()
        config_dict = settings.to_dict()
        
        assert "log_level" in config_dict
        assert config_dict["log_level"] == "INFO"
