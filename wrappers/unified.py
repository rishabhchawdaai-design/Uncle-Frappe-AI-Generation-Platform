"""
Unified Data Collection Layer
Routes requests across all 20 tools with intelligent fallback, retry, and deduplication.
"""
import asyncio
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .base import BaseCollector, CollectorResult

# ── Tool priority tiers ──────────────────────────────────────────
# Tier 1: Best-in-class dedicated tools (try first)
# Tier 2: Strong general-purpose tools (fallback)
# Tier 3: Lightweight/fast tools (last resort)

TIERS = {
    "tier1": ["firecrawl", "crawl4ai", "playwright_mcp", "brightdata_mcp", "jina_reader"],
    "tier2": ["tavily", "exa", "serpapi", "apify", "selenium", "browser_use", "agentreach"],
    "tier3": ["trafilatura", "newspaper3k", "readability", "requests_html", "scrapy", "bs4", "searxng", "puppeteer_mcp"],
}

# ── Content type → best tool mapping ─────────────────────────────
CONTENT_TYPE_MAP = {
    "news": ["newspaper3k", "trafilatura", "firecrawl"],
    "blog": ["readability", "trafilatura", "jina_reader"],
    "government": ["playwright_mcp", "selenium", "firecrawl"],
    "academic": ["trafilatura", "jina_reader", "firecrawl"],
    "restaurant": ["brightdata_mcp", "serpapi", "crawl4ai"],
    "tourism": ["firecrawl", "crawl4ai", "brightdata_mcp"],
    "social": ["brightdata_mcp", "browser_use", "agentreach"],
    "pdf": ["jina_reader", "firecrawl", "playwright_mcp"],
    "javascript": ["playwright_mcp", "selenium", "crawl4ai"],
    "static": ["trafilatura", "readability", "bs4"],
    "search": ["tavily", "exa", "serpapi", "searxng"],
}


@dataclass
class CollectionPlan:
    url: str
    content_type: str = "static"
    priority_tools: List[str] = field(default_factory=list)
    fallback_tier: str = "tier1"
    max_retries: int = 2
    timeout: float = 30.0


class UnifiedCollector:
    """
    Unified data collection orchestrator.
    Routes to the best tool, handles fallbacks, deduplication, and batch collection.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._collectors: Dict[str, BaseCollector] = {}
        self._results_cache: Dict[str, CollectorResult] = {}
        self._init_collectors()

    def _init_collectors(self):
        """Initialize all available collectors from the registry."""
        from . import COLLECTOR_REGISTRY
        for name, cls in COLLECTOR_REGISTRY.items():
            try:
                tool_config = self.config.get(name, {})
                self._collectors[name] = cls(config=tool_config)
            except Exception:
                pass

    def get_available_tools(self) -> List[str]:
        return list(self._collectors.keys())

    def plan_collection(self, url: str, content_type: str = "static") -> CollectionPlan:
        """Determine the best tool order for a given URL and content type."""
        tools = CONTENT_TYPE_MAP.get(content_type, [])
        if not tools:
            tools = TIERS["tier1"] + TIERS["tier2"]
        available = [t for t in tools if t in self._collectors]
        return CollectionPlan(url=url, content_type=content_type, priority_tools=available or list(self._collectors.keys())[:3])

    async def collect(self, url: str, content_type: str = "static", **kwargs) -> CollectorResult:
        """Collect from the best tool with automatic fallback."""
        if url in self._results_cache:
            return self._results_cache[url]

        plan = self.plan_collection(url, content_type)
        last_error = None

        for tool_name in plan.priority_tools:
            collector = self._collectors.get(tool_name)
            if not collector:
                continue
            try:
                result = await asyncio.wait_for(
                    collector.collect(url, **kwargs),
                    timeout=plan.timeout,
                )
                if result.status == "success" and result.content:
                    self._results_cache[url] = result
                    return result
                last_error = f"{tool_name}: {result.error or 'empty content'}"
            except asyncio.TimeoutError:
                last_error = f"{tool_name}: timeout"
            except Exception as e:
                last_error = f"{tool_name}: {str(e)}"

        return CollectorResult(
            url=url, status="error",
            error=f"All tools failed. Last: {last_error}",
            collector="unified",
        )

    async def batch_collect(self, urls: List[str], content_type: str = "static",
                            concurrency: int = 5, **kwargs) -> List[CollectorResult]:
        """Collect from multiple URLs with controlled concurrency."""
        sem = asyncio.Semaphore(concurrency)

        async def _limited(url):
            async with sem:
                return await self.collect(url, content_type=content_type, **kwargs)

        return await asyncio.gather(*[_limited(u) for u in urls])

    async def health_check_all(self) -> Dict[str, Any]:
        """Health check all 20 tools."""
        results = {}
        for name, collector in self._collectors.items():
            try:
                results[name] = await collector.health_check()
            except Exception as e:
                results[name] = {"tool": name, "status": "error", "error": str(e)}
        return results

    def save_results(self, results: List[CollectorResult], output_dir: str = "output"):
        """Save batch results to disk."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for r in results:
            r.save_result(r, output_dir)
        index = {
            "total": len(results),
            "success": sum(1 for r in results if r.status == "success"),
            "failed": sum(1 for r in results if r.status != "success"),
            "results": [{"url": r.url, "title": r.title, "status": r.status, "collector": r.collector, "duration_ms": r.duration_ms} for r in results],
        }
        (out / "_index.json").write_text(json.dumps(index, indent=2))
