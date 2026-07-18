"""Research MCP Stack - Data Collection Wrappers (20 Tools)"""
from .base import BaseCollector, CollectorResult
from .firecrawl_wrapper import FirecrawlCollector
from .crawl4ai_wrapper import Crawl4AICollector
from .browser_use_wrapper import BrowserUseCollector
from .agentreach_wrapper import AgentReachCollector
from .playwright_mcp_wrapper import PlaywrightMCP
from .puppeteer_mcp_wrapper import PuppeteerMCP
from .brightdata_mcp_wrapper import BrightDataMCP
from .jina_reader_wrapper import JinaReaderCollector
from .tavily_wrapper import TavilyCollector
from .exa_wrapper import ExaCollector
from .serpmcp_wrapper import SerpAPICollector
from .searxng_wrapper import SearXNGCollector
from .apify_wrapper import ApifyCollector
from .scrapy_wrapper import ScrapyCollector
from .selenium_wrapper import SeleniumCollector
from .trafilatura_wrapper import TrafilaturaCollector
from .newspaper_wrapper import NewspaperCollector
from .readability_wrapper import ReadabilityCollector
from .requests_html_wrapper import RequestsHTMLCollector
from .bs4_wrapper import BS4Collector

COLLECTOR_REGISTRY = {
    "firecrawl": FirecrawlCollector,
    "crawl4ai": Crawl4AICollector,
    "browser_use": BrowserUseCollector,
    "agentreach": AgentReachCollector,
    "playwright_mcp": PlaywrightMCP,
    "puppeteer_mcp": PuppeteerMCP,
    "brightdata_mcp": BrightDataMCP,
    "jina_reader": JinaReaderCollector,
    "tavily": TavilyCollector,
    "exa": ExaCollector,
    "serpapi": SerpAPICollector,
    "searxng": SearXNGCollector,
    "apify": ApifyCollector,
    "scrapy": ScrapyCollector,
    "selenium": SeleniumCollector,
    "trafilatura": TrafilaturaCollector,
    "newspaper3k": NewspaperCollector,
    "readability": ReadabilityCollector,
    "requests_html": RequestsHTMLCollector,
    "bs4": BS4Collector,
}
