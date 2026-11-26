from __future__ import annotations

import pytest
from app.adapters.neo4j import Neo4jAdapter


@pytest.mark.asyncio
async def test_merge_concepts_populates_memory_graph():
    adapter = Neo4jAdapter()

    await adapter.merge_concepts(
        "test-user-batch",
        [
            {
                "concept_id": "concept-1",
                "name": "Decision Trees",
                "normalized_name": "decision trees",
            },
            {
                "concept_id": "concept-2",
                "name": "Boosting",
                "normalized_name": "boosting",
            },
        ],
    )

    assert adapter._memory_nodes["test-user-batch:concept-1"]["name"] == "Decision Trees"
    assert adapter._memory_nodes["test-user-batch:concept-2"]["normalized_name"] == "boosting"


@pytest.mark.asyncio
async def test_neo4j_cycle_detection():
    adapter = Neo4jAdapter()
    user_id = "test-user-cycle-123"

    # Merge nodes A, B, C
    await adapter.merge_concept(user_id, "A", "Trees", "trees")
    await adapter.merge_concept(user_id, "B", "Ensembles", "ensembles")
    await adapter.merge_concept(user_id, "C", "Boosting", "boosting")

    # Add A -> B (ok)
    ok_1 = await adapter.merge_prerequisite_edge(user_id, "A", "B")
    assert ok_1 is True

    # Add B -> C (ok)
    ok_2 = await adapter.merge_prerequisite_edge(user_id, "B", "C")
    assert ok_2 is True

    # Attempt to add C -> A (CYCLE! C -> A -> B -> C)
    would_cycle = await adapter.check_cycle(user_id, "C", "A")
    assert would_cycle is True

    ok_cycle = await adapter.merge_prerequisite_edge(user_id, "C", "A")
    assert ok_cycle is False  # Must be rejected by cycle guard!


@pytest.mark.asyncio
async def test_neo4j_subgraph_and_review():
    adapter = Neo4jAdapter()
    user_id = "test-user-graph-456"

    await adapter.merge_concept(user_id, "c1", "Concept 1", "concept 1")
    await adapter.merge_concept(user_id, "c2", "Concept 2", "concept 2")
    await adapter.merge_prerequisite_edge(user_id, "c1", "c2")

    subgraph = await adapter.get_subgraph(user_id)
    assert len(subgraph["nodes"]) >= 2
    assert len(subgraph["edges"]) >= 1

    edge_id = subgraph["edges"][0]["data"]["id"]
    reviewed = await adapter.review_edge(user_id, edge_id, "rejected")
    assert reviewed is True
