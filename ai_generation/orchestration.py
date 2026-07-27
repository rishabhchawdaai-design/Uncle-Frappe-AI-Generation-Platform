"""
Multi-Agent Orchestration Engine — patterns from autodev-studio, custom-ai-agents, ai-dlc.

Provides: OrchestrationPipeline, DomainReviewAgent, KnowledgeBaseContext, RevisionLoop.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ── Pipeline Stage ─────────────────────────────────────────────

class PipelineStage(str, Enum):
    INTENT = "intent"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    QA = "qa"
    REVIEW = "review"
    SECURITY = "security"
    REVISION = "revision"
    DELIVERY = "delivery"


class StageResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    CHANGES_REQUESTED = "changes_requested"
    INCONCLUSIVE = "inconclusive"
    SKIPPED = "skipped"


@dataclass
class StageOutput:
    stage: str
    result: str
    summary: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "result": self.result,
            "summary": self.summary,
            "findings": self.findings,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
        }


# ── Domain Review Agents ──────────────────────────────────────

class AgentDomain(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    REFACTORING = "refactoring"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    DOCUMENTATION = "documentation"
    MAINTAINABILITY = "maintainability"


AGENT_PROMPTS: Dict[str, Dict[str, Any]] = {
    AgentDomain.SECURITY.value: {
        "name": "Security Reviewer",
        "description": "Focuses on security posture, threat surfaces, and secure coding practices.",
        "review_areas": [
            "Authentication and authorization",
            "Input validation and output encoding",
            "Data storage and transport (secrets, encryption, TLS)",
            "Error handling and logging (no sensitive leakage)",
            "OWASP Top 10 vulnerabilities",
            "Cryptographic issues",
        ],
        "output_format": "severity:file:line:issue_description",
    },
    AgentDomain.PERFORMANCE.value: {
        "name": "Performance Optimiser",
        "description": "Focuses on runtime performance, memory usage, and scalability.",
        "review_areas": [
            "Algorithm complexity and time/space usage",
            "Database query patterns (N+1, missing indexes)",
            "Caching opportunities",
            "Memory allocation and leaks",
            "Concurrency and parallelism",
            "Startup time and resource usage",
        ],
        "output_format": "metric:file:line:issue:impact",
    },
    AgentDomain.REFACTORING.value: {
        "name": "Refactoring Specialist",
        "description": "Focuses on improving code structure, readability, and maintainability.",
        "review_areas": [
            "God classes and methods",
            "Long parameter lists",
            "Duplicated logic",
            "Tight coupling and low cohesion",
            "SOLID principle violations",
            "Design pattern opportunities",
        ],
        "output_format": "smell:file:line:issue:refactoring_technique",
    },
    AgentDomain.TESTING.value: {
        "name": "Test Specialist",
        "description": "Focuses on test coverage, quality, and testing best practices.",
        "review_areas": [
            "Critical untested paths",
            "High-risk / complex code with weak tests",
            "Edge cases and boundary conditions",
            "Error handling coverage",
            "Test isolation and determinism",
            "Test maintainability",
        ],
        "output_format": "gap:file:line:issue:recommended_test",
    },
    AgentDomain.ARCHITECTURE.value: {
        "name": "Senior Software Architect",
        "description": "Focuses on software architecture and structural design.",
        "review_areas": [
            "Clean Architecture adherence",
            "Dependency direction and layer boundaries",
            "Module cohesion and coupling",
            "API contract design",
            "Configuration management",
            "Deployment architecture",
        ],
        "output_format": "violation:module:issue:recommendation",
    },
    AgentDomain.DOCUMENTATION.value: {
        "name": "Documentation Reviewer",
        "description": "Focuses on documentation coverage, accuracy, and alignment with code.",
        "review_areas": [
            "Public API documentation",
            "Architecture decision records",
            "README completeness",
            "Code comment quality",
            "Example coverage",
            "Changelog maintenance",
        ],
        "output_format": "gap:file:issue:recommendation",
    },
    AgentDomain.MAINTAINABILITY.value: {
        "name": "Maintainability Reviewer",
        "description": "Focuses on long-term code health and developer experience.",
        "review_areas": [
            "Code readability and naming",
            "Complexity management",
            "Technical debt indicators",
            "Consistency and conventions",
            "Error message quality",
            "Logging and observability",
        ],
        "output_format": "issue:file:line:description:impact",
    },
}


# ── Knowledge Base Context ─────────────────────────────────────

@dataclass
class KBEntry:
    key: str
    content: str
    source: str = ""
    relevance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeBaseContext:
    """RAG-based context retrieval for agent workflows — from autodev-studio."""

    def __init__(self):
        self._entries: Dict[str, KBEntry] = {}
        self._index: Dict[str, List[str]] = {}

    def add_entry(self, key: str, content: str, source: str = "", metadata: Optional[Dict[str, Any]] = None):
        entry = KBEntry(key=key, content=content, source=source, metadata=metadata or {})
        self._entries[key] = entry
        for word in set(content.lower().split()):
            if len(word) > 2:
                self._index.setdefault(word, []).append(key)

    def retrieve(self, query: str, max_results: int = 5) -> List[KBEntry]:
        query_words = set(query.lower().split())
        scores: Dict[str, float] = {}
        for word in query_words:
            for key in self._index.get(word, []):
                scores[key] = scores.get(key, 0) + 1
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:max_results]
        results = []
        for key in sorted_keys:
            entry = self._entries[key]
            entry.relevance = scores[key] / max(1, len(query_words))
            results.append(entry)
        return results

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self._entries),
            "index_terms": len(self._index),
            "sources": list(set(e.source for e in self._entries.values() if e.source)),
        }


# ── Revision Loop ──────────────────────────────────────────────

@dataclass
class RevisionRound:
    round_number: int
    qa_output: Optional[StageOutput] = None
    review_output: Optional[StageOutput] = None
    dev_output: Optional[StageOutput] = None
    decided_to_ship: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "qa_output": self.qa_output.to_dict() if self.qa_output else None,
            "review_output": self.review_output.to_dict() if self.review_output else None,
            "dev_output": self.dev_output.to_dict() if self.dev_output else None,
            "decided_to_ship": self.decided_to_ship,
        }


class RevisionLoop:
    """Bounded revision loop — from autodev-studio's Dev → QA → Review cycle."""

    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds
        self._rounds: List[RevisionRound] = []

    def should_continue(self, qa_output: StageOutput, review_output: StageOutput) -> bool:
        if len(self._rounds) >= self.max_rounds:
            return False
        needs_fix = (
            review_output.result == StageResult.CHANGES_REQUESTED.value or
            qa_output.result == StageResult.FAIL.value
        )
        return needs_fix

    def record_round(self, round_number: int, qa: StageOutput, review: StageOutput,
                     dev: Optional[StageOutput] = None, ship: bool = False):
        self._rounds.append(RevisionRound(
            round_number=round_number,
            qa_output=qa,
            review_output=review,
            dev_output=dev,
            decided_to_ship=ship,
        ))

    def get_rounds(self) -> List[RevisionRound]:
        return list(self._rounds)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_rounds": len(self._rounds),
            "max_rounds": self.max_rounds,
            "shipped": any(r.decided_to_ship for r in self._rounds),
        }


