"""Section 6: AI Research Agents — All 20 frameworks."""
import asyncio, time, json, os
from sections.base import BaseTool, ToolResult, ToolCategory

class OpenHandsAgent(BaseTool):
    name = "openhands"; category = ToolCategory.AI_RESEARCH
    mcp_server = "openhands-mcp"; capabilities = ["coding", "browser", "terminal", "planning"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:3000/api/execute",json={"task":query,"browser_config":{"headless":True}})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class OpenManusAgent(BaseTool):
    name = "openmanus"; category = ToolCategory.AI_RESEARCH
    capabilities = ["browser_agent", "file_ops", "code_gen"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:5000/execute",json={"task":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class CrewAIAgent(BaseTool):
    name = "crewai"; category = ToolCategory.AI_RESEARCH
    capabilities = ["multi_agent", "tasks", "tools", "memory"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from crewai import Agent, Task, Crew
            agent=Agent(role="Researcher",goal=f"Research: {query}",backstory="Expert researcher",allow_delegation=False)
            task=Task(description=query,agent=agent,expected_output="Research findings")
            crew=Crew(agents=[agent],tasks=[task])
            result=crew.kickoff()
            return ToolResult(source=query,raw=str(result),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install crewai",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class AutoGenAgent(BaseTool):
    name = "autogen"; category = ToolCategory.AI_RESEARCH
    capabilities = ["multi_agent", "chat", "code_exec", "tool_use"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8081/api/chat",json={"message":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class LangGraphAgent(BaseTool):
    name = "langgraph"; category = ToolCategory.AI_RESEARCH
    capabilities = ["state_graph", "cycles", "persistence", "human_in_loop"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8082/invoke",json={"input":{"query":query}})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class LangChainAgent(BaseTool):
    name = "langchain"; category = ToolCategory.AI_RESEARCH
    capabilities = ["chains", "agents", "retrieval", "tools", "callbacks"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from langchain_openai import ChatOpenAI
            from langchain.agents import create_tool_calling_agent, AgentExecutor
            llm=ChatOpenAI(model="gpt-4o-mini",api_key=os.environ.get("OPENAI_API_KEY",""))
            from langchain_core.prompts import ChatPromptTemplate
            prompt=ChatPromptTemplate.from_messages([("human","{input}")])
            agent=create_tool_calling_agent(llm,[],prompt)
            executor=AgentExecutor(agent=agent,tools=[],verbose=False)
            r=executor.invoke({"input":query})
            return ToolResult(source=query,raw=str(r.get("output","")),tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SmolAgents(BaseTool):
    name = "smolagents"; category = ToolCategory.AI_RESEARCH
    capabilities = ["code_agent", "tool_use", "lightweight"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from smolagents import CodeAgent
            agent=CodeAgent(tools=[])
            result=agent.run(query)
            return ToolResult(source=query,raw=str(result),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install smolagents",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class HaystackAgent(BaseTool):
    name = "haystack"; category = ToolCategory.AI_RESEARCH
    capabilities = ["pipelines", "retrieval", "generation", "custom_nodes"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8083/query",json={"query":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class DSPyAgent(BaseTool):
    name = "dspy"; category = ToolCategory.AI_RESEARCH
    capabilities = ["modules", "optimizers", "signatures", "cot"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8084/predict",json={"signature":"question -> answer","question":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class LlamaIndexAgent(BaseTool):
    name = "llamaindex"; category = ToolCategory.AI_RESEARCH
    capabilities = ["indexing", "retrieval", "rag", "agents", "workflows"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8085/query",json={"query":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class CamelAIAgent(BaseTool):
    name = "camelai"; category = ToolCategory.AI_RESEARCH
    capabilities = ["role_playing", "multi_agent", "task_oriented"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8086/task",json={"task":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MetaGPTAgent(BaseTool):
    name = "metagpt"; category = ToolCategory.AI_RESEARCH
    capabilities = ["multi_agent", "software_dev", "role_playing"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8087/task",json={"requirement":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class SuperAGIAgent(BaseTool):
    name = "superagi"; category = ToolCategory.AI_RESEARCH
    capabilities = ["autonomous", "tool_use", "workflows"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8088/goal",json={"goal":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class AgentVerseAgent(BaseTool):
    name = "agentverse"; category = ToolCategory.AI_RESEARCH
    capabilities = ["multi_agent", "simulation", "debate", "consensus"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8089/simulate",json={"topic":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class OpenDevinAgent(BaseTool):
    name = "opendevin"; category = ToolCategory.AI_RESEARCH
    capabilities = ["coding", "browser", "terminal", "sandbox"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                r=await c.post("http://localhost:3001/task",json={"task":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class GPTResearcherAgent(BaseTool):
    name = "gpt_researcher"; category = ToolCategory.AI_RESEARCH
    capabilities = ["deep_research", "report_gen", "multi_source", "citations"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                r=await c.post("http://localhost:8090/research",json={"query":query,"report_type":"research_report"})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class AgentReachAgent(BaseTool):
    name = "agentreach"; category = ToolCategory.AI_RESEARCH
    capabilities = ["web_scraping", "structured_extraction", "reach"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from agentreach import scrape
            result=await scrape(query,**kw)
            return ToolResult(source=query,raw=str(result),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install agentreach",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class BrowserUseAgent(BaseTool):
    name = "browser_use"; category = ToolCategory.AI_RESEARCH
    capabilities = ["ai_browsing", "form_fill", "multi_step", "screenshot"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from browser_use import Agent
            agent=Agent(task=query)
            result=await agent.run()
            return ToolResult(source=query,raw=str(result),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install browser-use",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class AutoScraperAgent(BaseTool):
    name = "autoscraper"; category = ToolCategory.AI_RESEARCH
    capabilities = ["auto_scrape", "pattern_learning", "rule_extraction"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from autoscraper import AutoScraper
            scraper=AutoScraper()
            result=scraper.build(query)
            return ToolResult(source=query,raw=json.dumps(result),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install autoscraper",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class DeepResearchAgent(BaseTool):
    name = "deep_research"; category = ToolCategory.AI_RESEARCH
    capabilities = ["multi_hop", "iterative", "citations", "report"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as c:
                r=await c.post("http://localhost:8091/research",json={"query":query,"depth":kw.get("depth",3)})
                return ToolResult(source=query,raw=r.text[:8000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

AI_RESEARCH_REGISTRY = {
    "openhands": OpenHandsAgent, "openmanus": OpenManusAgent,
    "crewai": CrewAIAgent, "autogen": AutoGenAgent,
    "langgraph": LangGraphAgent, "langchain": LangChainAgent,
    "smolagents": SmolAgents, "haystack": HaystackAgent,
    "dspy": DSPyAgent, "llamaindex": LlamaIndexAgent,
    "camelai": CamelAIAgent, "metagpt": MetaGPTAgent,
    "superagi": SuperAGIAgent, "agentverse": AgentVerseAgent,
    "opendevin": OpenDevinAgent, "gpt_researcher": GPTResearcherAgent,
    "agentreach": AgentReachAgent, "browser_use": BrowserUseAgent,
    "autoscraper": AutoScraperAgent, "deep_research": DeepResearchAgent,
}
