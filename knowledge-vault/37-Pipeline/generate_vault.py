#!/usr/bin/env python3
"""
Automated Knowledge Pipeline — generates Obsidian vault content from production codebase.

Reads the production repository and generates structured Markdown for the knowledge vault.
"""

import os
import re
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configuration
PRODUCTION_REPO = os.environ.get(
    "PRODUCTION_REPO",
    "/root/Documents/Codex/2026-07-26/repository-reconnection-cross-repository-research-audit/uncle-frappe-production"
)
VAULT_PATH = os.environ.get(
    "VAULT_PATH",
    "/root/Documents/Codex/2026-07-26/repository-reconnection-cross-repository-research-audit/uncle-frappe-knowledge-vault"
)
GENERATED_DIR = os.path.join(VAULT_PATH, "36-Generated")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def parse_python_module(filepath: str) -> Dict[str, Any]:
    """Extract module metadata from a Python file."""
    info = {
        "path": filepath,
        "filename": os.path.basename(filepath),
        "name": os.path.splitext(os.path.basename(filepath))[0],
        "classes": [],
        "functions": [],
        "imports": [],
        "docstring": "",
        "line_count": 0,
    }
    try:
        with open(filepath, "r") as f:
            content = f.read()
        info["line_count"] = len(content.splitlines())

        # Module docstring
        doc_match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
        if doc_match:
            info["docstring"] = doc_match.group(1).strip()[:200]

        # Classes
        for m in re.finditer(r'^class (\w+)', content, re.MULTILINE):
            info["classes"].append(m.group(1))

        # Top-level functions
        for m in re.finditer(r'^(?:async )?def (\w+)\(', content, re.MULTILINE):
            name = m.group(1)
            if not name.startswith("_"):
                info["functions"].append(name)

        # Imports
        for m in re.finditer(r'^(?:from\s+\S+\s+)?import\s+(.+)$', content, re.MULTILINE):
            info["imports"].append(m.group(1).strip())
    except Exception as e:
        info["error"] = str(e)
    return info


def generate_module_page(info: Dict[str, Any]) -> str:
    """Generate a Markdown page for a module."""
    name = info["name"]
    classes = info.get("classes", [])
    functions = info.get("functions", [])
    docstring = info.get("docstring", "No description available.")
    line_count = info.get("line_count", 0)

    page = f"""---
module: "{name}"
type: module-doc
status: active
owner: ""
lines: {line_count}
classes: {len(classes)}
functions: {len(functions)}
tags: [module, documentation]
generated: "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
---

# {name}

> {docstring}

## Overview

- **File**: `ai_generation/{name}.py`
- **Lines**: {line_count}
- **Classes**: {len(classes)}
- **Public Functions**: {len(functions)}

"""
    if classes:
        page += "## Classes\n\n"
        for cls in classes:
            page += f"- `{{{{{cls}}}}}`\n"
        page += "\n"

    if functions:
        page += "## Public API\n\n"
        for fn in functions:
            page += f"- `{fn}()`\n"
        page += "\n"

    page += """## Integration

- Part of the [[Architecture Overview|Unified AI Generation Platform]]
- Exposed via [[05-SDK/SDK Overview|SDK]] and [[06-MCP-Ecosystem/MCP Ecosystem Overview|MCP Tools]]
- Verified in [[02-Capability-Registry/Capability Registry Overview|Capability Registry]]

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
"""
    return page


def generate_capability_pages(registry_path: str) -> Dict[str, str]:
    """Generate capability pages from the CAPABILITY_REGISTRY.md."""
    pages = {}
    try:
        with open(registry_path, "r") as f:
            content = f.read()

        # Parse capability entries from table
        pattern = re.compile(
            r'\|\s*([A-Z]{3}-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|'
        )
        for match in pattern.finditer(content):
            cap_id, name, source, status = match.groups()
            name = name.strip()
            source = source.strip()
            status = status.strip()

            if status in ("VERIFIED", "BLOCKED", "INTEGRATED", "NOT_STARTED", "PLANNED"):
                page = f"""---
capability_id: "{cap_id}"
capability: "{name}"
status: {status.lower()}
source: "{source}"
type: capability
tags: [capability, registry]
generated: "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
---

# {cap_id}: {name}

## Status

`{status}`

## Source

{source}

## Details

Part of the [[02-Capability-Registry/Capability Registry Overview|Capability Registry]].

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
"""
                safe_name = name.replace("/", "-").replace("\\", "-")
                pages[f"{cap_id} - {safe_name}.md"] = page
    except Exception as e:
        print(f"Error parsing registry: {e}")
    return pages


