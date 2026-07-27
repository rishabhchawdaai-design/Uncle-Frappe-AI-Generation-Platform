"""Tests for health_monitor.py — HealthMonitor."""

import pytest
from ai_generation.health_monitor import HealthMonitor, HealthStatus


class TestHealthMonitor:
    def test_register_provider(self):
        monitor = HealthMonitor()
        monitor.register_provider("openai", "https://api.openai.com/health")
        assert "openai" in monitor.get_all_statuses()

    def test_get_status(self):
        monitor = HealthMonitor()
        monitor.register_provider("test_provider")
        status = monitor.get_status("test_provider")
        assert status is not None
        assert status["provider"] == "test_provider"

    def test_is_healthy_default(self):
        monitor = HealthMonitor()
        monitor.register_provider("test_provider")
        # Default status is healthy=True
        assert monitor.is_healthy("test_provider") is True

    def test_get_healthy_providers(self):
        monitor = HealthMonitor()
        monitor.register_provider("healthy_provider")
        monitor.register_provider("unhealthy_provider")
        healthy = monitor.get_healthy_providers()
        unhealthy = monitor.get_unhealthy_providers()
        assert isinstance(healthy, list)
        assert isinstance(unhealthy, list)

    def test_get_stats(self):
        monitor = HealthMonitor()
        monitor.register_provider("a")
        monitor.register_provider("b")
        stats = monitor.get_stats()
        assert "total_monitored" in stats
        assert stats["total_monitored"] == 2

    def test_nonexistent_provider(self):
        monitor = HealthMonitor()
        status = monitor.get_status("nonexistent")
        assert status is None

    def test_health_status_to_dict(self):
        status = HealthStatus(provider="test", healthy=True, latency_ms=100, last_check="2026-01-01")
        d = status.to_dict()
        assert d["provider"] == "test"
        assert d["healthy"] is True
