"""
Tests for research <-> implementation traceability: every VERIFIED
capability in CAPABILITY_REGISTRY.md must be linked to at least one
implementation module in the generated research index, and key capability
areas must resolve to their real modules.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

ROOT = Path(__file__).resolve().parent.parent.parent


def _registry_rows() -> dict:
    text = (ROOT / "CAPABILITY_REGISTRY.md").read_text()
    pattern = re.compile(r"\|\s*([A-Z]{3}-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|")
    return {
        m.group(1): {"name": m.group(2).strip(), "status": m.group(4).strip()}
        for m in pattern.finditer(text)
    }


@pytest.fixture
def engine(tmp_path):
    from ai_generation.research_integration import ResearchIntegrationEngine
    eng = ResearchIntegrationEngine(data_dir=str(tmp_path / "ri"))
    eng.build_index()
    return eng


@pytest.fixture
def index(engine):
    return engine._load_index()


def test_every_verified_capability_has_module_links(index):
    rows = _registry_rows()
    unlinked = [
        cap_id for cap_id, row in rows.items()
        if row["status"] == "VERIFIED"
        and not index["capability_links"].get(cap_id, {}).get("modules")
    ]
    assert unlinked == [], f"VERIFIED capabilities missing module links: {unlinked}"


def test_blocked_capabilities_may_stay_unlinked(index):
    rows = _registry_rows()
    blocked_with_links = [
        cap_id for cap_id, row in rows.items()
        if row["status"] == "BLOCKED"
        and index["capability_links"].get(cap_id, {}).get("modules")
    ]
    # blocked capabilities should not claim implementation links
    assert not blocked_with_links


def test_key_capability_to_module_mappings(index):
    expected = {
        "EDT-04": ["image_editing"],
        "AUD-01": ["audio_generation", "local_runtimes"],
        "EXE-05": ["execution_strategies"],
        "SEC-03": ["security"],
        "OBS-01": ["observability"],
        "BRW-02": ["browser_ai"],
        "OCR-07": ["document_intelligence"],
        "MSG-05": ["event_bus"],
        "EDG-04": ["edge_ai"],
        "CGR-07": ["capability_graph", "compatibility_matrix"],
    }
    for cap_id, modules in expected.items():
        got = index["capability_links"].get(cap_id, {}).get("modules", [])
        for module in modules:
            assert module in got, f"{cap_id} should link {module}, got {got}"


def test_trace_capability_returns_modules(engine):
    trace = engine.trace_capability("EDT-04")
    assert trace is not None
    assert trace.name == "Background Removal"
    assert "image_editing" in trace.modules
    assert trace.status == "VERIFIED"


def test_compatibility_matrix_doc_covered(engine, index):
    sat = index["document_satisfaction"].get("COMPATIBILITY_MATRIX", {})
    caps = sat.get("capabilities", [])
    for cap_id in ("CGR-03", "CGR-04", "CGR-07", "RUN-01"):
        assert cap_id in caps
