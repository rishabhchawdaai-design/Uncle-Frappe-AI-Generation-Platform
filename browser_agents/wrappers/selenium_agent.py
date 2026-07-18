"""12. Selenium - Industry-standard browser automation."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class SeleniumAgent(BaseBrowserAgent):
    name = "selenium"
    requires_docker = True
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.PDF_DOWNLOAD, BrowserCapability.CAPTCHA_DETECTION,
        BrowserCapability.SESSION_PERSIST, BrowserCapability.COOKIE_MANAGEMENT,
        BrowserCapability.FILE_DOWNLOAD, BrowserCapability.FORM_FILLING,
        BrowserCapability.MULTI_TAB, BrowserCapability.PROXY_SUPPORT,
        BrowserCapability.RECORDING, BrowserCapability.STRUCTURED_EXTRACTION,
        BrowserCapability.AUTO_RETRY, BrowserCapability.HEALTH_MONITOR,
    ]

    def __init__(self, config=None):
        super().__init__(config)
        self.grid_url = config.get("grid_url", "")

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By

            opts = Options()
            opts.add_argument("--headless")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")

            if kwargs.get("proxy"):
                opts.add_argument(f"--proxy-server={kwargs['proxy']}")

            if self.grid_url:
                driver = webdriver.Remote(self.grid_url, options=opts)
            else:
                driver = webdriver.Chrome(options=opts)

            driver.get(url)
            wait = kwargs.get("wait", 3)
            time.sleep(wait)

            if kwargs.get("auto_scroll"):
                last_height = driver.execute_script("return document.body.scrollHeight")
                for _ in range(20):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1.5)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

            content = driver.find_element(By.TAG_NAME, "body").text
            html = driver.page_source
            title = driver.title
            cookies = driver.get_cookies()

            screenshot = None
            if kwargs.get("take_screenshot"):
                screenshot = driver.get_screenshot_as_png()

            pdf = None
            if kwargs.get("save_pdf"):
                pdf = driver.print_page({"printBackground": True, "paperWidth": 8.27, "paperHeight": 11.69})

            driver.quit()
            return BrowserResult(
                url=url, content=content, html=html, title=title,
                screenshot=screenshot, pdf=pdf, cookies=cookies,
                agent=self.name, duration_ms=self._timing(start),
            )
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
