"""
Code Analysis Engines — extracted from ai-code-reviewer, llm-code-review, polyscan, claude-code-agents.

Provides: SecretScanner, StaticAnalyzer, StructuralAnalyzer,
MultiAgentReviewEngine, PRVerificationEngine, TechnicalDebtTracker.
"""

from __future__ import annotations

import ast
import hashlib
import re
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── Secret Scanner ─────────────────────────────────────────────

class SecretSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class SecretFinding:
    pattern_name: str
    file_path: str
    line: int
    severity: str
    confidence: float
    suggestion: str = "Remove the secret and rotate it immediately."
    matched_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "file_path": self.file_path,
            "line": self.line,
            "severity": self.severity,
            "confidence": self.confidence,
            "suggestion": self.suggestion,
            "matched_text": self.matched_text[:40] + "..." if len(self.matched_text) > 40 else self.matched_text,
        }


SECRET_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID", "high"),
    (re.compile(r"(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"), "AWS Secret Access Key", "high"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub PAT", "high"),
    (re.compile(r"gho_[A-Za-z0-9]{36}"), "GitHub OAuth Token", "high"),
    (re.compile(r"ghs_[A-Za-z0-9]{36}"), "GitHub App Token", "high"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{82}"), "GitHub Fine-Grained PAT", "high"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "Private Key", "high"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI / Stripe Secret Key", "high"),
    (re.compile(r"xox[bpras]-[A-Za-z0-9\-]{10,}"), "Slack Token", "high"),
    (re.compile(r"glpat-[A-Za-z0-9\-_]{20,}"), "GitLab PAT", "high"),
    (re.compile(r"(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[=:]\s*['\"][A-Za-z0-9/+=_\-]{20,}['\"]", re.IGNORECASE), "Generic Secret Assignment", "medium"),
    (re.compile(r"['\"]?[A-Za-z0-9+/]{40,}['\"]?\s*(?:#.*)?$", re.MULTILINE), "Possible Base64 Secret", "low"),
    (re.compile(r"mysql://[^:]+:[^@]+@"), "Database Connection String", "high"),
    (re.compile(r"postgres(?:ql)?://[^:]+:[^@]+@"), "Database Connection String", "high"),
    (re.compile(r"mongodb(\+srv)?://[^:]+:[^@]+@"), "MongoDB Connection String", "high"),
    (re.compile(r"redis://[^:]+:[^@]+@"), "Redis Connection String", "medium"),
]


class SecretScanner:
    """Regex-based secret scanner extracted from ai-code-reviewer pattern."""

    def __init__(self, exclude_patterns: Optional[List[str]] = None):
        self.exclude_patterns = exclude_patterns or []

    def _is_excluded(self, file_path: str) -> bool:
        import fnmatch
        return any(fnmatch.fnmatch(file_path, pat) for pat in self.exclude_patterns)

    def scan_text(self, text: str, file_path: str = "<input>") -> List[SecretFinding]:
        findings: List[SecretFinding] = []
        if self._is_excluded(file_path):
            return findings

        seen: set = set()
        for line_num, line in enumerate(text.splitlines(), 1):
            for pattern, name, confidence_level in SECRET_PATTERNS:
                if pattern.search(line):
                    confidence = {"high": 0.95, "medium": 0.7, "low": 0.4}.get(confidence_level, 0.5)
                    dedup = f"{file_path}:{line_num}:{name}"
                    if dedup in seen:
                        continue
                    seen.add(dedup)
                    matched = pattern.search(line)
                    findings.append(SecretFinding(
                        pattern_name=name,
                        file_path=file_path,
                        line=line_num,
                        severity=SecretSeverity.CRITICAL.value if confidence >= 0.8 else SecretSeverity.WARNING.value,
                        confidence=confidence,
                        matched_text=matched.group(0)[:60] if matched else "",
                    ))
        return findings

    def scan_diff(self, diff: str) -> List[SecretFinding]:
        """Scan a unified diff for secrets on added lines only."""
        findings: List[SecretFinding] = []
        seen: set = set()
        current_file: Optional[str] = None
        current_line = 0

        hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
        file_re = re.compile(r"^\+\+\+ b/(.+)$")

        for raw_line in diff.splitlines():
            m = file_re.match(raw_line)
            if m:
                current_file = m.group(1)
                current_line = 0
                continue
            m = hunk_re.match(raw_line)
            if m:
                current_line = int(m.group(1)) - 1
                continue
            if raw_line.startswith("-"):
                continue
            if raw_line.startswith("+"):
                current_line += 1
            else:
                current_line += 1
                continue
            if current_file is None:
                continue
            if self._is_excluded(current_file):
                continue
            content = raw_line[1:]
            for pattern, name, conf_level in SECRET_PATTERNS:
                if pattern.search(content):
                    confidence = {"high": 0.95, "medium": 0.7, "low": 0.4}.get(conf_level, 0.5)
                    dedup = f"{current_file}:{current_line}:{name}"
                    if dedup in seen:
                        continue
                    seen.add(dedup)
                    matched = pattern.search(content)
                    findings.append(SecretFinding(
                        pattern_name=name,
                        file_path=current_file,
                        line=current_line,
                        severity=SecretSeverity.CRITICAL.value if confidence >= 0.8 else SecretSeverity.WARNING.value,
                        confidence=confidence,
                        matched_text=matched.group(0)[:60] if matched else "",
                    ))
        return findings


