"""1. Browser Use - AI-driven browser automation agent."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class BrowserUseAgent(BaseBrowserAgent):
    name = "browser_use"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.CAPTCHA_DETECTION,
        BrowserCapability.JS_RENDERING, BrowserCapability.STRUCTURED_EXTRACTION,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from browser_use import Agent
            task = kwargs.get("task", f"Navigate to {url} and extract all visible text content")
            agent = Agent(task=task)
            result = await agent.run()
            return BrowserResult(
                url=url, content=str(result), agent=self.name,
                duration_ms=self._timing(start),
            )
        except ImportError:
            return BrowserResult(url=url, status="error", error="browser-use not installed. Run: pip install browser-use", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))

    async def login(self, url: str, credentials: dict, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from browser_use import Agent
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            task = f"Go to {url}, find the login form, enter username '{username}' and password '{password}', then submit the form"
            agent = Agent(task=task)
            result = await agent.run()
            return BrowserResult(url=url, content=str(result), agent=self.name, duration_ms=self._timing(start),
                                metadata={"action": "login", "url": url})
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
