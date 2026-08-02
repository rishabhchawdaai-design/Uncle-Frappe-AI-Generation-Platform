"""
Research Integration Layer — unifies ACOS-Research (canonical knowledge)
with the production platform (canonical implementation) without duplicating
research content.

The research repository remains the canonical upstream. This layer only
indexes, references, and links it:

- discover: scan the research repo (or the cached manifest) for documents
- index: map research documents -> capabilities -> modules -> tests ->
  SDK -> MCP tools -> benchmarks -> vault pages -> registry entries
- trace: full traceability for any capability
- impact: determine what changes when a research document changes
- sync: detect research changes and refresh the index + execution queue
- graph: a traversable implementation graph across the whole ecosystem
"""
import hashlib
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────

DEFAULT_RESEARCH_REPO = os.environ.get(
    "ACOS_RESEARCH_REPO",
    str(Path(__file__).resolve().parent.parent.parent / "acos-research"),
)
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "research"

RESEARCH_CATEGORIES = {
    "research/core_specs": "core_spec",
    "research/new_areas": "research_area",
    "docs/volumes/v2_chapters": "chapter",
    "docs/volumes": "volume",
    "docs/supporting": "supporting",
    "docs": "index",
    "research": "index",
}

# Registry domain (research source) -> research document id. Authoritative map;
# every capability row in CAPABILITY_REGISTRY.md resolves to exactly one document.
DOMAIN_ALIASES = {
    "agent frameworks research": "AGENT_FRAMEWORKS_RESEARCH",
    "audio speech research": "AUDIO_SPEECH_RESEARCH",
    "auto router": "NEGOTIATION_ENGINE_SPECIFICATION",
    "benchmark knowledge base": "BENCHMARK_KNOWLEDGE_BASE",
    "browser ai research": "BROWSER_AI_RESEARCH",
    "capability graph spec": "CAPABILITY_GRAPH_SPECIFICATION",
    "core platform": "VOLUME_II_KERNEL_ARCHITECTURE_AND_UNIVERSAL_AGENT",
    "decision ledger": "CHAPTER_09_KNOWLEDGE_AND_DECISION_LEDGER",
    "distributed ai research": "DISTRIBUTED_AI_RESEARCH",
    "edge ai research": "EDGE_AI_RESEARCH",
    "execution strategy library": "EXECUTION_STRATEGY_LIBRARY",
    "failure atlas": "FAILURE_ATLAS",
    "image gen research": "IMAGE_GENERATION_RESEARCH",
    "infrastructure registry": "INFRASTRUCTURE_CAPABILITY_REGISTRY",
    "messaging research": "MESSAGING_EVENTS_RESEARCH",
    "negotiation engine spec": "NEGOTIATION_ENGINE_SPECIFICATION",
    "networking research": "NETWORKING_MESH_RESEARCH",
    "ocr research": "OCR_DOCUMENTS_RESEARCH",
    "observability research": "OBSERVABILITY_RESEARCH",
    "plugin ecosystem research": "PLUGIN_ECOSYSTEM_RESEARCH",
    "runtime capability registry": "RUNTIME_CAPABILITY_REGISTRY",
    "search systems research": "SEARCH_SYSTEMS_RESEARCH",
    "security canon": "SECURITY_CANON",
    "storage research": "STORAGE_DATABASES_RESEARCH",
    "workflow research": "WORKFLOW_ORCHESTRATION_RESEARCH",
}


