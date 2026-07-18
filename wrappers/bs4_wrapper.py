"""20. BeautifulSoup4 - Fundamental HTML/XML parsing library."""
import time
from .base import BaseCollector, CollectorResult

class BS4Collector(BaseCollector):
    name = "bs4"
    capabilities = ["html_parsing", "xml_parsing", "css_selectors", "lightweight", "fast"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            from bs4 import BeautifulSoup
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"})
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                for tag in soup(["script", "style"]):
                    tag.decompose()
                content = soup.get_text(separator="\n", strip=True)
                meta = {}
                for m in soup.find_all("meta"):
                    name = m.get("name") or m.get("property", "")
                    if name:
                        meta[name] = m.get("content", "")
                return CollectorResult(
                    url=url, content=content, raw_html=resp.text, title=title,
                    metadata={"status_code": resp.status_code, "meta_tags": meta},
                    collector=self.name, duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
