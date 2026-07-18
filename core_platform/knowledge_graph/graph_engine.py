"""
Phase 15: Knowledge Graph with entity extraction, relationship mapping,
temporal links, geographical links, entity resolution, graph analytics.
"""
import asyncio, json, logging, hashlib, re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    id: str = ""
    name: str = ""
    entity_type: str = ""  # person, organization, restaurant, hotel, city, address, product, event, concept
    properties: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256(f"{self.entity_type}:{self.name}".encode()).hexdigest()[:12]

    def to_dict(self) -> Dict:
        return {"id": self.id, "name": self.name, "type": self.entity_type,
                "properties": self.properties, "confidence": self.confidence}

@dataclass
class Relationship:
    id: str = ""
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""  # located_in, serves, employs, part_of, owned_by, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    temporal: Optional[Dict] = None  # {"start": "...", "end": "..."}
    geographical: Optional[Dict] = None  # {"lat": ..., "lng": ..., "radius_m": ...}

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256(f"{self.source_id}:{self.relation_type}:{self.target_id}".encode()).hexdigest()[:12]


# ── Named Entity Extraction Patterns ──────────────────────────────
ENTITY_PATTERNS = {
    "restaurant": [
        r"(\w+(?:\s+\w+)?(?:\s+(?:Restaurant|Dhaba|Cafe|Kitchen|Food|Biryani|Thali|Grill)))",
    ],
    "hotel": [
        r"((?:Hotel|Resort|Inn|Lodge|Palace|Suites)\s+\w+)",
        r"(\w+\s+(?:Hotel|Resort|Inn|Lodge|Palace|Suites))",
    ],
    "organization": [
        r"(\w+(?:\s+\w+)?(?:\s+(?:Inc|Ltd|Corp|LLC|Pvt|Group|Company|Enterprises)))",
    ],
    "city": [
        r"(Raipur|Naya Raipur|Atal Nagar|Bhilai|Durg|Bilaspur|Korba|Rajnandgaon|Jagdalpur|Ambikapur|Champa|Raigarh|Dantewada|Surguja)",
    ],
    "person": [
        r"(?:Mr|Mrs|Dr|Prof|Shri|Smt|CM|PM)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",
    ],
}

# ── Relationship Patterns ─────────────────────────────────────────
RELATIONSHIP_PATTERNS = [
    (r"located in (?:\w+)", "located_in"),
    (r"based in (?:\w+)", "located_in"),
    (r"part of", "part_of"),
    (r"owned by", "owned_by"),
    (r"serves (?:\w+)", "serves"),
    (r"near (?:\w+)", "near"),
    (r"opened (?:in|at)", "founded_in"),
]


class EntityExtractor:
    """Extract entities from text using pattern matching + NLP."""

    def __init__(self):
        self._custom_terms: Dict[str, List[str]] = {
            "restaurant": ["restaurant", "dhaba", "cafe", "kitchen", "food", "biryani", "thali", "grill"],
            "hotel": ["hotel", "resort", "inn", "lodge", "palace", "suites"],
            "college": ["college", "university", "institute", "academy"],
            "hospital": ["hospital", "clinic", "medical", "healthcare"],
            "market": ["market", "bazaar", "mall", "complex"],
            "startup": ["startup", "tech", "digital", "innovation"],
        }

    def extract(self, text: str, source_id: str = "") -> List[Entity]:
        entities = []
        seen = set()

        # Pattern-based extraction
        for etype, patterns in ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1).strip() if match.lastindex else match.group(0).strip()
                    if len(name) > 2 and name.lower() not in seen:
                        seen.add(name.lower())
                        entities.append(Entity(name=name, entity_type=etype, properties={"source": source_id}))

        # Keyword-based extraction
        text_lower = text.lower()
        for etype, keywords in self._custom_terms.items():
            for kw in keywords:
                if kw in text_lower:
                    # Find the sentence containing the keyword
                    for sent in re.split(r'[.!?]', text):
                        if kw in sent.lower():
                            name = sent.strip()[:100]
                            if name.lower() not in seen:
                                seen.add(name.lower())
                                entities.append(Entity(name=name, entity_type=etype,
                                    properties={"source": source_id, "keyword_match": kw}))

        return entities


class RelationshipExtractor:
    """Extract relationships between entities."""

    def extract(self, text: str, entities: List[Entity]) -> List[Relationship]:
        relationships = []
        entity_map = {e.name.lower(): e for e in entities}
        entity_list = list(entity_map.keys())

        for sent in re.split(r'[.!?]', text):
            sent_lower = sent.lower()
            for pattern, rel_type in RELATIONSHIP_PATTERNS:
                for match in re.finditer(pattern, sent_lower):
                    # Find co-occurring entities in the sentence
                    matched_entities = [e for e in entity_list if e in sent_lower]
                    if len(matched_entities) >= 2:
                        src = entity_map[matched_entities[0]]
                        tgt = entity_map[matched_entities[1]]
                        relationships.append(Relationship(
                            source_id=src.id, target_id=tgt.id,
                            relation_type=rel_type, confidence=0.7,
                            properties={"sentence": sent.strip()[:200]},
                        ))

        return relationships


