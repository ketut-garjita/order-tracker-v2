"""OpenTelemetry setup for Order Tracker: metrics, logs and traces.

OTEL_EXPORTER=console (default) -> print signals to stdout (Question 2)
OTEL_EXPORTER=otlp              -> send to the OTel Collector (Question 3+)
                                   endpoint from OTEL_EXPORTER_OTLP_ENDPOINT,
                                   e.g. http://otel-collector:4318
"""
import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def _exporters():
    """Return (span_exporter, metric_exporter, log_exporter) for the chosen mode."""
    if os.getenv("OTEL_EXPORTER", "console").lower() == "otlp":
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        # Endpoint (and the /v1/<signal> suffix) comes from OTEL_EXPORTER_OTLP_ENDPOINT.
        return OTLPSpanExporter(), OTLPMetricExporter(), OTLPLogExporter()
    return ConsoleSpanExporter(), ConsoleMetricExporter(), ConsoleLogExporter()


def setup_telemetry() -> None:
    resource = Resource.create(
        {"service.name": os.getenv("OTEL_SERVICE_NAME", "order-tracker")}
    )
    span_exporter, metric_exporter, log_exporter = _exporters()

    # Traces
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Metrics (short interval so they show up quickly while testing)
    reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "5000")),
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    # Logs: bridge stdlib logging -> OTel. Records inside a request automatically
    # carry trace_id/span_id, which is what lets Grafana jump from log to trace.
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))
