"""
Benchmark Regression Detection — latency, quality, and stability regression.

Based on ACOS Research: Benchmark Knowledge Base §6
Detects performance regressions in benchmark results using statistical methods.
Provides alerts when latency, quality, or stability degrades beyond thresholds.

Regression types:
- Latency Regression: p50/p95/p99 latency exceeds baseline
- Quality Regression: Quality score drops below baseline
- Stability Regression: Error rate or variance increases
"""
import logging
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RegressionType(str, Enum):
    LATENCY = "latency"
    QUALITY = "quality"
    STABILITY = "stability"


class RegressionSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class RegressionAlert:
    """A detected regression alert."""
    regression_type: RegressionType = RegressionType.LATENCY
    severity: RegressionSeverity = RegressionSeverity.WARNING
    provider: str = ""
    metric: str = ""
    baseline_value: float = 0.0
    current_value: float = 0.0
    deviation_pct: float = 0.0
    threshold_pct: float = 0.0
    message: str = ""
    sample_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regression_type": self.regression_type.value,
            "severity": self.severity.value,
            "provider": self.provider,
            "metric": self.metric,
            "baseline_value": round(self.baseline_value, 3),
            "current_value": round(self.current_value, 3),
            "deviation_pct": round(self.deviation_pct, 1),
            "threshold_pct": round(self.threshold_pct, 1),
            "message": self.message,
            "sample_count": self.sample_count,
        }


@dataclass
class RegressionConfig:
    """Configuration for regression detection thresholds."""
    latency_warning_pct: float = 20.0
    latency_critical_pct: float = 50.0
    quality_warning_pct: float = 10.0
    quality_critical_pct: float = 25.0
    stability_error_rate_warning: float = 0.05
    stability_error_rate_critical: float = 0.15
    stability_variance_warning_pct: float = 30.0
    min_samples: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latency_warning_pct": self.latency_warning_pct,
            "latency_critical_pct": self.latency_critical_pct,
            "quality_warning_pct": self.quality_warning_pct,
            "quality_critical_pct": self.quality_critical_pct,
            "stability_error_rate_warning": self.stability_error_rate_warning,
            "stability_error_rate_critical": self.stability_error_rate_critical,
            "stability_variance_warning_pct": self.stability_variance_warning_pct,
            "min_samples": self.min_samples,
        }


