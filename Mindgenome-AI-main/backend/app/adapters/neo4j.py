from __future__ import annotations

import uuid
from typing import Any
from app.core.config import settings
from app.core.logging import logger

try:
    from neo4j import AsyncGraphDatabase
except Exception:
    AsyncGraphDatabase = None


class Neo4jAdapter:
    def __init__(self) -> None:
        self.uri = getattr(settings, "NEO4J_URI", "bolt://localhost:7687")
        self.user = getattr(settings, "NEO4J_USER", "neo4j")
        self.password = getattr(settings, "NEO4J_PASSWORD", "changeme")
        self.database = getattr(settings, "NEO4J_DATABASE", "neo4j")
        self._driver = None
        # In-memory graph structure for testing/standalone dev
        self._memory_nodes: dict[str, dict[str, Any]] = {}  # key: f"{user_id}:{concept_id}"
        self._memory_edges: list[dict[str, Any]] = []

    async def get_driver(self):
        if self._driver is None and AsyncGraphDatabase is not None:
            try:
                self._driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                )
                await self._driver.verify_connectivity()
                logger.info("neo4j_connected", uri=self.uri)
            except Exception as exc:
                logger.warning("neo4j_connection_failed_using_memory_graph", error=str(exc))
                self._driver = None
        return self._driver

    async def run_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run parameterized Cypher query with automatic user_id binding."""
        driver = await self.get_driver()
        if driver is not None:
            try:
                async with driver.session(database=self.database) as session:
                    result = await session.run(query, parameters or {})
                    records = await result.data()
                    return records
            except Exception as exc:
                logger.error("neo4j_query_failed", query=query, error=str(exc))
        return []

    # -------------------------------------------------------------------------
    # Cycle Prevention & Edge Writing
    # -------------------------------------------------------------------------

    async def check_cycle(self, user_id: str, from_concept_id: str, to_concept_id: str) -> bool:
        """
        Check if adding A -[:PREREQUISITE_OF]-> B would create a cycle (i.e. B already reaches A).
        Returns True if adding the edge would cause a cycle.
        """
        driver = await self.get_driver()
        if driver is not None:
            cypher = """
            MATCH (b:Concept {user_id: $user_id, concept_id: $b_id})
            MATCH path = (b)-[:PREREQUISITE_OF*1..16]->(a:Concept {user_id: $user_id, concept_id: $a_id})
            WHERE ALL(n IN nodes(path) WHERE n.user_id = $user_id)
              AND ALL(rel IN relationships(path) WHERE rel.user_id = $user_id)
            RETURN true AS would_cycle LIMIT 1;
            """
            res = await self.run_query(cypher, {"user_id": user_id, "b_id": to_concept_id, "a_id": from_concept_id})
            return bool(res and res[0].get("would_cycle"))

        # In-memory cycle check (BFS from to_concept_id looking for from_concept_id)
        visited = set()
        queue = [to_concept_id]
        while queue:
            curr = queue.pop(0)
            if curr == from_concept_id:
                return True
            if curr in visited:
                continue
            visited.add(curr)
            for e in self._memory_edges:
                if (
                    e["user_id"] == user_id
                    and e["type"] == "PREREQUISITE_OF"
                    and e["from"] == curr
                    and e.get("status") != "rejected"
                ):
                    queue.append(e["to"])
        return False

    async def merge_concept(
        self,
        user_id: str,
        concept_id: str,
        name: str,
        normalized_name: str,
    ) -> None:
        """Upsert Concept node with user_id tenant boundary."""
        driver = await self.get_driver()
        if driver is not None:
            cypher = """
            MERGE (c:Concept {user_id: $user_id, concept_id: $concept_id})
            ON CREATE SET c.name = $name, c.normalized_name = $normalized_name, c.created_at = datetime()
            ON MATCH SET c.name = $name
            """
            await self.run_query(cypher, {
                "user_id": user_id,
                "concept_id": concept_id,
                "name": name,
                "normalized_name": normalized_name,
            })
            return

        key = f"{user_id}:{concept_id}"
        self._memory_nodes[key] = {
            "user_id": user_id,
            "concept_id": concept_id,
            "name": name,
            "normalized_name": normalized_name,
        }

    async def merge_concepts(self, user_id: str, concepts: list[dict[str, str]]) -> None:
        if not concepts:
            return

        driver = await self.get_driver()
        if driver is not None:
            cypher = """
            UNWIND $concepts AS item
            MERGE (c:Concept {user_id: $user_id, concept_id: item.concept_id})
            ON CREATE SET c.name = item.name,
                          c.normalized_name = item.normalized_name,
                          c.created_at = datetime()
            ON MATCH SET c.name = item.name
            """
            await self.run_query(cypher, {"user_id": user_id, "concepts": concepts})
            return

        for concept in concepts:
            key = f"{user_id}:{concept['concept_id']}"
            self._memory_nodes[key] = {
                "user_id": user_id,
                "concept_id": concept["concept_id"],
                "name": concept["name"],
                "normalized_name": concept["normalized_name"],
            }

    async def merge_prerequisite_edge(
        self,
        user_id: str,
        from_concept_id: str,
        to_concept_id: str,
        confidence: float = 0.85,
        status: str = "confirmed",
    ) -> bool:
        """
        Merge PREREQUISITE_OF edge with cycle guard.
        Returns False if cycle detected (edge skipped).
        """
        if from_concept_id == to_concept_id:
            return False

        driver = await self.get_driver()
        if driver is not None:
            cypher = """
            MATCH (a:Concept {user_id: $user_id, concept_id: $from_id})
            MATCH (b:Concept {user_id: $user_id, concept_id: $to_id})
            CALL {
                WITH a, b
                OPTIONAL MATCH path = (b)-[:PREREQUISITE_OF*1..16]->(a)
                WHERE ALL(n IN nodes(path) WHERE n.user_id = $user_id)
                  AND ALL(rel IN relationships(path) WHERE rel.user_id = $user_id)
                RETURN count(path) > 0 AS would_cycle
            }
            WITH a, b, would_cycle
            WHERE NOT would_cycle
            MERGE (a)-[r:PREREQUISITE_OF {user_id: $user_id}]->(b)
            ON CREATE SET r.confidence = $confidence, r.status = $status, r.created_at = datetime()
            ON MATCH SET r.confidence = $confidence, r.status = $status
            RETURN true AS merged
            """
            result = await self.run_query(cypher, {
                "user_id": user_id,
                "from_id": from_concept_id,
                "to_id": to_concept_id,
                "confidence": confidence,
                "status": status,
            })
            if result and result[0].get("merged"):
                return True

            logger.warning(
                "prerequisite_edge_not_merged",
                from_id=from_concept_id,
                to_id=to_concept_id,
            )
            return False

        if await self.check_cycle(user_id, from_concept_id, to_concept_id):
            logger.warning("skipped_prerequisite_cycle", from_id=from_concept_id, to_id=to_concept_id)
            return False

        # In-memory edge
        edge_id = str(uuid.uuid4())
        self._memory_edges.append({
            "id": edge_id,
            "user_id": user_id,
            "from": from_concept_id,
            "to": to_concept_id,
            "type": "PREREQUISITE_OF",
            "confidence": confidence,
            "status": status,
        })
        return True

    async def get_subgraph(self, user_id: str, limit: int = 150) -> dict[str, Any]:
        """Fetch Cytoscape-formatted subgraph for the learner's dashboard."""
        driver = await self.get_driver()
        if driver is not None:
            cypher = """
            MATCH (c:Concept {user_id: $user_id})
            WITH c LIMIT $limit
            OPTIONAL MATCH (c)-[r {user_id: $user_id}]->(o:Concept {user_id: $user_id})
            WHERE r.status <> 'rejected'
            RETURN collect(DISTINCT c) AS concepts,
                   collect(DISTINCT {id: id(r), from: c.concept_id, to: o.concept_id, type: type(r), confidence: r.confidence, status: r.status}) AS edges
            """
            res = await self.run_query(cypher, {"user_id": user_id, "limit": limit})
            if res:
                row = res[0]
                nodes = [
                    {"data": {"id": c["concept_id"], "label": c.get("name", c["concept_id"])}}
                    for c in row.get("concepts", [])
                ]
                edges = [
                    {
                        "data": {
                            "id": str(e["id"]),
                            "source": e["from"],
                            "target": e["to"],
                            "type": e["type"],
                            "confidence": e.get("confidence", 1.0),
                            "status": e.get("status", "confirmed"),
                        }
                    }
                    for e in row.get("edges", []) if e.get("to")
                ]
                return {"nodes": nodes, "edges": edges}

        # Memory fallback
        nodes = [
            {"data": {"id": n["concept_id"], "label": n["name"]}}
            for n in self._memory_nodes.values()
            if n["user_id"] == user_id
        ]
        edges = [
            {
                "data": {
                    "id": e["id"],
                    "source": e["from"],
                    "target": e["to"],
                    "type": e["type"],
                    "confidence": e["confidence"],
                    "status": e["status"],
                }
            }
            for e in self._memory_edges
            if e["user_id"] == user_id and e.get("status") != "rejected"
        ]
        return {"nodes": nodes, "edges": edges}

    async def review_edge(self, user_id: str, edge_id: str, decision: str) -> bool:
        """Confirm or reject a relationship edge."""
        driver = await self.get_driver()
        if driver is not None:
            cypher = """
            MATCH ()-[r {user_id: $user_id}]->()
            WHERE id(r) = toInteger($edge_id)
            SET r.status = $decision
            RETURN r
            """
            res = await self.run_query(cypher, {"user_id": user_id, "edge_id": edge_id, "decision": decision})
            return bool(res)

        for e in self._memory_edges:
            if e["user_id"] == user_id and (e["id"] == edge_id or str(e.get("from")) in edge_id):
                e["status"] = decision
                return True
        return False


neo4j_adapter = Neo4jAdapter()
