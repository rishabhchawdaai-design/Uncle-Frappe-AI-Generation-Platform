"""19. OmniParser - Vision-based UI parsing for any screen."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class OmniParserAgent(BaseBrowserAgent):
    name = "omniparser"
    capabilities = [
        BrowserCapability.SCREENSHOT, BrowserCapability.STRUCTURED_EXTRACTION,
        BrowserCapability.JS_RENDERING, BrowserCapability.HUMAN_LIKE,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8081")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            import httpx
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1920, "height": 1080})
                await page.goto(url, wait_until="networkidle", timeout=self._timeout * 1000)
                screenshot_bytes = await page.screenshot(full_page=True)
                html = await page.content()
                title = await page.title()
                content = await page.inner_text("body")
                await browser.close()

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{self.base_url}/parse",
                    files={"image": ("screenshot.png", screenshot_bytes, "image/png")})
                parsed = resp.json()

            return BrowserResult(
                url=url, content=content, html=html, title=title,
                screenshot=screenshot_bytes,
                extracted_data={"omniparser": parsed.get("elements", [])},
                agent=self.name, duration_ms=self._timing(start),
            )
        except httpx.ConnectError:
            return BrowserResult(url=url, status="error",
                error="OmniParser not running. Start its server first.",
                agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
