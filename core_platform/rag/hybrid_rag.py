"""
Phase 13: Production Hybrid RAG
Chunking, embeddings, hybrid retrieval, reranking, citations, confidence scoring.
"""
import asyncio, json, logging, hashlib, re, os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    text: str
    document_id: str
    chunk_id: str = ""
    title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    tokens: int = 0
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.sha256(self.text.encode()).hexdigest()[:16]
        if self.text:
            self.tokens = len(self.text.split())

@dataclass
class RetrievedDocument:
    chunk: Chunk
    score: float = 0.0
    method: str = ""  # "vector", "keyword", "hybrid", "kg"
    source: str = ""
    relevance: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "score": round(self.score, 4), "method": self.method,
            "source": self.source, "confidence": round(self.confidence, 4),
            "text": self.chunk.text[:200],
            "document_id": self.chunk.document_id, "chunk_id": self.chunk.chunk_id,
        }


class Chunker:
    """Multi-strategy chunker for documents."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._semantic_splitter = self._compile_splitters()

    def _compile_splitters(self):
        """Compile regex patterns for semantic splitting."""
        return [
            re.compile(r"\n\n+"),      # Paragraphs
            re.compile(r"\n"),         # Lines
            re.compile(r"[.!?]\s+"),   # Sentences
        ]

    def chunk_text(self, text: str, document_id: str, title: str = "", strategy: str = "semantic") -> List[Chunk]:
        if strategy == "semantic":
            return self._semantic_chunk(text, document_id, title)
        elif strategy == "fixed":
            return self._fixed_chunk(text, document_id, title)
        elif strategy == "hierarchical":
            return self._hierarchical_chunk(text, document_id, title)
        return self._semantic_chunk(text, document_id, title)

    def _semantic_chunk(self, text: str, doc_id: str, title: str) -> List[Chunk]:
        """Chunk by semantic boundaries (paragraphs/titles)."""
        paragraphs = self._semantic_splitter[0].split(text)
        chunks = []
        current_text = ""
        current_id = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_text.split()) + len(para.split()) > self._chunk_size and current_text:
                chunk = Chunk(
                    text=current_text.strip(), document_id=doc_id,
                    chunk_id=f"{doc_id}_{current_id}", title=title,
                    metadata={"strategy": "semantic", "chunk_index": current_id},
                )
                chunks.append(chunk)
                current_id += 1
                # Keep overlap
                words = current_text.split()
                current_text = " ".join(words[-self._chunk_overlap:]) + " " + para
            else:
                current_text += "\n" + para

        if current_text.strip():
            chunk = Chunk(text=current_text.strip(), document_id=doc_id,
                chunk_id=f"{doc_id}_{current_id}", title=title,
                metadata={"strategy": "semantic", "chunk_index": current_id})
            chunks.append(chunk)

        return chunks

    def _fixed_chunk(self, text: str, doc_id: str, title: str) -> List[Chunk]:
        """Sliding window chunking."""
        words = text.split()
        chunks = []
        stride = self._chunk_size - self._chunk_overlap
        for i in range(0, len(words), stride):
            chunk_words = words[i:i + self._chunk_size]
            if len(chunk_words) < 10:
                continue
            chunk = Chunk(
                text=" ".join(chunk_words), document_id=doc_id,
                chunk_id=f"{doc_id}_{i//stride}", title=title,
                metadata={"strategy": "fixed", "chunk_index": i // stride},
            )
            chunks.append(chunk)
        return chunks

    def _hierarchical_chunk(self, text: str, doc_id: str, title: str) -> List[Chunk]:
        """Create overlapping chunks at multiple granularities."""
        chunks = self._fixed_chunk(text, doc_id, title)
        # Add summary-level chunks (every 3 fixed chunks combined)
        summaries = []
        for i in range(0, len(chunks), 3):
            combined = "\n\n".join(c.text for c in chunks[i:i+3])
            chunk = Chunk(text=combined, document_id=doc_id,
                chunk_id=f"{doc_id}_hier_{i}", title=title,
                metadata={"strategy": "hierarchical", "hierarchical_level": "section"})
            summaries.append(chunk)
        return chunks + summaries


class Embedder:
    """Embedding generation with multiple backend support."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self._model_name = model_name
        self._dimension = dimension
        self._model = None
        self._loaded = False

    async def _ensure_model(self):
        if not self._loaded:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                self._loaded = True
            except ImportError:
                logger.warning("sentence-transformers not available; using simple embeddings")
                self._loaded = True

    async def embed(self, text: str) -> List[float]:
        await self._ensure_model()
        if self._model:
            emb = self._model.encode(text, normalize_embeddings=True)
            return emb.tolist()
        # Fallback: simple TF-IDF-like vector
        words = set(text.lower().split())
        vec = np.zeros(self._dimension)
        for w in list(words)[:self._dimension]:
            vec[hash(w) % self._dimension] += 1
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        return vec.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        await self._ensure_model()
        if self._model:
            embs = self._model.encode(texts, normalize_embeddings=True)
            return [e.tolist() for e in embs]
        return [await self.embed(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dimension


class Retriever:
    """Hybrid retrieval combining vector, keyword, and metadata search."""

    def __init__(self, embedder: Embedder):
        self._embedder = embedder
        self._vector_store = None
        self._chunks: List[Chunk] = []
        self._keyword_index: Dict[str, List[int]] = {}

    def register_vector_store(self, store):
        self._vector_store = store

    def index_chunks(self, chunks: List[Chunk]):
        """Build in-memory keyword index for hybrid search."""
        self._chunks = chunks
        self._keyword_index.clear()
        for i, chunk in enumerate(chunks):
            words = set(re.findall(r'\w+', chunk.text.lower()))
            for word in words:
                if word not in self._keyword_index:
                    self._keyword_index[word] = []
                self._keyword_index[word].append(i)

    async def hybrid_retrieve(self, query: str, k: int = 10, alpha: float = 0.5,
                              vector_store_results: Optional[List[Tuple[Chunk, float]]] = None) -> List[RetrievedDocument]:
        """Hybrid search combining vector and keyword scores."""
        # 1. Vector search results
        vec_results = vector_store_results or []
        vec_scores = {id(chunk): score for chunk, score in vec_results}

        # 2. Keyword search (BM25-style scoring)
        query_terms = set(re.findall(r'\w+', query.lower()))
        keyword_scores: Dict[int, float] = {}
        for term in query_terms:
            for idx in self._keyword_index.get(term, []):
                keyword_scores[idx] = keyword_scores.get(idx, 0) + 1.0

        # Normalize keyword scores
        max_kw = max(keyword_scores.values()) if keyword_scores else 1
        for k in keyword_scores:
            keyword_scores[k] /= max_kw

        # 3. Hybrid combination
        combined: Dict[int, RetrievedDocument] = {}
        all_indices = set(vec_scores.keys()) | set(self._keyword_index.get(t, []) for t in query_terms)

        for chunk in self._chunks:
            idx = id(chunk)
            vec_score = vec_scores.get(idx, 0.0)
            kw_score = keyword_scores.get(self._chunks.index(chunk), 0.0)
            hybrid = alpha * vec_score + (1 - alpha) * kw_score
            if hybrid > 0:
                combined[idx] = RetrievedDocument(
                    chunk=chunk, score=round(hybrid, 4),
                    method="hybrid" if vec_score and kw_score else "vector" if vec_score else "keyword",
                    confidence=round(hybrid, 4),
                )

        # Also include pure vector results missing from chunks index
        for chunk, score in vec_results:
            idx = id(chunk)
            if idx not in combined:
                combined[idx] = RetrievedDocument(chunk=chunk, score=score, method="vector", confidence=score)

        return sorted(combined.values(), key=lambda x: x.score, reverse=True)[:k]

    async def keyword_search(self, query: str, k: int = 10) -> List[RetrievedDocument]:
        query_terms = set(re.findall(r'\w+', query.lower()))
        scores = {}
        for term in query_terms:
            for idx in self._keyword_index.get(term, []):
                scores[idx] = scores.get(idx, 0) + 1.0
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [RetrievedDocument(chunk=self._chunks[idx], score=score / max(scores.values(), default=1), method="keyword") for idx, score in top]


class Reranker:
    """Cross-encoder reranking with confidence scoring."""

    def __init__(self):
        self._model = None
        self._loaded = False

    async def _ensure_model(self):
        if not self._loaded:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                self._loaded = True
            except ImportError:
                self._loaded = True

    async def rerank(self, query: str, documents: List[RetrievedDocument], top_k: int = 10) -> List[RetrievedDocument]:
        if not documents:
            return documents
        await self._ensure_model()
        pairs = [(query, doc.chunk.text[:512]) for doc in documents]

        if self._model:
            scores = self._model.predict(pairs).tolist()
            if isinstance(scores, (int, float)):
                scores = [scores]
        else:
            # Fallback: use retrieval scores directly
            scores = [doc.score for doc in documents]

        for doc, score in zip(documents, scores):
            doc.relevance = round(float(score), 4)
            doc.confidence = round(min(1.0, max(0.0, (float(score) + 1) / 2)), 4)

        reranked = sorted(documents, key=lambda x: x.relevance, reverse=True)
        return reranked[:top_k]


class GenerationEngine:
    """Citation-aware generation with source attribution."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._api_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")

    async def generate(self, query: str, documents: List[RetrievedDocument], max_tokens: int = 2000) -> Dict[str, Any]:
        if not self._api_key:
            # Generate attribution-only summary
            return self._generate_no_llm(query, documents)

        try:
            import httpx
            context = "\n\n".join([
                f"[Doc {i+1}] (Source: {d.source}, Confidence: {d.confidence:.2f})\n{d.chunk.text[:1000]}"
                for i, d in enumerate(documents[:10])
            ])

            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post("https://api.openai.com/v1/chat/completions",
                    json={
                        "model": self.config.get("model", "gpt-4o-mini"),
                        "messages": [
                            {"role": "system", "content": "Answer using ONLY the provided context. Cite sources as [Doc N]."},
                            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.1,
                    },
                    headers={"Authorization": f"Bearer {self._api_key}"})

                data = r.json()
                answer = data["choices"][0]["message"]["content"]

        except Exception as e:
            answer = self._generate_no_llm(query, documents).get("answer", "")

        citations = []
        for i, doc in enumerate(documents[:5]):
            citations.append({
                "citation_id": i + 1, "source": doc.source,
                "confidence": doc.confidence, "score": doc.score,
                "text": doc.chunk.text[:150],
            })

        return {
            "answer": answer,
            "query": query,
            "citations": citations,
            "total_context_docs": len(documents),
            "confidence": round(sum(d.confidence for d in documents) / max(len(documents), 1), 4),
        }

    def _generate_no_llm(self, query: str, documents: List[RetrievedDocument]) -> Dict[str, Any]:
        context = "\n".join([d.chunk.text[:300] for d in documents[:5]])
        return {
            "answer": f"Based on {len(documents)} retrieved documents:\n{context[:2000]}",
            "query": query,
            "citations": [{"doc_id": i, "source": d.source, "confidence": d.confidence} for i, d in enumerate(documents[:5])],
            "total_context_docs": len(documents),
            "confidence": round(sum(d.confidence for d in documents) / max(len(documents), 1), 4),
        }


class HybridRAG:
    """Complete Hybrid RAG pipeline."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._chunker = Chunker(
            chunk_size=self.config.get("chunk_size", 512),
            chunk_overlap=self.config.get("chunk_overlap", 64),
        )
        self._embedder = Embedder(
            model_name=self.config.get("embedding_model", "all-MiniLM-L6-v2"),
            dimension=self.config.get("embedding_dim", 384),
        )
        self._retriever = Retriever(self._embedder)
        self._reranker = Reranker()
        self._generator = GenerationEngine(self.config)
        self._vector_store = None
        self._chunks: List[Chunk] = []

    def register_vector_store(self, store):
        self._vector_store = store
        self._retriever.register_vector_store(store)

    async def ingest(self, text: str, document_id: str, title: str = "",
                     strategy: str = "semantic", metadata: Optional[Dict] = None) -> List[Chunk]:
        chunks = self._chunker.chunk_text(text, document_id, title, strategy=strategy)

        # Add metadata
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)

        # Generate embeddings
        texts = [c.text for c in chunks]
        embeddings = await self._embedder.embed_batch(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        self._chunks.extend(chunks)
        self._retriever.index_chunks(self._chunks)

        # Index in vector store
        if self._vector_store:
            await self._vector_store.index_chunks(chunks)

        logger.info(f"Ingested {len(chunks)} chunks from {document_id}")
        return chunks

    async def search(self, query: str, k: int = 10, rerank: bool = True,
                     include_citations: bool = True) -> Dict[str, Any]:
        # 1. Vector search
        vector_docs = []
        if self._vector_store:
            vector_results = await self._vector_store.search(query, k=k * 2)
            vector_docs = [(chunk, score) for chunk, score in vector_results]

        # 2. Hybrid retrieval
        docs = await self._retriever.hybrid_retrieve(query, k=k * 2, vector_store_results=vector_docs)

        # 3. Reranking
        if rerank and docs:
            docs = await self._reranker.rerank(query, docs, top_k=k)

        # 4. Generation
        result = await self._generator.generate(query, docs)

        return {
            **result,
            "retrieved_documents": [d.to_dict() for d in docs],
            "total_retrieved": len(docs),
            "total_chunks": len(self._chunks),
        }
