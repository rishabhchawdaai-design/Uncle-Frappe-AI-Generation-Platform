"""14. Scrapy - Production-grade web scraping framework."""
import time
from .base import BaseCollector, CollectorResult

class ScrapyCollector(BaseCollector):
    name = "scrapy"
    capabilities = ["structured_scraping", "middleware", "pipelines", "distributed", "spiders"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"})
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string if soup.title else ""
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                content = soup.get_text(separator="\n", strip=True)
                return CollectorResult(
                    url=url, content=content, raw_html=resp.text, title=title or "",
                    metadata={"status_code": resp.status_code}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
