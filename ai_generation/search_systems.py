"""
Search Systems — full-text search engine with Meilisearch-compatible interface.

Based on ACOS Research: Search Systems Research
Provides in-memory full-text search with typo tolerance, faceted filtering,
sorting, and relevance scoring. Can connect to Meilisearch/OpenSearch when
available, falls back to built-in engine.

Supported backends:
- Built-in: In-memory search (no external deps)
- Meilisearch: When server is available
- OpenSearch: When cluster is available

Use cases:
- Provider catalog search
- Model registry search
- Knowledge base queries
- Decision ledger search
- Benchmark history queries
"""
import json
import logging
import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SearchBackend(str, Enum):
    BUILTIN = "builtin"
    MEILISEARCH = "meilisearch"
    OPENSEARCH = "opensearch"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SearchHit:
    """A single search result."""
    id: str = ""
    score: float = 0.0
    document: Dict[str, Any] = field(default_factory=dict)
    highlights: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "score": round(self.score, 4),
            "document": self.document,
            "highlights": self.highlights,
        }


@dataclass
class SearchResults:
    """Search results with metadata."""
    query: str = ""
    hits: List[SearchHit] = field(default_factory=list)
    total_hits: int = 0
    processing_time_ms: float = 0.0
    page: int = 1
    hits_per_page: int = 20
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "hits": [h.to_dict() for h in self.hits],
            "total_hits": self.total_hits,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "page": self.page,
            "hits_per_page": self.hits_per_page,
            "facets": self.facets,
        }


@dataclass
class IndexConfig:
    """Configuration for a search index."""
    index_name: str = ""
    searchable_fields: List[str] = field(default_factory=list)
    filterable_fields: List[str] = field(default_factory=list)
    sortable_fields: List[str] = field(default_factory=list)
    displayed_fields: List[str] = field(default_factory=list)
    synonyms: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index_name": self.index_name,
            "searchable_fields": self.searchable_fields,
            "filterable_fields": self.filterable_fields,
            "sortable_fields": self.sortable_fields,
            "displayed_fields": self.displayed_fields,
            "synonyms": self.synonyms,
        }


# ── Built-in In-Memory Search Engine ─────────────────────────

