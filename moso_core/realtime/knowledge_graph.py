from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


@dataclass
class Entity:
    id: str
    name: str
    type: str = "unknown"
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    confidence: float = 1.0
    source: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "aliases": self.aliases,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Relationship:
    id: str
    source_id: str
    target_id: str
    type: str = "related_to"
    label: str = ""
    weight: float = 1.0
    confidence: float = 1.0
    source: str = ""
    evidence: list[str] = field(default_factory=list)
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "label": self.label,
            "weight": self.weight,
            "confidence": self.confidence,
            "source": self.source,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }


@dataclass
class Event:
    id: str
    title: str
    description: str = ""
    entity_ids: list[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    source: str = ""
    confidence: float = 1.0
    metadata: dict = field(default_factory=list)
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "entity_ids": self.entity_ids,
            "timestamp": self.timestamp,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class Concept:
    id: str
    name: str
    definition: str = ""
    parent_id: Optional[str] = None
    confidence: float = 1.0
    source: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "parent_id": self.parent_id,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class KnowledgeGraph:
    def __init__(self, db_path: str | Path = "knowledge_graph.db"):
        if not NETWORKX_AVAILABLE:
            raise ImportError("networkx is required for KnowledgeGraph. Install with: pip install networkx")
        self._db_path = Path(db_path)
        self._graph = nx.DiGraph()
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()
        self._load_from_db()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'unknown',
                description TEXT DEFAULT '',
                aliases TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                type TEXT DEFAULT 'related_to',
                label TEXT DEFAULT '',
                weight REAL DEFAULT 1.0,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT '',
                evidence TEXT DEFAULT '[]',
                created_at REAL NOT NULL,
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                entity_ids TEXT DEFAULT '[]',
                timestamp TEXT,
                source TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                definition TEXT DEFAULT '',
                parent_id TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    def _load_from_db(self) -> None:
        rows = self._conn.execute("SELECT id, name, type, description, aliases, metadata, confidence, source, created_at, updated_at FROM entities").fetchall()
        for r in rows:
            self._graph.add_node(
                r[0],
                kind="entity",
                name=r[1],
                type=r[2],
                description=r[3],
                aliases=json.loads(r[4]),
                metadata=json.loads(r[5]),
                confidence=r[6],
                source=r[7],
                created_at=r[8],
                updated_at=r[9],
            )

        rows = self._conn.execute("SELECT id, source_id, target_id, type, label, weight, confidence, source, evidence, created_at FROM relationships").fetchall()
        for r in rows:
            self._graph.add_edge(
                r[1],
                r[2],
                kind="relationship",
                rel_id=r[0],
                type=r[3],
                label=r[4],
                weight=r[5],
                confidence=r[6],
                source=r[7],
                evidence=json.loads(r[8]),
                created_at=r[9],
            )

        rows = self._conn.execute("SELECT id, title, description, entity_ids, timestamp, source, confidence, metadata, created_at FROM events").fetchall()
        for r in rows:
            self._graph.add_node(
                r[0],
                kind="event",
                title=r[1],
                description=r[2],
                entity_ids=json.loads(r[3]),
                timestamp=r[4],
                source=r[5],
                confidence=r[6],
                metadata=json.loads(r[7]),
                created_at=r[8],
            )

        rows = self._conn.execute("SELECT id, name, definition, parent_id, confidence, source, metadata, created_at FROM concepts").fetchall()
        for r in rows:
            self._graph.add_node(
                r[0],
                kind="concept",
                name=r[1],
                definition=r[2],
                parent_id=r[3],
                confidence=r[4],
                source=r[5],
                metadata=json.loads(r[6]),
                created_at=r[7],
            )
            if r[3]:
                self._graph.add_edge(r[3], r[0], kind="subconcept_of")

    def add_entity(self, entity: Entity) -> str:
        now = time.time()
        entity.created_at = entity.created_at or now
        entity.updated_at = now
        with self._lock:
            self._graph.add_node(
                entity.id,
                kind="entity",
                name=entity.name,
                type=entity.type,
                description=entity.description,
                aliases=entity.aliases,
                metadata=entity.metadata,
                confidence=entity.confidence,
                source=entity.source,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO entities (id, name, type, description, aliases, metadata, confidence, source, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entity.id, entity.name, entity.type, entity.description, json.dumps(entity.aliases), json.dumps(entity.metadata), entity.confidence, entity.source, entity.created_at, entity.updated_at),
            )
            self._conn.commit()
        return entity.id

    def add_relationship(self, rel: Relationship) -> str:
        rel.created_at = rel.created_at or time.time()
        with self._lock:
            self._graph.add_edge(
                rel.source_id,
                rel.target_id,
                kind="relationship",
                rel_id=rel.id,
                type=rel.type,
                label=rel.label,
                weight=rel.weight,
                confidence=rel.confidence,
                source=rel.source,
                evidence=rel.evidence,
                created_at=rel.created_at,
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO relationships (id, source_id, target_id, type, label, weight, confidence, source, evidence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (rel.id, rel.source_id, rel.target_id, rel.type, rel.label, rel.weight, rel.confidence, rel.source, json.dumps(rel.evidence), rel.created_at),
            )
            self._conn.commit()
        return rel.id

    def add_event(self, event: Event) -> str:
        event.created_at = event.created_at or time.time()
        with self._lock:
            self._graph.add_node(
                event.id,
                kind="event",
                title=event.title,
                description=event.description,
                entity_ids=event.entity_ids,
                timestamp=event.timestamp,
                source=event.source,
                confidence=event.confidence,
                metadata=event.metadata,
                created_at=event.created_at,
            )
            for eid in event.entity_ids:
                if self._graph.has_node(eid):
                    self._graph.add_edge(eid, event.id, kind="involved_in")
            self._conn.execute(
                "INSERT OR REPLACE INTO events (id, title, description, entity_ids, timestamp, source, confidence, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event.id, event.title, event.description, json.dumps(event.entity_ids), event.timestamp, event.source, event.confidence, json.dumps(event.metadata), event.created_at),
            )
            self._conn.commit()
        return event.id

    def add_concept(self, concept: Concept) -> str:
        concept.created_at = concept.created_at or time.time()
        with self._lock:
            self._graph.add_node(
                concept.id,
                kind="concept",
                name=concept.name,
                definition=concept.definition,
                parent_id=concept.parent_id,
                confidence=concept.confidence,
                source=concept.source,
                metadata=concept.metadata,
                created_at=concept.created_at,
            )
            if concept.parent_id and self._graph.has_node(concept.parent_id):
                self._graph.add_edge(concept.parent_id, concept.id, kind="subconcept_of")
            self._conn.execute(
                "INSERT OR REPLACE INTO concepts (id, name, definition, parent_id, confidence, source, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (concept.id, concept.name, concept.definition, concept.parent_id, concept.confidence, concept.source, json.dumps(concept.metadata), concept.created_at),
            )
            self._conn.commit()
        return concept.id

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        node = self._graph.nodes.get(entity_id)
        if node is None or node.get("kind") != "entity":
            return None
        return Entity(
            id=entity_id,
            name=node["name"],
            type=node.get("type", "unknown"),
            description=node.get("description", ""),
            aliases=node.get("aliases", []),
            metadata=node.get("metadata", {}),
            confidence=node.get("confidence", 1.0),
            source=node.get("source", ""),
            created_at=node.get("created_at", 0),
            updated_at=node.get("updated_at", 0),
        )

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        for u, v, data in self._graph.edges(data=True):
            if data.get("rel_id") == rel_id:
                return Relationship(
                    id=rel_id,
                    source_id=u,
                    target_id=v,
                    type=data.get("type", "related_to"),
                    label=data.get("label", ""),
                    weight=data.get("weight", 1.0),
                    confidence=data.get("confidence", 1.0),
                    source=data.get("source", ""),
                    evidence=data.get("evidence", []),
                    created_at=data.get("created_at", 0),
                )
        return None

    def get_event(self, event_id: str) -> Optional[Event]:
        node = self._graph.nodes.get(event_id)
        if node is None or node.get("kind") != "event":
            return None
        return Event(
            id=event_id,
            title=node["title"],
            description=node.get("description", ""),
            entity_ids=node.get("entity_ids", []),
            timestamp=node.get("timestamp"),
            source=node.get("source", ""),
            confidence=node.get("confidence", 1.0),
            metadata=node.get("metadata", {}),
            created_at=node.get("created_at", 0),
        )

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        node = self._graph.nodes.get(concept_id)
        if node is None or node.get("kind") != "concept":
            return None
        return Concept(
            id=concept_id,
            name=node["name"],
            definition=node.get("definition", ""),
            parent_id=node.get("parent_id"),
            confidence=node.get("confidence", 1.0),
            source=node.get("source", ""),
            metadata=node.get("metadata", {}),
            created_at=node.get("created_at", 0),
        )

    def get_neighbors(self, node_id: str, max_depth: int = 1) -> list[dict]:
        if not self._graph.has_node(node_id):
            return []
        if max_depth <= 1:
            neighbors = list(self._graph.neighbors(node_id)) + list(self._graph.predecessors(node_id))
            seen = set()
            results = []
            for nid in neighbors:
                if nid not in seen:
                    seen.add(nid)
                    results.append({"id": nid, "data": dict(self._graph.nodes[nid])})
            return results
        sub = nx.ego_graph(self._graph, node_id, radius=max_depth)
        return [{"id": n, "data": dict(sub.nodes[n])} for n in sub.nodes if n != node_id]

    def find_path(self, source_id: str, target_id: str) -> list[list[str]]:
        try:
            paths = list(nx.all_simple_paths(self._graph, source_id, target_id, cutoff=6))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def search_entities(self, query: str, limit: int = 20) -> list[Entity]:
        ql = query.lower()
        results = []
        for nid, data in self._graph.nodes(data=True):
            if data.get("kind") != "entity":
                continue
            name: str = data.get("name", "")
            desc: str = data.get("description", "")
            aliases: list = data.get("aliases", [])
            if ql in name.lower() or ql in desc.lower():
                results.append(self.get_entity(nid))
            else:
                for alias in aliases:
                    if ql in alias.lower():
                        results.append(self.get_entity(nid))
                        break
        return results[:limit]

    def get_timeline(self, entity_id: Optional[str] = None) -> list[Event]:
        events = []
        for nid, data in self._graph.nodes(data=True):
            if data.get("kind") != "event":
                continue
            if entity_id and entity_id not in data.get("entity_ids", []):
                continue
            event = self.get_event(nid)
            if event:
                events.append(event)
        events.sort(key=lambda e: e.timestamp or "")
        return events

    def get_subgraph(self, node_ids: list[str]) -> nx.DiGraph:
        return self._graph.subgraph(node_ids)

    def export_json(self) -> dict:
        entities = []
        for nid, data in self._graph.nodes(data=True):
            if data.get("kind") == "entity":
                entities.append(self.get_entity(nid).to_dict())
        relationships = []
        for u, v, data in self._graph.edges(data=True):
            if data.get("kind") == "relationship":
                rel = self.get_relationship(data["rel_id"])
                if rel:
                    relationships.append(rel.to_dict())
        events = []
        for nid, data in self._graph.nodes(data=True):
            if data.get("kind") == "event":
                events.append(self.get_event(nid).to_dict())
        concepts = []
        for nid, data in self._graph.nodes(data=True):
            if data.get("kind") == "concept":
                concepts.append(self.get_concept(nid).to_dict())
        return {
            "entities": entities,
            "relationships": relationships,
            "events": events,
            "concepts": concepts,
        }

    def import_json(self, data: dict) -> None:
        for e in data.get("entities", []):
            self.add_entity(Entity(**e))
        for r in data.get("relationships", []):
            self.add_relationship(Relationship(**r))
        for e in data.get("events", []):
            self.add_event(Event(**e))
        for c in data.get("concepts", []):
            self.add_concept(Concept(**c))

    def stats(self) -> dict:
        return {
            "entities": sum(1 for _, d in self._graph.nodes(data=True) if d.get("kind") == "entity"),
            "relationships": self._graph.number_of_edges(),
            "events": sum(1 for _, d in self._graph.nodes(data=True) if d.get("kind") == "event"),
            "concepts": sum(1 for _, d in self._graph.nodes(data=True) if d.get("kind") == "concept"),
            "total_nodes": self._graph.number_of_nodes(),
        }

    def clear(self) -> None:
        with self._lock:
            self._graph.clear()
            for table in ("entities", "relationships", "events", "concepts"):
                self._conn.execute(f"DELETE FROM {table}")
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
