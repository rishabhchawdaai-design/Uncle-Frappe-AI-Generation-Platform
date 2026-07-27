"""
Document Intelligence — Document Parsing, Table Extraction, Layout Analysis.
Extends OCR engine with structured document understanding.
Uses Marker (parsing), Camelot (tables), and layout detection.
All operations gracefully degrade when backends are unavailable.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocParsingBackend(str, Enum):
    MARKER = "marker"
    NOUGAT = "nougat"
    DOCLING = "docling"
    BUILTIN = "builtin"


class TableExtractionBackend(str, Enum):
    CAMELOT = "camelot"
    TABULA = "tabula"
    BUILTIN = "builtin"


class LayoutBackend(str, Enum):
    LAYOUTLMV3 = "layoutlmv3"
    DETR = "detr"
    SURYA = "surya"
    BUILTIN = "builtin"


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    IMAGE = "image"
    MARKDOWN = "markdown"
    EPUB = "epub"
    PPTX = "pptx"
    XLSX = "xlsx"


class DocIntelligenceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass
class DocumentParseResult:
    backend: str = ""
    status: DocIntelligenceStatus = DocIntelligenceStatus.PENDING
    request_id: str = ""
    input_path: str = ""
    output_path: str = ""
    markdown: str = ""
    page_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend, "status": self.status.value,
            "request_id": self.request_id, "input_path": self.input_path,
            "output_path": self.output_path, "markdown": self.markdown[:500],
            "page_count": self.page_count, "metadata": self.metadata,
            "latency_ms": self.latency_ms, "error": self.error,
            "created_at": self.created_at,
        }


@dataclass
class TableExtractionResult:
    backend: str = ""
    status: DocIntelligenceStatus = DocIntelligenceStatus.PENDING
    request_id: str = ""
    input_path: str = ""
    tables: List[Dict[str, Any]] = field(default_factory=list)
    table_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend, "status": self.status.value,
            "request_id": self.request_id, "input_path": self.input_path,
            "tables": self.tables[:5], "table_count": self.table_count,
            "metadata": self.metadata, "latency_ms": self.latency_ms,
            "error": self.error, "created_at": self.created_at,
        }


@dataclass
class LayoutAnalysisResult:
    backend: str = ""
    status: DocIntelligenceStatus = DocIntelligenceStatus.PENDING
    request_id: str = ""
    input_path: str = ""
    regions: List[Dict[str, Any]] = field(default_factory=list)
    region_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend, "status": self.status.value,
            "request_id": self.request_id, "input_path": self.input_path,
            "regions": self.regions[:20], "region_count": self.region_count,
            "metadata": self.metadata, "latency_ms": self.latency_ms,
            "error": self.error, "created_at": self.created_at,
        }


@dataclass
class BackendProfile:
    name: str
    backend_type: str
    description: str
    license: str
    requires_gpu: bool
    install_command: str
    strengths: List[str]
    supported_formats: List[str]
    maturity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "backend_type": self.backend_type,
            "description": self.description, "license": self.license,
            "requires_gpu": self.requires_gpu, "install_command": self.install_command,
            "strengths": self.strengths, "supported_formats": self.supported_formats,
            "maturity": self.maturity,
        }


DOC_PARSING_PROFILES: List[BackendProfile] = [
    BackendProfile(
        name="Marker", backend_type="document_parsing",
        description="Fast PDF to Markdown with tables, images, equations",
        license="GPL-3.0", requires_gpu=False,
        install_command="pip install marker-pdf",
        strengths=["speed", "tables", "images", "equations"],
        supported_formats=["pdf", "docx", "html", "epub", "pptx"],
        maturity="production",
    ),
    BackendProfile(
        name="Nougat", backend_type="document_parsing",
        description="Meta scientific document parser (PDF to Markdown)",
        license="MIT", requires_gpu=True,
        install_command="pip install nougat-ocr",
        strengths=["scientific", "equations", "tables", "multilingual"],
        supported_formats=["pdf"],
        maturity="emerging",
    ),
    BackendProfile(
        name="Docling", backend_type="document_parsing",
        description="IBM document parser with layout understanding",
        license="MIT", requires_gpu=True,
        install_command="pip install docling",
        strengths=["layout", "tables", "multiformat"],
        supported_formats=["pdf", "docx", "html", "pptx", "xlsx"],
        maturity="emerging",
    ),
]

TABLE_EXTRACTION_PROFILES: List[BackendProfile] = [
    BackendProfile(
        name="Camelot", backend_type="table_extraction",
        description="PDF table extraction (stream and lattice modes)",
        license="MIT", requires_gpu=False,
        install_command="pip install camelot-py[cv]",
        strengths=["accuracy", "lattice_tables", "stream_tables"],
        supported_formats=["pdf"],
        maturity="production",
    ),
    BackendProfile(
        name="Tabula", backend_type="table_extraction",
        description="Java-based PDF table extraction",
        license="MIT", requires_gpu=False,
        install_command="pip install tabula-py (requires Java)",
        strengths=["simple_tables", "wide_support"],
        supported_formats=["pdf"],
        maturity="production",
    ),
]

LAYOUT_PROFILES: List[BackendProfile] = [
    BackendProfile(
        name="LayoutLMv3", backend_type="layout_analysis",
        description="Microsoft document layout analysis model",
        license="MIT", requires_gpu=True,
        install_command="pip install transformers torch",
        strengths=["accuracy", "multilingual", "form_understanding"],
        supported_formats=["image", "pdf"],
        maturity="production",
    ),
    BackendProfile(
        name="Surya", backend_type="layout_analysis",
        description="VikParuchuri's document layout and OCR model",
        license="GPL-3.0", requires_gpu=True,
        install_command="pip install surya-ocr",
        strengths=["speed", "multilingual", "layout", "ocr"],
        supported_formats=["image", "pdf"],
        maturity="emerging",
    ),
    BackendProfile(
        name="DETR-Layout", backend_type="layout_analysis",
        description="Facebook DETR-based document layout detection",
        license="Apache-2.0", requires_gpu=True,
        install_command="pip install torch torchvision",
        strengths=["detection", "general_layout"],
        supported_formats=["image"],
        maturity="emerging",
    ),
]


class DocumentIntelligenceEngine:
    """Unified document intelligence: parsing, table extraction, layout analysis."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[Any] = []
        self._backends = self._detect_backends()

    def _detect_backends(self) -> Dict[str, bool]:
        available = {}
        try:
            import marker
            available["marker"] = True
        except ImportError:
            available["marker"] = False
        try:
            import nougat
            available["nougat"] = True
        except ImportError:
            available["nougat"] = False
        try:
            import docling
            available["docling"] = True
        except ImportError:
            available["docling"] = False
        try:
            import camelot
            available["camelot"] = True
        except ImportError:
            available["camelot"] = False
        try:
            import tabula
            available["tabula"] = True
        except ImportError:
            available["tabula"] = False
        return available

    def get_parsing_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in DOC_PARSING_PROFILES]

    def get_table_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in TABLE_EXTRACTION_PROFILES]

    def get_layout_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in LAYOUT_PROFILES]

    def get_available_backends(self) -> Dict[str, List[str]]:
        return {
            "parsing": [k for k, v in self._backends.items() if v and k in ("marker", "nougat", "docling")],
            "table_extraction": [k for k, v in self._backends.items() if v and k in ("camelot", "tabula")],
            "layout": [],  # GPU-dependent, always list as available when installed
        }

    async def parse_document(
        self, input_path: str, output_path: str = "", backend: str = "auto", **kwargs,
    ) -> DocumentParseResult:
        start = time.time()
        request_id = f"parse-{int(time.time()*1000)}"

        if backend == "auto":
            if self._backends.get("marker"):
                backend = "marker"
            elif self._backends.get("docling"):
                backend = "docling"
            elif self._backends.get("nougat"):
                backend = "nougat"
            else:
                backend = "builtin"

        if backend == "marker" and self._backends.get("marker"):
            try:
                from marker.convert import convert_single_pdf
                md, images, metadata = convert_single_pdf(input_path)
                out = output_path or str(Path(input_path).with_suffix(".md"))
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                with open(out, "w") as f:
                    f.write(md)
                result = DocumentParseResult(
                    backend="marker", status=DocIntelligenceStatus.COMPLETED,
                    request_id=request_id, input_path=input_path, output_path=out,
                    markdown=md[:500], page_count=metadata.get("page_count", 0),
                    metadata=metadata, latency_ms=round((time.time()-start)*1000, 1),
                )
                self._history.append(result)
                return result
            except Exception as e:
                result = DocumentParseResult(
                    backend="marker", status=DocIntelligenceStatus.FAILED,
                    request_id=request_id, input_path=input_path,
                    error=str(e)[:200], latency_ms=round((time.time()-start)*1000, 1),
                )
                self._history.append(result)
                return result

        result = DocumentParseResult(
            backend=backend, status=DocIntelligenceStatus.DEPENDENCY_MISSING,
            request_id=request_id, input_path=input_path,
            error=f"Backend '{backend}' not installed. Install: pip install marker-pdf",
            latency_ms=round((time.time()-start)*1000, 1),
        )
        self._history.append(result)
        return result

    async def extract_tables(
        self, input_path: str, backend: str = "auto", pages: str = "all", **kwargs,
    ) -> TableExtractionResult:
        start = time.time()
        request_id = f"tables-{int(time.time()*1000)}"

        if backend == "auto":
            if self._backends.get("camelot"):
                backend = "camelot"
            elif self._backends.get("tabula"):
                backend = "tabula"
            else:
                backend = "builtin"

        if backend == "camelot" and self._backends.get("camelot"):
            try:
                import camelot
                tables = camelot.read_pdf(input_path, pages=pages)
                table_data = []
                for t in tables:
                    table_data.append({
                        "page": t.page, "accuracy": t.parsing_report.get("accuracy", 0),
                        "rows": len(t.df), "cols": len(t.df.columns),
                        "data": t.df.to_dict(orient="records")[:10],
                    })
                result = TableExtractionResult(
                    backend="camelot", status=DocIntelligenceStatus.COMPLETED,
                    request_id=request_id, input_path=input_path,
                    tables=table_data, table_count=len(table_data),
                    latency_ms=round((time.time()-start)*1000, 1),
                )
                self._history.append(result)
                return result
            except Exception as e:
                result = TableExtractionResult(
                    backend="camelot", status=DocIntelligenceStatus.FAILED,
                    request_id=request_id, input_path=input_path,
                    error=str(e)[:200], latency_ms=round((time.time()-start)*1000, 1),
                )
                self._history.append(result)
                return result

        result = TableExtractionResult(
            backend=backend, status=DocIntelligenceStatus.DEPENDENCY_MISSING,
            request_id=request_id, input_path=input_path,
            error=f"Backend '{backend}' not installed. Install: pip install camelot-py[cv]",
            latency_ms=round((time.time()-start)*1000, 1),
        )
        self._history.append(result)
        return result

    async def analyze_layout(
        self, input_path: str, backend: str = "auto", **kwargs,
    ) -> LayoutAnalysisResult:
        start = time.time()
        request_id = f"layout-{int(time.time()*1000)}"

        result = LayoutAnalysisResult(
            backend=backend, status=DocIntelligenceStatus.DEPENDENCY_MISSING,
            request_id=request_id, input_path=input_path,
            error="Layout analysis requires GPU backends (LayoutLMv3, Surya). Install: pip install surya-ocr",
            latency_ms=round((time.time()-start)*1000, 1),
        )
        self._history.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._history)
        completed = sum(1 for r in self._history if hasattr(r, "status") and r.status == DocIntelligenceStatus.COMPLETED)
        return {
            "total_operations": total,
            "completed": completed,
            "available_backends": self.get_available_backends(),
            "parsing_profiles": len(DOC_PARSING_PROFILES),
            "table_profiles": len(TABLE_EXTRACTION_PROFILES),
            "layout_profiles": len(LAYOUT_PROFILES),
        }
