"""6. Puppeteer MCP - Chrome DevTools Protocol browser automation."""
import time
from .base import BaseCollector, CollectorResult

class PuppeteerMCP(BaseCollector):
    name = "puppeteer_mcp"
    capabilities = ["chrome_automation", "js_rendering", "screenshot", "pdf"]
    requires_docker = True

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from pyppeteer import launch
            browser = await launch(headless=True, args=["--no-sandbox"])
            page = await browser.newPage()
            await page.goto(url, {"waitUntil": "networkidle0", "timeout": kwargs.get("timeout", 30000)})
            content = await page.evaluate("() => document.body.innerText")
            html = await page.content()
            title = await page.title()
            await browser.close()
            return CollectorResult(
                url=url, content=content, raw_html=html, title=title,
                collector=self.name, duration_ms=self._timing(start),
            )
        except ImportError:
            return CollectorResult(url=url, status="error", error="pyppeteer not installed", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