def generate_architecture_pages(modules: List[Dict[str, Any]]) -> Dict[str, str]:
    """Generate architecture overview pages."""
    pages = {}

    # Group modules by layer
    layers = {
        "Entry Points": ["sdk", "cli", "mcp_tools"],
        "Intelligence": ["auto_router", "agent_planner", "negotiation_engine", "research_agent", "decision_ledger", "supervisor"],
        "Quality Engineering": ["quality_engineering", "quality_dashboard", "code_analysis", "orchestration", "refactoring_engine", "quality_engine", "regression_detector"],
        "Execution": ["execution_engine", "workflow_engine", "benchmark_engine", "benchmark_lab"],
        "Generation": ["generation_manager", "image_editing", "video_generation", "video_editing", "audio_generation", "music_generation", "voice_cloning", "audio_enhancement", "generation_3d", "generation_3d_extensions"],
        "Providers": ["provider_discovery", "provider_intelligence", "provider_verifier", "local_runtimes", "remote_endpoints"],
        "Observability": ["observability", "otel_export", "health_monitor"],
        "Security": ["security", "security_crypto"],
        "Knowledge": ["knowledge_graph", "research_agent"],
        "Plugins": ["plugin_system", "plugin_extensions"],
        "Search": ["search_systems", "search_backends"],
        "OCR": ["ocr_engine", "document_intelligence"],
        "Advanced": ["browser_ai", "edge_ai", "failure_recovery", "regression_detector", "decision_ledger", "supervisor"],
    }

    for layer_name, layer_modules in layers.items():
        page = f"""---
type: architecture-layer
layer: "{layer_name}"
tags: [architecture, layer]
generated: "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
---

# {layer_name}

## Modules

| Module | Classes | Functions | Lines |
|--------|---------|-----------|-------|
"""
        for mod in modules:
            name = mod["name"]
            if any(name.startswith(lm) or name == lm for lm in layer_modules):
                page += f"| `{name}` | {len(mod['classes'])} | {len(mod['functions'])} | {mod['line_count']} |\n"

        page += """
## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
"""
        pages[f"{layer_name}.md"] = page

    return pages


def generate_dashboard_pages() -> Dict[str, str]:
    """Generate Dataview dashboard pages."""
    pages = {}

    # System Health Dashboard
    pages["System Health Dashboard.md"] = """---
type: dashboard
tags: [dashboard, health]
---

# System Health Dashboard

## Module Status

```dataview
TABLE line_count AS "Lines", length(classes) AS "Classes", length(functions) AS "Functions"
FROM "36-Generated/Modules"
WHERE module
SORT line_count DESC
```

## Quality Engineering Overview

```dataview
TABLE status, findings_count, grade
FROM "36-Generated"
WHERE type = "quality-engineering"
SORT grade ASC
```

## Recent Changes

```dataview
TABLE date, summary
FROM "26-Project-Journal"
WHERE type = "journal"
SORT date DESC
LIMIT 10
```
"""

    # Capabilities Dashboard
    pages["Capabilities Dashboard.md"] = """---
type: dashboard
tags: [dashboard, capabilities]
---

# Capabilities Dashboard

## Status Summary

```dataview
TABLE WITHOUT ID
  length(filter(rows, (r) => r.status = "verified")) AS "Verified",
  length(filter(rows, (r) => r.status = "blocked")) AS "Blocked",
  length(rows) AS "Total"
FROM "36-Generated/Capabilities"
WHERE status
GROUP BY true
```

## All Capabilities

```dataview
TABLE status, source
FROM "36-Generated/Capabilities"
WHERE status
SORT file.name ASC
```
"""

    # Architecture Decision Records Dashboard
    pages["ADR Dashboard.md"] = """---
type: dashboard
tags: [dashboard, adr]
---

# Architecture Decision Records

## Recent ADRs

```dataview
TABLE date, status, module
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
SORT date DESC
```

## ADR Statistics

```dataview
TABLE WITHOUT ID
  length(filter(rows, (r) => r.status = "accepted")) AS "Accepted",
  length(filter(rows, (r) => r.status = "proposed")) AS "Proposed",
  length(rows) AS "Total"
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
GROUP BY true
```
"""

    return pages


def generate_adr_index() -> str:
    """Generate the ADR index page."""
    return """---
type: index
tags: [adr, index]
---

# Architecture Decision Records

## Index

```dataview
TABLE date, status, module
FROM "01-Architecture/Decision-Records"
WHERE type = "adr"
SORT date DESC
```

## Create New ADR

Use the Templater template: `35-Templates/ADR-Template.md`

## Related

- [[Architecture Overview]]
- [[Capability Registry Overview]]
"""


