"""5. Stagehand - Browser automation framework with AI extraction."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class StagehandAgent(BaseBrowserAgent):
    name = "stagehand"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.STRUCTURED_EXTRACTION,
        BrowserCapability.JS_RENDERING, BrowserCapability.CAPTCHA_DETECTION,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post("http://localhost:7777/navigate", json={"url": url, "options": kwargs})
                data = resp.json()
                return BrowserResult(
                    url=url, content=data.get("content", ""), html=data.get("html", ""),
                    title=data.get("title", ""), agent=self.name,
                    duration_ms=self._timing(start), extracted_data=data.get("extracted", {}),
                )
        except httpx.ConnectError:
            return BrowserResult(url=url, status="error",
                error="Stagehand server not running. Install: npm install @browserbasehq/stagehand",
                agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))

    async def extract_structured(self, url: str, schema: dict, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post("http://localhost:7777/extract", json={"url": url, "schema": schema})
                data = resp.json()
                return BrowserResult(url=url, content=data.get("content", ""),
                    extracted_data=data.get("data", {}), agent=self.name,
                    duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
