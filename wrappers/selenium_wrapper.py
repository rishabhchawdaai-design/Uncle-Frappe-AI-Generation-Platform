"""15. Selenium Grid - Browser automation for complex pages."""
import time
from .base import BaseCollector, CollectorResult

class SeleniumCollector(BaseCollector):
    name = "selenium"
    capabilities = ["browser_automation", "js_rendering", "form_interactions", "grid_support"]

    def __init__(self, config=None):
        super().__init__(config)
        self.grid_url = config.get("grid_url", "")

    async def collect(self, url: str, **kwargs) -> CollectorResult:
        start = time.time()
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            opts = Options()
            opts.add_argument("--headless")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            if self.grid_url:
                driver = webdriver.Remote(self.grid_url, options=opts)
            else:
                driver = webdriver.Chrome(options=opts)
            driver.get(url)
            time.sleep(kwargs.get("wait", 2))
            content = driver.find_element(By.TAG_NAME, "body").text
            html = driver.page_source
            title = driver.title
            driver.quit()
            return CollectorResult(
                url=url, content=content, raw_html=html, title=title,
                collector=self.name, duration_ms=self._timing(start),
            )
        except Exception as e:
            return CollectorResult(url=url, status="error", error=str(e), collector=self.name, duration_ms=self._timing(start))
