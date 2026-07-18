"""16. LangGraph Browser Agent - LangChain/LangGraph browser automation."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class LangGraphBrowserAgent(BaseBrowserAgent):
    name = "langgraph_browser"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.JS_RENDERING,
        BrowserCapability.STRUCTURED_EXTRACTION, BrowserCapability.AUTO_RETRY,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from langchain_community.tools.playwright import NavigateWeb, ClickElement, ExtractText
            navigate_tool = NavigateWeb()
            result = await navigate_tool.ainvoke({"url": url})

            extract_tool = ExtractText()
            text_result = await extract_tool.ainvoke({})
            return BrowserResult(
                url=url, content=str(text_result), html=str(result),
                agent=self.name, duration_ms=self._timing(start),
            )
        except ImportError:
            return BrowserResult(url=url, status="error", error="pip install langchain-community", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
