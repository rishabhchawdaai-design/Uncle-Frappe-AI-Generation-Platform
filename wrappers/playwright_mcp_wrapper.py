"""5. Playwright MCP - Browser automation via MCP protocol."""
import time
from .base import BaseCollector, CollectorResult

class PlaywrightMCP(BaseCollector):
    name = "playwright_mcp"
    capabilities = ["browser_automation", "js_rendering", "screenshot", "pdf", "multi_browser"]
    requires_docker = True

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=kwargs.get("timeout", 30000))
                content = await page.inner_text("body")
                html = await page.content()
                title = await page.title()
                await browser.close()
                return CollectorResult(
                    url=url, content=content, raw_html=html, title=title,
                    collector=self.name, duration_ms=self._timing(start),
                )
        except ImportError:
            return CollectorResult(url=url, status="error", error="playwright not installed", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
