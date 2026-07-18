"""14. BrowserPilot - Natural language browser automation."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class BrowserPilotAgent(BaseBrowserAgent):
    name = "browserpilot"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.STRUCTURED_EXTRACTION,
        BrowserCapability.HUMAN_LIKE,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            task = kwargs.get("task", f"Go to {url} and extract all content")
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post("http://localhost:8889/execute", json={"task": task, "url": url})
                data = resp.json()
                return BrowserResult(
                    url=url, content=data.get("output", ""), agent=self.name,
                    duration_ms=self._timing(start),
                )
        except httpx.ConnectError:
            return BrowserResult(url=url, status="error",
                error="BrowserPilot server not running",
                agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
