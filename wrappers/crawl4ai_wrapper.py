"""2. Crawl4AI - Open-source async web crawler with LLM support."""
import time
from .base import BaseCollector, CollectorResult

class Crawl4AICollector(BaseCollector):
    name = "crawl4ai"
    capabilities = ["async_crawling", "js_rendering", "markdown", "screenshot", "llm_extraction"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return CollectorResult(
                    url=url,
                    content=result.markdown or "",
                    raw_html=result.html or "",
                    title=kwargs.get("title", ""),
                    metadata={"success": result.success},
                    collector=self.name,
                    duration_ms=self._timing(start),
                )
        except ImportError:
            return CollectorResult(url=url, status="error", error="crawl4ai not installed. Run: pip install crawl4ai", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
