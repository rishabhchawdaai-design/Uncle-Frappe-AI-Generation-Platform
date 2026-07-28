"""
Provider Knowledge Graph — continuously updated graph of providers, models,
capabilities, APIs, authentication, health, benchmarks, relationships, and dependencies.
"""
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class GraphNode:
    node_id: str = ""
    node_type: str = ""  # provider, model, capability, api, auth, benchmark
    name: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id, "node_type": self.node_type, "name": self.name,
            "properties": self.properties, "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class GraphEdge:
    source_id: str = ""
    target_id: str = ""
    edge_type: str = ""  # supports, requires, depends_on, benchmarks, uses_auth
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source_id, "target": self.target_id, "edge_type": self.edge_type, "properties": self.properties}


class KnowledgeGraph:
    """Provider knowledge graph for AIG-OS."""

    def __init__(self, data_dir: str = "data/knowledge"):
        self.data_dir = data_dir
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[str]] = {}
        os.makedirs(data_dir, exist_ok=True)
        self._load()

    def _load(self):
        path = os.path.join(self.data_dir, "knowledge_graph.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for nd in data.get("nodes", []):
                    n = GraphNode(**nd)
                    self._nodes[n.node_id] = n
                for ed in data.get("edges", []):
                    e = GraphEdge(**ed)
                    self._edges.append(e)
                    self._adjacency.setdefault(e.source_id, []).append(e.target_id)
            except Exception:
                pass

    def _save(self):
        path = os.path.join(self.data_dir, "knowledge_graph.json")
        data = {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add_node(self, node: GraphNode) -> GraphNode:
        existing = self._nodes.get(node.node_id)
        if existing:
            existing.properties.update(node.properties)
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return existing
        self._nodes[node.node_id] = node
        self._save()
        return node

    def add_edge(self, edge: GraphEdge):
        self._edges.append(edge)
        self._adjacency.setdefault(edge.source_id, []).append(edge.target_id)
        self._save()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[GraphNode]:
        neighbors = []
        for e in self._edges:
            if e.source_id == node_id:
                if edge_type is None or e.edge_type == edge_type:
                    n = self._nodes.get(e.target_id)
                    if n:
                        neighbors.append(n)
        return neighbors

    def find_nodes(self, node_type: Optional[str] = None, name_contains: str = "") -> List[GraphNode]:
        results = list(self._nodes.values())
        if node_type:
            results = [n for n in results if n.node_type == node_type]
        if name_contains:
            results = [n for n in results if name_contains.lower() in n.name.lower()]
        return results

    def query_providers_by_capability(self, capability: str) -> List[str]:
        provider_ids = set()
        for e in self._edges:
            if e.edge_type == "supports":
                target = self._nodes.get(e.target_id)
                if target and target.node_type == "capability" and capability in target.name.lower():
                    provider_ids.add(e.source_id)
        return list(provider_ids)

    def get_provider_models(self, provider_id: str) -> List[GraphNode]:
        return self.get_neighbors(provider_id, edge_type="offers_model")

    def get_stats(self) -> Dict[str, Any]:
        node_types = {}
        for n in self._nodes.values():
            node_types[n.node_type] = node_types.get(n.node_type, 0) + 1
        edge_types = {}
        for e in self._edges:
            edge_types[e.edge_type] = edge_types.get(e.edge_type, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_types": node_types,
            "edge_types": edge_types,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stats": self.get_stats(),
            "nodes": [n.to_dict() for n in list(self._nodes.values())[:50]],
            "edges": [e.to_dict() for e in self._edges[:50]],
        }
