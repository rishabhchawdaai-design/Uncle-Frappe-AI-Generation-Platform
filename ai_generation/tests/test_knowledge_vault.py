"""
Tests for the Obsidian knowledge vault synchronization: capability pages
must cover the registry 1:1 and architecture decisions must be recorded
as ADRs for every recent milestone.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _registry_ids():
    text = open(os.path.join(ROOT, "CAPABILITY_REGISTRY.md")).read()
    pattern = re.compile(r"\|\s*([A-Z]{3}-\d+)\s*\|")
    return {m.group(1) for m in pattern.finditer(text)}


def _capability_pages():
    pages_dir = os.path.join(ROOT, "knowledge-vault", "36-Generated", "Capabilities")
    ids = set()
    for name in os.listdir(pages_dir):
        if name.endswith(".md"):
            ids.add(name.split(" - ", 1)[0])
    return ids


def test_capability_pages_cover_registry():
    registry = _registry_ids()
    pages = _capability_pages()
    assert len(registry) == 255
    assert registry <= pages  # every capability has a vault page
    assert pages - registry == set()  # no orphan pages


def test_adrs_record_all_recent_milestones():
    adr_dir = os.path.join(ROOT, "knowledge-vault", "01-Architecture",
                           "Decision-Records")
    adr_text = ""
    for name in os.listdir(adr_dir):
        if name.startswith("ADR-") and name.endswith(".md"):
            adr_text += open(os.path.join(adr_dir, name)).read().lower()
    for topic in ("keyless local cpu backends", "storage and database",
                  "durable event log", "capability graph auto-sync",
                  "compatibility matrix", "truthful research traceability",
                  "verification harness", "optional local-backend dependency"):
        assert topic in adr_text, topic


def test_adr_index_lists_new_records():
    index_path = os.path.join(ROOT, "knowledge-vault", "01-Architecture",
                              "Decision-Records", "ADR Index.md")
    text = open(index_path).read()
    assert 'FROM "01-Architecture/Decision-Records"' in text
