"""
Unified Browser Agent Orchestrator
Routes browser tasks to the best agent with capability-based matching.
"""
import asyncio
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from wrappers.base import BaseBrowserAgent, BrowserResult, BrowserCapability
from wrappers import AGENT_REGISTRY

# ── Capability → Agent priority mapping ──────────────────────────
CAPABILITY_MAP = {
    BrowserCapability.LOGIN: ["playwright", "selenium", "browser_use", "open_operator", "skyvern"],
    BrowserCapability.SCROLLING: ["playwright", "selenium", "puppeteer", "helium", "camoufox"],
    BrowserCapability.SCREENSHOT: ["playwright", "puppeteer", "selenium", "omniparser", "vision_browser"],
    BrowserCapability.PDF_DOWNLOAD: ["playwright", "puppeteer", "browserless"],
    BrowserCapability.CAPTCHA_DETECTION: ["vision_browser", "playwright", "selenium", "steel"],
    BrowserCapability.SESSION_PERSIST: ["playwright", "selenium", "open_operator", "steel"],
    BrowserCapability.COOKIE_MANAGEMENT: ["playwright", "puppeteer", "selenium", "helium"],
    BrowserCapability.FILE_DOWNLOAD: ["playwright", "selenium", "puppeteer"],
    BrowserCapability.HUMAN_LIKE: ["camoufox", "steel", "helium", "skyvern", "vision_browser"],
    BrowserCapability.PARALLEL: ["playwright", "selenium", "browserless"],
    BrowserCapability.RECORDING: ["playwright", "puppeteer", "selenium"],
    BrowserCapability.STRUCTURED_EXTRACTION: ["stagehand", "playwright", "skyvern", "omniparser", "autogen_browser"],
    BrowserCapability.AUTO_RETRY: ["playwright", "selenium", "skyvern", "autogen_browser"],
    BrowserCapability.HEALTH_MONITOR: ["playwright", "selenium"],
    BrowserCapability.JS_RENDERING: ["playwright", "puppeteer", "selenium", "chromium_remote"],
    BrowserCapability.FORM_FILLING: ["playwright", "selenium", "puppeteer", "browser_use"],
    BrowserCapability.MULTI_TAB: ["playwright", "selenium"],
    BrowserCapability.PROXY_SUPPORT: ["playwright", "puppeteer", "selenium", "steel", "camoufox"],
    BrowserCapability.STEALTH: ["camoufox", "steel", "chromium_remote"],
}

# ── Task type → Agent routing ───────────────────────────────────
TASK_ROUTING = {
    "simple_fetch": ["playwright", "puppeteer", "selenium"],
    "login_form": ["playwright", "selenium", "browser_use", "skyvern"],
    "infinite_scroll": ["playwright", "selenium", "helium"],
    "screenshot_capture": ["playwright", "vision_browser", "omniparser"],
    "pdf_generation": ["playwright", "puppeteer", "browserless"],
    "captcha_solve": ["vision_browser", "skyvern", "browser_use"],
    "multi_step_form": ["skyvern", "playwright", "autogen_browser"],
    "structured_data": ["stagehand", "playwright", "skyvern"],
    "stealth_scraping": ["camoufox", "steel", "chromium_remote"],
    "ai_guided": ["browser_use", "autogen_browser", "langgraph_browser", "crewai_browser"],
    "parallel_browse": ["playwright", "browserless", "selenium"],
    "session_resume": ["playwright", "selenium", "steel"],
}