class GraphAnalytics:
    """Graph analytics operations."""

    @staticmethod
    def degree_centrality(entities: List[Entity], relationships: List[Relationship]) -> Dict[str, float]:
        degree = Counter()
        for r in relationships:
            degree[r.source_id] += 1
            degree[r.target_id] += 1
        total = len(entities)
        return {eid: round(count / max(total - 1, 1), 4) for eid, count in degree.items()}

    @staticmethod
    def find_communities(entities: List[Entity], relationships: List[Relationship]) -> List[Set[str]]:
        # Simple connected components
        adj: Dict[str, Set[str]] = {}
        for r in relationships:
            adj.setdefault(r.source_id, set()).add(r.target_id)
            adj.setdefault(r.target_id, set()).add(r.source_id)
        visited = set()
        communities = []
        for eid in adj:
            if eid not in visited:
                component = set()
                stack = [eid]
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        component.add(node)
                        stack.extend(adj.get(node, set()) - visited)
                if component:
                    communities.append(component)
        return communities

    @staticmethod
    def most_connected(entities: List[Entity], relationships: List[Relationship], top_n: int = 10) -> List[Dict]:
        degree = Counter()
        for r in relationships:
            degree[r.source_id] += 1
            degree[r.target_id] += 1
        entity_map = {e.id: e for e in entities}
        top = degree.most_common(top_n)
        return [{"entity": entity_map.get(eid, Entity(id=eid, name="?")).to_dict(), "connections": count} for eid, count in top]


class KnowledgeGraphEngine:
    """Production knowledge graph with extraction, storage, analytics."""

    def __init__(self, storage_path: str = "./data/knowledge_graph"):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._entity_extractor = EntityExtractor()
        self._relationship_extractor = RelationshipExtractor()
        self._analytics = GraphAnalytics()
        self._load()

    def _load(self):
        e_file = self._path / "entities.json"
        r_file = self._path / "relationships.json"
        if e_file.exists():
            for data in json.loads(e_file.read_text()):
                e = Entity(**data)
                self._entities[e.id] = e
        if r_file.exists():
            for data in json.loads(r_file.read_text()):
                r = Relationship(**data)
                self._relationships[r.id] = r
        logger.info(f"Loaded {len(self._entities)} entities, {len(self._relationships)} relationships")

    def save(self):
        (self._path / "entities.json").write_text(json.dumps(
            [e.to_dict() for e in self._entities.values()], indent=2))
        (self._path / "relationships.json").write_text(json.dumps(
            [{"id":r.id,"source_id":r.source_id,"target_id":r.target_id,"relation_type":r.relation_type,
              "properties":r.properties,"confidence":r.confidence} for r in self._relationships.values()], indent=2))

    def extract_from_text(self, text: str, source_id: str = "") -> Dict[str, Any]:
        entities = self._entity_extractor.extract(text, source_id)
        relationships = self._relationship_extractor.extract(text, entities)

        # Deduplicate and store
        for e in entities:
            if e.id not in self._entities:
                self._entities[e.id] = e
            else:
                self._entities[e.id].properties.update(e.properties)

        for r in relationships:
            key = f"{r.source_id}:{r.relation_type}:{r.target_id}"
            if key not in self._relationships:
                self._relationships[key] = r

        return {"new_entities": len(entities), "new_relationships": len(relationships)}

    def query_entity(self, name: str) -> Optional[Entity]:
        name_lower = name.lower()
        for e in self._entities.values():
            if e.name.lower() == name_lower:
                return e
        return None

    def query_relationships(self, entity_id: str) -> List[Relationship]:
        return [r for r in self._relationships.values() if r.source_id == entity_id or r.target_id == entity_id]

    def resolve_entities(self):
        """Simple entity resolution by name matching."""
        name_groups: Dict[str, List[Entity]] = {}
        for e in self._entities.values():
            key = e.name.lower().strip()
            name_groups.setdefault(key, []).append(e)
        resolved = 0
        for key, group in name_groups.items():
            if len(group) > 1:
                primary = group[0]
                for other in group[1:]:
                    primary.properties.update(other.properties)
                    del self._entities[other.id]
                    resolved += 1
        logger.info(f"Resolved {resolved} duplicate entities")
        return resolved

    def get_analytics(self) -> Dict[str, Any]:
        entities = list(self._entities.values())
        relationships = list(self._relationships.values())
        centrality = self._analytics.degree_centrality(entities, relationships)
        communities = self._analytics.find_communities(entities, relationships)
        top = self._analytics.most_connected(entities, relationships)

        type_counts = Counter(e.entity_type for e in entities)
        rel_counts = Counter(r.relation_type for r in relationships)

        return {
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "entity_types": dict(type_counts),
            "relationship_types": dict(rel_counts),
            "communities": len(communities),
            "most_connected": top,
        }

    def to_cypher(self) -> List[str]:
        """Generate Cypher queries for Neo4j import."""
        queries = []
        for e in self._entities.values():
            props = json.dumps(e.properties)
            queries.append(f"CREATE (n:{e.entity_type} {{id:'{e.id}',name:'{e.name}',props:{props}}})")
        for r in self._relationships.values():
            queries.append(f"MATCH (a {{id:'{r.source_id}'}}), (b {{id:'{r.target_id}'}}) CREATE (a)-[:{r.relation_type.upper()}]->(b)")
        return queries
