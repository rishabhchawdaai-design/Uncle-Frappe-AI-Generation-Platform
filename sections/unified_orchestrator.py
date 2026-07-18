"""
Unified Research Orchestrator — Sections 3-10
Routes queries across all 160 tools with capability matching.
"""
import asyncio, json, time
from pathlib import Path
from typing import Optional, Dict, Any, List
from sections.base import BaseTool, ToolResult, ToolCategory

# ── Import all registries ────────────────────────────────────────
from sections.search_mcp.wrappers.search_tools import SEARCH_REGISTRY
from sections.raipur_data.wrappers.raipur_tools import RAIPUR_REGISTRY
from sections.social_data.wrappers.social_tools import SOCIAL_REGISTRY
from sections.ai_research.wrappers.ai_tools import AI_RESEARCH_REGISTRY
from sections.ocr_docs.wrappers.ocr_tools import OCR_REGISTRY
from sections.knowledge_graph.wrappers.kg_tools import KG_REGISTRY
from sections.data_validation.wrappers.validation_tools import VALIDATION_REGISTRY
from sections.raipur_targets.wrappers.raipur_targets import RAIPUR_TARGETS_REGISTRY

ALL_REGISTRIES = {
    "search": SEARCH_REGISTRY,
    "raipur_data": RAIPUR_REGISTRY,
    "social": SOCIAL_REGISTRY,
    "ai_research": AI_RESEARCH_REGISTRY,
    "ocr": OCR_REGISTRY,
    "knowledge_graph": KG_REGISTRY,
    "validation": VALIDATION_REGISTRY,
    "raipur_targets": RAIPUR_TARGETS_REGISTRY,
}

# ── Category → best tools mapping ────────────────────────────────
CATEGORY_ROUTING = {
    "search": ["exa", "tavily", "brave", "serper", "jina"],
    "local_business": ["google_maps", "justdial", "zomato", "foursquare"],
    "news": ["google_pse", "tavily", "serper", "x"],
    "social": ["reddit", "x", "youtube", "bluesky", "hackernews"],
    "government": ["cg_gov", "smart_city", "raipur_mc", "data_gov_in"],
    "academic": ["openalex", "semantic_scholar", "crossref", "europepmc"],
    "restaurants": ["zomato", "swiggy", "google_maps", "justdial"],
    "document": ["docling", "pymupdf", "pdfplumber", "unstructured"],
    "image_ocr": ["tesseract", "paddleocr", "easyocr", "surya"],
    "graph": ["neo4j", "chroma", "weaviate", "qdrant"],
    "validation": ["deduplication", "fact_check", "hallucination", "url_health"],
    "ai_agent": ["gpt_researcher", "deep_research", "openhands", "crewai"],
}


class UnifiedOrchestrator:
    """Master orchestrator across all 160 tools (Sections 3-10)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._tools: Dict[str, BaseTool] = {}
        self._init_tools()

    def _init_tools(self):
        for category, registry in ALL_REGISTRIES.items():
            for name, cls in registry.items():
                try:
                    tool_config = self.config.get(name, {})
                    self._tools[name] = cls(config=tool_config)
                except Exception:
                    pass

        # Wire up Raipur targets with search dependencies
        for name in ["restaurants","cafes","hotels","cloud_kitchens","bakeries","food_trucks","street_food",
                      "shopping_malls","markets","colleges","schools","hospitals","tourist_places","events",
                      "festivals","startups","it_companies","government_offices","local_news","business_intelligence"]:
            tool = self._tools.get(name)
            if tool and hasattr(tool, '_set_dependencies'):
                tool._set_dependencies(SEARCH_REGISTRY, RAIPUR_REGISTRY)

    def get_all_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_tool_count(self) -> int:
        return len(self._tools)

    def get_category_tools(self, category: str) -> List[str]:
        return [name for name, tool in self._tools.items() if tool.category.value == category]

    async def search(self, query: str, category: str = "search", **kwargs) -> ToolResult:
        tools = self.get_category_tools(category)
        if not tools:
            tools = CATEGORY_ROUTING.get(category, [])[:3]

        for name in tools[:3]:
            tool = self._tools.get(name)
            if tool:
                try:
                    result = await asyncio.wait_for(tool.search(query, **kwargs), timeout=30)
                    if result.status == "success":
                        return result
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass

        return ToolResult(source=query, status="error", error="All tools failed", tool="orchestrator")

    async def multi_search(self, query: str, categories: List[str], **kwargs) -> Dict[str, ToolResult]:
        tasks = {}
        for cat in categories:
            tasks[cat] = self.search(query, category=cat, **kwargs)
        results = {}
        for cat, coro in tasks.items():
            try:
                results[cat] = await asyncio.wait_for(coro, timeout=60)
            except asyncio.TimeoutError:
                results[cat] = ToolResult(source=query, status="error", error="timeout", tool=cat)
        return results

    async def raipur_research(self, target: str, **kwargs) -> ToolResult:
        return await self.search(target, category="raipur_targets", target=target, **kwargs)

    async def full_raipur_research(self, **kwargs) -> Dict[str, Any]:
        targets = list(RAIPUR_QUERIES.keys())
        results = {}
        for t in targets:
            try:
                results[t] = await self.raipur_research(t, **kwargs)
            except Exception as e:
                results[t] = ToolResult(source=t, status="error", error=str(e), tool="raipur_research")
        return results

    async def health_check_all(self) -> Dict[str, Any]:
        results = {}
        for name, tool in self._tools.items():
            try:
                results[name] = await asyncio.wait_for(tool.health_check(), timeout=3)
            except asyncio.TimeoutError:
                results[name] = {"tool": name, "status": "timeout"}
            except Exception as e:
                results[name] = {"tool": name, "status": "error", "error": str(e)[:100]}
        return results

    def get_stats(self) -> Dict[str, Any]:
        stats = {"total": len(self._tools), "by_category": {}}
        for name, tool in self._tools.items():
            cat = tool.category.value
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        return stats

from sections.raipur_targets.wrappers.raipur_targets import RAIPUR_QUERIES
