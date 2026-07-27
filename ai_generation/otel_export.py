"""
OpenTelemetry Export — OTLP metrics, traces, logs export.

Based on ACOS Research: Observability Research
Provides OTLP (OpenTelemetry Protocol) exporters for Prometheus, Grafana, Tempo, Loki.
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OTLPTransport(str, Enum):
    HTTP_PROTOBUF = "http/protobuf"
    HTTP_JSON = "http/json"
    GRPC = "grpc"


class SignalType(str, Enum):
    METRICS = "metrics"
    TRACES = "traces"
    LOGS = "logs"


@dataclass
class OTLPConfig:
    endpoint: str = "http://localhost:4318"
    transport: OTLPTransport = OTLPTransport.HTTP_PROTOBUF
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_secs: float = 10.0
    compression: str = "gzip"
    batch_size: int = 100
    batch_timeout_ms: int = 5000
    enabled_signals: List[SignalType] = field(default_factory=lambda: [SignalType.METRICS, SignalType.TRACES, SignalType.LOGS])


@dataclass
class ExportResult:
    success: bool = False
    signal: SignalType = SignalType.METRICS
    exported_count: int = 0
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "signal": self.signal.value,
            "exported_count": self.exported_count,
            "error": self.error,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp,
        }


class OTLPMetricsExporter:
    """Exports metrics in OTLP format."""

    def __init__(self, config: OTLPConfig):
        self.config = config
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_secs)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _convert_metrics(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert internal metrics to OTLP metrics format."""
        otlp_metrics = []
        for key, value in metrics.items():
            metric_type = value.get("type", "gauge")
            metric = {
                "name": key,
                "description": "",
                "unit": "1",
                "data": {},
            }

            if metric_type == "counter":
                metric["data"]["sum"] = {
                    "data_points": [{
                        "attributes": [],
                        "start_time_unix_nano": str(int(time.time() * 1e9)),
                        "time_unix_nano": str(int(time.time() * 1e9)),
                        "value": str(value.get("value", 0)),
                    }]
                }
            elif metric_type == "gauge":
                metric["data"]["gauge"] = {
                    "data_points": [{
                        "attributes": [],
                        "time_unix_nano": str(int(time.time() * 1e9)),
                        "value": str(value.get("value", 0)),
                    }]
                }
            elif metric_type == "histogram":
                stats = value
                metric["data"]["histogram"] = {
                    "data_points": [{
                        "attributes": [],
                        "start_time_unix_nano": str(int(time.time() * 1e9)),
                        "time_unix_nano": str(int(time.time() * 1e9)),
                        "count": str(stats.get("count", 0)),
                        "sum": str(stats.get("sum", 0)),
                        "bucket_counts": [],
                        "explicit_bounds": [],
                    }]
                }
            otlp_metrics.append(metric)
        return otlp_metrics

    async def export(self, metrics: Dict[str, Any]) -> ExportResult:
        start = time.time()
        try:
            session = await self._get_session()
            otlp_metrics = self._convert_metrics(metrics)

            payload = {
                "resourceMetrics": [{
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "acos-platform"}},
                            {"key": "service.version", "value": {"stringValue": "1.0.0"}},
                        ]
                    },
                    "scopeMetrics": [{
                        "scope": {"name": "acos-metrics", "version": "1.0.0"},
                        "metrics": otlp_metrics,
                    }],
                }]
            }

            headers = {
                "Content-Type": "application/json",
                **self.config.headers,
            }

            endpoint = f"{self.config.endpoint}/v1/metrics"
            async with session.post(endpoint, json=payload, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    return ExportResult(
                        success=True,
                        signal=SignalType.METRICS,
                        exported_count=len(otlp_metrics),
                        latency_ms=(time.time() - start) * 1000,
                    )
                else:
                    text = await resp.text()
                    return ExportResult(
                        success=False,
                        signal=SignalType.METRICS,
                        error=f"HTTP {resp.status}: {text[:200]}",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except ImportError:
            return ExportResult(
                success=False,
                signal=SignalType.METRICS,
                error="aiohttp not installed",
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ExportResult(
                success=False,
                signal=SignalType.METRICS,
                error=str(e),
                latency_ms=(time.time() - start) * 1000,
            )

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class OTLPTracesExporter:
    """Exports traces in OTLP format."""

    def __init__(self, config: OTLPConfig):
        self.config = config
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_secs)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _convert_traces(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert internal traces to OTLP spans format."""
        otlp_spans = []
        for trace in traces:
            spans = trace.get("spans", [])
            for span in spans:
                otlp_spans.append({
                    "traceId": trace.get("trace_id", ""),
                    "spanId": span.get("span_id", ""),
                    "parentSpanId": span.get("parent_span_id", ""),
                    "name": span.get("name", ""),
                    "kind": "SPAN_KIND_INTERNAL",
                    "startTimeUnixNano": str(int(span.get("start_time", time.time()) * 1e9)),
                    "endTimeUnixNano": str(int(span.get("end_time", time.time()) * 1e9)),
                    "attributes": [
                        {"key": k, "value": {"stringValue": str(v)}}
                        for k, v in span.get("attributes", {}).items()
                    ],
                    "status": {"code": "STATUS_CODE_OK" if span.get("status") == "ok" else "STATUS_CODE_ERROR"},
                })
        return otlp_spans

    async def export(self, traces: List[Dict[str, Any]]) -> ExportResult:
        start = time.time()
        try:
            session = await self._get_session()
            otlp_spans = self._convert_traces(traces)

            payload = {
                "resourceSpans": [{
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "acos-platform"}},
                        ]
                    },
                    "scopeSpans": [{
                        "scope": {"name": "acos-traces", "version": "1.0.0"},
                        "spans": otlp_spans,
                    }],
                }]
            }

            headers = {"Content-Type": "application/json", **self.config.headers}
            endpoint = f"{self.config.endpoint}/v1/traces"
            async with session.post(endpoint, json=payload, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    return ExportResult(
                        success=True,
                        signal=SignalType.TRACES,
                        exported_count=len(otlp_spans),
                        latency_ms=(time.time() - start) * 1000,
                    )
                else:
                    text = await resp.text()
                    return ExportResult(
                        success=False,
                        signal=SignalType.TRACES,
                        error=f"HTTP {resp.status}: {text[:200]}",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except ImportError:
            return ExportResult(
                success=False,
                signal=SignalType.TRACES,
                error="aiohttp not installed",
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ExportResult(
                success=False,
                signal=SignalType.TRACES,
                error=str(e),
                latency_ms=(time.time() - start) * 1000,
            )

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class OTLPLogsExporter:
    """Exports logs in OTLP format."""

    def __init__(self, config: OTLPConfig):
        self.config = config
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_secs)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _convert_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert internal logs to OTLP log records."""
        otlp_logs = []
        for log in logs:
            otlp_logs.append({
                "timeUnixNano": str(int(log.get("timestamp", time.time()) * 1e9)),
                "severityNumber": self._severity_to_number(log.get("level", "info")),
                "severityText": log.get("level", "INFO").upper(),
                "body": {"stringValue": log.get("message", "")},
                "attributes": [
                    {"key": k, "value": {"stringValue": str(v)}}
                    for k, v in log.items()
                    if k not in ["timestamp", "level", "message"]
                ],
            })
        return otlp_logs

    def _severity_to_number(self, level: str) -> int:
        mapping = {"debug": 5, "info": 9, "warning": 13, "error": 17, "critical": 21}
        return mapping.get(level.lower(), 9)

    async def export(self, logs: List[Dict[str, Any]]) -> ExportResult:
        start = time.time()
        try:
            session = await self._get_session()
            otlp_logs = self._convert_logs(logs)

            payload = {
                "resourceLogs": [{
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "acos-platform"}},
                        ]
                    },
                    "scopeLogs": [{
                        "scope": {"name": "acos-logs", "version": "1.0.0"},
                        "logRecords": otlp_logs,
                    }],
                }]
            }

            headers = {"Content-Type": "application/json", **self.config.headers}
            endpoint = f"{self.config.endpoint}/v1/logs"
            async with session.post(endpoint, json=payload, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    return ExportResult(
                        success=True,
                        signal=SignalType.LOGS,
                        exported_count=len(otlp_logs),
                        latency_ms=(time.time() - start) * 1000,
                    )
                else:
                    text = await resp.text()
                    return ExportResult(
                        success=False,
                        signal=SignalType.LOGS,
                        error=f"HTTP {resp.status}: {text[:200]}",
                        latency_ms=(time.time() - start) * 1000,
                    )
        except ImportError:
            return ExportResult(
                success=False,
                signal=SignalType.LOGS,
                error="aiohttp not installed",
                latency_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ExportResult(
                success=False,
                signal=SignalType.LOGS,
                error=str(e),
                latency_ms=(time.time() - start) * 1000,
            )

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class OTLPExporterManager:
    """
    Unified OTLP exporter manager.

    Manages metrics, traces, and logs exporters with batching and retries.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._otel_config = OTLPConfig(
            endpoint=self.config.get("endpoint", "http://localhost:4318"),
            transport=OTLPTransport(self.config.get("transport", "http/protobuf")),
            headers=self.config.get("headers", {}),
            timeout_secs=self.config.get("timeout_secs", 10.0),
            enabled_signals=[
                SignalType(s) for s in self.config.get("enabled_signals", ["metrics", "traces", "logs"])
            ],
        )
        self._metrics_exporter = OTLPMetricsExporter(self._otel_config)
        self._traces_exporter = OTLPTracesExporter(self._otel_config)
        self._logs_exporter = OTLPLogsExporter(self._otel_config)
        self._observability = None
        self._export_task: Optional[asyncio.Task] = None
        self._export_interval = self.config.get("export_interval_secs", 30.0)
        self._running = False
        self._export_history: List[ExportResult] = []
        self._max_history = self.config.get("max_history", 100)

    def set_observability(self, observability):
        self._observability = observability

    async def start(self):
        self._running = True
        self._export_task = asyncio.create_task(self._export_loop())
        logger.info("OTLP exporter started")

    async def stop(self):
        self._running = False
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
        await self._metrics_exporter.close()
        await self._traces_exporter.close()
        await self._logs_exporter.close()
        logger.info("OTLP exporter stopped")

    async def _export_loop(self):
        while self._running:
            try:
                await self.export_all()
            except Exception as e:
                logger.error(f"Export loop error: {e}")
            await asyncio.sleep(self._export_interval)

    async def export_all(self) -> List[ExportResult]:
        if not self._observability:
            return []

        results = []
        all_data = self._observability.export_all()

        if SignalType.METRICS in self._otel_config.enabled_signals:
            result = await self._metrics_exporter.export(all_data.get("metrics", {}))
            results.append(result)
            self._export_history.append(result)

        if SignalType.TRACES in self._otel_config.enabled_signals:
            result = await self._traces_exporter.export(all_data.get("traces", []))
            results.append(result)
            self._export_history.append(result)

        if SignalType.LOGS in self._otel_config.enabled_signals:
            result = await self._logs_exporter.export(all_data.get("logs", []))
            results.append(result)
            self._export_history.append(result)

        # Trim history
        if len(self._export_history) > self._max_history:
            self._export_history = self._export_history[-self._max_history:]

        return results

    def get_stats(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "endpoint": self._otel_config.endpoint,
            "enabled_signals": [s.value for s in self._otel_config.enabled_signals],
            "export_interval_secs": self._export_interval,
            "total_exports": len(self._export_history),
            "successful_exports": sum(1 for r in self._export_history if r.success),
            "last_export": self._export_history[-1].to_dict() if self._export_history else None,
            "history_size": len(self._export_history),
        }

    def get_export_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._export_history[-limit:]]
