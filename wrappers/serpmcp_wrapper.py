"""11. SerpAPI MCP - Search engine results scraping."""
import time, os
from .base import BaseCollector, CollectorResult

class SerpAPICollector(BaseCollector):
    name = "serpapi"
    capabilities = ["google_search", "local_pack", "news", "maps", "structured_results"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("SERPAPI_KEY", "")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            params = {
                "engine": kwargs.get("engine", "google"),
                "q": url if not url.startswith("http") else "",
                "api_key": self.api_key,
            }
            if url.startswith("http"):
                params["q"] = kwargs.get("query", url)
            params.update(kwargs.get("extra_params", {}))
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get("https://serpapi.com/search", params=params)
                data = resp.json()
                content_parts = []
                for key in ["organic_results", "local_results", "news_results", "answer_box"]:
                    if key in data:
                        content_parts.append(f"=== {key} ===")
                        for item in data[key][:10]:
                            content_parts.append(str(item))
                return CollectorResult(
                    url=url, content="\n".join(content_parts), metadata=data,
                    collector=self.name, duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