# Evidence-based cross-references: research documents whose implementation
# lives under registry domains with a different canonical source. These do
# not change the canonical 1:1 capability -> research mapping; they add
# backlinks so every research document knows which capabilities implement it.
DOC_CAPABILITY_REFERENCES = {
    "EXECUTION_GRAPH_SCHEMA": {
        "capabilities": ["PLT-20", "WFL-01", "WFL-03", "PLT-16", "PLT-09", "EXE-01"],
        "note": "ExecutionTask/WorkflowStep graphs plus 4-layer execution routing",
    },
    "SCHEDULING_POLICY_SPECIFICATION": {
        "capabilities": ["EXE-01", "EXE-02", "RUN-12", "PLT-06"],
        "note": "Execution layer selection, resource strategies, runtime health",
    },
    "SECURITY_THREAT_MODEL": {
        "capabilities": ["SEC-03", "SEC-04", "SEC-05", "SEC-06", "SEC-07", "SEC-12", "RTG-05"],
        "note": "Authentication, RBAC, encryption, sandboxing, model checksum, privacy routing",
    },
    "CHAPTER_03_UNIVERSAL_WORKFLOW_COMPILER": {
        "capabilities": ["WFL-01", "WFL-03", "PLT-16", "PLT-19", "PLT-20"],
        "note": "Intent decomposition, workflow DAG compilation, generation chaining",
    },
    "CHAPTER_06_ADAPTIVE_SCHEDULER": {
        "capabilities": ["EXE-01", "EXE-02", "EXE-03", "EXE-04", "EXE-10", "RUN-12", "PLT-06"],
        "note": "Layer-based selection, offload strategies, runtime health scheduling",
    },
    "CHAPTER_07_UNIVERSAL_AGENT_KERNEL": {
        "capabilities": ["PLT-01", "PLT-08", "PLT-16", "PLT-17", "RTG-08", "OBS-02"],
        "note": "Unified SDK, event bus, supervisor, agent ecosystem, knowledge graph",
    },
    "CHAPTER_10_GLOBAL_BENCHMARK_INTELLIGENCE": {
        "capabilities": [
            "BMK-01", "BMK-02", "BMK-03", "BMK-04", "BMK-05",
            "BMK-06", "BMK-07", "BMK-08", "PLT-15",
        ],
        "note": "Benchmark engine, standardized suites, composite scoring, provider intelligence",
    },
    "CHAPTER_11_MULTI_STAGE_GENERATION_ENGINE": {
        "capabilities": ["PLT-11", "PLT-18", "PLT-20", "WFL-01", "WFL-03"],
        "note": "Cinematic 14-stage pipeline, generation chaining, quality evaluation",
    },
    "CHAPTER_12_AUTONOMOUS_OPTIMIZATION_LOOP": {
        "capabilities": ["PLT-18", "BMK-04", "BMK-06", "BMK-07", "BMK-08", "PLT-15"],
        "note": "Quality engine, regression detection, provider intelligence feedback",
    },
    "CHAPTER_13_OBSERVABILITY_DIGITAL_TWIN": {
        "capabilities": ["OBS-01", "OBS-02", "OBS-03", "OBS-04", "OBS-05", "OBS-06", "OBS-07", "PLT-06"],
        "note": "Metrics, tracing, logging, request tracking, OTel export, health monitoring",
    },
    "COMPATIBILITY_MATRIX": {
        "capabilities": [
            "CGR-03", "CGR-04", "CGR-07",
            "RUN-01", "RUN-02", "RUN-03", "RUN-04", "RUN-05", "RUN-06",
            "RUN-07", "RUN-08", "RUN-09", "RUN-10", "RUN-11",
        ],
        "note": "Capability matrix lookup, path validation, runtime registry",
    },
    "CHAPTER_01_UNIVERSAL_COMPUTE_GRAPH": {
        "capabilities": ["CGR-01", "CGR-04", "CGR-05", "CGR-07", "WFL-01", "EXE-01", "RUN-12"],
        "note": "Capability graph, path finding, DAG workflows, execution routing, runtime health",
    },
    "CHAPTER_08_PLUGIN_OPERATING_SYSTEM": {
        "capabilities": [
            "PLG-01", "PLG-02", "PLG-03", "PLG-04", "PLG-05", "PLG-06",
            "PLG-07", "PLG-08", "PLG-09", "PLG-10", "SEC-01", "SEC-02", "SEC-07", "SEC-10",
        ],
        "note": "Plugin lifecycle/registry/events/versioning/marketplace/hot-reload/signing + security model",
    },
    "MODEL_CAPABILITY_REGISTRY": {
        "capabilities": ["CGR-02", "CGR-03", "RUN-12", "PLT-15"],
        "note": "Model capability matrix, provider registry, runtime health, model intelligence",
    },
    "WORKFLOW_CAPABILITY_REGISTRY": {
        "capabilities": ["WFL-01", "WFL-02", "WFL-03", "PLT-11"],
        "note": "DAG workflow engine, templates, execution, cinematic pipeline",
    },
}


# ── Data models ───────────────────────────────────────────────────


