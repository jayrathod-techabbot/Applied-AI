"""Structured logging + CloudWatch metrics in one module."""
import json
import logging
import sys
import boto3
from app.config import get_settings

settings = get_settings()
_cw = None  # lazy CloudWatch client


def _get_cw():
    global _cw
    if _cw is None:
        _cw = boto3.client("cloudwatch", region_name=settings.aws_region)
    return _cw


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.environment,
            "version": settings.app_version,
        }
        for k, v in record.__dict__.items():
            if k not in ("msg", "args", "levelname", "levelno", "pathname", "filename",
                         "module", "exc_info", "exc_text", "lineno", "funcName",
                         "created", "msecs", "thread", "threadName", "processName",
                         "process", "name", "message", "relativeCreated", "stack_info"):
                entry[k] = v
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JSONFormatter())
    root.addHandler(h)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def put_metric(name: str, value: float, unit: str = "Count"):
    """Push a single metric to CloudWatch. Fails silently to avoid blocking requests."""
    try:
        _get_cw().put_metric_data(
            Namespace=f"LLMApp/{settings.environment}",
            MetricData=[{
                "MetricName": name,
                "Value": value,
                "Unit": unit,
                "Dimensions": [{"Name": "Environment", "Value": settings.environment}],
            }],
        )
    except Exception as e:
        logging.getLogger(__name__).warning("CloudWatch metric push failed", extra={"error": str(e)})


def record_request(latency_ms: float, input_tokens: int, output_tokens: int,
                   cost_usd: float, cached: bool, blocked: bool):
    put_metric("RequestCount", 1)
    put_metric("Latency", latency_ms, "Milliseconds")
    put_metric("InputTokens", input_tokens)
    put_metric("OutputTokens", output_tokens)
    put_metric("EstimatedCostUSD", cost_usd, "None")
    if cached:
        put_metric("CacheHit", 1)
    if blocked:
        put_metric("GuardrailBlock", 1)
