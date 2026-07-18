"""3. Open Operator - Open-source browser operator for automation."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class OpenOperatorAgent(BaseBrowserAgent):
    name = "open_operator"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.CAPTCHA_DETECTION,
        BrowserCapability.SESSION_PERSIST, BrowserCapability.COOKIE_MANAGEMENT,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self._timeout * 1000)
                content = await page.inner_text("body")
                html = await page.content()
                title = await page.title()
                cookies = await context.cookies()
                ss = await page.screenshot() if kwargs.get("take_screenshot") else None
                await browser.close()
                return BrowserResult(
                    url=url, content=content, html=html, title=title,
                    screenshot=ss, cookies=cookies, agent=self.name,
                    duration_ms=self._timing(start),
                )
        except ImportError:
            return BrowserResult(url=url, status="error", error="playwright not installed", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
