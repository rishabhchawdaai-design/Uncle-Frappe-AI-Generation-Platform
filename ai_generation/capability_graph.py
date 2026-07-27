"""
Capability Graph — graph-based capability pathfinding and fallback chain generation.

Based on ACOS Research: Capability Graph Specification
Provides graph operations for finding execution paths, fallback chains,
cost estimation, and path validation across the provider/runtime/infrastructure graph.

Graph structure:
- Nodes: Providers, Runtimes, Hardware, Models, Capabilities
- Edges: Supports, Requires, DependsOn, FallbackTo, Cost
"""
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    PROVIDER = "provider"
    RUNTIME = "runtime"
    HARDWARE = "hardware"
    MODEL = "model"
    CAPABILITY = "capability"


class EdgeType(str, Enum):
    SUPPORTS = "supports"
    REQUIRES = "requires"
    DEPENDS_ON = "depends_on"
    FALLBACK_TO = "fallback_to"
    COST = "cost"


@dataclass
class GraphNode:
    """A node in the capability graph."""
    node_id: str = ""
    node_type: NodeType = NodeType.CAPABILITY
    name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "attributes": self.attributes,
        }


@dataclass
class GraphEdge:
    """An edge in the capability graph."""
    source_id: str = ""
    target_id: str = ""
    edge_type: EdgeType = EdgeType.SUPPORTS
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
        }


@dataclass
class ExecutionPath:
    """A found execution path through the graph."""
    path_id: str = ""
    nodes: List[str] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    total_cost: float = 0.0
    estimated_latency_ms: float = 0.0
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_id": self.path_id,
            "nodes": self.nodes,
            "edges": self.edges,
            "total_cost": round(self.total_cost, 6),
            "estimated_latency_ms": round(self.estimated_latency_ms, 2),
            "confidence": round(self.confidence, 3),
            "path_length": len(self.nodes),
        }


