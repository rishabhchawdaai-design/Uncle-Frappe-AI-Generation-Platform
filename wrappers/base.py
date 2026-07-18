"""Base collector class for all 20 data collection tools."""
import asyncio
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

@dataclass
class CollectorResult:
    url: str
    content: str = ""
    title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_html: str = ""
    status: str = "success"
    error: Optional[str] = None
    collector: str = ""
    duration_ms: float = 0
    content_hash: str = ""

    def __post_init__(self):
        if self.content and not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]

class BaseCollector(ABC):
    name: str = "base"
    capabilities: List[str] = []
    requires_api_key: bool = False
    requires_docker: bool = False

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def collect(self, url: str, **kwargs) -> CollectorResult:
        pass

    async def health_check(self) -> Dict[str, Any]:
        return {"tool": self.name, "status": "available", "capabilities": self.capabilities}

    def _timing(self, start: float) -> float:
        return round((time.time() - start) * 1000, 2)

    async def batch_collect(self, urls: List[str], **kwargs) -> List[CollectorResult]:
        tasks = [self.collect(url, **kwargs) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def save_result(self, result: CollectorResult, output_dir: str = "output"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        safe_name = result.url.replace("https://", "").replace("http://", "").replace("/", "_")[:80]
        (out / f"{safe_name}.txt").write_text(f"URL: {result.url}\nTitle: {result.title}\nStatus: {result.status}\nCollector: {result.collector}\nDuration: {result.duration_ms}ms\n\n{result.content}")
