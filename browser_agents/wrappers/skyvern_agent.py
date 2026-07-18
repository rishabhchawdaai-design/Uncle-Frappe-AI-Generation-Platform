"""18. Skyvern - AI-powered browser automation for complex workflows."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class SkyvernAgent(BaseBrowserAgent):
    name = "skyvern"
    requires_docker = True
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.JS_RENDERING,
        BrowserCapability.CAPTCHA_DETECTION, BrowserCapability.SESSION_PERSIST,
        BrowserCapability.STRUCTURED_EXTRACTION, BrowserCapability.AUTO_RETRY,
        BrowserCapability.HUMAN_LIKE,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8080")
        self.api_key = config.get("api_key", "")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            headers = {"x-api-key": self.api_key} if self.api_key else {}
            async with httpx.AsyncClient(timeout=self._timeout + 30) as client:
                resp = await client.post(f"{self.base_url}/api/v1/tasks", json={
                    "url": url,
                    "navigation_payload": kwargs.get("payload", "Extract all content from this page"),
                    "proxy": kwargs.get("proxy"),
                    "totp_verification_url": kwargs.get("totp_url"),
                }, headers=headers)
                data = resp.json()
                task_id = data.get("task_id", "")

                if task_id:
                    import asyncio
                    for _ in range(30):
                        await asyncio.sleep(2)
                        status_resp = await client.get(f"{self.base_url}/api/v1/tasks/{task_id}", headers=headers)
                        status_data = status_resp.json()
                        if status_data.get("status") in ("completed", "failed"):
                            return BrowserResult(
                                url=url, content=status_data.get("extracted_text", ""),
                                extracted_data=status_data.get("extracted_data", {}),
                                metadata={"task_id": task_id, "status": status_data.get("status")},
                                agent=self.name, duration_ms=self._timing(start),
                            )
                return BrowserResult(url=url, content=data.get("output", ""), agent=self.name,
                                    duration_ms=self._timing(start), metadata=data)
        except httpx.ConnectError:
            return BrowserResult(url=url, status="error",
                error="Skyvern not running. Start: docker compose up skyvern",
                agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
