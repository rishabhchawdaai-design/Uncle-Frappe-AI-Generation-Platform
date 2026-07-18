"""2. AgentReach - Web scraping agent with reach capabilities."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class AgentReachAgent(BaseBrowserAgent):
    name = "agentreach"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.SCROLLING,
        BrowserCapability.STRUCTURED_EXTRACTION, BrowserCapability.AUTO_RETRY,
        BrowserCapability.CAPTCHA_DETECTION,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from agentreach import scrape
            result = await scrape(url, **kwargs)
            return BrowserResult(url=url, content=str(result), agent=self.name,
                                duration_ms=self._timing(start))
        except ImportError:
            return BrowserResult(url=url, status="error", error="agentreach not installed", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