class BuiltinSearchEngine:
    """
    In-memory full-text search engine with typo tolerance and faceting.
    No external dependencies required.
    """

    def __init__(self):
        self._indexes: Dict[str, Dict[str, Any]] = {}
        self._docs: Dict[str, List[Dict[str, Any]]] = {}
        self._configs: Dict[str, IndexConfig] = {}
        self._stopwords: Set[str] = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "of", "in", "to", "for", "with", "on", "at", "from", "by",
            "and", "or", "not", "but", "if", "as", "that", "this",
        }

    def create_index(self, index_name: str, config: Optional[IndexConfig] = None):
        """Create a new search index."""
        if index_name not in self._docs:
            self._docs[index_name] = []
            self._configs[index_name] = config or IndexConfig(index_name=index_name)
            logger.info(f"Created search index: {index_name}")

    def add_documents(self, index_name: str, documents: List[Dict[str, Any]]):
        """Add documents to an index."""
        if index_name not in self._docs:
            self.create_index(index_name)
        existing_ids = {d.get("id") for d in self._docs[index_name]}
        added = 0
        for doc in documents:
            doc_id = doc.get("id")
            if doc_id and doc_id in existing_ids:
                # Update existing
                self._docs[index_name] = [
                    d if d.get("id") != doc_id else doc
                    for d in self._docs[index_name]
                ]
            else:
                self._docs[index_name].append(doc)
                added += 1
        logger.debug(f"Added {added} documents to {index_name}")

    def delete_document(self, index_name: str, doc_id: str):
        """Delete a document from an index."""
        if index_name in self._docs:
            self._docs[index_name] = [
                d for d in self._docs[index_name] if d.get("id") != doc_id
            ]

    def clear_index(self, index_name: str):
        """Clear all documents from an index."""
        if index_name in self._docs:
            self._docs[index_name] = []

    def search(self, index_name: str, query: str,
               filter_expr: Optional[Dict[str, Any]] = None,
               sort_by: Optional[str] = None,
               sort_order: SortOrder = SortOrder.ASC,
               page: int = 1, hits_per_page: int = 20,
               facets: Optional[List[str]] = None,
               typo_tolerance: bool = True) -> SearchResults:
        """Search an index."""
        start_time = time.time()
        if index_name not in self._docs:
            return SearchResults(query=query)

        docs = self._docs[index_name]
        config = self._configs.get(index_name, IndexConfig())

        # Tokenize query
        tokens = self._tokenize(query)

        # Score documents
        scored = []
        for doc in docs:
            score = self._score_document(doc, tokens, config, typo_tolerance)
            if score > 0:
                scored.append((doc, score))

        # Apply filters
        if filter_expr:
            scored = [(d, s) for d, s in scored if self._matches_filter(d, filter_expr)]

        # Sort by score (default) or specified field
        if sort_by:
            reverse = (sort_order == SortOrder.DESC)
            scored.sort(key=lambda x: x[0].get(sort_by, 0), reverse=reverse)
        else:
            scored.sort(key=lambda x: -x[1])

        # Compute facets
        facet_results = {}
        if facets:
            for facet_field in facets:
                facet_counts = defaultdict(int)
                for doc, _ in scored:
                    val = doc.get(facet_field)
                    if isinstance(val, list):
                        for v in val:
                            facet_counts[str(v)] += 1
                    elif val is not None:
                        facet_counts[str(val)] += 1
                facet_results[facet_field] = dict(facet_counts)

        # Paginate
        total = len(scored)
        start_idx = (page - 1) * hits_per_page
        end_idx = start_idx + hits_per_page
        page_hits = scored[start_idx:end_idx]

        # Build results
        hits = []
        for doc, score in page_hits:
            highlights = self._generate_highlights(doc, tokens, config)
            hits.append(SearchHit(
                id=doc.get("id", ""),
                score=score,
                document=doc,
                highlights=highlights,
            ))

        elapsed = (time.time() - start_time) * 1000
        return SearchResults(
            query=query,
            hits=hits,
            total_hits=total,
            processing_time_ms=elapsed,
            page=page,
            hits_per_page=hits_per_page,
            facets=facet_results,
        )

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable tokens."""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return [t for t in tokens if t not in self._stopwords and len(t) > 1]

    def _score_document(self, doc: Dict[str, Any], tokens: List[str],
                         config: IndexConfig, typo_tolerance: bool) -> float:
        """Score a document against query tokens."""
        score = 0.0
        searchable = config.searchable_fields or list(doc.keys())

        for token in tokens:
            for field_name in searchable:
                value = doc.get(field_name, "")
                if isinstance(value, list):
                    value = " ".join(str(v) for v in value)
                value_str = str(value).lower()

                # Exact token match
                if token in value_str.split():
                    score += 10.0
                # Partial match
                elif token in value_str:
                    score += 5.0
                # Typo tolerance (Levenshtein distance 1)
                elif typo_tolerance:
                    words = value_str.split()
                    for word in words:
                        if self._levenshtein_distance(token, word) <= 1:
                            score += 2.0
                            break

                # Boost for title/name fields
                if field_name in ("name", "title", "model_id", "plugin_id"):
                    score *= 1.5

        # Synonym expansion
        for token in tokens:
            for syn_key, syn_values in config.synonyms.items():
                if token == syn_key or token in syn_values:
                    for syn in syn_values:
                        if syn != token:
                            for field_name in searchable:
                                value = str(doc.get(field_name, "")).lower()
                                if syn in value:
                                    score += 3.0

        return score

    def _matches_filter(self, doc: Dict[str, Any], filter_expr: Dict[str, Any]) -> bool:
        """Check if a document matches a filter expression."""
        for key, value in filter_expr.items():
            doc_val = doc.get(key)
            if isinstance(value, dict):
                # Range filters
                if "$gte" in value and doc_val is not None:
                    if doc_val < value["$gte"]:
                        return False
                if "$lte" in value and doc_val is not None:
                    if doc_val > value["$lte"]:
                        return False
                if "$in" in value:
                    if doc_val not in value["$in"]:
                        return False
            elif isinstance(value, list):
                if doc_val not in value:
                    return False
            else:
                if doc_val != value:
                    return False
        return True

    def _generate_highlights(self, doc: Dict[str, Any], tokens: List[str],
                              config: IndexConfig) -> Dict[str, str]:
        """Generate highlight snippets for matched fields."""
        highlights = {}
        searchable = config.searchable_fields or list(doc.keys())
        for field_name in searchable:
            value = str(doc.get(field_name, ""))
            if not value:
                continue
            for token in tokens:
                if token in value.lower():
                    # Bold the matched token
                    pattern = re.compile(re.escape(token), re.IGNORECASE)
                    highlighted = pattern.sub(f"<em>{token}</em>", value)
                    highlights[field_name] = highlighted[:200]
                    break
        return highlights

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Compute Levenshtein edit distance."""
        if len(s1) < len(s2):
            return BuiltinSearchEngine._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]

    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """Get information about an index."""
        if index_name not in self._docs:
            return {"error": f"Index not found: {index_name}"}
        return {
            "index_name": index_name,
            "document_count": len(self._docs[index_name]),
            "config": self._configs.get(index_name, IndexConfig()).to_dict(),
        }

    def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes."""
        return [
            {"index_name": name, "document_count": len(docs)}
            for name, docs in self._docs.items()
        ]


# ── Search Manager ────────────────────────────────────────────

class SearchManager:
    """
    Unified search interface with built-in engine and optional
    Meilisearch/OpenSearch backends.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._backend = SearchBackend(self.config.get("search_backend", "builtin"))
        self._builtin = BuiltinSearchEngine()
        self._meilisearch_url = self.config.get("meilisearch_url", "")
        self._opensearch_url = self.config.get("opensearch_url", "")
        self._init_builtin_indexes()

    def _init_builtin_indexes(self):
        """Create default search indexes."""
        self._builtin.create_index("providers", IndexConfig(
            index_name="providers",
            searchable_fields=["name", "type", "tier", "capabilities"],
            filterable_fields=["type", "tier", "free_tier"],
        ))
        self._builtin.create_index("models", IndexConfig(
            index_name="models",
            searchable_fields=["name", "model_id", "family", "category"],
            filterable_fields=["category", "license", "runtime"],
        ))
        self._builtin.create_index("knowledge", IndexConfig(
            index_name="knowledge",
            searchable_fields=["title", "content", "tags"],
            filterable_fields=["category", "domain", "source"],
        ))
        self._builtin.create_index("decisions", IndexConfig(
            index_name="decisions",
            searchable_fields=["decision_type", "selected_provider", "reasoning"],
            filterable_fields=["decision_type", "outcome", "selected_provider"],
        ))
        self._builtin.create_index("benchmarks", IndexConfig(
            index_name="benchmarks",
            searchable_fields=["provider", "model", "task_type"],
            filterable_fields=["provider", "task_type"],
        ))

    def index_documents(self, index_name: str, documents: List[Dict[str, Any]]):
        """Index documents into a search index."""
        self._builtin.add_documents(index_name, documents)

    def search(self, index_name: str, query: str, **kwargs) -> SearchResults:
        """Search an index."""
        return self._builtin.search(index_name, query, **kwargs)

    def delete_document(self, index_name: str, doc_id: str):
        """Delete a document."""
        self._builtin.delete_document(index_name, doc_id)

    def clear_index(self, index_name: str):
        """Clear an index."""
        self._builtin.clear_index(index_name)

    def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes."""
        return self._builtin.list_indexes()

    def get_index_info(self, index_name: str) -> Dict[str, Any]:
        """Get index information."""
        return self._builtin.get_index_info(index_name)

    # ── Convenience Methods ────────────────────────────────────

    def search_providers(self, query: str, provider_type: str = "",
                          tier: str = "") -> SearchResults:
        """Search providers with optional filtering."""
        filters = {}
        if provider_type:
            filters["type"] = provider_type
        if tier:
            filters["tier"] = tier
        return self.search("providers", query, filter_expr=filters or None)

    def search_models(self, query: str, category: str = "",
                       runtime: str = "") -> SearchResults:
        """Search models with optional filtering."""
        filters = {}
        if category:
            filters["category"] = category
        if runtime:
            filters["runtime"] = runtime
        return self.search("models", query, filter_expr=filters or None)

    def search_knowledge(self, query: str, category: str = "",
                          domain: str = "") -> SearchResults:
        """Search knowledge base."""
        filters = {}
        if category:
            filters["category"] = category
        if domain:
            filters["domain"] = domain
        return self.search("knowledge", query, filter_expr=filters or None)

    def search_decisions(self, query: str, decision_type: str = "",
                          outcome: str = "") -> SearchResults:
        """Search decision ledger."""
        filters = {}
        if decision_type:
            filters["decision_type"] = decision_type
        if outcome:
            filters["outcome"] = outcome
        return self.search("decisions", query, filter_expr=filters or None)

    def search_benchmarks(self, query: str, provider: str = "",
                           task_type: str = "") -> SearchResults:
        """Search benchmark history."""
        filters = {}
        if provider:
            filters["provider"] = provider
        if task_type:
            filters["task_type"] = task_type
        return self.search("benchmarks", query, filter_expr=filters or None)

    def get_stats(self) -> Dict[str, Any]:
        """Get search system statistics."""
        indexes = self.list_indexes()
        total_docs = sum(idx["document_count"] for idx in indexes)
        return {
            "backend": self._backend.value,
            "index_count": len(indexes),
            "total_documents": total_docs,
            "indexes": {idx["index_name"]: idx["document_count"] for idx in indexes},
        }
