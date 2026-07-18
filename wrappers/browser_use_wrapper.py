"""3. Browser Use - AI browser automation agent."""
import time
from .base import BaseCollector, CollectorResult

class BrowserUseCollector(BaseCollector):
    name = "browser_use"
    capabilities = ["ai_browsing", "form_filling", "multi_step", "screenshot", "dynamic_content"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from browser_use import Agent
            task = kwargs.get("task", f"Navigate to {url} and extract all content")
            agent = Agent(task=task)
            result = await agent.run()
            return CollectorResult(
                url=url,
                content=str(result),
                collector=self.name,
                duration_ms=self._timing(start),
            )
        except ImportError:
            return CollectorResult(url=url, status="error", error="browser-use not installed. Run: pip install browser-use", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
