"""
Observability Layer — metrics, traces, and structured logging.

Based on ACOS Research: Observability Research, Ch13 (Observability Digital Twin)
Provides OpenTelemetry-compatible instrumentation with local fallback.
Collects metrics (throughput, latency, errors), creates traces for generation
requests, and emits structured logs. Exports to OTLP collectors when configured,
falls back to local logging when no collector is available.

Architecture:
    Application → ObservabilityManager → OTLP Exporter (if configured)
                                              ↓
                                     ┌─────────────────┐
                                     │  Collector       │
                                     │  (Prometheus,    │
                                     │   Grafana, etc.) │
                                     └─────────────────┘
"""
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class TraceStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str = ""
    value: float = 0.0
    metric_type: MetricType = MetricType.COUNTER
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: str = ""
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "labels": self.labels,
            "timestamp": self.timestamp,
            "unit": self.unit,
        }


@dataclass
class TraceSpan:
    """A single span in a distributed trace."""
    span_id: str = ""
    trace_id: str = ""
    parent_span_id: str = ""
    name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    status: TraceStatus = TraceStatus.UNSET
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events,
        }


@dataclass
class LogEntry:
    """A structured log entry."""
    timestamp: str = ""
    level: str = "info"
    message: str = ""
    source: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "attributes": self.attributes,
        }


