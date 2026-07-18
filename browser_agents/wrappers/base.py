"""Base Browser Agent - Foundation for all 20 browser automation tools."""
import asyncio
import time
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from enum import Enum

class BrowserCapability(str, Enum):
    NAVIGATION = "navigation"
    LOGIN = "login"
    SCROLLING = "scrolling"
    SCREENSHOT = "screenshot"
    PDF_DOWNLOAD = "pdf_download"
    CAPTCHA_DETECTION = "captcha_detection"
    SESSION_PERSIST = "session_persist"
    COOKIE_MANAGEMENT = "cookie_management"
    FILE_DOWNLOAD = "file_download"
    HUMAN_LIKE = "human_like"
    PARALLEL = "parallel"
    RECORDING = "recording"
    STRUCTURED_EXTRACTION = "structured_extraction"
    AUTO_RETRY = "auto_retry"
    HEALTH_MONITOR = "health_monitor"
    JS_RENDERING = "js_rendering"
    FORM_FILLING = "form_filling"
    MULTI_TAB = "multi_tab"
    PROXY_SUPPORT = "proxy_support"
    STEALTH = "stealth"

@dataclass
class BrowserResult:
    url: str
    content: str = ""
    html: str = ""
    title: str = ""
    screenshot: Optional[bytes] = None
    pdf: Optional[bytes] = None
    cookies: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    error: Optional[str] = None
    agent: str = ""
    duration_ms: float = 0
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.content and not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            "url": self.url, "title": self.title, "status": self.status,
            "agent": self.agent, "duration_ms": self.duration_ms,
            "content_length": len(self.content), "content_hash": self.content_hash,
            "has_screenshot": self.screenshot is not None,
            "has_pdf": self.pdf is not None,
            "cookie_count": len(self.cookies),
            "metadata": self.metadata, "extracted_data": self.extracted_data,
        }

@dataclass
class SessionState:
    session_id: str
    cookies: List[Dict] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    local_storage: Dict[str, str] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

class BaseBrowserAgent(ABC):
    name: str = "base"
    capabilities: List[BrowserCapability] = []
    requires_api_key: bool = False
    requires_docker: bool = False
    headless: bool = True
    supports_async: bool = True

    def __init__(self, config=None):
        self.config = config if config is not None else {}
        self._sessions: Dict[str, SessionState] = {}
        self._retry_count = config.get("max_retries", 3)
        self._timeout = config.get("timeout", 30)

    @abstractmethod
    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        pass

    async def login(self, url: str, credentials: Dict[str, str], **kwargs) -> BrowserResult:
        raise NotImplementedError(f"{self.name} does not support login automation")

    async def screenshot(self, url: str, **kwargs) -> BrowserResult:
        return await self.navigate(url, take_screenshot=True, **kwargs)

    async def scroll_page(self, url: str, **kwargs) -> BrowserResult:
        return await self.navigate(url, auto_scroll=True, **kwargs)

    async def download_pdf(self, url: str, **kwargs) -> BrowserResult:
        return await self.navigate(url, save_pdf=True, **kwargs)

    async def extract_structured(self, url: str, schema: Dict, **kwargs) -> BrowserResult:
        result = await self.navigate(url, **kwargs)
        result.extracted_data = schema
        return result

    async def detect_captcha(self, url: str, **kwargs) -> BrowserResult:
        result = await self.navigate(url, **kwargs)
        text = result.content.lower()
        captcha_indicators = ["captcha", "verify you are human", "robot check", "i'm not a robot", "recaptcha", "hcaptcha"]
        result.metadata["captcha_detected"] = any(ind in text for ind in captcha_indicators)
        return result

    async def batch_navigate(self, urls: List[str], concurrency: int = 3, **kwargs) -> List[BrowserResult]:
        sem = asyncio.Semaphore(concurrency)
        async def _limited(url):
            async with sem:
                return await self.navigate_with_retry(url, **kwargs)
        return await asyncio.gather(*[_limited(u) for u in urls])

    async def navigate_with_retry(self, url: str, retries: int = None, **kwargs) -> BrowserResult:
        max_retries = retries or self._retry_count
        last_error = None
        for attempt in range(max_retries):
            try:
                result = await asyncio.wait_for(self.navigate(url, **kwargs), timeout=self._timeout)
                if result.status == "success":
                    return result
                last_error = result.error
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self._timeout}s"
            except Exception as e:
                last_error = str(e)
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
        return BrowserResult(url=url, status="error", error=f"Failed after {max_retries} retries: {last_error}", agent=self.name)

    def create_session(self) -> str:
        import uuid
        sid = str(uuid.uuid4())[:8]
        self._sessions[sid] = SessionState(session_id=sid)
        return sid

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def save_session(self, session_id: str, output_dir: str = "sessions"):
        session = self._sessions.get(session_id)
        if session:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{session_id}.json").write_text(json.dumps({
                "session_id": session.session_id,
                "cookies": session.cookies,
                "headers": session.headers,
                "local_storage": session.local_storage,
                "history": session.history,
                "created_at": session.created_at,
            }, indent=2))

    def load_session(self, session_id: str, output_dir: str = "sessions") -> bool:
        path = Path(output_dir) / f"{session_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            self._sessions[session_id] = SessionState(**data)
            return True
        return False

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "status": "available",
            "capabilities": [c.value for c in self.capabilities],
            "headless": self.headless,
            "requires_docker": self.requires_docker,
        }

    def _timing(self, start: float) -> float:
        return round((time.time() - start) * 1000, 2)
