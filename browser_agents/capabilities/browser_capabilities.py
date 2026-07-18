"""
Reusable browser capability mixins.
Each capability encapsulates a cross-cutting concern (login, scrolling, etc.)
that can be composed into any browser agent pipeline.
"""
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class LoginCapability:
    """Handles login automation across different site patterns."""

    COMMON_SELECTORS = {
        "username": [
            'input[name="username"]', 'input[name="email"]', 'input[type="email"]',
            '#username', '#email', '[data-testid="username"]',
        ],
        "password": [
            'input[name="password"]', 'input[type="password"]', '#password',
            '[data-testid="password"]',
        ],
        "submit": [
            'button[type="submit"]', 'input[type="submit"]',
            'button:has-text("Log in")', 'button:has-text("Sign in")',
        ],
    }

    @staticmethod
    async def auto_login(page, url: str, credentials: Dict[str, str], selectors: Optional[Dict] = None):
        """Auto-detect and fill login forms."""
        sel = selectors or LoginCapability.COMMON_SELECTORS
        for username_sel in sel.get("username", []):
            try:
                element = await page.query_selector(username_sel)
                if element:
                    await element.fill(credentials.get("username", ""))
                    for password_sel in sel.get("password", []):
                        pwd = await page.query_selector(password_sel)
                        if pwd:
                            await pwd.fill(credentials.get("password", ""))
                            for submit_sel in sel.get("submit", []):
                                btn = await page.query_selector(submit_sel)
                                if btn:
                                    await btn.click()
                                    await page.wait_for_load_state("networkidle")
                                    return True
            except Exception:
                continue
        return False