# ── Orchestration Pipeline ─────────────────────────────────────

@dataclass
class PipelineConfig:
    max_revision_rounds: int = 3
    min_agents_for_consensus: int = 2
    enable_fast_path: bool = True
    fast_path_max_files: int = 3
    fast_path_max_lines: int = 50
    agent_domains: List[str] = field(default_factory=lambda: [d.value for d in AgentDomain])


class OrchestrationPipeline:
    """Multi-agent orchestration pipeline — patterns from autodev-studio."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._kb = KnowledgeBaseContext()
        self._revision_loop = RevisionLoop(self.config.max_revision_rounds)
        self._pipeline_history: List[Dict[str, Any]] = []

    @property
    def knowledge_base(self) -> KnowledgeBaseContext:
        return self._kb

    def plan_agents(self, task_description: str) -> List[Dict[str, Any]]:
        """Select appropriate agents for a given task."""
        selected = []
        task_lower = task_description.lower()
        for domain in self.config.agent_domains:
            agent_info = AGENT_PROMPTS.get(domain, {})
            if not agent_info:
                continue
            relevance = sum(1 for area in agent_info.get("review_areas", [])
                          if any(word in task_lower for word in area.lower().split()))
            if relevance > 0 or domain in ("security", "testing"):
                selected.append({
                    "domain": domain,
                    "name": agent_info["name"],
                    "description": agent_info["description"],
                    "relevance": relevance,
                    "review_areas": agent_info["review_areas"],
                })
        selected.sort(key=lambda a: a["relevance"], reverse=True)
        return selected

    def run_stage(self, stage: str, code: str, context: Optional[Dict[str, Any]] = None) -> StageOutput:
        """Execute a pipeline stage with appropriate analysis."""
        ctx = context or {}
        findings: List[Dict[str, Any]] = []

        if stage == PipelineStage.INTENT.value:
            return self._run_intent_stage(code, ctx)
        elif stage == PipelineStage.PLANNING.value:
            return self._run_planning_stage(code, ctx)
        elif stage == PipelineStage.IMPLEMENTATION.value:
            return self._run_implementation_stage(code, ctx)
        elif stage == PipelineStage.QA.value:
            return self._run_qa_stage(code, ctx)
        elif stage == PipelineStage.REVIEW.value:
            return self._run_review_stage(code, ctx)
        elif stage == PipelineStage.SECURITY.value:
            return self._run_security_stage(code, ctx)
        elif stage == PipelineStage.DELIVERY.value:
            return self._run_delivery_stage(code, ctx)
        else:
            return StageOutput(stage=stage, result=StageResult.SKIPPED.value, summary=f"Unknown stage: {stage}")

    def _run_intent_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        agents = self.plan_agents(ctx.get("description", code[:200]))
        return StageOutput(
            stage=PipelineStage.INTENT.value,
            result=StageResult.PASS.value,
            summary=f"Intent analyzed. {len(agents)} agents selected.",
            metrics={"agents_selected": len(agents), "agents": [a["name"] for a in agents]},
        )

    def _run_planning_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        kb_results = self._kb.retrieve(ctx.get("description", ""), max_results=3)
        return StageOutput(
            stage=PipelineStage.PLANNING.value,
            result=StageResult.PASS.value,
            summary=f"Planning complete. {len(kb_results)} KB entries retrieved.",
            metrics={"kb_entries": len(kb_results)},
        )

    def _run_implementation_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        return StageOutput(
            stage=PipelineStage.IMPLEMENTATION.value,
            result=StageResult.PASS.value,
            summary="Implementation stage passed.",
            metrics={"code_length": len(code)},
        )

    def _run_qa_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        from .code_analysis import StaticAnalyzer, SecretScanner
        analyzer = StaticAnalyzer()
        scanner = SecretScanner()
        issues = analyzer.analyze_code(code, ctx.get("file_path", "<input>"))
        secrets = scanner.scan_text(code, ctx.get("file_path", "<input>"))
        findings = [i.to_dict() for i in issues] + [s.to_dict() for s in secrets]
        critical = sum(1 for f in findings if f.get("severity") == "critical")
        result = StageResult.FAIL.value if critical > 0 else StageResult.PASS.value
        return StageOutput(
            stage=PipelineStage.QA.value,
            result=result,
            summary=f"QA: {len(findings)} findings, {critical} critical.",
            findings=findings,
            metrics={"total_findings": len(findings), "critical": critical},
        )

    def _run_review_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        from .code_analysis import MultiAgentReviewEngine
        engine = MultiAgentReviewEngine()
        roles = ctx.get("roles", None)
        review = engine.simulate_review(code, ctx.get("file_path", "<input>"), roles)
        result = StageResult.CHANGES_REQUESTED.value if review.total_findings > 0 else StageResult.PASS.value
        return StageOutput(
            stage=PipelineStage.REVIEW.value,
            result=result,
            summary=f"Review: {review.total_findings} findings, quality score {review.quality_score}.",
            findings=review.consensus_findings,
            metrics={"quality_score": review.quality_score, "total_findings": review.total_findings},
        )

    def _run_security_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        from .code_analysis import SecretScanner, StaticAnalyzer
        scanner = SecretScanner()
        analyzer = StaticAnalyzer()
        secrets = scanner.scan_text(code, ctx.get("file_path", "<input>"))
        issues = analyzer.analyze_code(code, ctx.get("file_path", "<input>"))
        security_issues = [i.to_dict() for i in issues if i.category == "security"]
        findings = [s.to_dict() for s in secrets] + security_issues
        critical = len(findings)
        result = StageResult.FAIL.value if critical > 0 else StageResult.PASS.value
        return StageOutput(
            stage=PipelineStage.SECURITY.value,
            result=result,
            summary=f"Security: {critical} issues found.",
            findings=findings,
            metrics={"security_issues": critical},
        )

    def _run_delivery_stage(self, code: str, ctx: Dict[str, Any]) -> StageOutput:
        return StageOutput(
            stage=PipelineStage.DELIVERY.value,
            result=StageResult.PASS.value,
            summary="Delivery stage passed.",
            metrics={"code_length": len(code)},
        )

    def run_full_pipeline(self, code: str, file_path: str = "<input>",
                          description: str = "") -> Dict[str, Any]:
        """Run the complete orchestration pipeline."""
        start_time = time.time()
        stages: List[StageOutput] = []
        ctx = {"file_path": file_path, "description": description or code[:200]}

        stage_order = [
            PipelineStage.INTENT.value,
            PipelineStage.PLANNING.value,
            PipelineStage.QA.value,
            PipelineStage.REVIEW.value,
            PipelineStage.SECURITY.value,
            PipelineStage.DELIVERY.value,
        ]

        for stage_name in stage_order:
            output = self.run_stage(stage_name, code, ctx)
            stages.append(output)
            if output.result == StageResult.FAIL.value:
                break

        elapsed = time.time() - start_time
        all_findings = []
        for s in stages:
            all_findings.extend(s.findings)

        pipeline_result = {
            "stages": [s.to_dict() for s in stages],
            "total_stages": len(stages),
            "total_findings": len(all_findings),
            "elapsed_seconds": round(elapsed, 3),
            "final_result": stages[-1].result if stages else "unknown",
        }

        self._pipeline_history.append(pipeline_result)
        return pipeline_result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_pipelines_run": len(self._pipeline_history),
            "kb_stats": self._kb.get_stats(),
            "revision_stats": self._revision_loop.get_stats(),
        }
