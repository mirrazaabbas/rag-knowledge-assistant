"""Optional observability helpers for production deployments."""
from __future__ import annotations

import os


def configure_observability(app) -> bool:
    """Configure FastAPI tracing when OTEL_ENABLED is true.

    Returns True when instrumentation is enabled. The application remains fully
    functional without OpenTelemetry dependencies in the local baseline setup.
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

    service_name = os.getenv("OTEL_SERVICE_NAME", "rag-knowledge-assistant")
    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name})
    )
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    return True