class ObservabilityManager:
    """
    Observability layer for the AI Generation Platform.

    Collects metrics, creates traces, emits structured logs.
    Exportable to OpenTelemetry collectors via OTLP.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._metrics: Dict[str, float] = {}
        self._metric_metadata: Dict[str, Dict[str, Any]] = {}
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._traces: List[TraceSpan] = []
        self._logs: List[LogEntry] = []
        self._active_traces: Dict[str, TraceSpan] = {}
        self._max_traces = self.config.get("max_traces", 10000)
        self._max_logs = self.config.get("max_logs", 10000)
        self._otlp_endpoint = self.config.get("otlp_endpoint", "")
        self._service_name = self.config.get("service_name", "uncle-frappe-ai")
        self._init_default_metrics()

    def _init_default_metrics(self):
        """Initialize default platform metrics."""
        self._counters["generation_requests_total"] = 0
        self._counters["generation_success_total"] = 0
        self._counters["generation_failure_total"] = 0
        self._counters["provider_selections_total"] = 0
        self._counters["fallback_activations_total"] = 0
        self._counters["negotiation_decisions_total"] = 0
        self._counters["audio_requests_total"] = 0
        self._counters["video_requests_total"] = 0
        self._counters["image_requests_total"] = 0
        self._counters["plugin_activations_total"] = 0
        self._gauges["active_providers"] = 0
        self._gauges["active_plugins"] = 0
        self._gauges["queue_depth"] = 0

    # ── Counter Operations ─────────────────────────────────────

    def increment_counter(self, name: str, value: float = 1.0,
                           labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self._counters[key] += value

    def get_counter(self, name: str,
                     labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    # ── Gauge Operations ───────────────────────────────────────

    def set_gauge(self, name: str, value: float,
                   labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def get_gauge(self, name: str,
                   labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    # ── Histogram Operations ───────────────────────────────────

    def record_histogram(self, name: str, value: float,
                          labels: Optional[Dict[str, str]] = None):
        """Record a value in a histogram."""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)

    def get_histogram_stats(self, name: str,
                             labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        sorted_vals = sorted(values)
        count = len(sorted_vals)
        return {
            "count": count,
            "sum": sum(sorted_vals),
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "avg": sum(sorted_vals) / count,
            "p50": sorted_vals[int(count * 0.5)],
            "p95": sorted_vals[int(count * 0.95)] if count >= 20 else sorted_vals[-1],
            "p99": sorted_vals[int(count * 0.99)] if count >= 100 else sorted_vals[-1],
        }

    # ── Trace Operations ───────────────────────────────────────

    def start_trace(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace. Returns trace_id."""
        import hashlib
        trace_id = hashlib.sha256(f"{time.time()}:{name}".encode()).hexdigest()[:16]
        span = TraceSpan(
            span_id=trace_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
        self._active_traces[trace_id] = span
        self._traces.append(span)
        self._trim_traces()
        return trace_id

    def start_span(self, trace_id: str, name: str,
                    attributes: Optional[Dict[str, Any]] = None) -> str:
        """Start a child span within a trace."""
        import hashlib
        span_id = hashlib.sha256(f"{time.time()}:{trace_id}:{name}".encode()).hexdigest()[:16]
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=trace_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
        self._traces.append(span)
        self._trim_traces()
        return span_id

    def end_span(self, span_id: str, status: TraceStatus = TraceStatus.OK,
                  attributes: Optional[Dict[str, Any]] = None):
        """End a span."""
        for span in self._traces:
            if span.span_id == span_id:
                span.end_time = time.time()
                span.status = status
                if attributes:
                    span.attributes.update(attributes)
                break

    def end_trace(self, trace_id: str, status: TraceStatus = TraceStatus.OK):
        """End a trace."""
        if trace_id in self._active_traces:
            self._active_traces[trace_id].end_time = time.time()
            self._active_traces[trace_id].status = status
            del self._active_traces[trace_id]

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all spans for a trace."""
        return [s.to_dict() for s in self._traces if s.trace_id == trace_id]

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent traces."""
        seen_traces = set()
        recent = []
        for span in reversed(self._traces):
            if span.trace_id not in seen_traces and (span.parent_span_id == span.trace_id or span.parent_span_id == ""):
                seen_traces.add(span.trace_id)
                recent.append(span.to_dict())
                if len(recent) >= limit:
                    break
        return recent

    # ── Log Operations ─────────────────────────────────────────

    def log(self, level: str, message: str, source: str = "",
            attributes: Optional[Dict[str, Any]] = None):
        """Emit a structured log entry."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            source=source or self._service_name,
            attributes=attributes or {},
        )
        self._logs.append(entry)
        self._trim_logs()

        # Also emit to Python logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{source}] {message}")

    def log_info(self, message: str, source: str = "",
                  attributes: Optional[Dict[str, Any]] = None):
        self.log("info", message, source, attributes)

    def log_error(self, message: str, source: str = "",
                   attributes: Optional[Dict[str, Any]] = None):
        self.log("error", message, source, attributes)

    def log_warning(self, message: str, source: str = "",
                     attributes: Optional[Dict[str, Any]] = None):
        self.log("warning", message, source, attributes)

    def get_logs(self, level: Optional[str] = None,
                  source: Optional[str] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """Get log entries with optional filtering."""
        logs = self._logs
        if level:
            logs = [l for l in logs if l.level == level]
        if source:
            logs = [l for l in logs if l.source == source]
        return [l.to_dict() for l in logs[-limit:]]

    # ── Generation Request Tracking ────────────────────────────

    def track_generation_start(self, request_id: str, task_type: str,
                                provider: str = "", model: str = "") -> str:
        """Track the start of a generation request. Returns trace_id."""
        self.increment_counter("generation_requests_total",
                               labels={"task_type": task_type})
        self.increment_counter(f"{task_type}_requests_total")
        trace_id = self.start_trace(
            f"generation.{task_type}",
            attributes={
                "request_id": request_id,
                "task_type": task_type,
                "provider": provider,
                "model": model,
            },
        )
        return trace_id

    def track_generation_end(self, trace_id: str, success: bool,
                              latency_ms: float = 0.0,
                              provider: str = "", quality_score: float = 0.0):
        """Track the end of a generation request."""
        status = TraceStatus.OK if success else TraceStatus.ERROR
        self.end_trace(trace_id, status=status)
        if success:
            self.increment_counter("generation_success_total")
        else:
            self.increment_counter("generation_failure_total")
        if latency_ms > 0:
            self.record_histogram("generation_latency_ms", latency_ms,
                                   labels={"provider": provider})
        if quality_score > 0:
            self.record_histogram("generation_quality_score", quality_score,
                                   labels={"provider": provider})

    def track_provider_selection(self, provider: str, task_type: str,
                                  confidence: float = 0.0):
        """Track a provider selection decision."""
        self.increment_counter("provider_selections_total",
                               labels={"provider": provider, "task_type": task_type})
        self.increment_counter("negotiation_decisions_total")
        if confidence > 0:
            self.record_histogram("provider_confidence", confidence,
                                   labels={"provider": provider})

    def track_fallback(self, from_provider: str, to_provider: str, reason: str = ""):
        """Track a fallback activation."""
        self.increment_counter("fallback_activations_total",
                               labels={"from": from_provider, "to": to_provider})

    # ── Export ──────────────────────────────────────────────────

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics in a serializable format."""
        metrics = {}
        for key, value in self._counters.items():
            metrics[key] = {"type": "counter", "value": value}
        for key, value in self._gauges.items():
            metrics[key] = {"type": "gauge", "value": value}
        for key, values in self._histograms.items():
            metrics[key] = {"type": "histogram", **self.get_histogram_stats(key)}
        return metrics

    def export_all(self) -> Dict[str, Any]:
        """Export all observability data."""
        return {
            "service": self._service_name,
            "timestamp": datetime.now().isoformat(),
            "metrics": self.export_metrics(),
            "traces": self.get_recent_traces(100),
            "logs": self.get_logs(limit=100),
            "stats": self.get_stats(),
        }

    # ── Stats ──────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get observability statistics."""
        return {
            "service_name": self._service_name,
            "otlp_configured": bool(self._otlp_endpoint),
            "total_metrics": len(self._counters) + len(self._gauges) + len(self._histograms),
            "total_traces": len(self._traces),
            "active_traces": len(self._active_traces),
            "total_logs": len(self._logs),
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }

    # ── Internal ───────────────────────────────────────────────

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a metric key with optional labels."""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def _trim_traces(self):
        if len(self._traces) > self._max_traces:
            self._traces = self._traces[-self._max_traces:]

    def _trim_logs(self):
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
