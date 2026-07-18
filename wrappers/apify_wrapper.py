"""13. Apify - Web scraping and automation platform."""
import time, os
from .base import BaseCollector, CollectorResult

class ApifyCollector(BaseCollector):
    name = "apify"
    capabilities = ["actor_marketplace", "web_scraping", "data_extraction", "proxy", "schedule"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("APIFY_TOKEN", "")
        self.base_url = "https://api.apify.com/v2"

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            actor_id = kwargs.get("actor_id", "apify/web-scraper")
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.base_url}/acts/{actor_id}/run-sync-get-dataset-items?token={self.api_key}",
                    json={"startUrls": [url], "maxPagesPerCrawl": kwargs.get("max_pages", 1)},
                )
                data = resp.json()
                content = "\n\n".join([str(item) for item in data[:20]])
                return CollectorResult(
                    url=url, content=content,
                    metadata={"items_count": len(data)}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