@dataclass
class ResearchDocument:
    """Metadata for one research document. Content is never copied."""

    research_id: str
    title: str
    path: str
    category: str
    sha256: str
    status: str = "active"
    source_url: str = ""
    commit: str = ""
    related_capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityTrace:
    """Full traceability record for a single capability."""

    capability_id: str
    name: str
    status: str
    research_documents: List[Dict[str, Any]] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    sdk_interfaces: List[str] = field(default_factory=list)
    mcp_tools: List[str] = field(default_factory=list)
    benchmarks: List[str] = field(default_factory=list)
    vault_page: str = ""
    registry_entry: str = ""
    introduced_commit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImpactReport:
    """What changes when a research document changes."""

    research_id: str
    title: str
    changed: bool
    affected_capabilities: List[str] = field(default_factory=list)
    affected_modules: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    affected_sdk_interfaces: List[str] = field(default_factory=list)
    affected_mcp_tools: List[str] = field(default_factory=list)
    affected_docs: List[str] = field(default_factory=list)
    affected_benchmarks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QueueItem:
    """Autonomous research evolution item."""

    item_id: str
    topic: str
    source_research: str
    classification: str  # implementable | blocked | speculative
    reason: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Curated capability-name -> module aliases for capabilities whose names do
# not token-overlap with their implementation modules.
CAPABILITY_MODULE_ALIASES = {
    "FindCapabilityPath": ["capability_graph", "compatibility_matrix"],
    "ValidatePath": ["capability_graph", "compatibility_matrix"],
    "Capability Matrix": ["capability_matrix", "compatibility_matrix"],
    "EstimateExecutionCost (Graph)": ["capability_graph"],
    "Periodic Discovery": ["capability_graph"],
}

CAPABILITY_ID_MODULE_ALIASES = {
    "AUD-01": ["local_runtimes", "audio_generation"],
    "AUD-02": ["local_runtimes", "audio_generation"],
    "AUD-03": ["audio_generation"],
    "AUD-04": ["local_runtimes"],
    "BMK-05": ["negotiation_engine", "benchmark_engine"],
    "BRW-01": ["browser_ai"],
    "BRW-02": ["browser_ai"],
    "BRW-03": ["browser_ai"],
    "BRW-04": ["browser_ai"],
    "BRW-06": ["browser_ai"],
    "EDG-04": ["edge_ai"],
    "EDG-05": ["edge_ai"],
    "EDT-01": ["image_editing"],
    "EDT-02": ["image_editing"],
    "EDT-03": ["image_editing"],
    "EDT-04": ["image_editing"],
    "EDT-05": ["image_editing"],
    "EDT-06": ["image_editing"],
    "EDT-08": ["image_editing"],
    "EXE-03": ["execution_engine", "kimi_k3", "local_runtimes"],
    "EXE-04": ["execution_strategies"],
    "EXE-05": ["execution_strategies"],
    "EXE-07": ["execution_strategies"],
    "EXE-08": ["execution_strategies"],
    "EXE-09": ["execution_strategies"],
    "EXE-10": ["execution_strategies"],
    "FLT-02": ["failure_recovery"],
    "FLT-04": ["supervisor", "failure_recovery"],
    "IMG-12": ["prompt_engine"],
    "MSG-05": ["event_bus"],
    "OBS-01": ["observability"],
    "OBS-02": ["observability", "otel_export"],
    "OBS-03": ["observability"],
    "OBS-06": ["observability", "failure_recovery"],
    "OCR-07": ["document_intelligence"],
    "OCR-09": ["document_intelligence"],
    "RTG-04": ["negotiation_engine"],
    "RTG-05": ["auto_router", "negotiation_engine"],
    "RTG-06": ["auto_router", "negotiation_engine"],
    "RTG-07": ["negotiation_engine"],
    "RTG-08": ["auto_router"],
    "SEC-03": ["security"],
    "SEC-04": ["security"],
    "SRC-02": ["search_systems"],
    "SRC-03": ["search_systems"],
    "SRC-09": ["search_backends"],
    "SRC-10": ["search_backends"],
}


# ── Engine ────────────────────────────────────────────────────────


