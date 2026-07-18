"""Section 3: Search MCPs — All 20 tools."""
import asyncio, time, os
from sections.base import BaseTool, ToolResult, ToolCategory

class ExaSearch(BaseTool):
    name = "exa"; category = ToolCategory.SEARCH; requires_api_key = True
    mcp_server = "@anthropic-ai/mcp-server-exa"
    capabilities = ["neural_search", "similarity", "contents", "autocomplete"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"x-api-key":self._get_api_key("EXA_API_KEY"),"Content-Type":"application/json"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("https://api.exa.ai/search",json={"query":query,"numResults":kw.get("num",10),"contents":{"text":True}},headers=h)
                d=r.json()
                return ToolResult(source=query,raw=json.dumps(d.get("results",[])),metadata={"count":len(d.get("results",[]))},tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

import json

class TavilySearch(BaseTool):
    name = "tavily"; category = ToolCategory.SEARCH; requires_api_key = True
    mcp_server = "tavily-mcp"; capabilities = ["search", "extract", "qa"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from tavily import TavilyClient
            client=TavilyClient(api_key=self._get_api_key("TAVILY_API_KEY"))
            r=client.search(query=query,search_depth=kw.get("depth","advanced"))
            return ToolResult(source=query,raw=json.dumps(r.get("results",[])),metadata={"answer":r.get("answer","")},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install tavily-python",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class BraveSearch(BaseTool):
    name = "brave"; category = ToolCategory.SEARCH; requires_api_key = True
    mcp_server = "@anthropic-ai/mcp-server-brave-search"
    capabilities = ["web_search", "news", "images", "videos", "suggestions"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Accept":"application/json","X-Subscription-Token":self._get_api_key("BRAVE_API_KEY")}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.search.brave.com/res/v1/web/search",params={"q":query,"count":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class DuckDuckGoSearch(BaseTool):
    name = "duckduckgo"; category = ToolCategory.SEARCH
    capabilities = ["web_search", "news", "images", "instant_answers"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results=[r for r in ddgs.text(query,max_results=kw.get("num",10))]
            return ToolResult(source=query,raw=json.dumps(results),metadata={"count":len(results)},tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install duckduckgo-search",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class GoogleSearch(BaseTool):
    name = "google_pse"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["web_search", "custom_search", "cse"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            params={"key":self._get_api_key("GOOGLE_API_KEY"),"cx":kw.get("cx",self._get_api_key("GOOGLE_CX")),"q":query,"num":kw.get("num",10)}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.googleapis.com/customsearch/v1",params=params)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class BingSearch(BaseTool):
    name = "bing"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["web_search", "news", "images", "videos"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Ocp-Apim-Subscription-Key":self._get_api_key("BING_API_KEY")}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.bing.microsoft.com/v7.0/search",params={"q":query,"count":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SearXNGSearch(BaseTool):
    name = "searxng"; category = ToolCategory.SEARCH; requires_docker = True
    capabilities = ["metasearch", "privacy", "multi_engine", "self_hosted"]
    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url","http://localhost:8080") if config else "http://localhost:8080"
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"{self.base_url}/search",params={"q":query,"format":"json","categories":kw.get("categories","general")})
                d=r.json(); results=d.get("results",[])
                return ToolResult(source=query,raw=json.dumps(results),metadata={"count":len(results)},tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PerplexitySearch(BaseTool):
    name = "perplexity"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["ai_search", "citations", "real_time", "follow_up"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bearer {self._get_api_key('PERPLEXITY_API_KEY')}","Content-Type":"application/json"}
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("https://api.perplexity.ai/chat/completions",json={"model":kw.get("model","llama-3.1-sonar-small-128k-online"),"messages":[{"role":"user","content":query}]},headers=h)
                data=r.json(); content=data.get("choices",[{}])[0].get("message",{}).get("content","")
                return ToolResult(source=query,raw=content,metadata={"model":data.get("model","")},tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class JinaSearch(BaseTool):
    name = "jina"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["search", "reader", "deep_research"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bearer {self._get_api_key('JINA_API_KEY')}","Accept":"application/json"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"https://s.jina.ai/{query}",headers=h)
                return ToolResult(source=query,raw=r.text,tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SerpAPISearch(BaseTool):
    name = "serpapi"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["google", "bing", "baidu", "local", "news", "scholar"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            params={"api_key":self._get_api_key("SERPAPI_KEY"),"q":query,"engine":kw.get("engine","google"),"num":kw.get("num",10)}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://serpapi.com/search",params=params)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SerperSearch(BaseTool):
    name = "serper"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["google_search", "images", "news", "places", "suggest"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"X-API-KEY":self._get_api_key("SERPER_API_KEY"),"Content-Type":"application/json"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("https://google.serper.dev/search",json={"q":query,"num":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class KagiSearch(BaseTool):
    name = "kagi"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["ad_free", "privacy", "summarizer", "enrichment"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"Authorization":f"Bot {self._get_api_key('KAGI_API_KEY')}"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("https://kagi.com/api/v0/search",json={"query":query},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MetaphorSearch(BaseTool):
    name = "metaphor"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["neural", "similar", "contents", "auto_query"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={"x-api-key":self._get_api_key("METAPHOR_API_KEY"),"Content-Type":"application/json"}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("https://api.metaphor.systems/search",json={"query":query,"numResults":kw.get("num",10)},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class YaCySearch(BaseTool):
    name = "yacy"; category = ToolCategory.SEARCH; requires_docker = True
    capabilities = ["p2p", "self_hosted", "privacy", "distributed"]
    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = config.get("base_url","http://localhost:8090") if config else "http://localhost:8090"
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get(f"{self.base_url}/yacysearch.json",params={"query":query,"maximumResults":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class CommonCrawlSearch(BaseTool):
    name = "commoncrawl"; category = ToolCategory.SEARCH
    capabilities = ["web_archive", "bulk_data", "index", "CDX"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.get("https://index.commoncrawl.org/CC-MAIN-2024-10-index",params={"q":query,"output":"json","limit":kw.get("num",10)})
                results=[json.loads(line) for line in r.text.strip().split("\n") if line]
                return ToolResult(source=query,raw=json.dumps(results),metadata={"count":len(results)},tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))
import json

class OpenAlexSearch(BaseTool):
    name = "openalex"; category = ToolCategory.SEARCH
    capabilities = ["academic", "works", "authors", "institutions", "concepts"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.openalex.org/works",params={"search":query,"per_page":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class CrossrefSearch(BaseTool):
    name = "crossref"; category = ToolCategory.SEARCH
    capabilities = ["academic", "DOI", "citations", "metadata"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.crossref.org/works",params={"query":query,"rows":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SemanticScholarSearch(BaseTool):
    name = "semantic_scholar"; category = ToolCategory.SEARCH; requires_api_key = True
    capabilities = ["academic", "citations", "references", "tldr", "author"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            h={}; k=self._get_api_key("SEMANTIC_SCHOLAR_API_KEY")
            if k: h["x-api-key"]=k
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://api.semanticscholar.org/graph/v1/paper/search",params={"query":query,"limit":kw.get("num",10),"fields":"title,abstract,citationCount,year,url"},headers=h)
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class EuropePMCSearch(BaseTool):
    name = "europepmc"; category = ToolCategory.SEARCH
    capabilities = ["biomedical", "life_science", "open_access", "citations"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",params={"query":query,"format":"json","pageSize":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class WikidataSearch(BaseTool):
    name = "wikidata"; category = ToolCategory.SEARCH
    capabilities = ["entities", "sparql", "structured_data", "knowledge_base"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":query,"language":"en","format":"json","limit":kw.get("num",10)})
                return ToolResult(source=query,raw=json.dumps(r.json()),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

SEARCH_REGISTRY = {
    "exa": ExaSearch, "tavily": TavilySearch, "brave": BraveSearch,
    "duckduckgo": DuckDuckGoSearch, "google_pse": GoogleSearch,
    "bing": BingSearch, "searxng": SearXNGSearch, "perplexity": PerplexitySearch,
    "jina": JinaSearch, "serpapi": SerpAPISearch, "serper": SerperSearch,
    "kagi": KagiSearch, "metaphor": MetaphorSearch, "yacy": YaCySearch,
    "commoncrawl": CommonCrawlSearch, "openalex": OpenAlexSearch,
    "crossref": CrossrefSearch, "semantic_scholar": SemanticScholarSearch,
    "europepmc": EuropePMCSearch, "wikidata": WikidataSearch,
}