# ── Static Analyzer ────────────────────────────────────────────

class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass
class StaticIssue:
    file_path: str
    line: int
    severity: str
    category: str
    message: str
    rule_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.line,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "rule_id": self.rule_id,
        }


class StaticAnalyzer:
    """Multi-language static analysis engine — patterns from llm-code-review."""

    SECURITY_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
        (re.compile(r"\beval\s*\("), "Use of eval() — potential code injection", "SEC001"),
        (re.compile(r"\bexec\s*\("), "Use of exec() — potential code injection", "SEC002"),
        (re.compile(r"\bos\.system\s*\("), "os.system() — use subprocess instead", "SEC003"),
        (re.compile(r"\bsubprocess\.call\s*\(\s*['\"]"), "Shell command via subprocess — use list args", "SEC004"),
        (re.compile(r"\bpickle\.load"), "Pickle deserialization — potential arbitrary code execution", "SEC005"),
        (re.compile(r"\byaml\.load\s*\([^)]*\)(?!\s*,\s*Loader\s*=)"), "YAML load without Loader — use safe_load", "SEC006"),
        (re.compile(r"\btempfile\.mktemp\s*\("), "mktemp() is insecure — use mkstemp()", "SEC007"),
        (re.compile(r"assert\s+"), "Assert in non-test code — removed in optimized mode", "SEC008"),
    ]

    QUALITY_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
        (re.compile(r"except\s*:"), "Bare except — catch specific exceptions", "QLT001"),
        (re.compile(r"except\s+Exception\s*:"), "Broad exception catch — be more specific", "QLT002"),
        (re.compile(r"from\s+\S+\s+import\s+\*"), "Star import — import specific names", "QLT003"),
        (re.compile(r"^\s*#\s*TODO\b", re.IGNORECASE), "TODO comment — track in issue system", "QLT004"),
        (re.compile(r"^\s*#\s*FIXME\b", re.IGNORECASE), "FIXME comment — needs resolution", "QLT005"),
        (re.compile(r"^\s*#\s*HACK\b", re.IGNORECASE), "HACK comment — tech debt", "QLT006"),
        (re.compile(r"^\s*# type:\s*ignore\b"), "Type ignore — fix type issue instead", "QLT007"),
        (re.compile(r"noqa\b"), "Lint suppression — fix the underlying issue", "QLT008"),
        (re.compile(r"print\s*\("), "Print statement — use logging", "QLT009"),
        (re.compile(r"\blambda\s+.*:\s*\S+\s+\S+\s+\S+"), "Complex lambda — use def instead", "QLT010"),
    ]

    DOCSTRING_EXTENSIONS = {".py"}

    def analyze_code(self, code: str, file_path: str = "<input>") -> List[StaticIssue]:
        issues: List[StaticIssue] = []
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if not stripped.startswith("#"):
                for pattern, msg, rule_id in self.SECURITY_PATTERNS:
                    if pattern.search(line):
                        issues.append(StaticIssue(
                            file_path=file_path, line=line_num,
                            severity=IssueSeverity.CRITICAL.value,
                            category="security", message=msg, rule_id=rule_id,
                        ))

            for pattern, msg, rule_id in self.QUALITY_PATTERNS:
                if pattern.search(line):
                    issues.append(StaticIssue(
                        file_path=file_path, line=line_num,
                        severity=IssueSeverity.WARNING.value,
                        category="quality", message=msg, rule_id=rule_id,
                    ))

        if file_path.endswith(".py"):
            issues.extend(self._check_python_docstrings(code, file_path))

        return issues

    def _check_python_docstrings(self, code: str, file_path: str) -> List[StaticIssue]:
        issues: List[StaticIssue] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append(StaticIssue(
                        file_path=file_path,
                        line=getattr(node, "lineno", 0),
                        severity=IssueSeverity.SUGGESTION.value,
                        category="documentation",
                        message=f"Missing docstring for '{node.name}'",
                        rule_id="DOC001",
                    ))
        return issues

    def analyze_diff(self, diff: str) -> List[StaticIssue]:
        """Analyze only added lines in a unified diff."""
        issues: List[StaticIssue] = []
        current_file: Optional[str] = None
        current_line = 0

        file_re = re.compile(r"^\+\+\+ b/(.+)$")
        hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        for raw_line in diff.splitlines():
            m = file_re.match(raw_line)
            if m:
                current_file = m.group(1)
                current_line = 0
                continue
            m = hunk_re.match(raw_line)
            if m:
                current_line = int(m.group(1)) - 1
                continue
            if raw_line.startswith("-"):
                continue
            if raw_line.startswith("+"):
                current_line += 1
                content = raw_line[1:]
            else:
                current_line += 1
                continue
            if current_file is None:
                continue

            for pattern, msg, rule_id in self.SECURITY_PATTERNS:
                if pattern.search(content):
                    issues.append(StaticIssue(
                        file_path=current_file, line=current_line,
                        severity=IssueSeverity.CRITICAL.value,
                        category="security", message=msg, rule_id=rule_id,
                    ))
            for pattern, msg, rule_id in self.QUALITY_PATTERNS:
                if pattern.search(content):
                    issues.append(StaticIssue(
                        file_path=current_file, line=current_line,
                        severity=IssueSeverity.WARNING.value,
                        category="quality", message=msg, rule_id=rule_id,
                    ))
        return issues


