"""
Health Check System for all 20 data collection tools.
Checks availability, connectivity, and capability status.
"""
import asyncio
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from wrappers import COLLECTOR_REGISTRY

TOOL_INFO = {
    "firecrawl":       {"tier": 1, "needs": "API key (FIRECRAWL_API_KEY)", "docker": True},
    "crawl4ai":        {"tier": 1, "needs": "pip install crawl4ai + browsers", "docker": True},
    "browser_use":     {"tier": 2, "needs": "pip install browser-use + browser", "docker": False},
    "agentreach":      {"tier": 2, "needs": "pip install agentreach", "docker": False},
    "playwright_mcp":  {"tier": 1, "needs": "pip install playwright + browsers", "docker": True},
    "puppeteer_mcp":   {"tier": 1, "needs": "pip install pyppeteer", "docker": True},
    "brightdata_mcp":  {"tier": 1, "needs": "API key (BRIGHT_DATA_API_KEY)", "docker": False},
    "jina_reader":     {"tier": 1, "needs": "API key (JINA_API_KEY) or free tier", "docker": False},
    "tavily":          {"tier": 2, "needs": "API key (TAVILY_API_KEY)", "docker": False},
    "exa":             {"tier": 2, "needs": "API key (EXA_API_KEY)", "docker": False},
    "serpapi":         {"tier": 2, "needs": "API key (SERPAPI_KEY)", "docker": False},
    "searxng":         {"tier": 3, "needs": "Docker service on port 8080", "docker": True},
    "apify":           {"tier": 2, "needs": "API key (APIFY_TOKEN)", "docker": True},
    "scrapy":          {"tier": 3, "needs": "pip install scrapy", "docker": False},
    "selenium":        {"tier": 2, "needs": "Docker grid or chromedriver", "docker": True},
    "trafilatura":     {"tier": 3, "needs": "pip install trafilatura", "docker": False},
    "newspaper3k":     {"tier": 3, "needs": "pip install newspaper3k", "docker": False},
    "readability":     {"tier": 3, "needs": "pip install readability-lxml", "docker": False},
    "requests_html":   {"tier": 3, "needs": "pip install requests-html", "docker": False},
    "bs4":             {"tier": 3, "needs": "pip install beautifulsoup4", "docker": False},
}


async def check_all():
    """Run health checks on all registered collectors."""
    print("=" * 70)
    print("  RESEARCH MCP STACK — DATA COLLECTION HEALTH CHECK")
    print("  20 Tools | Unified Collector | MCP Adapters")
    print("=" * 70)
    print()

    results = {}
    healthy = 0
    total = len(COLLECTOR_REGISTRY)

    for name, cls in COLLECTOR_REGISTRY.items():
        info = TOOL_INFO.get(name, {})
        tier = info.get("tier", "?")
        try:
            collector = cls(config={})
            check = await asyncio.wait_for(collector.health_check(), timeout=5)
            status = check.get("status", "unknown")
            emoji = {"healthy": "✅", "needs_api_key": "🔑", "available": "✅"}.get(status, "⚠️")
            if status in ("healthy", "available"):
                healthy += 1
        except asyncio.TimeoutError:
            status = "timeout"
            emoji = "⏰"
        except Exception as e:
            status = "error"
            emoji = "❌"

        results[name] = {"tier": tier, "status": status, "needs": info.get("needs", ""), "docker": info.get("docker", False)}
        print(f"  {emoji}  T{tier}  {name:18s}  [{status:15s}]  {info.get('needs', '')}")

    print()
    print(f"  Result: {healthy}/{total} tools ready")
    print(f"  T1 (Best):  {sum(1 for n,i in TOOL_INFO.items() if i['tier']==1 and results.get(n,{}).get('status') in ('healthy','available'))}/6 ready")
    print(f"  T2 (Strong): {sum(1 for n,i in TOOL_INFO.items() if i['tier']==2 and results.get(n,{}).get('status') in ('healthy','available'))}/7 ready")
    print(f"  T3 (Fast):   {sum(1 for n,i in TOOL_INFO.items() if i['tier']==3 and results.get(n,{}).get('status') in ('healthy','available'))}/7 ready")
    print("=" * 70)

    report = Path(__file__).parent / "health_report.json"
    report.write_text(json.dumps(results, indent=2))
    print(f"\n  Report saved: {report}")
    return results


if __name__ == "__main__":
    asyncio.run(check_all())
