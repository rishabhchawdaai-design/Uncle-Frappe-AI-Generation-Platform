"""7. Puppeteer - Google Chrome DevTools Protocol automation."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class PuppeteerAgent(BaseBrowserAgent):
    name = "puppeteer"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.PDF_DOWNLOAD, BrowserCapability.CAPTCHA_DETECTION,
        BrowserCapability.COOKIE_MANAGEMENT, BrowserCapability.FILE_DOWNLOAD,
        BrowserCapability.JS_RENDERING, BrowserCapability.FORM_FILLING,
        BrowserCapability.PROXY_SUPPORT, BrowserCapability.RECORDING,
        BrowserCapability.STRUCTURED_EXTRACTION,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from pyppeteer import launch
            browser = await launch(
                headless=kwargs.get("headless", self.headless),
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            page = await browser.newPage()
            await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0")
            await page.setViewport({"width": 1920, "height": 1080})

            if kwargs.get("proxy"):
                await page.setRequestInterception(True)

            await page.goto(url, {"waitUntil": "networkidle0", "timeout": self._timeout * 1000})

            if kwargs.get("auto_scroll"):
                for _ in range(20):
                    prev = await page.evaluate("document.body.scrollHeight")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1.5)
                    new = await page.evaluate("document.body.scrollHeight")
                    if new == prev:
                        break

            content = await page.evaluate("() => document.body.innerText")
            html = await page.content()
            title = await page.title()
            cookies = await page.cookies()

            screenshot = None
            if kwargs.get("take_screenshot"):
                screenshot = await page.screenshot({"fullPage": kwargs.get("full_page", False)})

            pdf = None
            if kwargs.get("save_pdf"):
                pdf = await page.pdf({"format": "A4", "printBackground": True})

            await browser.close()
            return BrowserResult(
                url=url, content=content, html=html, title=title,
                screenshot=screenshot, pdf=pdf, cookies=cookies,
                agent=self.name, duration_ms=self._timing(start),
            )
        except ImportError:
            return BrowserResult(url=url, status="error", error="pyppeteer not installed", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))

import asyncio