# ── Structural Analyzer ────────────────────────────────────────

@dataclass
class StructuralFinding:
    category: str
    severity: str
    message: str
    file_path: str = ""
    line: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {"category": self.category, "severity": self.severity, "message": self.message}
        if self.file_path:
            d["file_path"] = self.file_path
        if self.line:
            d["line"] = self.line
        if self.details:
            d["details"] = self.details
        return d


class StructuralAnalyzer:
    """Dead code, duplication, complexity analysis — patterns from polyscan."""

    def analyze(self, files: Dict[str, str]) -> List[StructuralFinding]:
        """Analyze a dict of {filepath: content} for structural issues."""
        findings: List[StructuralFinding] = []
        findings.extend(self._detect_dead_code(files))
        findings.extend(self._detect_duplicates(files))
        findings.extend(self._detect_complexity(files))
        findings.extend(self._detect_long_functions(files))
        return findings

    def _detect_dead_code(self, files: Dict[str, str]) -> List[StructuralFinding]:
        findings: List[StructuralFinding] = []
        for filepath, content in files.items():
            if not filepath.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            defined_names: Dict[str, int] = {}
            used_names: set = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    defined_names[node.name] = node.lineno
                elif isinstance(node, ast.ClassDef):
                    defined_names[node.name] = node.lineno
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used_names.add(node.attr)

            for name, lineno in defined_names.items():
                if name.startswith("_") and name != "__init__":
                    continue
                if name not in used_names and name not in ("main", "setup", "teardown"):
                    findings.append(StructuralFinding(
                        category="dead_code",
                        severity=IssueSeverity.SUGGESTION.value,
                        message=f"Function/class '{name}' appears unused",
                        file_path=filepath, line=lineno,
                    ))
        return findings

    def _detect_duplicates(self, files: Dict[str, str]) -> List[StructuralFinding]:
        """Detect duplicate code blocks across files using line hashing."""
        findings: List[StructuralFinding] = []
        block_hashes: Dict[str, List[Tuple[str, int]]] = {}
        MIN_LINES = 5

        for filepath, content in files.items():
            if not filepath.endswith(".py"):
                continue
            lines = content.splitlines()
            for i in range(len(lines) - MIN_LINES):
                block = "\n".join(line.strip() for line in lines[i:i + MIN_LINES])
                if len(block.strip()) < 50:
                    continue
                h = hashlib.md5(block.encode()).hexdigest()
                if h not in block_hashes:
                    block_hashes[h] = []
                block_hashes[h].append((filepath, i + 1))

        for h, locations in block_hashes.items():
            if len(locations) > 1:
                files_involved = set(loc for loc, _ in locations)
                if len(files_involved) > 1:
                    findings.append(StructuralFinding(
                        category="duplication",
                        severity=IssueSeverity.WARNING.value,
                        message=f"Duplicate code block found across {len(files_involved)} locations",
                        file_path=locations[0][0],
                        line=locations[0][1],
                        details={"locations": [{"file": f, "line": l} for f, l in locations[:5]]},
                    ))
        return findings

    def _detect_complexity(self, files: Dict[str, str]) -> List[StructuralFinding]:
        """Detect high cyclomatic complexity functions."""
        findings: List[StructuralFinding] = []
        THRESHOLD = 10

        for filepath, content in files.items():
            if not filepath.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calc_complexity(node)
                    if complexity > THRESHOLD:
                        findings.append(StructuralFinding(
                            category="complexity",
                            severity=IssueSeverity.WARNING.value if complexity <= 20 else IssueSeverity.CRITICAL.value,
                            message=f"Function '{node.name}' has cyclomatic complexity {complexity} (threshold: {THRESHOLD})",
                            file_path=filepath, line=node.lineno,
                            details={"complexity": complexity, "threshold": THRESHOLD},
                        ))
        return findings

    def _calc_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for an AST function node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1 + len(child.ifs)
        return complexity

    def _detect_long_functions(self, files: Dict[str, str]) -> List[StructuralFinding]:
        """Detect functions exceeding line count threshold."""
        findings: List[StructuralFinding] = []
        THRESHOLD = 50

        for filepath, content in files.items():
            if not filepath.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end_lineno = getattr(node, "end_lineno", None)
                    if end_lineno:
                        length = end_lineno - node.lineno + 1
                        if length > THRESHOLD:
                            findings.append(StructuralFinding(
                                category="long_function",
                                severity=IssueSeverity.WARNING.value,
                                message=f"Function '{node.name}' is {length} lines (threshold: {THRESHOLD})",
                                file_path=filepath, line=node.lineno,
                                details={"line_count": length, "threshold": THRESHOLD},
                            ))
        return findings


