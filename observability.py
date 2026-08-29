"""Optional observability helpers for production deployments."""
from __future__ import annotations

import os


def configure_observability(app) -> bool:
    """Configure FastAPI tracing when OTEL_ENABLED is true.

    When OTEL_EXPORTER_OTLP_TRACES_ENDPOINT is configured, spans are exported
    over OTLP/HTTP to the selected collector/backend. Otherwise the application
    keeps the console exporter as a safe local fallback.
    """
    enabled = os.getenv("OTEL_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not enabled:
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError as exc:  # pragma: no cover - depends on production extras
        raise RuntimeError(
            "OTEL_ENABLED requires dependencies from requirements-production.txt"
        ) from exc

    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip()
    if traces_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
        except ImportError as exc:  # pragma: no cover - depends on production extras
            raise RuntimeError(
                "OTLP tracing requires dependencies from requirements-production.txt"
            ) from exc
        exporter = OTLPSpanExporter(endpoint=traces_endpoint)
    else:
        exporter = ConsoleSpanExporter()

    service_name = os.getenv("OTEL_SERVICE_NAME", "rag-knowledge-assistant")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    return True
