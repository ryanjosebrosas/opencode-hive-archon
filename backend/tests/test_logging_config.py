"""Tests for structured logging configuration."""

import json
from unittest.mock import patch

import pytest

from second_brain.config import Settings, get_settings
from second_brain.logging_config import (
    configure_logging,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    get_logger,
)


class TestLoggingConfiguration:
    """Test configure_logging function."""

    def test_configure_logging_is_idempotent(self) -> None:
        """configure_logging can be called multiple times without side effects."""
        configure_logging(log_level="DEBUG")
        configure_logging(log_level="DEBUG")
        configure_logging(log_level="INFO")

    def test_configure_logging_default_level(self) -> None:
        """configure_logging uses INFO as default level."""
        configure_logging()

    def test_configure_logging_accepts_valid_levels(self) -> None:
        """configure_logging accepts valid log level strings."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            configure_logging(log_level=level)


class TestCorrelationId:
    """Test correlation_id context management."""

    def setup_method(self) -> None:
        """Clear correlation_id before each test."""
        clear_correlation_id()

    def test_get_correlation_id_default(self) -> None:
        """get_correlation_id returns None by default."""
        assert get_correlation_id() is None

    def test_set_and_get_correlation_id(self) -> None:
        """set_correlation_id stores value, get_correlation_id retrieves it."""
        test_id = "test-correlation-123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id

    def test_correlation_id_is_context_var(self) -> None:
        """correlation_id uses contextvars for isolation."""
        set_correlation_id("id-1")
        assert get_correlation_id() == "id-1"

        set_correlation_id("id-2")
        assert get_correlation_id() == "id-2"

    def test_clear_correlation_id(self) -> None:
        """clear_correlation_id removes correlation_id from context."""
        set_correlation_id("test-id")
        clear_correlation_id()
        assert get_correlation_id() is None


class TestLogger:
    """Test structlog logger."""

    def test_get_logger_returns_logger(self) -> None:
        """get_logger returns a logger instance."""
        logger = get_logger("test")
        assert logger is not None

    def test_logger_logs_with_correlation_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Logger includes correlation_id when set."""
        configure_logging(log_level="DEBUG")
        set_correlation_id("test-corr-id")
        
        logger = get_logger("test_module")
        logger.info("test message", extra_field="extra_value")
        
        output = capsys.readouterr().out
        if output.strip():
            for line in output.strip().split("\n"):
                if line.strip():
                    data = json.loads(line)
                    assert data.get("correlation_id") == "test-corr-id"
                    assert data.get("extra_field") == "extra_value"

    def test_logger_without_correlation_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Logger works without correlation_id set."""
        configure_logging(log_level="DEBUG")
        clear_correlation_id()
        
        logger = get_logger("test_module")
        logger.info("test message")
        
        output = capsys.readouterr().out
        if output.strip():
            for line in output.strip().split("\n"):
                if line.strip():
                    data = json.loads(line)
                    assert "correlation_id" not in data or data.get("correlation_id") is None


class TestSettingsIntegration:
    """Test Settings integration with logging."""

    def test_settings_has_log_level_field(self) -> None:
        """Settings class has log_level field."""
        get_settings.cache_clear()
        settings = Settings()
        assert hasattr(settings, "log_level")
        assert settings.log_level == "INFO"

    def test_settings_log_level_from_env(self) -> None:
        """log_level can be set via environment variable."""
        get_settings.cache_clear()
        
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_settings_to_dict_includes_log_level(self) -> None:
        """Settings.to_dict() includes log_level field."""
        get_settings.cache_clear()
        settings = Settings()
        config_dict = settings.to_dict()
        assert "log_level" in config_dict
        assert config_dict["log_level"] == "INFO"

    def test_settings_rejects_invalid_log_level(self) -> None:
        """Settings rejects invalid log_level values."""
        from pydantic import ValidationError
        get_settings.cache_clear()
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")
    
    def test_settings_log_level_case_insensitive(self) -> None:
        """Settings normalizes log_level to uppercase."""
        get_settings.cache_clear()
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"


class TestStructuredLoggingOutput:
    """Test structured logging output format."""

    def test_log_output_is_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Log output is valid JSON."""
        configure_logging(log_level="DEBUG")
        
        logger = get_logger("second_brain")
        logger.info("test json output")
        
        output = capsys.readouterr().out
        if output.strip():
            for line in output.strip().split("\n"):
                if line.strip():
                    json.loads(line)

    def test_log_includes_timestamp(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Log entries include timestamp."""
        configure_logging(log_level="DEBUG")
        
        logger = get_logger("second_brain")
        logger.info("test timestamp")
        
        output = capsys.readouterr().out
        if output.strip():
            for line in output.strip().split("\n"):
                if line.strip():
                    data = json.loads(line)
                    assert "timestamp" in data

    def test_log_includes_logger_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Log entries include logger name."""
        configure_logging(log_level="DEBUG")
        
        logger = get_logger("second_brain.test_module")
        logger.info("test logger name")
        
        output = capsys.readouterr().out
        if output.strip():
            for line in output.strip().split("\n"):
                if line.strip():
                    data = json.loads(line)
                    assert "logger" in data
                    assert data["logger"] == "second_brain.test_module"

    def test_log_includes_level(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Log entries include log level."""
        configure_logging(log_level="DEBUG")
        
        logger = get_logger("second_brain")
        logger.warning("test warning level")
        
        output = capsys.readouterr().out
        if output.strip():
            for line in output.strip().split("\n"):
                if line.strip():
                    data = json.loads(line)
                    assert data["level"] == "warning"