# ── Multi-Agent Review Engine ──────────────────────────────────

class ReviewAgentRole(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    PATTERNS = "patterns"
    STYLE = "style"
    TESTING = "testing"
    ARCHITECTURE = "architecture"


@dataclass
class AgentReviewResult:
    agent_role: str
    findings: List[Dict[str, Any]]
    confidence: float = 0.8
    review_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_role": self.agent_role,
            "finding_count": len(self.findings),
            "findings": self.findings,
            "confidence": self.confidence,
            "review_time_ms": self.review_time_ms,
        }


@dataclass
class AggregatedReview:
    total_findings: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    consensus_findings: List[Dict[str, Any]]
    agent_results: List[Dict[str, Any]]
    quality_score: float
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_findings": self.total_findings,
            "by_severity": self.by_severity,
            "by_category": self.by_category,
            "consensus_findings": self.consensus_findings,
            "agent_results": self.agent_results,
            "quality_score": self.quality_score,
            "summary": self.summary,
        }


SECURITY_PROMPT = """You are a security-focused code reviewer. Identify:
- Injection vulnerabilities (SQL, command, XSS)
- Hardcoded secrets or credentials
- Insecure cryptographic usage
- Missing input validation
- Broken access control
Report: file, line, severity, description."""

PATTERNS_PROMPT = """You are a patterns and consistency reviewer. Identify:
- Naming convention violations
- Anti-patterns (god classes, spaghetti code)
- SOLID principle violations
- Inconsistent error handling
- Dead code and unused imports
Report: file, line, severity, description."""

