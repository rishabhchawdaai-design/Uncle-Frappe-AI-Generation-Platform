"""18. readability-lxml - Content extraction via Mozilla Readability algorithm."""
import time
from .base import BaseCollector, CollectorResult

class ReadabilityCollector(BaseCollector):
    name = "readability"
    capabilities = ["content_extraction", "readability_algorithm", "lightweight"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            from readability import Document
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                doc = Document(resp.text)
                content = doc.summary()
                title = doc.title()
                from bs4 import BeautifulSoup
                text = BeautifulSoup(content, "html.parser").get_text(separator="\n", strip=True)
                return CollectorResult(
                    url=url, content=text, raw_html=content, title=title,
                    metadata={"status_code": resp.status_code}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
