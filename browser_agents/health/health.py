"""Health check system for all 20 browser agents."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from wrappers import AGENT_REGISTRY

AGENT_INFO = {
    "browser_use":       {"tier": 1, "needs": "pip install browser-use + browser", "docker": False},
    "agentreach":        {"tier": 2, "needs": "pip install agentreach", "docker": False},
    "open_operator":     {"tier": 1, "needs": "pip install playwright", "docker": False},
    "openhands":         {"tier": 1, "needs": "Docker: openhands service", "docker": True},
    "stagehand":         {"tier": 1, "needs": "npm install @anthropic-ai/stagehand", "docker": True},
    "playwright":        {"tier": 1, "needs": "pip install playwright + browsers", "docker": False},
    "puppeteer":         {"tier": 1, "needs": "pip install pyppeteer", "docker": False},
    "chromium_remote":   {"tier": 2, "needs": "Chrome on port 9222", "docker": True},
    "browserless":       {"tier": 1, "needs": "Docker: browserless service", "docker": True},
    "steel":             {"tier": 1, "needs": "Docker: steel service", "docker": True},
    "camoufox":          {"tier": 1, "needs": "pip install camoufox", "docker": False},
    "selenium":          {"tier": 1, "needs": "Docker Selenium Grid or chromedriver", "docker": True},
    "helium":            {"tier": 2, "needs": "pip install helium[all]", "docker": False},
    "browserpilot":      {"tier": 2, "needs": "pip install browserpilot", "docker": False},
    "autogen_browser":   {"tier": 2, "needs": "pip install pyautogen", "docker": False},
    "langgraph_browser": {"tier": 2, "needs": "pip install langchain-community", "docker": False},
    "crewai_browser":    {"tier": 2, "needs": "pip install crewai crewai-tools", "docker": False},
    "skyvern":           {"tier": 1, "needs": "Docker: skyvern service", "docker": True},
    "omniparser":        {"tier": 1, "needs": "Docker: omniparser + GPU", "docker": True},
    "vision_browser":    {"tier": 1, "needs": "pip install playwright + OpenAI API key", "docker": False},
}


async def check_all():
    print("=" * 72)
    print("  RESEARCH MCP STACK — BROWSER AGENTS HEALTH CHECK")
    print("  20 Tools | Unified Agent | Capability Modules")
    print("=" * 72)
    print()

    results = {}
    healthy = 0
    total = len(AGENT_REGISTRY)

    for name, cls in AGENT_REGISTRY.items():
        info = AGENT_INFO.get(name, {})
        tier = info.get("tier", "?")
        try:
            agent = cls(config={})
            check = await asyncio.wait_for(agent.health_check(), timeout=3)
            status = check.get("status", "unknown")
            caps = len(check.get("capabilities", []))
            emoji = {"available": "✅", "healthy": "✅"}.get(status, "⚠️")
            if status in ("available", "healthy"):
                healthy += 1
            print(f"  {emoji}  T{tier}  {name:20s}  [{status:12s}]  {caps:2d} caps  {info.get('needs', '')}")
        except asyncio.TimeoutError:
            print(f"  ⏰  T{tier}  {name:20s}  [timeout     ]  {info.get('needs', '')}")
            results[name] = {"tier": tier, "status": "timeout"}
        except Exception as e:
            print(f"  ❌  T{tier}  {name:20s}  [error       ]  {str(e)[:40]}")
            results[name] = {"tier": tier, "status": "error", "error": str(e)[:100]}

    print()
    print(f"  Result: {healthy}/{total} agents ready")
    print("=" * 72)

    report = Path(__file__).parent / "health_report.json"
    report.write_text(json.dumps(results, indent=2))
    print(f"\n  Report: {report}")
    return results


if __name__ == "__main__":
    asyncio.run(check_all())
