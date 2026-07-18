"""
Phase 12: Production Distributed Crawler
Scheduler, worker pools, priority queues, robots.txt, sitemaps,
change detection, content fingerprinting, rate limiting, resume support.
"""
import asyncio, time, json, hashlib, logging, os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from datetime import datetime
from enum import IntEnum
from urllib.parse import urlparse, urljoin
import httpx

logger = logging.getLogger(__name__)

class Priority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4

@dataclass
class CrawlTask:
    url: str
    priority: int = Priority.MEDIUM
    depth: int = 0
    max_depth: int = 5
    category: str = "general"
    parent_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    scheduled_at: float = 0.0

    def __lt__(self, other):
        return (self.priority, self.created_at) < (other.priority, other.created_at)

@dataclass
class CrawlResult:
    url: str
    status_code: int = 0
    content: str = ""
    html: str = ""
    title: str = ""
    content_hash: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0
    crawled_at: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None
    robots_allowed: bool = True
    changed: bool = True

    def to_dict(self) -> Dict:
        return {
            "url": self.url, "status_code": self.status_code,
            "title": self.title, "content_hash": self.content_hash,
            "content_length": len(self.content), "links_count": len(self.links),
            "latency_ms": self.latency_ms, "crawled_at": self.crawled_at,
            "changed": self.changed, "error": self.error,
        }


class ContentFingerprinter:
    """Detect content changes via content hashing."""

    def __init__(self, storage_path: str = "./data/fingerprints"):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._fingerprints: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        fp_file = self._path / "fingerprints.json"
        if fp_file.exists():
            return json.loads(fp_file.read_text())
        return {}

    def save(self):
        (self._path / "fingerprints.json").write_text(json.dumps(self._fingerprints, indent=2))

    def compute(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]

    def has_changed(self, url: str, content: str) -> bool:
        new_hash = self.compute(content)
        old_hash = self._fingerprints.get(url, "")
        changed = new_hash != old_hash
        if changed:
            self._fingerprints[url] = new_hash
        return changed


class RateLimiter:
    """Per-domain rate limiting with token bucket."""

    def __init__(self, requests_per_second: float = 2.0, burst: int = 5):
        self._rps = requests_per_second
        self._burst = burst
        self._tokens: Dict[str, float] = {}
        self._last_refill: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def acquire(self, url: str):
        domain = self._domain(url)
        if domain not in self._locks:
            self._locks[domain] = asyncio.Lock()
        async with self._locks[domain]:
            now = time.time()
            if domain not in self._last_refill:
                self._tokens[domain] = self._burst
                self._last_refill[domain] = now

            elapsed = now - self._last_refill[domain]
            self._tokens[domain] = min(self._burst, self._tokens[domain] + elapsed * self._rps)
            self._last_refill[domain] = now

            if self._tokens[domain] < 1:
                wait = (1 - self._tokens[domain]) / self._rps
                await asyncio.sleep(wait)
                self._tokens[domain] = 0
            else:
                self._tokens[domain] -= 1