class CapabilityGraph:
    """
    Graph-based capability registry for pathfinding and fallback chain generation.

    Nodes represent providers, runtimes, hardware, models, and capabilities.
    Edges represent relationships (supports, requires, fallback_to, cost).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._reverse_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._update_history: List[Dict[str, Any]] = []
        self._init_default_graph()

    def _init_default_graph(self):
        """Initialize the default capability graph with known providers."""
        providers = [
            ("pollinations", "Pollinations", NodeType.PROVIDER, {"tier": "free", "type": "image"}),
            ("craiyon", "Craiyon", NodeType.PROVIDER, {"tier": "free", "type": "image"}),
            ("huggingface", "HuggingFace", NodeType.PROVIDER, {"tier": "free", "type": "image"}),
            ("siliconflow", "SiliconFlow", NodeType.PROVIDER, {"tier": "free", "type": "image"}),
            ("together", "Together AI", NodeType.PROVIDER, {"tier": "free", "type": "image"}),
            ("stability", "Stability AI", NodeType.PROVIDER, {"tier": "paid", "type": "image"}),
            ("fal", "Fal.ai", NodeType.PROVIDER, {"tier": "paid", "type": "image"}),
            ("replicate", "Replicate", NodeType.PROVIDER, {"tier": "paid", "type": "image"}),
            ("piper", "Piper TTS", NodeType.PROVIDER, {"tier": "free", "type": "audio"}),
            ("kokoro", "Kokoro", NodeType.PROVIDER, {"tier": "free", "type": "audio"}),
            ("openai_tts", "OpenAI TTS", NodeType.PROVIDER, {"tier": "paid", "type": "audio"}),
            ("whisper", "Whisper", NodeType.PROVIDER, {"tier": "free", "type": "audio"}),
        ]
        for pid, name, ntype, attrs in providers:
            self.add_node(pid, ntype, name, attrs)

        capabilities = [
            ("text_to_image", "Text-to-Image", NodeType.CAPABILITY),
            ("text_to_video", "Text-to-Video", NodeType.CAPABILITY),
            ("text_to_speech", "Text-to-Speech", NodeType.CAPABILITY),
            ("speech_to_text", "Speech-to-Text", NodeType.CAPABILITY),
            ("image_editing", "Image Editing", NodeType.CAPABILITY),
            ("text_generation", "Text Generation", NodeType.CAPABILITY),
        ]
        for cid, name, ntype in capabilities:
            self.add_node(cid, ntype, name)

        # Connect providers to capabilities
        self.add_edge("pollinations", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("craiyon", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("huggingface", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("siliconflow", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("together", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("stability", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("fal", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("replicate", "text_to_image", EdgeType.SUPPORTS)
        self.add_edge("replicate", "text_to_video", EdgeType.SUPPORTS)
        self.add_edge("fal", "text_to_video", EdgeType.SUPPORTS)
        self.add_edge("piper", "text_to_speech", EdgeType.SUPPORTS)
        self.add_edge("kokoro", "text_to_speech", EdgeType.SUPPORTS)
        self.add_edge("openai_tts", "text_to_speech", EdgeType.SUPPORTS)
        self.add_edge("whisper", "speech_to_text", EdgeType.SUPPORTS)

        # Fallback chains (prefer free, then paid)
        for cap in ["text_to_image"]:
            free = ["pollinations", "craiyon", "huggingface", "siliconflow", "together"]
            paid = ["stability", "fal", "replicate"]
            for i in range(len(free) - 1):
                self.add_edge(free[i], free[i + 1], EdgeType.FALLBACK_TO, weight=0.9)
            if free and paid:
                self.add_edge(free[-1], paid[0], EdgeType.FALLBACK_TO, weight=0.7)
            for i in range(len(paid) - 1):
                self.add_edge(paid[i], paid[i + 1], EdgeType.FALLBACK_TO, weight=0.8)

    def add_node(self, node_id: str, node_type: NodeType = NodeType.CAPABILITY,
                  name: str = "", attributes: Optional[Dict[str, Any]] = None):
        """Add a node to the graph."""
        self._nodes[node_id] = GraphNode(
            node_id=node_id, node_type=node_type,
            name=name or node_id, attributes=attributes or {},
        )

    def add_edge(self, source_id: str, target_id: str,
                  edge_type: EdgeType = EdgeType.SUPPORTS,
                  weight: float = 1.0,
                  attributes: Optional[Dict[str, Any]] = None):
        """Add an edge to the graph."""
        edge = GraphEdge(
            source_id=source_id, target_id=target_id,
            edge_type=edge_type, weight=weight,
            attributes=attributes or {},
        )
        self._edges[source_id].append(edge)
        self._reverse_edges[target_id].append(edge)

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID."""
        node = self._nodes.get(node_id)
        return node.to_dict() if node else None

    def get_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Dict[str, Any]]:
        """Get neighboring nodes."""
        edges = self._edges.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return [self._nodes[e.target_id].to_dict() for e in edges if e.target_id in self._nodes]

    def find_capability_path(self, capability: str,
                               preferred_provider: Optional[str] = None,
                               max_cost: float = float('inf'),
                               max_latency_ms: float = float('inf')) -> List[ExecutionPath]:
        """Find execution paths from providers to a capability."""
        paths = []
        providers = []
        for node_id, node in self._nodes.items():
            if node.node_type == NodeType.PROVIDER:
                for edge in self._edges.get(node_id, []):
                    if edge.target_id == capability and edge.edge_type == EdgeType.SUPPORTS:
                        providers.append(node_id)

        if preferred_provider and preferred_provider in providers:
            providers = [preferred_provider] + [p for p in providers if p != preferred_provider]

        for i, provider in enumerate(providers):
            path = ExecutionPath(
                path_id=f"path-{i}",
                nodes=[provider, capability],
                confidence=1.0 - (i * 0.05),
            )
            paths.append(path)

        return paths

    def find_fallback_chain(self, capability: str,
                             failed_provider: Optional[str] = None,
                             max_fallbacks: int = 5) -> List[Dict[str, Any]]:
        """Find fallback chain for a capability, optionally excluding a failed provider."""
        chain = []
        visited = set()

        # Find providers that support this capability
        providers = []
        for node_id in self._nodes:
            for edge in self._edges.get(node_id, []):
                if edge.target_id == capability and edge.edge_type == EdgeType.SUPPORTS:
                    if node_id != failed_provider:
                        providers.append((node_id, edge.weight))

        # Sort by weight (prefer higher weight = more reliable)
        providers.sort(key=lambda x: -x[1])

        for provider_id, weight in providers[:max_fallbacks]:
            if provider_id not in visited:
                visited.add(provider_id)
                chain.append({
                    "provider": provider_id,
                    "weight": weight,
                    "node": self._nodes[provider_id].to_dict() if provider_id in self._nodes else {},
                })

        return chain

    def estimate_execution_cost(self, provider_id: str,
                                 capability: str) -> Dict[str, Any]:
        """Estimate execution cost for a provider-capability pair."""
        node = self._nodes.get(provider_id)
        if not node:
            return {"error": f"Provider not found: {provider_id}"}

        attrs = node.attributes
        tier = attrs.get("tier", "unknown")

        cost_map = {"free": 0.0, "community": 0.0, "paid": 0.01}
        return {
            "provider": provider_id,
            "capability": capability,
            "estimated_cost_usd": cost_map.get(tier, 0.005),
            "tier": tier,
            "node": node.to_dict(),
        }

    def validate_path(self, path: ExecutionPath) -> Dict[str, Any]:
        """Validate that a path is valid in the graph."""
        issues = []
        for i, node_id in enumerate(path.nodes):
            if node_id not in self._nodes:
                issues.append(f"Node not found: {node_id}")

        for i in range(len(path.nodes) - 1):
            src, tgt = path.nodes[i], path.nodes[i + 1]
            found = False
            for edge in self._edges.get(src, []):
                if edge.target_id == tgt:
                    found = True
                    break
            if not found:
                issues.append(f"No edge from {src} to {tgt}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "path_length": len(path.nodes),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_types = defaultdict(int)
        edge_types = defaultdict(int)
        for node in self._nodes.values():
            node_types[node.node_type.value] += 1
        for edges in self._edges.values():
            for edge in edges:
                edge_types[edge.edge_type.value] += 1

        return {
            "node_count": len(self._nodes),
            "edge_count": sum(len(e) for e in self._edges.values()),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
        }

    # ── Dynamic Graph Updates (CGR-08) ──

    def dynamic_add_node(self, node_id: str, node_type: NodeType = NodeType.CAPABILITY,
                          name: str = "", attributes: Dict[str, Any] = None) -> Dict[str, Any]:
        if node_id in self._nodes:
            return {"success": False, "error": "Node already exists: " + node_id}
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            name=name or node_id,
            attributes=attributes or {},
        )
        self._nodes[node_id] = node
        self._edges[node_id] = []
        self._update_history.append({
            "action": "add_node", "node_id": node_id,
            "node_type": node_type.value, "timestamp": __import__("time").time(),
        })
        return {"success": True, "node": node.to_dict()}

    def dynamic_add_edge(self, source_id: str, target_id: str,
                          edge_type: EdgeType = EdgeType.SUPPORTS,
                          weight: float = 1.0,
                          attributes: Dict[str, Any] = None) -> Dict[str, Any]:
        if source_id not in self._nodes:
            return {"success": False, "error": "Source not found: " + source_id}
        if target_id not in self._nodes:
            return {"success": False, "error": "Target not found: " + target_id}
        edge = GraphEdge(
            source_id=source_id, target_id=target_id,
            edge_type=edge_type, weight=weight,
            attributes=attributes or {},
        )
        self._edges[source_id].append(edge)
        self._update_history.append({
            "action": "add_edge", "source_id": source_id,
            "target_id": target_id, "edge_type": edge_type.value,
            "timestamp": __import__("time").time(),
        })
        return {"success": True, "edge": edge.to_dict()}

    def dynamic_update_node(self, node_id: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        if node_id not in self._nodes:
            return {"success": False, "error": "Node not found: " + node_id}
        node = self._nodes[node_id]
        old_attrs = dict(node.attributes)
        node.attributes.update(attributes)
        self._update_history.append({
            "action": "update_node", "node_id": node_id,
            "fields": list(attributes.keys()),
            "timestamp": __import__("time").time(),
        })
        return {"success": True, "old": old_attrs, "new": dict(node.attributes)}

    def dynamic_remove_node(self, node_id: str) -> Dict[str, Any]:
        if node_id not in self._nodes:
            return {"success": False, "error": "Node not found: " + node_id}
        node_data = self._nodes[node_id].to_dict()
        del self._nodes[node_id]
        self._edges.pop(node_id, None)
        for src in self._edges:
            self._edges[src] = [e for e in self._edges[src] if e.target_id != node_id]
        self._update_history.append({
            "action": "remove_node", "node_id": node_id,
            "timestamp": __import__("time").time(),
        })
        return {"success": True, "removed": node_data}

    def dynamic_remove_edge(self, source_id: str, target_id: str,
                             edge_type: Optional[EdgeType] = None) -> Dict[str, Any]:
        if source_id not in self._edges:
            return {"success": False, "error": "No edges from: " + source_id}
        before = len(self._edges[source_id])
        if edge_type:
            self._edges[source_id] = [
                e for e in self._edges[source_id]
                if not (e.target_id == target_id and e.edge_type == edge_type)
            ]
        else:
            self._edges[source_id] = [
                e for e in self._edges[source_id] if e.target_id != target_id
            ]
        removed = before - len(self._edges[source_id])
        self._update_history.append({
            "action": "remove_edge", "source_id": source_id,
            "target_id": target_id, "removed": removed,
            "timestamp": __import__("time").time(),
        })
        return {"success": removed > 0, "removed_count": removed}

    def batch_update_benchmark(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        updated = 0
        errors = []
        for u in updates:
            node_id = u.get("node_id", "")
            if node_id not in self._nodes:
                errors.append("Node not found: " + node_id)
                continue
            attrs = {}
            if "benchmark_score" in u:
                attrs["benchmark_score"] = u["benchmark_score"]
            if "latency_ms" in u:
                attrs["latency_ms"] = u["latency_ms"]
            if "quality_score" in u:
                attrs["quality_score"] = u["quality_score"]
            if attrs:
                self._nodes[node_id].attributes.update(attrs)
                updated += 1
        self._update_history.append({
            "action": "batch_benchmark", "updated": updated,
            "errors": len(errors), "timestamp": __import__("time").time(),
        })
        return {"success": True, "updated": updated, "errors": errors}

    def batch_update_health(self, updates: Dict[str, float]) -> Dict[str, Any]:
        updated = 0
        errors = []
        for node_id, health in updates.items():
            if node_id not in self._nodes:
                errors.append("Node not found: " + node_id)
                continue
            self._nodes[node_id].attributes["health_score"] = max(0.0, min(1.0, health))
            updated += 1
        self._update_history.append({
            "action": "batch_health", "updated": updated,
            "errors": len(errors), "timestamp": __import__("time").time(),
        })
        return {"success": True, "updated": updated, "errors": errors}

    def get_update_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._update_history[-limit:]))

    def dynamic_get_stats(self) -> Dict[str, Any]:
        base = self.get_stats()
        base["update_count"] = len(self._update_history)
        return base