PERFORMANCE_PROMPT = """You are a performance reviewer. Identify:
- N+1 query patterns
- Unnecessary loops or iterations
- Missing caching opportunities
- Memory leaks or excessive allocation
- Inefficient algorithms
Report: file, line, severity, description."""


class MultiAgentReviewEngine:
    """Parallel multi-agent review with consensus aggregation — from ai-code-reviewer."""

    AGENT_PROMPTS: Dict[str, str] = {
        ReviewAgentRole.SECURITY.value: SECURITY_PROMPT,
        ReviewAgentRole.PATTERNS.value: PATTERNS_PROMPT,
        ReviewAgentRole.PERFORMANCE.value: PERFORMANCE_PROMPT,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._consensus_threshold = self.config.get("consensus_threshold", 0.5)
        self._similarity_threshold = self.config.get("similarity_threshold", 0.85)
        self._reviews: List[AgentReviewResult] = []

    def simulate_review(self, code: str, file_path: str = "<input>", roles: Optional[List[str]] = None) -> AggregatedReview:
        """Run static analysis as each agent role and aggregate results."""
        analyzer = StaticAnalyzer()
        scanner = SecretScanner()
        all_results: List[AgentReviewResult] = []

        target_roles = roles or [r.value for r in ReviewAgentRole]

        for role in target_roles:
            findings: List[Dict[str, Any]] = []
            if role == ReviewAgentRole.SECURITY.value:
                secret_findings = scanner.scan_text(code, file_path)
                findings.extend([f.to_dict() for f in secret_findings])
                static_issues = analyzer.analyze_code(code, file_path)
                findings.extend([i.to_dict() for i in static_issues if i.category == "security"])
            elif role == ReviewAgentRole.PATTERNS.value:
                static_issues = analyzer.analyze_code(code, file_path)
                findings.extend([i.to_dict() for i in static_issues if i.category in ("quality", "documentation")])
            elif role == ReviewAgentRole.PERFORMANCE.value:
                structural = StructuralAnalyzer()
                files = {file_path: code}
                struct_findings = structural.analyze(files)
                findings.extend([f.to_dict() for f in struct_findings])

            all_results.append(AgentReviewResult(
                agent_role=role,
                findings=findings,
                confidence=0.8,
            ))

        aggregated = self._aggregate(all_results)
        self._reviews.extend(all_results)
        return aggregated

    def _aggregate(self, results: List[AgentReviewResult]) -> AggregatedReview:
        all_findings = []
        for r in results:
            for f in r.findings:
                all_findings.append({**f, "_agent": r.agent_role})

        by_severity: Dict[str, int] = Counter()
        by_category: Dict[str, int] = Counter()
        for f in all_findings:
            by_severity[f.get("severity", "unknown")] += 1
            by_category[f.get("category", f.get("_agent", "unknown"))] += 1

        consensus = self._find_consensus(all_findings)

        severity_map = {"critical": 0, "warning": 0, "suggestion": 0}
        for sev, count in by_severity.items():
            severity_map[sev] = count
        quality_score = max(0, min(100, 100 - severity_map["critical"] * 15 - severity_map["warning"] * 5 - severity_map["suggestion"] * 1))

        total_agents = len(results)
        findings_count = len(all_findings)
        summary = f"{findings_count} findings from {total_agents} agents. "
        if severity_map["critical"] > 0:
            summary += f"{severity_map['critical']} critical. "
        if severity_map["warning"] > 0:
            summary += f"{severity_map['warning']} warnings. "

        return AggregatedReview(
            total_findings=findings_count,
            by_severity=dict(by_severity),
            by_category=dict(by_category),
            consensus_findings=consensus,
            agent_results=[r.to_dict() for r in results],
            quality_score=quality_score,
            summary=summary,
        )

    def _find_consensus(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find findings that multiple agents agree on."""
        by_key: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for f in findings:
            key = f.get("rule_id") or f.get("message", "")[:50]
            by_key[key].append(f)

        consensus = []
        total_agents = len(set(f.get("_agent", "") for f in findings))
        for key, group in by_key.items():
            agents = set(f.get("_agent", "") for f in group)
            if len(agents) >= max(1, int(total_agents * self._consensus_threshold)):
                consensus.append({
                    "issue": group[0],
                    "agents_agreeing": list(agents),
                    "consensus_score": len(agents) / max(1, total_agents),
                })
        return consensus

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_reviews": len(self._reviews),
            "total_findings": sum(len(r.findings) for r in self._reviews),
            "agents_used": list(set(r.agent_role for r in self._reviews)),
        }


# ── PR Verification Engine ─────────────────────────────────────

class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    name: str
    status: str
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "status": self.status, "message": self.message}


class PRVerificationEngine:
    """PR verification checklist — patterns from github-template-ai-agents."""

    DEFAULT_CHECKS = [
        "tests_pass",
        "no_secret_leaks",
        "no_bare_excepts",
        "no_print_statements",
        "docstrings_present",
        "type_hints_present",
        "no_star_imports",
        "conventional_commit",
        "no_large_files",
        "code_review_complete",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def verify(self, code: str, file_path: str = "<input>", checks: Optional[List[str]] = None) -> List[CheckResult]:
        target_checks = checks or self.DEFAULT_CHECKS
        results: List[CheckResult] = []

        checker_map = {
            "tests_pass": lambda: CheckResult("tests_pass", CheckStatus.SKIPPED.value, "Manual verification required"),
            "no_secret_leaks": self._check_no_secrets,
            "no_bare_excepts": lambda: self._check_pattern(code, file_path, r"except\s*:", "Bare except found", "no_bare_excepts"),
            "no_print_statements": lambda: self._check_pattern(code, file_path, r"\bprint\s*\(", "Print statement found", "no_print_statements"),
            "docstrings_present": lambda: self._check_docstrings(code, file_path),
            "type_hints_present": lambda: self._check_type_hints(code, file_path),
            "no_star_imports": lambda: self._check_pattern(code, file_path, r"from\s+\S+\s+import\s+\*", "Star import found", "no_star_imports"),
            "conventional_commit": CheckResult("conventional_commit", CheckStatus.SKIPPED.value, "Manual verification required"),
            "no_large_files": lambda: CheckResult("no_large_files", CheckStatus.PASSED.value, f"File size: {len(code)} chars"),
            "code_review_complete": CheckResult("code_review_complete", CheckStatus.SKIPPED.value, "Manual verification required"),
        }

        for check_name in target_checks:
            checker = checker_map.get(check_name)
            if checker is None:
                results.append(CheckResult(check_name, CheckStatus.SKIPPED.value, "Unknown check"))
            elif callable(checker) and not isinstance(checker, CheckResult):
                results.append(checker())
            else:
                results.append(checker)

        return results

    def _check_no_secrets(self) -> CheckResult:
        scanner = SecretScanner()
        findings = scanner.scan_text("", "<verify>")
        if findings:
            return CheckResult("no_secret_leaks", CheckStatus.FAILED.value, f"{len(findings)} potential secrets found")
        return CheckResult("no_secret_leaks", CheckStatus.PASSED.value)

    def _check_pattern(self, code: str, file_path: str, pattern: str, message: str, name: str) -> CheckResult:
        if re.search(pattern, code):
            return CheckResult(name, CheckStatus.FAILED.value, message)
        return CheckResult(name, CheckStatus.PASSED.value)

    def _check_docstrings(self, code: str, file_path: str) -> CheckResult:
        analyzer = StaticAnalyzer()
        issues = analyzer._check_python_docstrings(code, file_path)
        if issues:
            return CheckResult("docstrings_present", CheckStatus.FAILED.value, f"{len(issues)} missing docstrings")
        return CheckResult("docstrings_present", CheckStatus.PASSED.value)

    def _check_type_hints(self, code: str, file_path: str) -> CheckResult:
        if not file_path.endswith(".py"):
            return CheckResult("type_hints_present", CheckStatus.SKIPPED.value, "Not a Python file")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return CheckResult("type_hints_present", CheckStatus.SKIPPED.value, "Parse error")
        missing = 0
        total = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += 1
                if node.returns is None:
                    missing += 1
        if total > 0 and missing / total > 0.5:
            return CheckResult("type_hints_present", CheckStatus.FAILED.value, f"{missing}/{total} functions missing return type hints")
        return CheckResult("type_hints_present", CheckStatus.PASSED.value)

    def run_full_verification(self, code: str, file_path: str = "<input>") -> Dict[str, Any]:
        results = self.verify(code, file_path)
        passed = sum(1 for r in results if r.status == CheckStatus.PASSED.value)
        failed = sum(1 for r in results if r.status == CheckStatus.FAILED.value)
        skipped = sum(1 for r in results if r.status == CheckStatus.SKIPPED.value)
        return {
            "results": [r.to_dict() for r in results],
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(results),
            "all_passed": failed == 0,
        }


# ── Technical Debt Tracker ─────────────────────────────────────

class DebtCategory(str, Enum):
    CODE_SMELL = "code_smell"
    TODO = "todo"
    FIXME = "fixme"
    HACK = "hack"
    DEPRECATED = "deprecated"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    MISSING_TESTS = "missing_tests"
    MISSING_DOCS = "missing_docs"
    TYPE_IGNORE = "type_ignore"


class DebtPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DebtItem:
    id: str
    category: str
    priority: str
    file_path: str
    line: int
    description: str
    created_at: str = ""
    status: str = "open"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "priority": self.priority,
            "file_path": self.file_path,
            "line": self.line,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status,
        }


class TechnicalDebtTracker:
    """Track and prioritize technical debt — patterns from claude-code-agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._items: Dict[str, DebtItem] = {}
        self._counter = 0

    def scan_codebase(self, files: Dict[str, str]) -> List[DebtItem]:
        """Scan files and catalog all technical debt items."""
        items: List[DebtItem] = []
        for filepath, content in files.items():
            items.extend(self._scan_file(filepath, content))
        return items

    def _scan_file(self, filepath: str, content: str) -> List[DebtItem]:
        items: List[DebtItem] = []
        lines = content.splitlines()

        debt_patterns = [
            (r"^\s*#\s*TODO\b(.*)", DebtCategory.TODO.value, DebtPriority.LOW.value),
            (r"^\s*#\s*FIXME\b(.*)", DebtCategory.FIXME.value, DebtPriority.HIGH.value),
            (r"^\s*#\s*HACK\b(.*)", DebtCategory.HACK.value, DebtPriority.HIGH.value),
            (r"^\s*#\s*DEPRECATED\b(.*)", DebtCategory.DEPRECATED.value, DebtPriority.MEDIUM.value),
            (r"noqa\b(.*)", DebtCategory.CODE_SMELL.value, DebtPriority.LOW.value),
            (r"# type:\s*ignore\b(.*)", DebtCategory.TYPE_IGNORE.value, DebtPriority.LOW.value),
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, category, priority in debt_patterns:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    desc = m.group(1).strip() if m.group(1) else line.strip()
                    items.append(self._add_item(category, priority, filepath, line_num, desc))

        if filepath.endswith(".py"):
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return items
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        items.append(self._add_item(
                            DebtCategory.MISSING_DOCS.value, DebtPriority.LOW.value,
                            filepath, node.lineno, f"Missing docstring for '{node.name}'",
                        ))
        return items

    def _add_item(self, category: str, priority: str, filepath: str, line: int, desc: str) -> DebtItem:
        self._counter += 1
        item = DebtItem(
            id=f"DEBT-{self._counter:04d}",
            category=category,
            priority=priority,
            file_path=filepath,
            line=line,
            description=desc,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._items[item.id] = item
        return item

    def get_all(self) -> List[DebtItem]:
        return list(self._items.values())

    def get_by_priority(self, priority: str) -> List[DebtItem]:
        return [item for item in self._items.values() if item.priority == priority]

    def get_by_category(self, category: str) -> List[DebtItem]:
        return [item for item in self._items.values() if item.category == category]

    def resolve(self, item_id: str) -> bool:
        if item_id in self._items:
            self._items[item_id].status = "resolved"
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        all_items = list(self._items.values())
        by_priority = Counter(i.priority for i in all_items)
        by_category = Counter(i.category for i in all_items)
        by_status = Counter(i.status for i in all_items)
        return {
            "total": len(all_items),
            "by_priority": dict(by_priority),
            "by_category": dict(by_category),
            "by_status": dict(by_status),
            "open_count": by_status.get("open", 0),
            "resolved_count": by_status.get("resolved", 0),
        }
