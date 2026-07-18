"""17. CrewAI Browser Agent - CrewAI browser automation task agent."""
import time
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability

class CrewAIBrowserAgent(BaseBrowserAgent):
    name = "crewai_browser"
    capabilities = [
        BrowserCapability.NAVIGATION, BrowserCapability.LOGIN,
        BrowserCapability.SCROLLING, BrowserCapability.SCREENSHOT,
        BrowserCapability.FORM_FILLING, BrowserCapability.STRUCTURED_EXTRACTION,
    ]

    async def navigate(self, url: str, **kwargs) -> BrowserResult:
        start = time.time()
        try:
            from crewai import Agent, Task, Crew
            from crewai_tools import ScrapeWebsiteTool

            browser_agent = Agent(
                role="Web Browser Agent",
                goal="Navigate to websites and extract structured information",
                backstory="Expert at browsing and extracting web content",
                tools=[ScrapeWebsiteTool()],
                allow_delegation=False,
            )
            task = Task(
                description=kwargs.get("task", f"Navigate to {url} and extract all text content"),
                agent=browser_agent,
                expected_output="Extracted web content",
            )
            crew = Crew(agents=[browser_agent], tasks=[task])
            result = crew.kickoff()
            return BrowserResult(url=url, content=str(result), agent=self.name, duration_ms=self._timing(start))
        except ImportError:
            return BrowserResult(url=url, status="error", error="pip install crewai crewai-tools", agent=self.name, duration_ms=self._timing(start))
        except Exception as e:
            return BrowserResult(url=url, status="error", error=str(e), agent=self.name, duration_ms=self._timing(start))
