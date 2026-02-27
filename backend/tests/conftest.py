"""Pytest configuration and fixtures."""

import pytest
import second_brain.logging_config as logging_config_module
from second_brain.logging_config import configure_logging


@pytest.fixture(scope="session", autouse=True)
def setup_logging() -> None:
    """Configure logging for tests.
    
    This fixture runs once per session and configures structlog for testing.
    cache_logger_on_first_use=False ensures test isolation.
    """
    configure_logging(log_level="DEBUG")


@pytest.fixture(autouse=True)
def reset_logging_config() -> None:
    """Reset logging config state before each test for isolation."""
    logging_config_module._CONFIGURED = False
