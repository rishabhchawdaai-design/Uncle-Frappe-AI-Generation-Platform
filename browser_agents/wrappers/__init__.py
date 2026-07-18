"""Section 2: Internet & Browser Agents (20 Tools)"""
from .base import BaseBrowserAgent, BrowserResult, BrowserCapability, SessionState
from .browser_use_agent import BrowserUseAgent
from .agentreach_agent import AgentReachAgent
from .open_operator_agent import OpenOperatorAgent
from .openhands_agent import OpenHandsAgent
from .stagehand_agent import StagehandAgent
from .playwright_agent import PlaywrightAgent
from .puppeteer_agent import PuppeteerAgent
from .chromium_remote_agent import ChromiumRemoteAgent
from .browserless_agent import BrowserlessAgent
from .steel_agent import SteelAgent
from .camoufox_agent import CamoufoxAgent
from .selenium_agent import SeleniumAgent
from .helium_agent import HeliumAgent
from .browserpilot_agent import BrowserPilotAgent
from .autogen_browser_agent import AutoGenBrowserAgent
from .langgraph_browser_agent import LangGraphBrowserAgent
from .crewai_browser_agent import CrewAIBrowserAgent
from .skyvern_agent import SkyvernAgent
from .omniparser_agent import OmniParserAgent
from .vision_browser_agent import VisionBrowserAgent

AGENT_REGISTRY = {
    "browser_use": BrowserUseAgent,
    "agentreach": AgentReachAgent,
    "open_operator": OpenOperatorAgent,
    "openhands": OpenHandsAgent,
    "stagehand": StagehandAgent,
    "playwright": PlaywrightAgent,
    "puppeteer": PuppeteerAgent,
    "chromium_remote": ChromiumRemoteAgent,
    "browserless": BrowserlessAgent,
    "steel": SteelAgent,
    "camoufox": CamoufoxAgent,
    "selenium": SeleniumAgent,
    "helium": HeliumAgent,
    "browserpilot": BrowserPilotAgent,
    "autogen_browser": AutoGenBrowserAgent,
    "langgraph_browser": LangGraphBrowserAgent,
    "crewai_browser": CrewAIBrowserAgent,
    "skyvern": SkyvernAgent,
    "omniparser": OmniParserAgent,
    "vision_browser": VisionBrowserAgent,
}