class UnifiedBrowserAgent:
    """Orchestrator for all 20 browser agents with capability routing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._agents: Dict[str, BaseBrowserAgent] = {}
        self._results_cache: Dict[str, BrowserResult] = {}
        self._init_agents()

    def _init_agents(self):
        for name, cls in AGENT_REGISTRY.items():
            try:
                agent_config = self.config.get(name, {})
                self._agents[name] = cls(config=agent_config)
            except Exception:
                pass

    def get_available_agents(self) -> List[str]:
        return list(self._agents.keys())

    def get_agents_with_capability(self, capability: BrowserCapability) -> List[str]:
        return [name for name, agent in self._agents.items() if capability in agent.capabilities]

    def route_task(self, task_type: str, required_capabilities: Optional[List[BrowserCapability]] = None) -> List[str]:
        """Determine the best agents for a task."""
        candidates = []

        if task_type in TASK_ROUTING:
            candidates = [a for a in TASK_ROUTING[task_type] if a in self._agents]

        if required_capabilities:
            cap_scores = {}
            for name, agent in self._agents.items():
                score = sum(1 for cap in required_capabilities if cap in agent.capabilities)
                if score > 0:
                    cap_scores[name] = score
            cap_ranked = sorted(cap_scores, key=cap_scores.get, reverse=True)
            candidates = list(dict.fromkeys(candidates + cap_ranked))

        if not candidates:
            candidates = list(self._agents.keys())

        return candidates

    async def navigate(self, url: str, task_type: str = "simple_fetch", **kwargs) -> BrowserResult:
        """Navigate using the best agent for the task."""
        if url in self._results_cache and not kwargs.get("force"):
            return self._results_cache[url]

        agents = self.route_task(task_type)
        last_error = None

        for agent_name in agents[:3]:
            agent = self._agents.get(agent_name)
            if not agent:
                continue
            try:
                result = await asyncio.wait_for(
                    agent.navigate(url, **kwargs),
                    timeout=kwargs.get("timeout", 30),
                )
                if result.status == "success" and result.content:
                    self._results_cache[url] = result
                    return result
                last_error = f"{agent_name}: {result.error or 'empty'}"
            except asyncio.TimeoutError:
                last_error = f"{agent_name}: timeout"
            except Exception as e:
                last_error = f"{agent_name}: {str(e)[:80]}"

        return BrowserResult(url=url, status="error", error=f"All agents failed. Last: {last_error}", agent="unified")

    async def login(self, url: str, credentials: dict, **kwargs) -> BrowserResult:
        agents = self.route_task("login_form")
        for agent_name in agents[:3]:
            agent = self._agents.get(agent_name)
            if not agent:
                continue
            try:
                result = await asyncio.wait_for(
                    agent.login(url, credentials, **kwargs),
                    timeout=kwargs.get("timeout", 30),
                )
                if result.status == "success":
                    return result
            except Exception:
                continue
        return BrowserResult(url=url, status="error", error="Login failed on all agents", agent="unified")

    async def take_screenshot(self, url: str, **kwargs) -> BrowserResult:
        agents = self.route_task("screenshot_capture")
        for agent_name in agents[:3]:
            agent = self._agents.get(agent_name)
            if not agent:
                continue
            try:
                result = await asyncio.screenshot(url, take_screenshot=True, full_page=kwargs.get("full_page", False))
                if result.screenshot:
                    return result
            except Exception:
                continue
        return await self.navigate(url, take_screenshot=True, **kwargs)

    async def scroll_and_extract(self, url: str, max_scrolls: int = 20, **kwargs) -> BrowserResult:
        return await self.navigate(url, task_type="infinite_scroll", auto_scroll=True, max_scrolls=max_scrolls, **kwargs)

    async def detect_captcha(self, url: str, **kwargs) -> BrowserResult:
        vision = self._agents.get("vision_browser")
        if vision:
            try:
                return await vision.detect_captcha(url, **kwargs)
            except Exception:
                pass
        return await self.navigate(url, task_type="captcha_solve", **kwargs)

    async def batch_navigate(self, urls: List[str], task_type: str = "simple_fetch",
                             concurrency: int = 5, **kwargs) -> List[BrowserResult]:
        sem = asyncio.Semaphore(concurrency)
        async def _limited(url):
            async with sem:
                return await self.navigate(url, task_type=task_type, **kwargs)
        return await asyncio.gather(*[_limited(u) for u in urls])

    async def health_check_all(self) -> Dict[str, Any]:
        results = {}
        for name, agent in self._agents.items():
            try:
                results[name] = await asyncio.wait_for(agent.health_check(), timeout=3)
            except asyncio.TimeoutError:
                results[name] = {"agent": name, "status": "timeout"}
            except Exception as e:
                results[name] = {"agent": name, "status": "error", "error": str(e)[:100]}
        return results

    def save_results(self, results: List[BrowserResult], output_dir: str = "output"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for r in results:
            safe = r.url.replace("https://", "").replace("http://", "").replace("/", "_")[:80]
            (out / f"{safe}.json").write_text(json.dumps(r.to_dict(), indent=2))
        index = {
            "total": len(results),
            "success": sum(1 for r in results if r.status == "success"),
            "results": [r.to_dict() for r in results],
        }
        (out / "_index.json").write_text(json.dumps(index, indent=2))
