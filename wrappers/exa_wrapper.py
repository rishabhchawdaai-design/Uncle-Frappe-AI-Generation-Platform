"""10. Exa Search - Neural search engine for web content."""
import time, os
from .base import BaseCollector, CollectorResult

class ExaCollector(BaseCollector):
    name = "exa"
    capabilities = ["neural_search", "content_extraction", "similar_pages", "autocomplete"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("EXA_API_KEY", "")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=30) as client:
                if kwargs.get("mode") == "similar":
                    resp = await client.post("https://api.exa.ai/findSimilar", json={"url": url, "contents": {"text": True}}, headers=headers)
                else:
                    resp = await client.post("https://api.exa.ai/contents", json={"urls": [url], "contents": {"text": True}}, headers=headers)
                data = resp.json()
                results = data.get("results", [])
                content = "\n\n".join([r.get("text", "") for r in results])
                return CollectorResult(
                    url=url, content=content,
                    metadata={"result_count": len(results)}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
