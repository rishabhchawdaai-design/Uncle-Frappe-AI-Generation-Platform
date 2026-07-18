"""19. requests-html - HTML parsing with JavaScript rendering."""
import time
from .base import BaseCollector, CollectorResult

class RequestsHTMLCollector(BaseCollector):
    name = "requests_html"
    capabilities = ["html_parsing", "js_rendering", "css_selectors", "xpath"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from requests_html import AsyncHTMLSession
            session = AsyncHTMLSession()
            r = await session.get(url, timeout=kwargs.get("timeout", 30))
            if kwargs.get("render", False):
                await r.html.arender(timeout=10)
            content = r.html.text
            title = r.html.find("title", first=True).text if r.html.find("title") else ""
            return CollectorResult(
                url=url, content=content, raw_html=r.html.html,
                title=title, metadata={"status_code": r.status_code},
                collector=self.name, duration_ms=self._timing(start),
            )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
