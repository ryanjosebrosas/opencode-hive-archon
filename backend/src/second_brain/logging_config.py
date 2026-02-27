"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging.config
from typing import Optional

import structlog

_CONFIGURED = False


def get_correlation_id() -> Optional[str]:
    """Get current correlation_id from contextvars."""
    try:
        ctx = structlog.contextvars.get_contextvars()
        return ctx.get("correlation_id")
    except (TypeError, AttributeError):
        return None


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set correlation_id for current context using structlog contextvars."""
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation_id from context."""
    structlog.contextvars.unbind_contextvars("correlation_id")


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog with JSON output. Idempotent - safe to call multiple times.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _CONFIGURED
    
    if _CONFIGURED:
        return
    
    level_num = getattr(logging, log_level.upper())
    
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
                    structlog.processors.dict_tracebacks,
                ],
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
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
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    _CONFIGURED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
