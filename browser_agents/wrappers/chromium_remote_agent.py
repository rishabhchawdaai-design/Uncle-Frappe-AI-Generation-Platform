"""8. Chromium Remote Browser - Remote Chrome instance via CDP."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class ChromiumRemoteAgent(BaseBrowserAgent):
    name = "chromium_remote"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.JS_RENDERING,
        BrowserCapability.SCREENSHOT, BrowserCapability.PROXY_SUPPORT,
        BrowserCapability.SESSION_PERSIST, BrowserCapability.COOKIE_MANAGEMENT,
        BrowserCapability.FORM_FILLING,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.cdp_url = config.get("cdp_url", "http://localhost:9222")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(self.cdp_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self._timeout * 1000)
                content = await page.inner_text("body")
                html = await page.content()
                title = await page.title()
                screenshot = await page.screenshot() if kwargs.get("take_screenshot") else None
                cookies = await context.cookies()
                await page.close()
                return BrowserResult(
                    url=url, content=content, html=html, title=title,
                    screenshot=screenshot, cookies=cookies, agent=self.name,
                    duration_ms=self._timing(start),
                )
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
