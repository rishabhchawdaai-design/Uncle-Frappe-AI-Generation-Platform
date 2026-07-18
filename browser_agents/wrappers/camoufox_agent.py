"""11. Camoufox - Firefox-based anti-fingerprint browser."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class CamoufoxAgent(BaseBrowserAgent):
    name = "camoufox"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.STEALTH,
        BrowserCapability.PROXY_SUPPORT, BrowserCapability.COOKIE_MANAGEMENT,
        BrowserCapability.SCREENSHOT, BrowserCapability.HUMAN_LIKE,
        BrowserCapability.CAPTCHA_DETECTION, BrowserCapability.JS_RENDERING,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.firefox.launch(
                    headless=kwargs.get("headless", self.headless),
                    firefox_user_prefs={
                        "dom.webdriver.enabled": False,
                        "useAutomationExtension": False,
                    },
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                )
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self._timeout * 1000)
                content = await page.inner_text("body")
                html = await page.content()
                title = await page.title()
                screenshot = await page.screenshot() if kwargs.get("take_screenshot") else None
                cookies = await context.cookies()
                await browser.close()
                return BrowserResult(
                    url=url, content=content, html=html, title=title,
                    screenshot=screenshot, cookies=cookies,
                    metadata={"browser": "camoufox", "anti_fingerprint": True},
                    agent=self.name, duration_ms=self._timing(start),
                )
        except ImportError:
            return BrowserResult(url=url, status="error", error="Install camoufox: pip install camoufox", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
