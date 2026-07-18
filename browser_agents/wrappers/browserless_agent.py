"""9. Browserless - Headless browser as a service."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class BrowserlessAgent(BaseBrowserAgent):
    name = "browserless"
    requires_docker = True
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.PDF_DOWNLOAD, BrowserCapability.JS_RENDERING,
        BrowserCapability.COOKIE_MANAGEMENT, BrowserCapability.PROXY_SUPPORT,
        BrowserCapability.FORM_FILLING, BrowserCapability.STRUCTURED_EXTRACTION,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:3000")
        self.token = config.get("token", "")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            payload = {
                "url": url,
                "waitForSelector": kwargs.get("selector", "body"),
                "gotoOptions": {"waitUntil": "networkidle", "timeout": self._timeout * 1000},
            }
            if kwargs.get("take_screenshot"):
                payload["screenshot"] = {"type": "png", "fullPage": kwargs.get("full_page", False)}
            if kwargs.get("save_pdf"):
                payload["pdf"] = {"format": "A4", "printBackground": True}

            async with httpx.AsyncClient(timeout=self._timeout + 10) as client:
                endpoint = f"{self.base_url}/pdf" if kwargs.get("save_pdf") else f"{self.base_url}/content"
                params = {"token": self.token} if self.token else {}
                resp = await client.post(endpoint, json=payload, params=params)
                if kwargs.get("save_pdf") and resp.headers.get("content-type", "").startswith("application/pdf"):
                    return BrowserResult(url=url, pdf=resp.content, agent=self.name, duration_ms=self._timing(start))
                data = resp.json() if "json" in resp.headers.get("content-type", "") else {"content": resp.text}
                return BrowserResult(url=url, content=data.get("content", ""), html=data.get("html", ""),
                                    agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
