"""Master health check for all 160 tools across Sections 3-10."""
import asyncio, json, sys
from pathlib import Path

from sections.search_mcp.wrappers.search_tools import SEARCH_REGISTRY
from sections.raipur_data.wrappers.raipur_tools import RAIPUR_REGISTRY
from sections.social_data.wrappers.social_tools import SOCIAL_REGISTRY
from sections.ai_research.wrappers.ai_tools import AI_RESEARCH_REGISTRY
from sections.ocr_docs.wrappers.ocr_tools import OCR_REGISTRY
from sections.knowledge_graph.wrappers.kg_tools import KG_REGISTRY
from sections.data_validation.wrappers.validation_tools import VALIDATION_REGISTRY
from sections.raipur_targets.wrappers.raipur_targets import RAIPUR_TARGETS_REGISTRY

SECTIONS = {
    "Section 3 - Search MCPs": SEARCH_REGISTRY,
    "Section 4 - Raipur Data": RAIPUR_REGISTRY,
    "Section 5 - Social Data": SOCIAL_REGISTRY,
    "Section 6 - AI Research": AI_RESEARCH_REGISTRY,
    "Section 7 - OCR & Docs": OCR_REGISTRY,
    "Section 8 - Knowledge Graph": KG_REGISTRY,
    "Section 9 - Validation": VALIDATION_REGISTRY,
    "Section 10 - Raipur Targets": RAIPUR_TARGETS_REGISTRY,
}

async def health_check_all():
    print("=" * 76)
    print("  RESEARCH MCP STACK — SECTIONS 3-10 MASTER HEALTH CHECK")
    print("=" * 76)
    
    total = 0; ready = 0
    
    for section_name, registry in SECTIONS.items():
        print(f"\n  {section_name} ({len(registry)} tools)")
        print("  " + "-" * 50)
        
        for name, cls in registry.items():
            total += 1
            try:
                tool = cls(config={})
                check = await asyncio.wait_for(tool.health_check(), timeout=3)
                status = check.get("status", "unknown")
                emoji = {"available": "✅"}.get(status, "⚠️")
                if status == "available": ready += 1
                caps = len(check.get("capabilities", []))
                api = "🔑" if check.get("requires_api_key") else "  "
                docker = "🐳" if check.get("requires_docker") else "  "
                mcp = "🔌" if tool.mcp_server else "  "
                print(f"    {emoji} {api}{docker}{mcp} {name:22s} [{status}] {caps} caps")
            except asyncio.TimeoutError:
                print(f"    ⏰    {name:22s} [timeout]")
            except Exception as e:
                print(f"    ❌    {name:22s} [error: {str(e)[:30]}]")
    
    print()
    print("=" * 76)
    print(f"  TOTAL: {total} tools | READY: {ready} | AVAILABILITY: {round(ready/max(total,1)*100,1)}%")
    print("=" * 76)
    return total, ready

if __name__ == "__main__":
    total, ready = asyncio.run(health_check_all())