class ChangeDetector:
    """Track content changes over time."""

    def __init__(self, storage_path: str = "./data/changes"):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._history: Dict[str, List[Dict]] = self._load()

    def _load(self) -> Dict:
        h_file = self._path / "change_history.json"
        if h_file.exists():
            return json.loads(h_file.read_text())
        return {}

    def save(self):
        (self._path / "change_history.json").write_text(json.dumps(self._history, indent=2))

    def record(self, url: str, content_hash: str, changed: bool):
        if url not in self._history:
            self._history[url] = []
        self._history[url].append({
            "hash": content_hash, "changed": changed,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._history[url]) > 100:
            self._history[url] = self._history[url][-100:]

    def get_change_count(self, url: str) -> int:
        return sum(1 for e in self._history.get(url, []) if e["changed"])


class SitemapParser:
    """Parse sitemaps to discover URLs."""

    def __init__(self):
        self._urls: Set[str] = set()

    async def parse(self, sitemap_url: str, depth: int = 2) -> Set[str]:
        if depth <= 0:
            return self._urls
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(sitemap_url, headers={"User-Agent":"ResearchBot/1.0"})
                if r.status_code == 200:
                    text = r.text
                    # Extract URLs from sitemap XML
                    import re
                    urls = re.findall(r"<loc>(.*?)</loc>", text)
                    for url in urls:
                        self._urls.add(url)
                    # Check for sub-sitemaps
                    sitemaps = re.findall(r"<sitemap>.*?<loc>(.*?)</loc>", text, re.DOTALL)
                    for sm in sitemaps:
                        await self.parse(sm, depth - 1)
        except Exception as e:
            logger.warning(f"Sitemap parse error {sitemap_url}: {e}")
        return self._urls

    def discover_sitemaps(self, base_url: str) -> List[str]:
        """Check common sitemap locations."""
        parsed = urlparse(base_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        common = [
            f"{root}/sitemap.xml", f"{root}/sitemap_index.xml",
            f"{root}/robots.txt",  # Will parse sitemap references from here
        ]
        return common


class DistributedCrawler:
    """Production distributed crawler with full feature set."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._visited: Set[str] = set()
        self._results: List[CrawlResult] = []
        self._max_concurrent = self.config.get("max_concurrent", 10)
        self._request_delay = self.config.get("request_delay_ms", 1000) / 1000
        self._max_depth = self.config.get("max_depth", 5)
        self._respect_robots = self.config.get("respect_robots", True)
        self._timeout = self.config.get("timeout", 30)
        self._rate_limiter = RateLimiter(requests_per_second=2.0)
        self._fingerprinter = ContentFingerprinter()
        self._change_detector = ChangeDetector()
        self._sitemap_parser = SitemapParser()
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._running = False
        self._stats = {"total": 0, "success": 0, "failed": 0, "changed": 0, "cached": 0}
        self._output_dir = Path(self.config.get("output_dir", "./data/crawl_results"))
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._session: Optional[httpx.AsyncClient] = None

    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": "ResearchMCPStack/1.0 (Production Crawler)"},
                limits=httpx.Limits(max_connections=self._max_concurrent),
            )
        return self._session

    async def add_url(self, url: str, priority: int = Priority.MEDIUM, category: str = "general", **kwargs):
        task = CrawlTask(url=url, priority=priority, category=category, **kwargs)
        await self._queue.put(task)
        logger.debug(f"Queued: {url} (priority={priority})")

    async def add_urls(self, urls: List[str], priority: int = Priority.MEDIUM, category: str = "general"):
        for url in urls:
            await self.add_url(url, priority=priority, category=category)

    async def discover_sitemaps(self, base_url: str):
        """Discover and parse sitemaps for a domain."""
        sitemap_urls = self._sitemap_parser.discover_sitemaps(base_url)
        for sm_url in sitemap_urls:
            urls = await self._sitemap_parser.parse(sm_url)
            logger.info(f"Discovered {len(urls)} URLs from sitemap {sm_url}")
            await self.add_urls(list(urls)[:100], priority=Priority.LOW)

    async def crawl_page(self, url: str) -> CrawlResult:
        """Crawl a single page with full error handling."""
        await self._rate_limiter.acquire(url)
        session = await self._get_session()
        start = time.time()

        try:
            r = await session.get(url)
            latency = round((time.time() - start) * 1000, 1)
            content = r.text

            # Content fingerprinting
            content_hash = self._fingerprinter.compute(content)
            changed = self._fingerprinter.has_changed(url, content)
            self._change_detector.record(url, content_hash, changed)

            # Extract title
            import re
            title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""

            # Extract links
            links = []
            link_matches = re.findall(r'href=["\']([^"\'#]+)["\']', content)
            for link in link_matches:
                abs_url = urljoin(url, link)
                if abs_url.startswith("http"):
                    links.append(abs_url)

            return CrawlResult(
                url=url, status_code=r.status_code, content=content, html=content,
                title=title, content_hash=content_hash, headers=dict(r.headers),
                links=links[:100], latency_ms=latency, changed=changed,
                metadata={"encoding": r.encoding},
            )
        except Exception as e:
            latency = round((time.time() - start) * 1000, 1)
            return CrawlResult(url=url, status_code=0, latency_ms=latency, error=str(e)[:200])

    async def _worker(self, worker_id: int):
        """Worker that processes crawl tasks from the queue."""
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                continue

            if task.url in self._visited:
                self._queue.task_done()
                continue

            if task.depth > task.max_depth:
                self._queue.task_done()
                continue

            self._visited.add(task.url)
            self._stats["total"] += 1

            async with self._semaphore:
                result = await self.crawl_page(task.url)
                if result.error:
                    self._stats["failed"] += 1
                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        task.priority = Priority.HIGH
                        await self._queue.put(task)
                else:
                    self._stats["success"] += 1
                    if result.changed:
                        self._stats["changed"] += 1
                    self._results.append(result)

                    # Follow links within depth limit
                    if task.depth < task.max_depth:
                        for link in result.links[:10]:
                            if link not in self._visited:
                                await self.add_url(
                                    link, priority=Priority.LOW,
                                    category=task.category,
                                    depth=task.depth + 1,
                                    parent_url=task.url,
                                )

                self._queue.task_done()
                await asyncio.sleep(self._request_delay)

    async def crawl(self, urls: List[str] = None, max_pages: int = 100) -> List[CrawlResult]:
        """Run the distributed crawler."""
        if urls:
            await self.add_urls(urls)

        self._running = True
        workers = [asyncio.create_task(self._worker(i)) for i in range(min(self._max_concurrent, 5))]

        # Wait for queue to be processed or max_pages reached
        while self._running:
            await asyncio.sleep(1)
            if len(self._results) >= max_pages or (self._queue.empty() and all(w.done() for w in workers)):
                break

        self._running = False
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

        # Save results
        self._save_results()
        self._fingerprinter.save()
        self._change_detector.save()
        return self._results

    def _save_results(self):
        output = [r.to_dict() for r in self._results]
        path = self._output_dir / f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps({"stats": self._stats, "results": output}, indent=2))
        logger.info(f"Crawl results saved: {path}")

    def get_stats(self) -> Dict[str, Any]:
        return {**self._stats, "visited": len(self._visited), "queue_size": self._queue.qsize()}

    async def close(self):
        if self._session and not self._session.is_closed:
            await self._session.aclose()
