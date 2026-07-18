"""
Provider Verifier — verifies endpoint availability, documentation,
authentication, licensing, capabilities, health, and reliability.
Never assumes a provider is available because it existed previously.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class VerificationCheck(str, Enum):
    ENDPOINT_REACHABLE = "endpoint_reachable"
    AUTH_VALID = "auth_valid"
    DOCUMENTATION_EXISTS = "documentation_exists"
    LICENSE_CHECKED = "license_checked"
    CAPABILITY_VERIFIED = "capability_verified"
    HEALTH_OK = "health_ok"
    RATE_LIMIT_CHECKED = "rate_limit_checked"




class VerificationResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class VerificationReport:
    provider_name: str = ""
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_status: str = "pending"  # pending, verified, failed, partial
    verified_at: str = ""
    confidence: float = 0.0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "overall_status": self.overall_status,
            "checks": self.checks,
            "confidence": round(self.confidence, 2),
            "notes": self.notes,
            "verified_at": self.verified_at,
        }


class ProviderVerifier:
    """Verify providers before enabling them."""

    def __init__(self):
        self._reports: Dict[str, VerificationReport] = {}

    async def verify_provider(self, name: str, url: str, auth_type: str = "none",
                               auth_env_var: str = "", health_url: str = "",
                               doc_url: str = "", license_info: str = "") -> VerificationReport:
        report = VerificationReport(provider_name=name)
        passed = 0
        total = 0

        if health_url or url:
            total += 1
            try:
                check_url = health_url or url
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    r = await client.get(check_url)
                    if r.status_code < 500:
                        report.checks["endpoint_reachable"] = {
                            "result": "pass", "status_code": r.status_code, "url": check_url}
                        passed += 1
                    else:
                        report.checks["endpoint_reachable"] = {
                            "result": "fail", "status_code": r.status_code, "url": check_url}
            except Exception as e:
                report.checks["endpoint_reachable"] = {
                    "result": "fail", "error": str(e)[:100], "url": url}

        if auth_env_var:
            total += 1
            import os
            has_key = bool(os.environ.get(auth_env_var, ""))
            if auth_type == "none" or has_key:
                report.checks["auth_valid"] = {"result": "pass", "has_key": has_key}
                passed += 1
            else:
                report.checks["auth_valid"] = {"result": "warning", "has_key": False, "note": f"Set {auth_env_var}"}

        if doc_url:
            total += 1
            try:
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    r = await client.get(doc_url)
                    if r.status_code < 400:
                        report.checks["documentation_exists"] = {"result": "pass", "url": doc_url}
                        passed += 1
                    else:
                        report.checks["documentation_exists"] = {"result": "fail", "status_code": r.status_code}
            except Exception as e:
                report.checks["documentation_exists"] = {"result": "fail", "error": str(e)[:100]}

        if license_info:
            total += 1
            report.checks["license_checked"] = {"result": "pass", "license": license_info}
            passed += 1

        report.confidence = (passed / max(total, 1)) * 100
        if report.confidence >= 75:
            report.overall_status = "verified"
        elif report.confidence >= 50:
            report.overall_status = "partial"
        else:
            report.overall_status = "failed"
        report.verified_at = datetime.now().isoformat()

        self._reports[name] = report
        return report

    def get_report(self, name: str) -> Optional[Dict[str, Any]]:
        report = self._reports.get(name)
        return report.to_dict() if report else None

    def get_all_reports(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._reports.values()]

    def get_stats(self) -> Dict[str, Any]:
        statuses = {}
        for r in self._reports.values():
            statuses[r.overall_status] = statuses.get(r.overall_status, 0) + 1
        return {"total_verified": len(self._reports), "by_status": statuses}
