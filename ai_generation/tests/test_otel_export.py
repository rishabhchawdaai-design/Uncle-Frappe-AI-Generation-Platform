"""
Tests for the OpenTelemetry export layer (otel_export.py).

Verifies OBS-07 (OpenTelemetry Export): OTLP metric/trace/log conversion,
export results, exporter manager wiring, and truthful failure reporting when
aiohttp is unavailable (platform is stdlib-first).
"""
import pytest

from ai_generation.otel_export import (
    OTLPConfig,
    OTLPExporterManager,
    OTLPLogsExporter,
    OTLPMetricsExporter,
    OTLPTransport,
    OTLPTracesExporter,
    ExportResult,
    SignalType,
)


def test_otlp_config_defaults():
    config = OTLPConfig()
    assert config.endpoint == "http://localhost:4318"
    assert config.transport == OTLPTransport.HTTP_PROTOBUF
    assert config.timeout_secs == 10.0
    assert config.batch_size == 100
    assert SignalType.METRICS in config.enabled_signals


def test_export_result_to_dict():
    result = ExportResult(success=True, signal=SignalType.METRICS,
                          exported_count=3, latency_ms=12.34)
    d = result.to_dict()
    assert d["success"] is True
    assert d["signal"] == "metrics"
    assert d["exported_count"] == 3
    assert d["latency_ms"] == 12.34


def test_metrics_conversion_counter_gauge_histogram():
    exporter = OTLPMetricsExporter(OTLPConfig())
    metrics = {
        "requests_total": {"type": "counter", "value": 42},
        "temperature": {"type": "gauge", "value": 0.8},
        "latency": {"type": "histogram", "count": 10, "sum": 500},
    }
    otlp = exporter._convert_metrics(metrics)
    by_name = {m["name"]: m for m in otlp}
    assert by_name["requests_total"]["data"]["sum"]["data_points"][0]["value"] == "42"
    assert by_name["temperature"]["data"]["gauge"]["data_points"][0]["value"] == "0.8"
    hist = by_name["latency"]["data"]["histogram"]["data_points"][0]
    assert hist["count"] == "10"
    assert hist["sum"] == "500"
    assert len(otlp) == 3


def test_traces_conversion():
    exporter = OTLPTracesExporter(OTLPConfig())
    traces = [{
        "trace_id": "t1",
        "spans": [{
            "span_id": "s1",
            "parent_span_id": "",
            "name": "generate",
            "start_time": 100.0,
            "end_time": 200.0,
            "status": "ok",
            "attributes": {"provider": "hf"},
        }],
    }]
    spans = exporter._convert_traces(traces)
    assert len(spans) == 1
    assert spans[0]["name"] == "generate"
    assert spans[0]["status"]["code"] == "STATUS_CODE_OK"
    assert spans[0]["attributes"][0]["value"]["stringValue"] == "hf"


def test_logs_conversion_and_severity():
    exporter = OTLPLogsExporter(OTLPConfig())
    logs = [
        {"timestamp": 100.0, "level": "error", "message": "boom", "module": "router"},
        {"timestamp": 200.0, "level": "info", "message": "ok"},
    ]
    otlp = exporter._convert_logs(logs)
    assert len(otlp) == 2
    assert otlp[0]["severityNumber"] == 17
    assert otlp[0]["severityText"] == "ERROR"
    assert otlp[1]["severityNumber"] == 9
    assert otlp[1]["body"]["stringValue"] == "ok"
    assert exporter._severity_to_number("critical") == 21
    assert exporter._severity_to_number("unknown") == 9


@pytest.mark.asyncio
async def test_export_without_aiohttp_reports_truthfully():
    # aiohttp is not a platform dependency; export must fail truthfully
    exporter = OTLPMetricsExporter(OTLPConfig())
    result = await exporter.export({"requests": {"type": "counter", "value": 1}})
    assert result.success is False
    assert result.error == "aiohttp not installed"


class _FakeResponse:
    def __init__(self, status):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def text(self):
        return "boom"


class _FakeSession:
    def __init__(self, status):
        self.status = status
        self.sent = []

    def post(self, url, json=None, headers=None):
        # aiohttp returns a _RequestContextManager (async context manager)
        self.sent.append((url, json, headers))
        return _FakeResponse(self.status)

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_export_success_path_with_mocked_session(monkeypatch):
    exporter = OTLPMetricsExporter(OTLPConfig())
    fake = _FakeSession(200)

    async def fake_session():
        return fake

    monkeypatch.setattr(exporter, "_get_session", fake_session)
    result = await exporter.export({"requests": {"type": "counter", "value": 1}})
    assert result.success is True
    assert result.exported_count == 1
    assert result.signal == SignalType.METRICS
    url, payload, headers = fake.sent[0]
    assert url.endswith("/v1/metrics")
    assert payload["resourceMetrics"][0]["resource"]["attributes"][0]["value"]["stringValue"] == "acos-platform"


@pytest.mark.asyncio
async def test_export_http_error_path(monkeypatch):
    exporter = OTLPMetricsExporter(OTLPConfig())
    fake = _FakeSession(500)

    async def fake_session():
        return fake

    monkeypatch.setattr(exporter, "_get_session", fake_session)
    result = await exporter.export({"requests": {"type": "counter", "value": 1}})
    assert result.success is False
    assert result.error.startswith("HTTP 500")


def test_exporter_manager_stats():
    manager = OTLPExporterManager({"endpoint": "http://otel:4318"})
    stats = manager.get_stats()
    assert stats["endpoint"] == "http://otel:4318"
    assert stats["total_exports"] == 0
    assert stats["running"] is False
    assert "metrics" in stats["enabled_signals"]


@pytest.mark.asyncio
async def test_exporter_manager_export_all_without_observability():
    manager = OTLPExporterManager()
    assert await manager.export_all() == []


@pytest.mark.asyncio
async def test_exporter_manager_with_fake_observability():
    manager = OTLPExporterManager({"enabled_signals": ["metrics"]})

    class FakeObs:
        def export_all(self):
            return {"metrics": {"requests": {"type": "counter", "value": 1}},
                    "traces": [], "logs": []}

    manager.set_observability(FakeObs())
    results = await manager.export_all()
    assert len(results) == 1
    # aiohttp missing -> truthful failure, but history is recorded
    assert results[0].success is False
    assert manager.get_stats()["total_exports"] == 1
    history = manager.get_export_history()
    assert history[0]["signal"] == "metrics"
