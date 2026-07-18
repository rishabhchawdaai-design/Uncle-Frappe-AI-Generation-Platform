"""6. Playwright - Microsoft browser automation framework."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class PlaywrightAgent(BaseBrowserAgent):
    name = "playwright"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.PDF_DOWNLOAD, BrowserCapability.CAPTCHA_DETECTION,
        BrowserCapability.SESSION_PERSIST, BrowserCapability.COOKIE_MANAGEMENT,
        BrowserCapability.FILE_DOWNLOAD, BrowserCapability.JS_RENDERING,
        BrowserCapability.FORM_FILLING, BrowserCapability.MULTI_TAB,
        BrowserCapability.PROXY_SUPPORT, BrowserCapability.RECORDING,
        BrowserCapability.STRUCTURED_EXTRACTION, BrowserCapability.AUTO_RETRY,
        BrowserCapability.HEALTH_MONITOR,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self._browser = None
        self._playwright = None
        self._context = None

    async def _get_browser(self, **kwargs):
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            browser_type = kwargs.get("browser", "chromium")
            launcher = getattr(self._playwright, browser_type)
            launch_args = {
                "headless": kwargs.get("headless", self.headless),
                "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            }
            if kwargs.get("proxy"):
                launch_args["proxy"] = {"server": kwargs["proxy"]}
            self._browser = await launcher.launch(**launch_args)
        if self._context is None:
            self._context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            if self._sessions:
                last_session = list(self._sessions.values())[-1]
                if last_session.cookies:
                    await self._context.add_cookies(last_session.cookies)
        return self._context

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            context = await self._get_browser(**kwargs)
            page = await context.new_page()
            await page.goto(url, wait_until=kwargs.get("wait_until", "networkidle"), timeout=self._timeout * 1000)

            if kwargs.get("auto_scroll"):
                await self._auto_scroll(page)

            content = await page.inner_text("body")
            html = await page.content()
            title = await page.title()
            cookies = await context.cookies()

            screenshot = None
            if kwargs.get("take_screenshot"):
                screenshot = await page.screenshot(full_page=kwargs.get("full_page", False))

            pdf = None
            if kwargs.get("save_pdf"):
                pdf = await page.pdf(format="A4")

            if kwargs.get("save_cookies") and self._sessions:
                last_sid = list(self._sessions.keys())[-1] if self._sessions else self.create_session()
                self._sessions[last_sid].cookies = cookies

            await page.close()
            return BrowserResult(
                url=url, content=content, html=html, title=title,
                screenshot=screenshot, pdf=pdf, cookies=cookies,
                agent=self.name, duration_ms=self._timing(start),
                session_id=kwargs.get("session_id"),
            )
        except ImportError:
            return BrowserResult(url=url, status="error", error="playwright not installed", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))

    async def login(self, url: str, credentials: dict, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            context = await self._get_browser(**kwargs)
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self._timeout * 1000)

            selectors = kwargs.get("selectors", {})
            username_sel = selectors.get("username", 'input[name="username"], input[name="email"], input[type="email"], #username, #email')
            password_sel = selectors.get("password", 'input[name="password"], input[type="password"], #password')
            submit_sel = selectors.get("submit", 'button[type="submit"], input[type="submit"]')

            await page.fill(username_sel, credentials.get("username", ""))
            await page.fill(password_sel, credentials.get("password", ""))
            await page.click(submit_sel)
            await page.wait_for_load_state("networkidle")

            content = await page.inner_text("body")
            cookies = await context.cookies()
            await page.close()
            return BrowserResult(url=url, content=content, cookies=cookies, agent=self.name,
                                duration_ms=self._timing(start), metadata={"action": "login"})
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))

    async def _auto_scroll(self, page, max_scrolls: int = 20):
        for _ in range(max_scrolls):
            prev_height = await page.evaluate("document.body.scrollHeight")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                break

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._context = None

import asyncio
