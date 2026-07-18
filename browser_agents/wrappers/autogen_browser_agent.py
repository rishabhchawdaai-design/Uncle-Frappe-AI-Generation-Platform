"""15. AutoGen Browser Agent - Microsoft AutoGen browser integration."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class AutoGenBrowserAgent(BaseBrowserAgent):
    name = "autogen_browser"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.JS_RENDERING,
        BrowserCapability.STRUCTURED_EXTRACTION,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from autogen.agentchat.contrib.web_surfer import WebSurferAgent
            from autogen import UserProxyAgent
            llm_config = kwargs.get("llm_config", {"model": "gpt-4", "api_key": "PLACEHOLDER"})

            web_surfer = WebSurferAgent(
                name="web_surfer",
                llm_config=llm_config,
                browser_config={"headless": self.headless},
            )
            user = UserProxyAgent("user", human_input_mode="NEVER")
            task = kwargs.get("task", f"Navigate to {url} and extract all text content")
            result = await user.a_initiate_chat(web_surfer, message=task, max_turns=3)
            content = result.summary if hasattr(result, "summary") else str(result)
            return BrowserResult(url=url, content=content, agent=self.name, duration_ms=self._timing(start))
        except ImportError:
            return BrowserResult(url=url, status="error", error="pip install pyautogen[largeagent]", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
