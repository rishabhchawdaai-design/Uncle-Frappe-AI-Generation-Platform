"""9. Tavily Search - AI-optimized search and extraction."""
import time, os
from .base import BaseCollector, CollectorResult

class TavilyCollector(BaseCollector):
    name = "tavily"
    capabilities = ["web_search", "content_extraction", "answer_generation", "structured_data"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("TAVILY_API_KEY", "")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            result = client.search(query=url, search_depth="advanced", include_raw_content=True)
            content = "\n\n".join([r.get("content", "") for r in result.get("results", [])])
            return CollectorResult(
                url=url, content=content,
                metadata={"result_count": len(result.get("results", []))},
                collector=self.name, duration_ms=self._timing(start),
            )
        except ImportError:
            return CollectorResult(url=url, status="error", error="tavily-python not installed", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
