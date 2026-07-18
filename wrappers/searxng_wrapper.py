"""12. SearXNG - Self-hosted metasearch engine."""
import time
from .base import BaseCollector, CollectorResult

class SearXNGCollector(BaseCollector):
    name = "searxng"
    capabilities = ["metasearch", "privacy_search", "self_hosted", "multi_engine"]

    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8080")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self.base_url}/search", params={
                    "q": url if not url.startswith("http") else "",
                    "format": "json",
                    "categories": kwargs.get("categories", "general"),
                })
                data = resp.json()
                results = data.get("results", [])
                content = "\n\n".join([
                    f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('content', '')}"
                    for r in results[:20]
                ])
                return CollectorResult(
                    url=url, content=content,
                    metadata={"result_count": len(results)}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