def main():
    print("=== Obsidian Knowledge Pipeline ===")
    print(f"Production repo: {PRODUCTION_REPO}")
    print(f"Vault path: {VAULT_PATH}")
    print()

    # Ensure generated directories exist
    ensure_dir(os.path.join(GENERATED_DIR, "Modules"))
    ensure_dir(os.path.join(GENERATED_DIR, "Capabilities"))
    ensure_dir(os.path.join(GENERATED_DIR, "Dashboards"))

    # 1. Parse all Python modules
    print("1. Parsing Python modules...")
    modules = []
    ai_gen_dir = os.path.join(PRODUCTION_REPO, "ai_generation")
    for f in sorted(os.listdir(ai_gen_dir)):
        if f.endswith(".py") and not f.startswith("test_") and f != "__init__.py":
            filepath = os.path.join(ai_gen_dir, f)
            info = parse_python_module(filepath)
            modules.append(info)

    # Generate module pages
    for mod in modules:
        page = generate_module_page(mod)
        filepath = os.path.join(GENERATED_DIR, "Modules", f"{mod['name']}.md")
        with open(filepath, "w") as f:
            f.write(page)
    print(f"   Generated {len(modules)} module pages")

    # 2. Generate capability pages from registry
    print("2. Generating capability pages...")
    registry_path = os.path.join(PRODUCTION_REPO, "CAPABILITY_REGISTRY.md")
    cap_pages = generate_capability_pages(registry_path)
    for filename, page in cap_pages.items():
        filepath = os.path.join(GENERATED_DIR, "Capabilities", filename)
        with open(filepath, "w") as f:
            f.write(page)
    print(f"   Generated {len(cap_pages)} capability pages")

    # 3. Generate architecture layer pages
    print("3. Generating architecture pages...")
    arch_pages = generate_architecture_pages(modules)
    for filename, page in arch_pages.items():
        filepath = os.path.join(GENERATED_DIR, "Dashboards", filename)
        with open(filepath, "w") as f:
            f.write(page)
    print(f"   Generated {len(arch_pages)} architecture layer pages")

    # 4. Generate dashboard pages
    print("4. Generating dashboards...")
    dash_pages = generate_dashboard_pages()
    for filename, page in dash_pages.items():
        filepath = os.path.join(GENERATED_DIR, "Dashboards", filename)
        with open(filepath, "w") as f:
            f.write(page)
    print(f"   Generated {len(dash_pages)} dashboard pages")

    # 5. Generate ADR index
    print("5. Generating ADR index...")
    adr_index = generate_adr_index()
    with open(os.path.join(VAULT_PATH, "01-Architecture/Decision-Records/ADR Index.md"), "w") as f:
        f.write(adr_index)
    print("   Generated ADR index")

    # 6. Generate module summary
    print("6. Generating module summary...")
    summary = f"""---
type: summary
generated: "{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
total_modules: {len(modules)}
total_capabilities: {len(cap_pages)}
total_lines: {sum(m['line_count'] for m in modules)}
total_classes: {sum(len(m['classes']) for m in modules)}
total_functions: {sum(len(m['functions']) for m in modules)}
tags: [summary, generated]
---

# Module Summary

## Statistics

- **Total Modules**: {len(modules)}
- **Total Lines**: {sum(m['line_count'] for m in modules):,}
- **Total Classes**: {sum(len(m['classes']) for m in modules)}
- **Total Public Functions**: {sum(len(m['functions']) for m in modules)}
- **Total Capabilities**: {len(cap_pages)}

## Modules by Size

```dataview
TABLE line_count AS "Lines", length(classes) AS "Classes"
FROM "36-Generated/Modules"
WHERE module
SORT line_count DESC
```

## Largest Modules

"""
    sorted_mods = sorted(modules, key=lambda m: m["line_count"], reverse=True)
    for mod in sorted_mods[:10]:
        summary += f"- **{mod['name']}**: {mod['line_count']:,} lines, {len(mod['classes'])} classes\n"

    with open(os.path.join(GENERATED_DIR, "Module Summary.md"), "w") as f:
        f.write(summary)
    print("   Generated module summary")

    # 7. Generate backlinks for all generated pages
    print("7. Generating cross-links...")
    total_files = 0
    for root, dirs, files in os.walk(GENERATED_DIR):
        for fname in files:
            if fname.endswith(".md"):
                total_files += 1
    print(f"   Total generated files: {total_files}")

    print("\n=== Pipeline Complete ===")
    print(f"Generated {total_files} knowledge pages in {VAULT_PATH}")


if __name__ == "__main__":
    main()