class ResearchIntegrationEngine:
    """Structured importer, index, registry, and graph for ACOS-Research."""

    def __init__(self, research_repo: Optional[str] = None, data_dir: Optional[str] = None):
        self.research_repo = Path(research_repo or DEFAULT_RESEARCH_REPO)
        self.data_dir = Path(data_dir or DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._registry: List[Dict[str, str]] = []
        self._modules: List[str] = []
        self._documents: Optional[List[ResearchDocument]] = None

    # ── Registry parsing ──────────────────────────────────────────

    def _load_registry(self) -> List[Dict[str, str]]:
        if self._registry:
            return self._registry
        registry_path = Path(__file__).resolve().parent.parent / "CAPABILITY_REGISTRY.md"
        if not registry_path.exists():
            return []
        pattern = re.compile(r"\|\s*([A-Z]{3}-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|")
        rows = []
        for match in pattern.finditer(registry_path.read_text()):
            cap_id, name, source, status = match.groups()
            rows.append({
                "capability_id": cap_id.strip(),
                "name": name.strip(),
                "source": source.strip(),
                "status": status.strip(),
            })
        self._registry = rows
        return rows

    def _load_modules(self) -> List[str]:
        if self._modules:
            return self._modules
        package = Path(__file__).resolve().parent
        self._modules = sorted(
            f[:-3] for f in os.listdir(package)
            if f.endswith(".py") and not f.startswith("__") and f != "research_integration.py"
        )
        return self._modules

    # ── Research discovery ────────────────────────────────────────

    def discover_documents(self, refresh: bool = False) -> List[ResearchDocument]:
        """Scan the research repo (or cached manifest) for documents."""
        if self._documents is not None and not refresh:
            return self._documents
        if self.research_repo.exists():
            documents = self._scan_research_repo()
            self._populate_related(documents)
            self._documents = documents
            return documents
        documents = self._load_manifest_documents()
        self._populate_related(documents)
        return documents

    def _populate_related(self, documents: List[ResearchDocument]) -> None:
        """Attach related capability ids to each research document."""
        registry = self._load_registry()
        domain_index: Dict[str, List[str]] = {}
        for row in registry:
            domain_index.setdefault(row["source"], []).append(row["capability_id"])
        for doc in documents:
            if doc.related_capabilities:
                continue
            related: Set[str] = set()
            for source, caps in domain_index.items():
                if self._domain_matches_doc(source, doc):
                    related.update(caps)
            doc.related_capabilities = sorted(related)

    def _scan_research_repo(self) -> List[ResearchDocument]:
        repo = self.research_repo
        documents: List[ResearchDocument] = []
        source_url = ""
        try:
            remote = subprocess.run(
                ["git", "-C", str(repo), "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=10,
            )
            if remote.returncode == 0:
                url = remote.stdout.strip().rstrip(".git")
                source_url = url.replace("git@github.com:", "https://github.com/")
                source_url = re.sub(r"https://x-access-token:[^@]+@", "https://", source_url)
        except Exception:
            pass

        used_ids: Set[str] = set()
        for md in sorted(repo.rglob("*.md")):
            rel = md.relative_to(repo).as_posix()
            if ".git" in rel:
                continue
            category = "document"
            for prefix, cat in RESEARCH_CATEGORIES.items():
                if rel.startswith(prefix):
                    category = cat
                    break
            content = md.read_text(errors="ignore")
            title = self._extract_title(content, md.stem)
            stem_id = self._research_id_from_path(rel, md.stem)
            research_id = self._research_id_disambiguate(rel, stem_id, used_ids)
            used_ids.add(research_id)
            doc = ResearchDocument(
                research_id=research_id,
                title=title,
                path=rel,
                category=category,
                sha256=hashlib.sha256(content.encode()).hexdigest(),
                status=self._detect_doc_status(content),
                source_url=f"{source_url}/blob/main/{rel}" if source_url else "",
                commit=self._file_commit(md),
            )
            documents.append(doc)
        return documents

    @staticmethod
    def _extract_title(content: str, fallback: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return fallback.replace("_", " ").title()

    @staticmethod
    def _research_id_from_path(rel: str, stem: str) -> str:
        return stem.upper().replace(" ", "_")

    @staticmethod
    def _research_id_disambiguate(rel: str, stem_id: str, used: Set[str]) -> str:
        """Guarantee unique research ids when two paths share a stem."""
        research_id = stem_id
        if research_id in used:
            parent = re.sub(r"[^a-z0-9]", "_", rel.rsplit("/", 1)[0]).strip("_").upper()
            research_id = f"{stem_id}_{parent}" if parent else f"{stem_id}_2"
        return research_id

    @staticmethod
    def _detect_doc_status(content: str) -> str:
        lower = content.lower()
        if re.search(r"status[:\s]*[🟡🟠🔴]", lower) or "emerging" in lower:
            return "emerging"
        if "speculative" in lower:
            return "speculative"
        if "experimental" in lower:
            return "experimental"
        return "active"

    def _file_commit(self, path: Path) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.research_repo), "log", "-1", "--format=%h", "--", str(path)],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _load_manifest_documents(self) -> List[ResearchDocument]:
        manifest = self.data_dir / "research_manifest.json"
        if not manifest.exists():
            return []
        try:
            data = json.loads(manifest.read_text())
            return [ResearchDocument(**doc) for doc in data.get("documents", [])]
        except Exception:
            return []

    # ── Satisfaction cross-references ───────────────────────────────

    def _satisfaction_references(self) -> Dict[str, List[str]]:
        """research_id -> capability ids that implement the document."""
        registry_ids = {r["capability_id"] for r in self._load_registry()}
        return {
            rid: [cap for cap in ref.get("capabilities", []) if cap in registry_ids]
            for rid, ref in DOC_CAPABILITY_REFERENCES.items()
        }

    def _build_satisfaction(self, registry: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        registry_ids = {r["capability_id"] for r in registry}
        result: Dict[str, Dict[str, Any]] = {}
        for rid, ref in DOC_CAPABILITY_REFERENCES.items():
            caps = [cap for cap in ref.get("capabilities", []) if cap in registry_ids]
            if not caps:
                continue
            result[rid] = {"capabilities": caps, "note": ref.get("note", "")}
        return result

    # ── Index building ────────────────────────────────────────────

    def build_index(self) -> Dict[str, Any]:
        """Build the research <-> implementation index and cache it."""
        documents = self.discover_documents()
        registry = self._load_registry()
        modules = self._load_modules()

        doc_by_id = {d.research_id: d for d in documents}
        cap_by_id: Dict[str, Dict[str, str]] = {}
        for row in registry:
            cap_by_id[row["capability_id"]] = row

        sdk_map = self._parse_sdk_interfaces()
        test_map = self._parse_test_modules()
        mcp_map = self._parse_mcp_tools()
        benchmark_map = self._parse_benchmarks()

        # capability -> module/tests via keyword overlap + curated aliases
        capability_links: Dict[str, Dict[str, Any]] = {}
        for cap_id, row in cap_by_id.items():
            if row["status"] == "BLOCKED":
                # blocked capabilities are not implemented: never claim links
                capability_links[cap_id] = {"modules": [], "tests": [],
                                            "sdk_interfaces": [], "mcp_tools": [],
                                            "benchmarks": []}
                continue
            modules_for, tests_for, sdk_for, mcp_for, benchmarks_for = self._link_capability(
                row["capability_id"], row["name"], modules,
                sdk_map, mcp_map, test_map, benchmark_map
            )
            capability_links[cap_id] = {
                "modules": modules_for,
                "tests": tests_for,
                "sdk_interfaces": sdk_for,
                "mcp_tools": mcp_for,
                "benchmarks": benchmarks_for,
            }

        index = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "research_documents": len(documents),
            "capabilities": len(registry),
            "modules": modules,
            "capability_links": capability_links,
            "document_satisfaction": self._build_satisfaction(registry),
            "documents": [d.to_dict() for d in documents],
        }
        (self.data_dir / "research_index.json").write_text(
            json.dumps(index, indent=2, default=str)
        )
        return index

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9]", "", text.lower())

    def _domain_matches_doc(self, source: str, doc: ResearchDocument) -> bool:
        alias = DOMAIN_ALIASES.get(source.lower())
        if alias:
            return alias == doc.research_id
        return self._normalize(source) in (
            self._normalize(doc.research_id.replace("_", " ")),
            self._normalize(doc.title),
        )

    def _parse_sdk_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """sdk property name -> {modules, method names}."""
        sdk_path = Path(__file__).resolve().parent / "sdk.py"
        content = sdk_path.read_text()
        result: Dict[str, Dict[str, Any]] = {}
        for prop in re.finditer(
            r"@property\n\s+def (\w+)\(self\):.*?\n(.*?)(?=\n\s{4}(?:@property|async def|def )|\Z)",
            content, re.DOTALL,
        ):
            name = prop.group(1)
            body = prop.group(2)
            modules = re.findall(r"from \.(\w+) import", body)
            methods = re.findall(r"def (\w+)\(", body)
            result[name] = {"modules": sorted(set(modules)), "methods": sorted(set(methods))}
        return result

    def _parse_test_modules(self) -> Dict[str, List[str]]:
        tests_dir = Path(__file__).resolve().parent / "tests"
        result: Dict[str, List[str]] = {}
        for test_file in tests_dir.glob("test_*.py"):
            content = test_file.read_text()
            modules = sorted(set(
                m.group(1) for m in re.finditer(r"from ai_generation\.(\w+) import", content)
            ))
            result[test_file.stem] = modules
        return result

    def _parse_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """tool name -> sdk properties used by its handler."""
        mcp_path = Path(__file__).resolve().parent / "mcp_tools.py"
        content = mcp_path.read_text()
        result: Dict[str, Dict[str, Any]] = {}
        handlers: Dict[str, str] = {}
        handle_match = re.search(r"async def handle\(self, tool_name, arguments\):(.*?)(?=\n    async def |\Z)", content, re.DOTALL)
        if handle_match:
            for m in re.finditer(r'"([a-z0-9_]+)": self\.(_handle_\w+)', handle_match.group(1)):
                handlers[m.group(2)] = m.group(1)
        for handler_name, tool in handlers.items():
            handler_match = re.search(
                rf"async def {re.escape(handler_name)}\(self, args\):(.*?)(?=\n    async def |\Z)",
                content, re.DOTALL,
            )
            properties = []
            if handler_match:
                properties = sorted(set(
                    m.group(1) for m in re.finditer(r"self\.sdk\.(\w+)", handler_match.group(1))
                ))
            result[tool] = {"handler": handler_name, "sdk_properties": properties}
        return result

    def _parse_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for name in ("benchmark_lab", "cinema_benchmark", "benchmark_engine"):
            path = Path(__file__).resolve().parent / f"{name}.py"
            if not path.exists():
                continue
            content = path.read_text()
            matches = re.findall(r'"([a-z_]+_suite)"', content) + re.findall(r'"suite":\s*"([a-z_]+)"', content)
            suites = sorted(set(matches))
            result[name] = {"suites": suites}
        return result

    def _link_capability(
        self,
        cap_id: str,
        name: str,
        modules: List[str],
        sdk_map: Dict[str, Dict[str, Any]],
        mcp_map: Dict[str, Dict[str, Any]],
        test_map: Dict[str, List[str]],
        benchmark_map: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
        tokens = set(re.findall(r"[a-z0-9]+", name.lower()))
        linked_modules = []
        linked_sdk = []
        for prop, info in sdk_map.items():
            prop_tokens = set(re.findall(r"[a-z0-9]+", prop))
            if tokens & prop_tokens:
                linked_sdk.append(prop)
                linked_modules.extend(info["modules"])
        for module in modules:
            module_tokens = set(re.findall(r"[a-z0-9]+", module))
            if tokens & module_tokens:
                linked_modules.append(module)
        linked_modules.extend(
            m for m in CAPABILITY_MODULE_ALIASES.get(name, []) if m in modules
        )
        linked_modules.extend(
            m for m in CAPABILITY_ID_MODULE_ALIASES.get(cap_id, []) if m in modules
        )
        linked_modules = sorted(set(linked_modules))
        linked_tests = sorted(
            t for t, mods in test_map.items() if set(mods) & set(linked_modules)
        )
        linked_mcp = sorted(
            tool for tool, info in mcp_map.items()
            if set(info.get("sdk_properties", [])) & set(linked_sdk)
        )
        linked_benchmarks = sorted(
            b for b, info in benchmark_map.items() if info.get("suites")
        )[:3]
        return linked_modules, linked_tests, linked_sdk, linked_mcp, linked_benchmarks

    # ── Traceability ──────────────────────────────────────────────

    def trace_capability(self, capability_id: str) -> Optional[CapabilityTrace]:
        """Full traceability for one capability."""
        index = self._load_index()
        documents = self.discover_documents()
        row = next((r for r in self._load_registry() if r["capability_id"] == capability_id), None)
        if not row:
            return None
        links = index.get("capability_links", {}).get(capability_id, {})
        research = [
            doc.to_dict() for doc in documents
            if capability_id in doc.related_capabilities
        ]
        trace = CapabilityTrace(
            capability_id=capability_id,
            name=row["name"],
            status=row["status"],
            research_documents=research,
            modules=links.get("modules", []),
            tests=links.get("tests", []),
            sdk_interfaces=links.get("sdk_interfaces", []),
            mcp_tools=links.get("mcp_tools", []),
            benchmarks=links.get("benchmarks", []),
            vault_page=f"knowledge-vault/36-Generated/Capabilities/{capability_id} - {row['name']}.md",
            registry_entry=f"CAPABILITY_REGISTRY.md#{capability_id}",
        )
        if trace.modules:
            trace.introduced_commit = self._module_introduced_commit(trace.modules[0])
        return trace

    def _module_introduced_commit(self, module: str) -> str:
        repo = Path(__file__).resolve().parent.parent
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "log", "-1", "--format=%h", "--", f"ai_generation/{module}.py"],
                capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _load_index(self) -> Dict[str, Any]:
        index_path = self.data_dir / "research_index.json"
        if not index_path.exists():
            return self.build_index()
        try:
            return json.loads(index_path.read_text())
        except Exception:
            return self.build_index()

    # ── Impact analysis ───────────────────────────────────────────

    def research_impact(self, research_id: str) -> Optional[ImpactReport]:
        """Determine the implementation blast radius of a research document."""
        documents = self.discover_documents()
        doc = next((d for d in documents if d.research_id == research_id), None)
        if not doc:
            return None
        index = self._load_index()
        satisfaction = index.get("document_satisfaction", {})
        affected_caps = list(dict.fromkeys(
            doc.related_capabilities + satisfaction.get(research_id, {}).get("capabilities", [])
        ))
        modules: Set[str] = set()
        tests: Set[str] = set()
        sdk: Set[str] = set()
        mcp: Set[str] = set()
        for cap in affected_caps:
            links = index.get("capability_links", {}).get(cap, {})
            modules.update(links.get("modules", []))
            tests.update(links.get("tests", []))
            sdk.update(links.get("sdk_interfaces", []))
            mcp.update(links.get("mcp_tools", []))
        docs = sorted({f"knowledge-vault/36-Generated/Capabilities/{cap} - *.md" for cap in affected_caps})
        report = ImpactReport(
            research_id=research_id,
            title=doc.title,
            changed=False,
            affected_capabilities=affected_caps,
            affected_modules=sorted(modules),
            affected_tests=sorted(tests),
            affected_sdk_interfaces=sorted(sdk),
            affected_mcp_tools=sorted(mcp),
            affected_docs=docs,
            affected_benchmarks=["benchmark_lab", "cinema_benchmark"],
            recommendations=self._recommendations(doc, affected_caps),
        )
        return report

    @staticmethod
    def _recommendations(doc: ResearchDocument, affected_caps: List[str]) -> List[str]:
        recs = [f"Verify {len(affected_caps)} linked capabilities after research change"]
        if doc.status in ("emerging", "speculative", "experimental"):
            recs.append(f"Document as future opportunity (status: {doc.status}) — no implementation action")
        else:
            recs.append("Re-run linked test suites and regenerate the knowledge vault")
        return recs

    # ── Change detection & sync ───────────────────────────────────

    def detect_changes(self) -> List[Dict[str, Any]]:
        """Compare the live research repo against the cached manifest."""
        if not self.research_repo.exists():
            return []
        live = {d.research_id: d for d in self._scan_research_repo()}
        cached = {d.research_id: d for d in self._load_manifest_documents()}
        changes = []
        for research_id, doc in live.items():
            if research_id not in cached:
                changes.append({"type": "new", "research_id": research_id, "title": doc.title})
            elif cached[research_id].sha256 != doc.sha256:
                changes.append({"type": "modified", "research_id": research_id, "title": doc.title})
        for research_id in cached:
            if research_id not in live:
                changes.append({"type": "removed", "research_id": research_id})
        return changes

    def sync(self) -> Dict[str, Any]:
        """Detect research changes, refresh the index, and update the queue."""
        changes = self.detect_changes()
        documents = self.discover_documents(refresh=True)
        self._write_manifest(documents)
        self.build_index()
        queue_added = []
        for change in changes:
            if change["type"] != "new":
                continue
            doc = next((d for d in documents if d.research_id == change["research_id"]), None)
            if doc is None:
                continue
            item = self._classify_new_research(doc)
            if item:
                queue_added.append(item.to_dict())
                self._append_queue_item(item)
        return {
            "changes": changes,
            "queue_added": queue_added,
            "documents_indexed": len(documents),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    def _write_manifest(self, documents: List[ResearchDocument]) -> None:
        (self.data_dir / "research_manifest.json").write_text(
            json.dumps({"documents": [d.to_dict() for d in documents]}, indent=2, default=str)
        )

    def _classify_new_research(self, doc: ResearchDocument) -> Optional[QueueItem]:
        try:
            content = (self.research_repo / doc.path).read_text(errors="ignore")
        except Exception:
            content = ""
        lower = content.lower()
        registry_ids = {r["capability_id"]: r["status"] for r in self._load_registry()}
        cap_ids = list(dict.fromkeys(
            doc.related_capabilities + self._satisfaction_references().get(doc.research_id, [])
        ))
        verified = [c for c in cap_ids if registry_ids.get(c) == "VERIFIED"]
        if verified:
            blocked = [c for c in cap_ids if registry_ids.get(c) == "BLOCKED"]
            suffix = f"; {len(blocked)} blocked tracked in registry" if blocked else ""
            classification, reason = (
                "satisfied",
                f"Implemented by {len(verified)} verified capabilities{suffix}",
            )
        elif doc.category in ("index", "document", "volume"):
            classification, reason = "speculative", "Meta/index document — reference only, no implementation action"
        elif any(k in lower for k in (
            "requires api key", "requires credentials", "requires authentication",
            "api key required", "authentication required",
            "proprietary model", "proprietary software", "closed-source", "closed source",
            "commercial license", "commercially licensed",
        )):
            classification, reason = "blocked", "External dependency (credentials/licensing)"
        elif doc.status in ("emerging", "speculative", "experimental") or "timeline" in lower:
            classification, reason = "speculative", f"Research status: {doc.status}"
        elif cap_ids:
            blocked_caps = [c for c in cap_ids if registry_ids.get(c) == "BLOCKED"]
            if blocked_caps:
                classification, reason = (
                    "blocked",
                    f"{len(blocked_caps)}/{len(cap_ids)} registered capabilities blocked by external dependencies",
                )
            else:
                classification, reason = "implementable", "Capabilities registered but not yet verified"
        else:
            classification, reason = "speculative", "No registered capability — evaluate as future opportunity"
        return QueueItem(
            item_id=f"rq-{hashlib.sha1(doc.research_id.encode()).hexdigest()[:10]}",
            topic=doc.title,
            source_research=doc.research_id,
            classification=classification,
            reason=reason,
        )

    def _append_queue_item(self, item: QueueItem) -> None:
        queue_path = self.data_dir / "execution_queue.json"
        items = []
        if queue_path.exists():
            try:
                items = json.loads(queue_path.read_text())
            except Exception:
                items = []
        if not any(i.get("item_id") == item.item_id for i in items):
            items.append(item.to_dict())
            queue_path.write_text(json.dumps(items, indent=2, default=str))

    def execution_queue(self) -> List[Dict[str, Any]]:
        queue_path = self.data_dir / "execution_queue.json"
        if not queue_path.exists():
            return []
        try:
            return json.loads(queue_path.read_text())
        except Exception:
            return []

    # ── Implementation graph ──────────────────────────────────────

    def implementation_graph(self) -> Dict[str, Any]:
        """Traversable graph across the whole research <-> implementation ecosystem."""
        index = self._load_index()
        documents = self.discover_documents()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        satisfaction_refs = self._satisfaction_references()
        for doc in documents:
            nodes.append({
                "id": f"research:{doc.research_id}", "type": "research", "label": doc.title,
                "category": doc.category, "status": doc.status,
            })
            for cap in doc.related_capabilities:
                edges.append({"from": f"research:{doc.research_id}", "to": f"capability:{cap}"})
            for cap in satisfaction_refs.get(doc.research_id, []):
                edges.append({"from": f"research:{doc.research_id}", "to": f"capability:{cap}"})
        for row in self._load_registry():
            cap_id = row["capability_id"]
            nodes.append({"id": f"capability:{cap_id}", "type": "capability", "label": row["name"]})
            links = index.get("capability_links", {}).get(cap_id, {})
            for module in links.get("modules", []):
                edges.append({"from": f"capability:{cap_id}", "to": f"module:{module}"})
            for test in links.get("tests", []):
                edges.append({"from": f"capability:{cap_id}", "to": f"test:{test}"})
        for module in index.get("modules", []):
            nodes.append({"id": f"module:{module}", "type": "module", "label": module})
        for test in index.get("capability_links", {}).values():
            for t in test.get("tests", []):
                nodes.append({"id": f"test:{t}", "type": "test", "label": t})
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def neighbors(self, node_id: str) -> List[str]:
        graph = self.implementation_graph()
        return sorted(
            set(
                edge["to"] for edge in graph["edges"] if edge["from"] == node_id
            ) | set(
                edge["from"] for edge in graph["edges"] if edge["to"] == node_id
            )
        )

    # ── Stats ─────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        documents = self.discover_documents()
        registry = self._load_registry()
        index = self._load_index()
        changes = self.detect_changes()
        satisfaction = index.get("document_satisfaction", {})
        mapped_docs = sum(
            1 for d in documents
            if d.related_capabilities or satisfaction.get(d.research_id, {}).get("capabilities")
        )
        return {
            "research_documents": len(documents),
            "capabilities": len(registry),
            "modules": len(index.get("modules", [])),
            "linked_capabilities": sum(1 for links in index.get("capability_links", {}).values() if links.get("modules")),
            "mapped_documents": mapped_docs,
            "pending_changes": len(changes),
            "queue_items": len(self.execution_queue()),
            "live_research_repo": self.research_repo.exists(),
        }