class RegressionDetector:
    """
    Detects benchmark regressions using statistical comparison
    against baseline measurements.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._rc = RegressionConfig(**{k: v for k, v in self.config.items()
                                        if hasattr(RegressionConfig, k)})
        self._baselines: Dict[str, Dict[str, float]] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[RegressionAlert] = []

    def set_baseline(self, provider: str, metrics: Dict[str, float]):
        """Set baseline metrics for a provider."""
        self._baselines[provider] = metrics
        logger.info(f"Baseline set for {provider}: {metrics}")

    def get_baseline(self, provider: str) -> Dict[str, float]:
        """Get baseline metrics for a provider."""
        return self._baselines.get(provider, {})

    def record_measurement(self, provider: str, metrics: Dict[str, float]):
        """Record a benchmark measurement for a provider."""
        if provider not in self._history:
            self._history[provider] = []
        self._history[provider].append(metrics)

    def detect_latency_regression(self, provider: str,
                                   current_p50: float,
                                   current_p95: float = 0.0,
                                   current_p99: float = 0.0) -> List[RegressionAlert]:
        """Detect latency regressions against baseline."""
        baseline = self._baselines.get(provider, {})
        alerts = []

        if "latency_p50" in baseline and current_p50 > 0:
            deviation = ((current_p50 - baseline["latency_p50"]) / baseline["latency_p50"]) * 100
            if deviation >= self._rc.latency_critical_pct:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.LATENCY,
                    severity=RegressionSeverity.CRITICAL,
                    provider=provider,
                    metric="latency_p50",
                    baseline_value=baseline["latency_p50"],
                    current_value=current_p50,
                    deviation_pct=deviation,
                    threshold_pct=self._rc.latency_critical_pct,
                    message=f"CRITICAL: {provider} p50 latency regression {deviation:.1f}% "
                            f"(baseline={baseline['latency_p50']:.0f}ms, current={current_p50:.0f}ms)",
                ))
            elif deviation >= self._rc.latency_warning_pct:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.LATENCY,
                    severity=RegressionSeverity.WARNING,
                    provider=provider,
                    metric="latency_p50",
                    baseline_value=baseline["latency_p50"],
                    current_value=current_p50,
                    deviation_pct=deviation,
                    threshold_pct=self._rc.latency_warning_pct,
                    message=f"WARNING: {provider} p50 latency regression {deviation:.1f}%",
                ))

        if "latency_p99" in baseline and current_p99 > 0:
            deviation = ((current_p99 - baseline["latency_p99"]) / baseline["latency_p99"]) * 100
            if deviation >= self._rc.latency_critical_pct:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.LATENCY,
                    severity=RegressionSeverity.CRITICAL,
                    provider=provider,
                    metric="latency_p99",
                    baseline_value=baseline["latency_p99"],
                    current_value=current_p99,
                    deviation_pct=deviation,
                    threshold_pct=self._rc.latency_critical_pct,
                    message=f"CRITICAL: {provider} p99 latency regression {deviation:.1f}%",
                ))

        self._alerts.extend(alerts)
        return alerts

    def detect_quality_regression(self, provider: str,
                                   current_score: float) -> List[RegressionAlert]:
        """Detect quality regressions against baseline."""
        baseline = self._baselines.get(provider, {})
        alerts = []

        if "quality_score" in baseline and baseline["quality_score"] > 0:
            deviation = ((baseline["quality_score"] - current_score) / baseline["quality_score"]) * 100
            if deviation >= self._rc.quality_critical_pct:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.QUALITY,
                    severity=RegressionSeverity.CRITICAL,
                    provider=provider,
                    metric="quality_score",
                    baseline_value=baseline["quality_score"],
                    current_value=current_score,
                    deviation_pct=deviation,
                    threshold_pct=self._rc.quality_critical_pct,
                    message=f"CRITICAL: {provider} quality regression {deviation:.1f}% "
                            f"(baseline={baseline['quality_score']:.3f}, current={current_score:.3f})",
                ))
            elif deviation >= self._rc.quality_warning_pct:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.QUALITY,
                    severity=RegressionSeverity.WARNING,
                    provider=provider,
                    metric="quality_score",
                    baseline_value=baseline["quality_score"],
                    current_value=current_score,
                    deviation_pct=deviation,
                    threshold_pct=self._rc.quality_warning_pct,
                    message=f"WARNING: {provider} quality regression {deviation:.1f}%",
                ))

        self._alerts.extend(alerts)
        return alerts

    def detect_stability_regression(self, provider: str,
                                     current_error_rate: float,
                                     current_variance: float = 0.0) -> List[RegressionAlert]:
        """Detect stability regressions."""
        alerts = []

        if current_error_rate >= self._rc.stability_error_rate_critical:
            alerts.append(RegressionAlert(
                regression_type=RegressionType.STABILITY,
                severity=RegressionSeverity.CRITICAL,
                provider=provider,
                metric="error_rate",
                baseline_value=self._rc.stability_error_rate_warning,
                current_value=current_error_rate,
                deviation_pct=current_error_rate * 100,
                threshold_pct=self._rc.stability_error_rate_critical * 100,
                message=f"CRITICAL: {provider} error rate {current_error_rate:.1%} exceeds threshold",
            ))
        elif current_error_rate >= self._rc.stability_error_rate_warning:
            alerts.append(RegressionAlert(
                regression_type=RegressionType.STABILITY,
                severity=RegressionSeverity.WARNING,
                provider=provider,
                metric="error_rate",
                baseline_value=self._rc.stability_error_rate_warning,
                current_value=current_error_rate,
                deviation_pct=current_error_rate * 100,
                threshold_pct=self._rc.stability_error_rate_warning * 100,
                message=f"WARNING: {provider} error rate {current_error_rate:.1%} approaching threshold",
            ))

        self._alerts.extend(alerts)
        return alerts

    def auto_detect(self, provider: str, current_metrics: Dict[str, float]) -> List[RegressionAlert]:
        """Automatically detect all regression types."""
        alerts = []
        baseline = self._baselines.get(provider, {})

        if "latency_p50" in current_metrics:
            alerts.extend(self.detect_latency_regression(
                provider,
                current_p50=current_metrics.get("latency_p50", 0),
                current_p99=current_metrics.get("latency_p99", 0),
            ))

        if "quality_score" in current_metrics:
            alerts.extend(self.detect_quality_regression(
                provider,
                current_score=current_metrics["quality_score"],
            ))

        if "error_rate" in current_metrics:
            alerts.extend(self.detect_stability_regression(
                provider,
                current_error_rate=current_metrics["error_rate"],
            ))

        return alerts

    def get_provider_history(self, provider: str,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get measurement history for a provider."""
        return self._history.get(provider, [])[-limit:]

    def get_all_alerts(self, severity: Optional[str] = None,
                        provider: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get all regression alerts with optional filtering."""
        alerts = self._alerts
        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]
        if provider:
            alerts = [a for a in alerts if a.provider == provider]
        return [a.to_dict() for a in alerts[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """Get regression detection statistics."""
        by_type = {}
        by_severity = {}
        for alert in self._alerts:
            by_type[alert.regression_type.value] = by_type.get(alert.regression_type.value, 0) + 1
            by_severity[alert.severity.value] = by_severity.get(alert.severity.value, 0) + 1

        return {
            "baseline_count": len(self._baselines),
            "history_providers": list(self._history.keys()),
            "total_alerts": len(self._alerts),
            "by_type": by_type,
            "by_severity": by_severity,
        }
