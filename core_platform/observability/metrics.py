"""
Phase 19: Observability — Prometheus metrics, structured logging, distributed tracing.
"""
import asyncio, json, logging, time, threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import os

logger = logging.getLogger(__name__)


class StructuredLogger:
    """JSON structured logging with context."""

    def __init__(self, name: str = "research_platform", log_dir: str = "./logs"):
        self._path = Path(log_dir)
        self._path.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(name)
        handler = logging.FileHandler(self._path / f"{name}.log")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def log(self, level: str, message: str, **context):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **context,
        }
        getattr(self._logger, level.lower(), self._logger.info)(json.dumps(entry))
        return entry

    def info(self, msg, **ctx): return self.log("INFO", msg, **ctx)
    def error(self, msg, **ctx): return self.log("ERROR", msg, **ctx)
    def warning(self, msg, **ctx): return self.log("WARNING", msg, **ctx)
    def debug(self, msg, **ctx): return self.log("DEBUG", msg, **ctx)


@dataclass
class MetricPoint:
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metric_type: str = "gauge"  # gauge, counter, histogram, summary

    def to_prometheus(self) -> str:
        label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        label_str = f"{{{label_str}}}" if label_str else ""
        return f"{self.name}{label_str} {self.value} {int(self.timestamp * 1000)}"


class MetricsCollector:
    """Prometheus-compatible metrics collector."""

    def __init__(self, storage_path: str = "./data/metrics"):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def counter(self, name: str, value: float = 1.0, **labels):
        with self._lock:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
            self._counters[key] += value
            self._metrics[name].append(MetricPoint(name, self._counters[key], labels, metric_type="counter"))

    def gauge(self, name: str, value: float, **labels):
        with self._lock:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
            self._gauges[key] = value
            self._metrics[name].append(MetricPoint(name, value, labels, metric_type="gauge"))

    def histogram(self, name: str, value: float, **labels):
        with self._lock:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
            self._histograms[key].append(value)
            self._metrics[name].append(MetricPoint(name, value, labels, metric_type="histogram"))

    def to_prometheus(self) -> str:
        lines = ["# Research Platform Metrics"]
        for name, points in self._metrics.items():
            lines.append(f"# TYPE {name} {points[-1].metric_type if points else 'gauge'}")
            seen = set()
            for p in points:
                label_key = json.dumps(p.labels, sort_keys=True)
                if label_key not in seen:
                    lines.append(p.to_prometheus())
                    seen.add(label_key)
        return "\n".join(lines)

    def get_dashboard_data(self) -> Dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: {"count": len(v), "avg": round(sum(v)/max(len(v),1), 2), "min": min(v) if v else 0, "max": max(v) if v else 0} for k, v in self._histograms.items()},
            "total_metrics": sum(len(v) for v in self._metrics.values()),
        }

    def save(self):
        data = {name: [{"value": p.value, "labels": p.labels, "timestamp": p.timestamp, "type": p.metric_type} for p in points[-100:]] for name, points in self._metrics.items()}
        (self._path / "metrics_snapshot.json").write_text(json.dumps(data, indent=2))


class TracingMiddleware:
    """Simple distributed tracing."""

    def __init__(self):
        self._traces: List[Dict] = []

    def start_trace(self, operation: str, **attributes) -> str:
        trace_id = f"{int(time.time()*1000)}-{threading.get_ident()}"
        self._traces.append({
            "trace_id": trace_id, "operation": operation,
            "start_time": datetime.now().isoformat(),
            "attributes": attributes, "status": "in_progress",
        })
        return trace_id

    def end_trace(self, trace_id: str, status: str = "ok"):
        for t in self._traces:
            if t["trace_id"] == trace_id:
                t["end_time"] = datetime.now().isoformat()
                t["status"] = status
                break

    def get_traces(self, limit: int = 50) -> List[Dict]:
        return self._traces[-limit:]

    def export(self, path: str = "./data/traces.json"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self._traces[-1000:], indent=2))