class ScrollingCapability:
    """Infinite scroll and controlled scrolling."""

    @staticmethod
    async def infinite_scroll(page, max_scrolls: int = 20, wait: float = 1.5):
        """Scroll to bottom, detecting when new content stops loading."""
        last_height = 0
        scroll_count = 0
        for i in range(max_scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(wait)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1
        return {"scrolls": scroll_count, "final_height": last_height}

    @staticmethod
    async def scroll_to_element(page, selector: str):
        await page.evaluate(f'document.querySelector("{selector}")?.scrollIntoView()')

    @staticmethod
    async def scroll_progress(page) -> Dict[str, Any]:
        return await page.evaluate("""() => ({
            scrollTop: window.scrollY,
            scrollHeight: document.body.scrollHeight,
            clientHeight: document.documentElement.clientHeight,
            percent: Math.round((window.scrollY / (document.body.scrollHeight - document.documentElement.clientHeight)) * 100)
        })""")


class ScreenshotCapability:
    """Screenshot capture with various modes."""

    @staticmethod
    async def full_page(page) -> bytes:
        return await page.screenshot(full_page=True)

    @staticmethod
    async def viewport(page) -> bytes:
        return await page.screenshot(full_page=False)

    @staticmethod
    async def element(page, selector: str) -> bytes:
        element = await page.query_selector(selector)
        if element:
            return await element.screenshot()
        return b""

    @staticmethod
    async def save_screenshot(screenshot_bytes: bytes, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(screenshot_bytes)
        return path


class PDFCapability:
    """PDF generation from pages."""

    @staticmethod
    async def generate(page, path: Optional[str] = None, **kwargs) -> bytes:
        pdf = await page.pdf(
            format=kwargs.get("format", "A4"),
            print_background=kwargs.get("print_background", True),
            margin=kwargs.get("margin", {"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"}),
        )
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(pdf)
        return pdf


class CaptchaCapability:
    """CAPTCHA detection and handling."""

    CAPTCHA_INDICATORS = [
        "captcha", "recaptcha", "hcaptcha", "verify you are human",
        "robot check", "i'm not a robot", "challenge-platform",
        "cf-challenge", "turnstile", "funcaptcha",
    ]

    @staticmethod
    async def detect(page) -> Dict[str, Any]:
        text = await page.content()
        text_lower = text.lower()
        detected = [ind for ind in CaptchaCapability.CAPTCHA_INDICATORS if ind in text_lower]

        captcha_frames = await page.query_selector_all("iframe[src*='captcha'], iframe[src*='recaptcha'], iframe[src*='hcaptcha']")
        return {
            "detected": bool(detected) or bool(captcha_frames),
            "indicators_found": detected,
            "captcha_iframes": len(captcha_frames),
            "suggestion": "Use vision-based CAPTCHA solver or manual intervention" if detected else None,
        }


class SessionCapability:
    """Session persistence across browsing sessions."""

    @staticmethod
    async def save_session(page, session_id: str, output_dir: str = "sessions"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        cookies = await page.context.cookies()
        storage = await page.evaluate("() => JSON.stringify(localStorage)")
        (out / f"{session_id}.json").write_text(json.dumps({
            "cookies": cookies,
            "local_storage": json.loads(storage) if storage else {},
            "url": page.url,
            "saved_at": time.time(),
        }, indent=2))
        return str(out / f"{session_id}.json")

    @staticmethod
    async def load_session(context, session_id: str, output_dir: str = "sessions") -> bool:
        path = Path(output_dir) / f"{session_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            if data.get("cookies"):
                await context.add_cookies(data["cookies"])
            return True
        return False


class CookieCapability:
    """Cookie management operations."""

    @staticmethod
    async def export_cookies(context) -> List[Dict]:
        return await context.cookies()

    @staticmethod
    async def import_cookies(context, cookies: List[Dict]):
        await context.add_cookies(cookies)

    @staticmethod
    async def clear_cookies(context):
        await context.clear_cookies()

    @staticmethod
    async def get_cookie_by_name(context, name: str) -> Optional[Dict]:
        cookies = await context.cookies()
        return next((c for c in cookies if c["name"] == name), None)


class DownloadCapability:
    """File download handling."""

    @staticmethod
    async def setup_download_dir(page, download_path: str) -> str:
        Path(download_path).mkdir(parents=True, exist_ok=True)
        return download_path

    @staticmethod
    async def download_file(page, url: str, download_path: str) -> str:
        async with page.expect_download() as download_info:
            await page.goto(url)
        download = await download_info.value
        save_path = str(Path(download_path) / download.suggested_filename)
        await download.save_as(save_path)
        return save_path


class HumanLikeCapability:
    """Human-like browsing behavior simulation."""

    @staticmethod
    async def random_delay(min_s: float = 0.5, max_s: float = 2.0):
        import random
        await asyncio.sleep(random.uniform(min_s, max_s))

    @staticmethod
    async def human_type(page, selector: str, text: str):
        element = await page.query_selector(selector)
        if element:
            for char in text:
                await element.type(char, delay=50)
                import random
                await asyncio.sleep(random.uniform(0.05, 0.15))

    @staticmethod
    async def human_click(page, selector: str):
        element = await page.query_selector(selector)
        if element:
            box = await element.bounding_box()
            if box:
                import random
                x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
                y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)
                await page.mouse.move(x, y, steps=10)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.mouse.click(x, y)

    @staticmethod
    async def random_mouse_movement(page, steps: int = 5):
        import random
        for _ in range(steps):
            x = random.randint(100, 1800)
            y = random.randint(100, 900)
            await page.mouse.move(x, y, steps=5)
            await asyncio.sleep(random.uniform(0.1, 0.3))


class ParallelCapability:
    """Parallel browsing across multiple contexts."""

    @staticmethod
    async def parallel_navigate(agent, urls: List[str], concurrency: int = 5, **kwargs) -> List:
        sem = asyncio.Semaphore(concurrency)
        async def _limited(url):
            async with sem:
                return await agent.navigate(url, **kwargs)
        return await asyncio.gather(*[_limited(u) for u in urls])


class RecordingCapability:
    """Browser recording and replay."""

    @staticmethod
    async def start_recording(context):
        return await context.new_recording()

    @staticmethod
    async def stop_recording(recording, output_path: str):
        if recording:
            await recording.stop()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            return output_path
        return None


class ExtractionCapability:
    """Structured data extraction helpers."""

    @staticmethod
    async def extract_by_selectors(page, selectors: Dict[str, str]) -> Dict[str, Any]:
        result = {}
        for key, selector in selectors.items():
            elements = await page.query_selector_all(selector)
            texts = []
            for el in elements:
                text = await el.inner_text()
                if text.strip():
                    texts.append(text.strip())
            result[key] = texts if len(texts) > 1 else (texts[0] if texts else "")
        return result

    @staticmethod
    async def extract_table(page, table_selector: str = "table") -> List[Dict[str, str]]:
        return await page.evaluate(f"""() => {{
            const rows = document.querySelectorAll('{table_selector} tr');
            if (rows.length === 0) return [];
            const headers = Array.from(rows[0].querySelectorAll('th, td')).map(h => h.textContent.trim());
            return Array.from(rows).slice(1).map(row => {{
                const cells = Array.from(row.querySelectorAll('td')).map(c => c.textContent.trim());
                const obj = {{}};
                headers.forEach((h, i) => obj[h] = cells[i] || '');
                return obj;
            }});
        }}""")

    @staticmethod
    async def extract_all_links(page) -> List[Dict[str, str]]:
        return await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.textContent.trim(),
                href: a.href,
                title: a.title || ''
            })).filter(l => l.href && l.text);
        }""")


class RetryCapability:
    """Automatic retry with exponential backoff."""

    @staticmethod
    async def with_retry(coro_func, max_retries: int = 3, base_delay: float = 1.0):
        last_error = None
        for attempt in range(max_retries):
            try:
                return await coro_func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
        raise last_error


class HealthMonitorCapability:
    """Browser health monitoring and diagnostics."""

    @staticmethod
    async def check_browser_health(context) -> Dict[str, Any]:
        try:
            pages = context.pages
            return {
                "status": "healthy",
                "open_pages": len(pages),
                "current_urls": [p.url for p in pages],
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
