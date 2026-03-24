from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from starlette.applications import Starlette

from enterprise_mcp.config import AppConfig


def configure_telemetry(app: Starlette, config: AppConfig) -> None:
    if not config.otel_enabled:
        return

    resource = Resource.create(
        {
            "service.name": config.otel_service_name,
            "deployment.environment": config.app_env,
        }
    )
    tracer_provider = TracerProvider(resource=resource)

    if config.otel_exporter == "console":
        exporter = ConsoleSpanExporter()
    else:
        exporter = OTLPSpanExporter(endpoint=config.otel_otlp_endpoint)

    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)
    StarletteInstrumentor().instrument_app(app)
