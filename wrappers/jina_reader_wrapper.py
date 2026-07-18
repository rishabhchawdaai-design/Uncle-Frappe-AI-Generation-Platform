"""8. Jina AI Reader - URL-to-content extraction API."""
import time, os
from .base import BaseCollector, CollectorResult

class JinaReaderCollector(BaseCollector):
    name = "jina_reader"
    capabilities = ["url_reading", "content_extraction", "search", "markdown", "pdf_support"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("JINA_API_KEY", "")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            reader_url = f"https://r.jina.ai/{url}"
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(reader_url, headers=headers)
                content = resp.text
                title = content.split("\n")[0].replace("# ", "") if content else ""
                return CollectorResult(
                    url=url, content=content, title=title,
                    metadata={"status_code": resp.status_code}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
