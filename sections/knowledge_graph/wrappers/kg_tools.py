"""Section 8: Knowledge Graph — All 20 tools."""
import asyncio, time, json, os
from sections.base import BaseTool, ToolResult, ToolCategory

class Neo4jTool(BaseTool):
    name = "neo4j"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    mcp_server = "neo4j-mcp"; capabilities = ["graph_db", "cypher", "ACID", "OLAP", "aura"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from neo4j import GraphDatabase
            driver=GraphDatabase.driver(kw.get("uri","bolt://localhost:7687"),auth=(kw.get("user","neo4j"),kw.get("password","")))
            with driver.session() as session:
                result=session.run(query)
                data=[r.data() for r in result]
            driver.close()
            return ToolResult(source=query,raw=json.dumps(data),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install neo4j",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MemgraphTool(BaseTool):
    name = "memgraph"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["graph_db", "cypher", "in_memory", "streaming"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:7444/",json={"statements":[{"statement":query}]})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class FalkorDBTool(BaseTool):
    name = "falkordb"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["graph_db", "redis_compatible", "fast", "cypher"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from falkordb import FalkorDB
            db=FalkorDB(host=kw.get("host","localhost"),port=kw.get("port",6380))
            result=db.query(query)
            return ToolResult(source=query,raw=json.dumps(result.result_set),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install falkordb",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class TypeDBTool(BaseTool):
    name = "typedb"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["logic_programming", "type_theory", "schema", "reasoning"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:17300/query",json={"query":query})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ArangoDBTool(BaseTool):
    name = "arangodb"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["graph_db", "document", "key_value", "AQL", "foxx"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from arango import ArangoClient
            client=ArangoClient(hosts=kw.get("host","http://localhost:8529"))
            db=client.db("testdb",username="root",password=kw.get("password",""))
            cursor=db.aql.execute(query)
            data=[doc for doc in cursor]
            return ToolResult(source=query,raw=json.dumps(data),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install python-arango",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class RDFLibTool(BaseTool):
    name = "rdflib"; category = ToolCategory.KNOWLEDGE_GRAPH
    capabilities = ["rdf", "sparql", "owl", "turtle", "triples"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from rdflib import Graph, Literal, Namespace
            from rdflib.namespace import RDF, FOAF
            g=Graph()
            if kw.get("file"):
                g.parse(kw["file"])
            results=list(g.query(query))
            return ToolResult(source=query,raw=json.dumps([str(r) for r in results]),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install rdflib",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class BlazegraphTool(BaseTool):
    name = "blazegraph"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["triplestore", "sparql", "RDF", "OLAP"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:8080/blazegraph/sparql",data={"query":query},headers={"Accept":"application/json"})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class GraphitiTool(BaseTool):
    name = "graphiti"; category = ToolCategory.KNOWLEDGE_GRAPH
    capabilities = ["temporal_graph", "episodic", "entity_resolution", "cypher"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post("http://localhost:8096/search",json={"query":query})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class NetworkXTool(BaseTool):
    name = "networkx"; category = ToolCategory.KNOWLEDGE_GRAPH
    capabilities = ["graph_analysis", "algorithms", "centrality", "community"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import networkx as nx
            G=nx.DiGraph()
            if kw.get("edges"):
                G.add_edges_from(kw["edges"])
            metrics={"nodes":G.number_of_nodes(),"edges":G.number_of_edges()}
            if G.number_of_nodes()>0 and G.number_of_nodes()<10000:
                metrics["centrality"]=nx.degree_centrality(G)
            return ToolResult(source=query,raw=json.dumps(metrics),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install networkx",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ApacheJenaTool(BaseTool):
    name = "jena"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["triplestore", "sparql", "RDF", "fuseki"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:3030/query",data={"query":query},headers={"Accept":"application/sparql-results+json"})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class WeaviateTool(BaseTool):
    name = "weaviate"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    mcp_server = "weaviate-mcp"; capabilities = ["vector_db", "semantic_search", "hybrid", "GraphQL"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                query_str = '{ Get { ' + kw.get('class','Article') + '(nearText: {concepts: ["' + query + '"]} limit: ' + str(kw.get('num',5)) + ') { title _additional { id } } } }'
                r=await c.post("http://localhost:8080/v1/graphql",json={"query":query_str})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class QdrantTool(BaseTool):
    name = "qdrant"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    mcp_server = "qdrant-mcp"; capabilities = ["vector_db", "similarity", "filtering", "clustering"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:6333/collections/search",json={"vector":[0.1]*128,"limit":kw.get("num",10)})
                return ToolResult(source=query,raw=r.text[:5000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class MilvusTool(BaseTool):
    name = "milvus"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["vector_db", "scalable", "GPU", "hybrid_search"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            from pymilvus import connections, Collection
            connections.connect("default",host=kw.get("host","localhost"),port="19530")
            col=Collection(kw.get("collection","default"))
            result=col.search([query],["vector_field"],limit=kw.get("num",10))
            return ToolResult(source=query,raw=json.dumps([r.entity.get("id") for r in result[0]]),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install pymilvus",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ChromaDBTool(BaseTool):
    name = "chroma"; category = ToolCategory.KNOWLEDGE_GRAPH
    mcp_server = "chroma-mcp"; capabilities = ["vector_db", "lightweight", "embeddings", "local"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import chromadb
            client=chromadb.PersistentClient(path=kw.get("path","./chroma_db"))
            col=client.get_or_create_collection(kw.get("collection","default"))
            results=col.query(query_texts=[query],n_results=kw.get("num",10))
            return ToolResult(source=query,raw=json.dumps(results),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install chromadb",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class LanceDBTool(BaseTool):
    name = "lancedb"; category = ToolCategory.KNOWLEDGE_GRAPH
    capabilities = ["vector_db", "serverless", "multi_modal", " Lance format"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import lancedb
            db=lancedb.connect(kw.get("path","./lancedb"))
            table=db.open_table(kw.get("table","default"))
            results=table.search(query).limit(kw.get("num",10)).to_list()
            return ToolResult(source=query,raw=json.dumps(results),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install lancedb",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class FAISSTool(BaseTool):
    name = "faiss"; category = ToolCategory.KNOWLEDGE_GRAPH
    capabilities = ["similarity_search", "vector_db", "gpu", "efficient"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import faiss, numpy as np
            dim=kw.get("dim",128)
            index=faiss.IndexFlatL2(dim)
            if kw.get("vectors"):
                index.add(np.array(kw["vectors"],dtype=np.float32))
            return ToolResult(source=query,raw=json.dumps({"index_size":index.ntotal,"dim":dim}),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install faiss-cpu",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class PgvectorTool(BaseTool):
    name = "pgvector"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["vector_db", "postgres", "sql", "IVFFlat", "HNSW"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import asyncpg
            conn=await asyncpg.connect(kw.get("dsn","postgresql://localhost:5432/vectordb"))
            results=await conn.fetch(f"SELECT * FROM {kw.get('table','embeddings')} ORDER BY embedding <=> $1 LIMIT {kw.get('num',10)}",query)
            await conn.close()
            return ToolResult(source=query,raw=json.dumps([dict(r) for r in results]),tool=self.name,duration_ms=self._timing(s))
        except ImportError: return ToolResult(source=query,status="error",error="pip install asyncpg pgvector",tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class VespaTool(BaseTool):
    name = "vespa"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["search_engine", "vector", "text", "hybrid", "real_time"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:8080/search",json={"yql":f'select * from {kw.get("schema","doc")} where userQuery()"{query}"'})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class OpenSearchTool(BaseTool):
    name = "opensearch"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    capabilities = ["search_engine", "analytics", "knn", "full_text"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:9200/_search",json={"query":{"multi_match":{"query":query,"fields":["*"]}}})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

class ElasticsearchTool(BaseTool):
    name = "elasticsearch"; category = ToolCategory.KNOWLEDGE_GRAPH; requires_docker = True
    mcp_server = "elasticsearch-mcp"; capabilities = ["search_engine", "full_text", "analytics", "ml"]
    async def search(self, query, **kw):
        s=time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post("http://localhost:9200/_search",json={"query":{"match":{"_all":query}},"size":kw.get("num",10)})
                return ToolResult(source=query,raw=r.text[:10000],tool=self.name,duration_ms=self._timing(s))
        except Exception as e: return ToolResult(source=query,status="error",error=str(e),tool=self.name,duration_ms=self._timing(s))

KG_REGISTRY = {
    "neo4j": Neo4jTool, "memgraph": MemgraphTool, "falkordb": FalkorDBTool,
    "typedb": TypeDBTool, "arangodb": ArangoDBTool, "rdflib": RDFLibTool,
    "blazegraph": BlazegraphTool, "graphiti": GraphitiTool, "networkx": NetworkXTool,
    "jena": ApacheJenaTool, "weaviate": WeaviateTool, "qdrant": QdrantTool,
    "milvus": MilvusTool, "chroma": ChromaDBTool, "lancedb": LanceDBTool,
    "faiss": FAISSTool, "pgvector": PgvectorTool, "vespa": VespaTool,
    "opensearch": OpenSearchTool, "elasticsearch": ElasticsearchTool,
}
