"""4. OpenHands (formerly OpenDevin) - AI software engineer with browser."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class OpenHandsAgent(BaseBrowserAgent):
    name = "openhands"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.JS_RENDERING,
        BrowserCapability.STRUCTURED_EXTRACTION, BrowserCapability.AUTO_RETRY,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            task = kwargs.get("task", f"Navigate to {url} and extract all content")
            payload = {"task": task, "browser_config": {"headless": self.headless}}
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post("http://localhost:3000/api/execute", json=payload)
                data = resp.json()
                return BrowserResult(
                    url=url, content=data.get("output", ""), agent=self.name,
                    duration_ms=self._timing(start),
                    metadata={"exit_code": data.get("exit_code", -1)},
                )
        except httpx.ConnectError:
            return BrowserResult(url=url, status="error",
                error="OpenHands server not running. Start with: docker compose -f docker/docker-compose.yml up -d openhands",
                agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
