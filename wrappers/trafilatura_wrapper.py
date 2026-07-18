"""16. trafilatura - Web content extraction and text processing."""
import time
from .base import BaseCollector, CollectorResult

class TrafilaturaCollector(BaseCollector):
    name = "trafilatura"
    capabilities = ["content_extraction", "main_text", "metadata", "dedup", "feeds"]

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded, include_comments=False, include_tables=True, output_format="txt")
                metadata = trafilatura.extract(downloaded, output_format="json")
                meta_dict = {}
                try:
                    import json
                    meta_dict = json.loads(metadata) if metadata else {}
                except (json.JSONDecodeError, TypeError):
                    meta_dict = {"raw": metadata}
                return CollectorResult(
                    url=url, content=content or "", title=meta_dict.get("title", ""),
                    metadata=meta_dict, collector=self.name, duration_ms=self._timing(start),
                )
            return CollectorResult(url=url, status="error", error="Failed to download URL", collector=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
