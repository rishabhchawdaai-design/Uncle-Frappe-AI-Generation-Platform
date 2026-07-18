"""20. Vision Browser Agent - AI vision model + browser automation."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class VisionBrowserAgent(BaseBrowserAgent):
    name = "vision_browser"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.SCREENSHOT,
        BrowserCapability.CAPTCHA_DETECTION, BrowserCapability.STRUCTURED_EXTRACTION,
        BrowserCapability.HUMAN_LIKE, BrowserCapability.JS_RENDERING,
        BrowserCapability.FORM_FILLING,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get("openai_api_key", "")
        self.model = config.get("model", "gpt-4o")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1920, "height": 1080})
                await page.goto(url, wait_until="networkidle", timeout=self._timeout * 1000)

                content = await page.inner_text("body")
                html = await page.content()
                title = await page.title()
                screenshot_bytes = await page.screenshot(full_page=True)

                vision_analysis = await self._analyze_screenshot(screenshot_bytes, kwargs.get("prompt", "Describe this page and extract all visible text and data"))
                await browser.close()

            return BrowserResult(
                url=url, content=content, html=html, title=title,
                screenshot=screenshot_bytes,
                extracted_data={"vision_analysis": vision_analysis},
                agent=self.name, duration_ms=self._timing(start),
            )
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))

    async def _analyze_screenshot(self, image_bytes: bytes, prompt: str) -> str:
        try:
            import httpx
            import base64
            b64 = base64.b64encode(image_bytes).decode()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ]}],
                        "max_tokens": 2000,
                    })
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception:
            return "Vision analysis unavailable (API key needed)"

    async def detect_captcha(self, url: str, **kwargs) -> BrowserResult:
        result = await self.navigate(url, prompt="Is there a CAPTCHA, verification challenge, or bot detection on this page? Describe it in detail.", **kwargs)
        analysis = result.extracted_data.get("vision_analysis", "")
        result.metadata["captcha_detected"] = any(word in analysis.lower() for word in ["captcha", "robot", "verification", "challenge", "recaptcha"])
        result.metadata["captcha_details"] = analysis
        return result
