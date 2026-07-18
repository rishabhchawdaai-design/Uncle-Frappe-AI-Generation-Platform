"""1. Firecrawl - Web crawling and extraction API."""
import os
from .base import BaseCollector, CollectorResult

class FirecrawlCollector(BaseCollector):
    name = "firecrawl"
    capabilities = ["web_crawling", "markdown_extraction", "screenshot", "pdf", "structured_extraction"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("FIRECRAWL_API_KEY", "")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        import time
        start = time.time()
        try:
            from firecrawl import FirecrawlApp
            app = FirecrawlApp(api_key=self.api_key)
            result = app.scrape_url(url, params={"formats": ["markdown", "html"]})
            return CollectorResult(
                url=url,
                content=result.get("markdown", ""),
                raw_html=result.get("html", ""),
                title=result.get("metadata", {}).get("title", ""),
                metadata=result.get("metadata", {}),
                collector=self.name,
                duration_ms=self._timing(start),
            )
        except ImportError:
            return CollectorResult(url=url, status="error", error="firecrawl-py not installed. Run: pip install firecrawl-py", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))

    async def health_check(self):
        ok = bool(self.api_key)
        return {"tool": self.name, "status": "healthy" if ok else "needs_api_key", "capabilities": self.capabilities}
