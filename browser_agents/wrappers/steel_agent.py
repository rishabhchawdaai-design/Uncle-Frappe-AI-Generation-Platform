"""10. Steel Browser - Anti-detect browser for scraping."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class SteelAgent(BaseBrowserAgent):
    name = "steel"
    requires_docker = True
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.STEALTH,
        BrowserCapability.PROXY_SUPPORT, BrowserCapability.COOKIE_MANAGEMENT,
        BrowserCapability.SESSION_PERSIST, BrowserCapability.SCREENSHOT,
        BrowserCapability.HUMAN_LIKE, BrowserCapability.CAPTCHA_DETECTION,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:3001")
        self.api_key = config.get("api_key", "")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                session_resp = await client.post(f"{self.base_url}/v1/browser/sessions", json={
                    "proxy": kwargs.get("proxy"),
                    "userAgent": kwargs.get("user_agent"),
                }, headers=headers)
                session = session_resp.json()
                session_id = session.get("id", "")

                nav_resp = await client.post(f"{self.base_url}/v1/browser/navigate", json={
                    "sessionId": session_id, "url": url,
                }, headers=headers)
                data = nav_resp.json()
                return BrowserResult(
                    url=url, content=data.get("content", ""), html=data.get("html", ""),
                    title=data.get("title", ""),
                    metadata={"steel_session": session_id, "stealth": True},
                    agent=self.name, duration_ms=self._timing(start),
                )
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
