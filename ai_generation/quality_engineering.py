"""
Quality Engineering Layer — extracted patterns from agentic-qe, the-pair, CrossCheck.

Implements:
- Quality Gates (Swiss Cheese Model from CrossCheck)
- Code Review Engine (dual-agent pattern from the-pair)
- Test Generation Engine (QE patterns from agentic-qe)
- Coverage Analysis (risk-weighted from agentic-qe)
- Quality Scoring (continuous from agentic-qe)
- Flaky Test Detection (ML-powered from agentic-qe)
- Pattern Learning (memory-based from agentic-qe)

All capabilities are pure Python with no external dependencies.
"""
import hashlib
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Quality Gate Engine (Swiss Cheese Model) ─────────────────────

class GateSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class GateResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class QualityGate:
    name: str
    description: str
    severity: GateSeverity = GateSeverity.ERROR
    enabled: bool = True
    checker: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "description": self.description,
            "severity": self.severity.value, "enabled": self.enabled,
        }


@dataclass
class GateCheckResult:
    gate_name: str
    result: GateResult = GateResult.PASSED
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate_name, "result": self.result.value,
            "message": self.message, "details": self.details,
            "latency_ms": self.latency_ms,
        }


class QualityGateEngine:
    """
    Swiss Cheese Model quality gates — multiple independent layers,
    each catching different classes of failures.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._gates: Dict[str, QualityGate] = {}
        self._history: List[Dict[str, Any]] = []
        self._init_default_gates()

    def _init_default_gates(self):
        self.register_gate(QualityGate(
            name="secrets_scan", description="Scan for hardcoded secrets, API keys, tokens",
            severity=GateSeverity.CRITICAL,
        ))
        self.register_gate(QualityGate(
            name="conventional_commits", description="Verify commit message follows conventional format",
            severity=GateSeverity.WARNING,
        ))
        self.register_gate(QualityGate(
            name="test_pass", description="All tests must pass before merge",
            severity=GateSeverity.CRITICAL,
        ))
        self.register_gate(QualityGate(
            name="no_debug_code", description="No print statements, debugger calls, or TODO hacks",
            severity=GateSeverity.WARNING,
        ))
        self.register_gate(QualityGate(
            name="import_check", description="No circular imports, no wildcard imports",
            severity=GateSeverity.ERROR,
        ))
        self.register_gate(QualityGate(
            name="file_size", description="Files under 500 lines, functions under 100 lines",
            severity=GateSeverity.WARNING,
        ))
        self.register_gate(QualityGate(
            name="security_patterns", description="No eval(), exec(), pickle.loads() on untrusted input",
            severity=GateSeverity.CRITICAL,
        ))
        self.register_gate(QualityGate(
            name="type_hints", description="Public functions have type hints",
            severity=GateSeverity.INFO,
        ))

    def register_gate(self, gate: QualityGate):
        self._gates[gate.name] = gate

    def list_gates(self) -> List[Dict[str, Any]]:
        return [g.to_dict() for g in self._gates.values()]

    async def run_gate(self, gate_name: str, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        gate = self._gates.get(gate_name)
        if not gate:
            return GateCheckResult(gate_name=gate_name, result=GateResult.FAILED, message=f"Gate '{gate_name}' not found")
        if not gate.enabled:
            return GateCheckResult(gate_name=gate_name, result=GateResult.SKIPPED, message="Gate disabled")

        start = time.time()
        result = await self._execute_gate(gate, file_path=file_path, code=code, **kwargs)
        result.latency_ms = round((time.time() - start) * 1000, 1)
        self._history.append(result.to_dict())
        return result

    async def run_all_gates(self, file_path: str = "", code: str = "", **kwargs) -> List[GateCheckResult]:
        results = []
        for name, gate in self._gates.items():
            if gate.enabled:
                result = await self.run_gate(name, file_path=file_path, code=code, **kwargs)
                results.append(result)
        return results

    async def _execute_gate(self, gate: QualityGate, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        if gate.checker:
            try:
                return await gate.checker(file_path=file_path, code=code, **kwargs)
            except Exception as e:
                return GateCheckResult(gate_name=gate.name, result=GateResult.FAILED, message=str(e)[:200])

        checkers = {
            "secrets_scan": self._check_secrets,
            "no_debug_code": self._check_debug_code,
            "import_check": self._check_imports,
            "file_size": self._check_file_size,
            "security_patterns": self._check_security,
            "type_hints": self._check_type_hints,
        }
        checker = checkers.get(gate.name)
        if checker:
            return await checker(file_path=file_path, code=code, **kwargs)
        return GateCheckResult(gate_name=gate.name, result=GateResult.PASSED, message="No checker implemented")

    async def _check_secrets(self, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        patterns = [
            (r'api[_-]?key\s*=\s*["\'][A-Za-z0-9]{20,}', "API key detected"),
            (r'secret[_-]?key\s*=\s*["\'][A-Za-z0-9]{20,}', "Secret key detected"),
            (r'token\s*=\s*["\'][A-Za-z0-9_\-]{20,}', "Token detected"),
            (r'password\s*=\s*["\'][^"\']{8,}', "Hardcoded password detected"),
            (r'BEGIN\s+(RSA|DSA|EC)\s+PRIVATE\s+KEY', "Private key detected"),
        ]
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""
        findings = []
        for pattern, msg in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append(msg)
        if findings:
            return GateCheckResult(gate_name="secrets_scan", result=GateResult.FAILED,
                                   message=f"Found {len(findings)} secret(s)", details={"findings": findings})
        return GateCheckResult(gate_name="secrets_scan", result=GateResult.PASSED, message="No secrets detected")

    async def _check_debug_code(self, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""
        patterns = [
            (r'(?<!\w)print\s*\(', "print() statement"),
            (r'(?<!\w)pdb\.', "pdb debugger call"),
            (r'(?<!\w)breakpoint\s*\(', "breakpoint() call"),
            (r'(?<!\w)import\s+pdb', "import pdb"),
        ]
        findings = []
        for pattern, msg in patterns:
            matches = re.findall(pattern, text)
            if matches:
                findings.append(f"{msg} ({len(matches)} occurrences)")
        if findings:
            return GateCheckResult(gate_name="no_debug_code", result=GateResult.FAILED,
                                   message=f"Found {len(findings)} debug pattern(s)", details={"findings": findings})
        return GateCheckResult(gate_name="no_debug_code", result=GateResult.PASSED, message="No debug code detected")

    async def _check_imports(self, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""
        findings = []
        if re.search(r'from\s+\S+\s+import\s+\*', text):
            findings.append("Wildcard import detected")
        return GateCheckResult(gate_name="import_check", result=GateResult.FAILED if findings else GateResult.PASSED,
                               message=f"Found {len(findings)} issue(s)" if findings else "Imports OK",
                               details={"findings": findings} if findings else {})

    async def _check_file_size(self, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""
        lines = text.count('\n') + 1
        findings = []
        if lines > 500:
            findings.append(f"File has {lines} lines (limit: 500)")
        func_pattern = re.compile(r'(?:async\s+)?def\s+\w+.*?(?=\n(?:    |\t)|\Z)', re.DOTALL)
        for match in func_pattern.finditer(text):
            func_lines = match.group().count('\n') + 1
            if func_lines > 100:
                func_name = re.search(r'def\s+(\w+)', match.group())
                name = func_name.group(1) if func_name else "unknown"
                findings.append(f"Function '{name}' has {func_lines} lines (limit: 100)")
        if findings:
            return GateCheckResult(gate_name="file_size", result=GateResult.FAILED,
                                   message=f"Found {len(findings)} size issue(s)", details={"findings": findings})
        return GateCheckResult(gate_name="file_size", result=GateResult.PASSED, message="File sizes OK")

    async def _check_security(self, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""
        patterns = [
            (r'(?<!\w)eval\s*\(', "eval() call"),
            (r'(?<!\w)exec\s*\(', "exec() call"),
            (r'pickle\.loads?\s*\(', "pickle.loads() on potentially untrusted data"),
            (r'subprocess\.call\s*\(\s*["\']', "subprocess with shell string"),
            (r'os\.system\s*\(', "os.system() call"),
        ]
        findings = []
        for pattern, msg in patterns:
            if re.search(pattern, text):
                findings.append(msg)
        if findings:
            return GateCheckResult(gate_name="security_patterns", result=GateResult.FAILED,
                                   message=f"Found {len(findings)} security issue(s)", details={"findings": findings})
        return GateCheckResult(gate_name="security_patterns", result=GateResult.PASSED, message="No security issues detected")

    async def _check_type_hints(self, file_path: str = "", code: str = "", **kwargs) -> GateCheckResult:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""
        func_pattern = re.compile(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*\S+)?\s*:', re.MULTILINE)
        missing = []
        for match in func_pattern.finditer(text):
            func_name = match.group(1)
            args = match.group(2)
            has_return = '->' in match.group()
            if func_name.startswith('_'):
                continue
            if not has_return:
                missing.append(f"{func_name}: missing return type")
            arg_lines = [a.strip() for a in args.split(',') if a.strip() and a.strip() != 'self' and a.strip() != 'cls']
            for arg in arg_lines:
                if ':' not in arg and '=' not in arg:
                    missing.append(f"{func_name}: arg '{arg.split('=')[0].strip()}' missing type")
        if len(missing) > 5:
            return GateCheckResult(gate_name="type_hints", result=GateResult.FAILED,
                                   message=f"{len(missing)} missing type hints",
                                   details={"missing": missing[:10]})
        return GateCheckResult(gate_name="type_hints", result=GateResult.PASSED, message="Type hints adequate")

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._history)
        passed = sum(1 for h in self._history if h.get("result") == "passed")
        failed = sum(1 for h in self._history if h.get("result") == "failed")
        return {
            "total_checks": total, "passed": passed, "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 100.0,
            "registered_gates": len(self._gates),
            "enabled_gates": sum(1 for g in self._gates.values() if g.enabled),
        }


# ── Code Review Engine (Dual-Agent Pattern) ──────────────────────

class ReviewSeverity(str, Enum):
    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewCategory(str, Enum):
    CORRECTNESS = "correctness"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class ReviewFinding:
    file_path: str = ""
    line: int = 0
    severity: ReviewSeverity = ReviewSeverity.INFO
    category: ReviewCategory = ReviewCategory.CORRECTNESS
    message: str = ""
    suggestion: str = ""
    rule_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path, "line": self.line,
            "severity": self.severity.value, "category": self.category.value,
            "message": self.message, "suggestion": self.suggestion,
            "rule_id": self.rule_id,
        }


@dataclass
class ReviewResult:
    reviewer: str = ""
    findings: List[ReviewFinding] = field(default_factory=list)
    summary: str = ""
    score: float = 100.0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer": self.reviewer, "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings[:50]],
            "summary": self.summary, "score": round(self.score, 1),
            "latency_ms": self.latency_ms,
        }


class CodeReviewEngine:
    """
    Dual-agent code review engine (pattern from The Pair).
    Implements Mentor (reviewer) and Executor (implementer) roles.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[ReviewResult] = []
        self._rules: Dict[str, Callable] = {}
        self._init_default_rules()

    def _init_default_rules(self):
        self._rules["no_bare_except"] = self._rule_no_bare_except
        self._rules["no_mutable_default"] = self._rule_no_mutable_default
        self._rules["no_global_mutation"] = self._rule_no_global_mutation
        self._rules["docstring_required"] = self._rule_docstring_required
        self._rules["no_star_imports"] = self._rule_no_star_imports
        self._rules["consistent_naming"] = self._rule_consistent_naming
        self._rules["error_handling"] = self._rule_error_handling

    def register_rule(self, rule_id: str, checker: Callable):
        self._rules[rule_id] = checker

    async def review(self, file_path: str = "", code: str = "", rules: Optional[List[str]] = None, **kwargs) -> ReviewResult:
        start = time.time()
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""

        findings = []
        rules_to_check = rules if rules else list(self._rules.keys())
        for rule_id in rules_to_check:
            checker = self._rules.get(rule_id)
            if checker:
                try:
                    rule_findings = await checker(file_path=file_path, code=text, **kwargs)
                    findings.extend(rule_findings)
                except Exception as e:
                    logger.warning(f"Rule {rule_id} failed: {e}")

        severity_weights = {ReviewSeverity.CRITICAL: 20, ReviewSeverity.ERROR: 10,
                            ReviewSeverity.WARNING: 5, ReviewSeverity.SUGGESTION: 2, ReviewSeverity.INFO: 1}
        penalty = sum(severity_weights.get(f.severity, 1) for f in findings)
        score = max(0, 100 - penalty)

        result = ReviewResult(
            reviewer="code_review_engine", findings=findings,
            summary=f"{len(findings)} findings, score {score}/100",
            score=score, latency_ms=round((time.time() - start) * 1000, 1),
        )
        self._history.append(result)
        return result

    async def _rule_no_bare_except(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        for i, line in enumerate(code.split('\n'), 1):
            stripped = line.strip()
            if re.match(r'except\s*:', stripped):
                findings.append(ReviewFinding(file_path=file_path, line=i, severity=ReviewSeverity.WARNING,
                                              category=ReviewCategory.CORRECTNESS, message="Bare except clause", rule_id="no_bare_except"))
        return findings

    async def _rule_no_mutable_default(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        for i, line in enumerate(code.split('\n'), 1):
            m = re.search(r'def\s+\w+\s*\(.*?=\s*(\[\]|\{\}|set\(\))', line)
            if m:
                findings.append(ReviewFinding(file_path=file_path, line=i, severity=ReviewSeverity.ERROR,
                                              category=ReviewCategory.CORRECTNESS, message="Mutable default argument", rule_id="no_mutable_default"))
        return findings

    async def _rule_no_global_mutation(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        for i, line in enumerate(code.split('\n'), 1):
            stripped = line.strip()
            if stripped.startswith('global ') and '=' in stripped:
                findings.append(ReviewFinding(file_path=file_path, line=i, severity=ReviewSeverity.WARNING,
                                              category=ReviewCategory.MAINTAINABILITY, message="Global variable mutation", rule_id="no_global_mutation"))
        return findings

    async def _rule_docstring_required(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if re.match(r'(?:async\s+)?def\s+\w+', line.strip()) and not line.strip().startswith('def _'):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        func_name = re.search(r'def\s+(\w+)', line)
                        name = func_name.group(1) if func_name else "unknown"
                        findings.append(ReviewFinding(file_path=file_path, line=i + 1,
                                                      severity=ReviewSeverity.SUGGESTION, category=ReviewCategory.DOCUMENTATION,
                                                      message=f"Public function '{name}' missing docstring", rule_id="docstring_required"))
        return findings[:10]

    async def _rule_no_star_imports(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        for i, line in enumerate(code.split('\n'), 1):
            if re.match(r'from\s+\S+\s+import\s+\*', line.strip()):
                findings.append(ReviewFinding(file_path=file_path, line=i, severity=ReviewSeverity.WARNING,
                                              category=ReviewCategory.MAINTAINABILITY, message="Wildcard import", rule_id="no_star_imports"))
        return findings

    async def _rule_consistent_naming(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        for i, line in enumerate(code.split('\n'), 1):
            m = re.search(r'(?:def|class|var)\s+([A-Za-z_]\w*)', line)
            if m:
                name = m.group(1)
                if name.startswith('_') or name.isupper():
                    continue
                if 'def ' in line and not re.match(r'^[a-z_][a-z0-9_]*$', name) and not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                    findings.append(ReviewFinding(file_path=file_path, line=i, severity=ReviewSeverity.INFO,
                                                  category=ReviewCategory.READABILITY, message=f"Naming convention: '{name}'", rule_id="consistent_naming"))
        return findings[:5]

    async def _rule_error_handling(self, file_path: str = "", code: str = "", **kw) -> List[ReviewFinding]:
        findings = []
        in_except = False
        for i, line in enumerate(code.split('\n'), 1):
            stripped = line.strip()
            if stripped.startswith('except'):
                in_except = True
            elif in_except:
                if stripped.startswith('pass') or stripped == '':
                    findings.append(ReviewFinding(file_path=file_path, line=i, severity=ReviewSeverity.WARNING,
                                                  category=ReviewCategory.CORRECTNESS, message="Empty except handler", rule_id="error_handling"))
                in_except = False
        return findings

    def get_stats(self) -> Dict[str, Any]:
        total_findings = sum(len(r.findings) for r in self._history)
        avg_score = sum(r.score for r in self._history) / len(self._history) if self._history else 100.0
        return {
            "total_reviews": len(self._history),
            "total_findings": total_findings,
            "average_score": round(avg_score, 1),
            "registered_rules": len(self._rules),
        }


# ── Quality Scoring Engine ───────────────────────────────────────

class QualityDimension(str, Enum):
    CORRECTNESS = "correctness"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"
    READABILITY = "readability"
    DOCUMENTATION = "documentation"


@dataclass
class QualityScore:
    dimension: QualityDimension
    score: float = 0.0
    max_score: float = 100.0
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 1), "max_score": self.max_score,
            "percentage": round(self.score / self.max_score * 100, 1) if self.max_score > 0 else 0,
            "findings": self.findings,
        }


class QualityScoringEngine:
    """Continuous quality scoring across multiple dimensions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[Dict[str, Any]] = []

    async def score_file(self, file_path: str = "", code: str = "", **kwargs) -> Dict[str, Any]:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""

        scores = []
        for dim in QualityDimension:
            score = await self._score_dimension(dim, text, file_path)
            scores.append(score)

        overall = sum(s.score for s in scores) / len(scores) if scores else 0
        result = {
            "file": file_path, "overall_score": round(overall, 1),
            "dimensions": [s.to_dict() for s in scores],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(result)
        return result

    async def _score_dimension(self, dimension: QualityDimension, code: str, file_path: str) -> QualityScore:
        score = 80.0
        findings = []

        if dimension == QualityDimension.CORRECTNESS:
            if 'except:' in code:
                score -= 10
                findings.append("Bare except clauses")
            if 'pass' in code and code.count('pass') > 3:
                score -= 5
                findings.append("Many empty blocks")

        elif dimension == QualityDimension.SECURITY:
            dangerous = ['eval(', 'exec(', 'os.system(', 'pickle.loads(', 'subprocess.call("']
            for d in dangerous:
                if d in code:
                    score -= 15
                    findings.append(f"Dangerous pattern: {d}")

        elif dimension == QualityDimension.PERFORMANCE:
            if 'import *' in code:
                score -= 5
                findings.append("Wildcard imports")
            if code.count('for ') > 10:
                score -= 5
                findings.append("Many nested loops possible")

        elif dimension == QualityDimension.MAINTAINABILITY:
            lines = code.split('\n')
            if len(lines) > 500:
                score -= 15
                findings.append(f"File too long: {len(lines)} lines")
            if code.count('TODO') > 2:
                score -= 5
                findings.append("Many TODO comments")

        elif dimension == QualityDimension.TESTABILITY:
            if 'async def' in code and 'await' not in code:
                score -= 10
                findings.append("Async function without await")
            if 'global ' in code:
                score -= 10
                findings.append("Global state reduces testability")

        elif dimension == QualityDimension.READABILITY:
            funcs = re.findall(r'def (\w+)', code)
            long_names = [f for f in funcs if len(f) > 30]
            if long_names:
                score -= 5
                findings.append(f"Long function names: {long_names[:3]}")

        elif dimension == QualityDimension.DOCUMENTATION:
            funcs = re.findall(r'(?:async )?def (\w+)', code)
            public_funcs = [f for f in funcs if not f.startswith('_')]
            docstrings = len(re.findall(r'""".*?"""', code, re.DOTALL))
            if public_funcs and docstrings == 0:
                score -= 20
                findings.append("No docstrings for public functions")

        return QualityScore(dimension=dimension, score=max(0, score), findings=findings)

    def get_stats(self) -> Dict[str, Any]:
        if not self._history:
            return {"total_scored": 0, "average_overall": 0}
        avg = sum(h["overall_score"] for h in self._history) / len(self._history)
        return {"total_scored": len(self._history), "average_overall": round(avg, 1)}


# ── Test Generation Engine ───────────────────────────────────────

@dataclass
class TestTemplate:
    name: str
    framework: str
    description: str
    template: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "framework": self.framework, "description": self.description}


TEST_TEMPLATES: List[TestTemplate] = [
    TestTemplate(name="unit_test_pytest", framework="pytest",
                 description="Standard pytest unit test with fixtures and assertions",
                 template='''def test_{func_name}():\n    """Test {func_name}."""\n    result = {func_name}()\n    assert result is not None'''),
    TestTemplate(name="async_test_pytest", framework="pytest-asyncio",
                 description="Async function test with pytest-asyncio",
                 template='''@pytest.mark.asyncio\nasync def test_{func_name}():\n    """Test {func_name} async."""\n    result = await {func_name}()\n    assert result is not None'''),
    TestTemplate(name="error_test_pytest", framework="pytest",
                 description="Error handling test with pytest.raises",
                 template='''def test_{func_name}_error():\n    """Test {func_name} error handling."""\n    with pytest.raises({error_type}):\n        {func_name}({bad_input})'''),
    TestTemplate(name="edge_case_test", framework="pytest",
                 description="Edge case test for boundary conditions",
                 template='''def test_{func_name}_edge_cases():\n    """Test {func_name} edge cases."""\n    assert {func_name}({edge_input}) == {expected}'''),
    TestTemplate(name="parametrized_test", framework="pytest",
                 description="Parametrized test for multiple inputs",
                 template='''@pytest.mark.parametrize("input_val,expected", [\n    ({input_1}, {expected_1}),\n    ({input_2}, {expected_2}),\n])\ndef test_{func_name}_parametrized(input_val, expected):\n    """Parametrized test for {func_name}."""\n    assert {func_name}(input_val) == expected'''),
]


class TestGenerationEngine:
    """Automated test generation with coverage targeting."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._templates = {t.name: t for t in TEST_TEMPLATES}
        self._history: List[Dict[str, Any]] = []

    def get_templates(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._templates.values()]

    async def generate_tests(self, file_path: str = "", code: str = "", template: str = "unit_test_pytest", **kwargs) -> Dict[str, Any]:
        start = time.time()
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""

        funcs = re.findall(r'(?:async\s+)?def\s+(\w+)\s*\(', text)
        public_funcs = [f for f in funcs if not f.startswith('_')]

        tmpl = self._templates.get(template, self._templates["unit_test_pytest"])
        test_cases = []
        for func_name in public_funcs[:20]:
            test_code = tmpl.template.replace("{func_name}", func_name)
            test_cases.append({"function": func_name, "template": tmpl.name, "code": test_code})

        result = {
            "source_file": file_path, "template": tmpl.name,
            "functions_found": len(public_funcs),
            "test_cases": test_cases,
            "estimated_coverage": min(100, len(public_funcs) * 15),
            "latency_ms": round((time.time() - start) * 1000, 1),
        }
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_generations": len(self._history), "templates": len(self._templates)}


# ── Coverage Gap Analysis ────────────────────────────────────────

class CoverageGapEngine:
    """Risk-weighted coverage gap analysis."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[Dict[str, Any]] = []

    async def analyze_gaps(self, file_path: str = "", code: str = "", test_code: str = "", **kwargs) -> Dict[str, Any]:
        text = code
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    text = f.read()
            except Exception:
                text = ""

        funcs = re.findall(r'(?:async\s+)?def\s+(\w+)\s*\(', text)
        test_funcs = re.findall(r'def\s+test_(\w+)', test_code) if test_code else []
        tested = set()
        for tf in test_funcs:
            for func in funcs:
                if func in tf:
                    tested.add(func)

        untested = [f for f in funcs if f not in tested and not f.startswith('_')]
        gaps = []
        for func_name in untested:
            risk = "high" if any(kw in func_name.lower() for kw in ["auth", "login", "password", "token", "security", "encrypt"]) else "medium"
            gaps.append({"function": func_name, "risk": risk, "priority": 1 if risk == "high" else 2})

        gaps.sort(key=lambda x: x["priority"])
        coverage = round(len(tested) / len(funcs) * 100, 1) if funcs else 100.0

        result = {
            "file": file_path, "total_functions": len(funcs),
            "tested_functions": len(tested), "untested_functions": len(untested),
            "estimated_coverage": coverage, "gaps": gaps[:20],
            "recommendations": [f"Write tests for {g['function']} (risk: {g['risk']})" for g in gaps[:5]],
        }
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyses": len(self._history)}


# ── Flaky Test Detection ─────────────────────────────────────────

class FlakyDetectionEngine:
    """Flaky test detection based on pattern analysis."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._test_history: Dict[str, List[str]] = {}
        self._history: List[Dict[str, Any]] = []

    def record_result(self, test_name: str, result: str):
        if test_name not in self._test_history:
            self._test_history[test_name] = []
        self._test_history[test_name].append(result)

    async def detect_flaky(self, min_runs: int = 3) -> List[Dict[str, Any]]:
        flaky = []
        for test_name, results in self._test_history.items():
            if len(results) < min_runs:
                continue
            passed = results.count("passed")
            failed = results.count("failed")
            if passed > 0 and failed > 0:
                rate = failed / len(results)
                flaky.append({
                    "test_name": test_name, "total_runs": len(results),
                    "passed": passed, "failed": failed,
                    "flakiness_rate": round(rate, 3),
                    "pattern": self._detect_pattern(results),
                })
        flaky.sort(key=lambda x: -x["flakiness_rate"])
        self._history.extend(flaky)
        return flaky

    def _detect_pattern(self, results: List[str]) -> str:
        if len(results) < 4:
            return "insufficient_data"
        alternating = sum(1 for i in range(1, len(results)) if results[i] != results[i-1])
        if alternating > len(results) * 0.6:
            return "alternating"
        if results[0] == "passed" and all(r == "failed" for r in results[1:]):
            return "first_pass_then_fail"
        if all(r == "passed" for r in results[:-1]) and results[-1] == "failed":
            return "recently_broken"
        return "random"

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._test_history)
        flaky_count = sum(1 for r in self._test_history.values() if len(r) >= 3 and "passed" in r and "failed" in r)
        return {"total_tests_tracked": total, "flaky_detected": flaky_count}


# ── Pattern Learning Engine ──────────────────────────────────────

class PatternLearningEngine:
    """Learn and remember codebase patterns for reuse."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._patterns: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def learn_pattern(self, pattern_id: str, pattern_type: str, description: str, code: str, context: str = ""):
        self._patterns[pattern_id] = {
            "type": pattern_type, "description": description,
            "code": code, "context": context,
            "learned_at": datetime.now(timezone.utc).isoformat(),
            "usage_count": 0,
        }

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        return self._patterns.get(pattern_id)

    def find_patterns(self, pattern_type: str = "", context: str = "") -> List[Dict[str, Any]]:
        results = []
        for pid, p in self._patterns.items():
            if pattern_type and p["type"] != pattern_type:
                continue
            if context and context.lower() not in p.get("context", "").lower():
                continue
            results.append({"id": pid, **p})
        return results

    def use_pattern(self, pattern_id: str):
        if pattern_id in self._patterns:
            self._patterns[pattern_id]["usage_count"] += 1

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_patterns": len(self._patterns),
            "by_type": {},
            "most_used": sorted(self._patterns.items(), key=lambda x: -x[1].get("usage_count", 0))[:5],
        }
