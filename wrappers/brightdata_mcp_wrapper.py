"""7. Bright Data MCP - Web data collection platform with MCP support."""
import time, os
from .base import BaseCollector, CollectorResult

class BrightDataMCP(BaseCollector):
    name = "brightdata_mcp"
    capabilities = ["web_unlocker", "serp_api", "scraping_browser", "data_center_proxies", "mcp_server"]
    requires_api_key = True

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.environ.get("BRIGHT_DATA_API_KEY", "")
        self.base_url = "https://api.brightdata.com"

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{self.base_url}/datasets/web_unlocker", json={"url": url}, headers=headers)
                data = resp.json()
                return CollectorResult(
                    url=url, content=data.get("body", ""), raw_html=data.get("body", ""),
                    metadata={"status_code": resp.status_code}, collector=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))

    async def health_check(self):
        return {"tool": self.name, "status": "healthy" if self.api_key else "needs_api_key", "capabilities": self.capabilities}
