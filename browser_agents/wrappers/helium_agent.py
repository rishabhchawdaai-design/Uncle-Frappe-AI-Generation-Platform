"""13. Helium - Simplified browser automation API."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class HeliumAgent(BaseBrowserAgent):
    name = "helium"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.COOKIE_MANAGEMENT,
        BrowserCapability.HUMAN_LIKE,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from helium import start_chrome, scroll_down, kill_browser, get_driver
            driver = start_chrome(url, headless=kwargs.get("headless", self.headless))
            time.sleep(kwargs.get("wait", 2))

            if kwargs.get("auto_scroll"):
                for _ in range(10):
                    scroll_down(3)
                    time.sleep(1)

            content = driver.find_element("tag name", "body").text
            html = driver.page_source
            title = driver.title
            screenshot = driver.get_screenshot_as_png() if kwargs.get("take_screenshot") else None
            cookies = driver.get_cookies()

            kill_browser()
            return BrowserResult(
                url=url, content=content, html=html, title=title,
                screenshot=screenshot, cookies=cookies,
                metadata={"library": "helium"}, agent=self.name,
                duration_ms=self._timing(start),
            )
        except ImportError:
            return BrowserResult(url=url, status="error", error="pip install helium[all]", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
