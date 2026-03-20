"""Structured JSON logging with Azure Application Insights integration."""
import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any
from app.config import get_settings

settings = get_settings()

# Context variables for request tracing
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_session_id: ContextVar[str] = ContextVar("session_id", default="")
_user_id: ContextVar[str] = ContextVar("user_id", default="")


def set_request_context(request_id: str, session_id: str = "", user_id: str = ""):
    _request_id.set(request_id)
    _session_id.set(session_id)
    _user_id.set(user_id)


class JSONFormatter(logging.Formatter):
    """Emit logs as structured JSON for ingestion into Log Analytics / App Insights."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.environment,
            "app_version": settings.app_version,
            "request_id": _request_id.get(""),
            "session_id": _session_id.get(""),
            "user_id": _user_id.get(""),
        }

        # Merge extra fields from the log call
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "msg", "args", "levelname", "levelno", "pathname", "filename",
                    "module", "exc_info", "exc_text", "stack_info", "lineno",
                    "funcName", "created", "msecs", "relativeCreated", "thread",
                    "threadName", "processName", "process", "name", "message",
                ):
                    log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging():
    """Configure root logger with JSON output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Azure Application Insights (OpenCensus)
    if settings.applicationinsights_connection_string:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            configure_azure_monitor(
                connection_string=settings.applicationinsights_connection_string,
            )
            logging.getLogger(__name__).info("Azure Monitor / Application Insights configured")
        except ImportError:
            logging.getLogger(__name__).warning(
                "azure-monitor-opentelemetry not installed — skipping App Insights"
            )

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestTimer:
    """Context manager to measure and log request latency."""

    def __init__(self, operation: str, logger: logging.Logger):
        self.operation = operation
        self.logger = logger
        self.start = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed_ms = (time.perf_counter() - self.start) * 1000
        self.logger.info(
            f"{self.operation} completed",
            extra={"operation": self.operation, "latency_ms": round(elapsed_ms, 2)},
        )
        self.elapsed_ms = elapsed_ms
