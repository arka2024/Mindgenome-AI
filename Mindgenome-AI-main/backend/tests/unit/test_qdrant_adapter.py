from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from app.adapters.qdrant import QdrantAdapter
from app.core.config import settings


def unit_vector(dimension: int, index: int = 0) -> list[float]:
    vector = [0.0] * dimension
    vector[index] = 1.0
    return vector


@pytest.mark.asyncio
async def test_memory_vector_upsert_and_versioned_similarity(monkeypatch):
    adapter = QdrantAdapter()
    monkeypatch.setattr(settings, "APP_ENV", "local")
    monkeypatch.setattr(adapter, "get_client", _no_client)
    vector = unit_vector(adapter.dim)

    await adapter.upsert_points(
        [
            {
                "id": "matching",
                "vector": vector,
                "payload": {
                    "user_id": "user-1",
                    "document_id": "doc-1",
                    "embedding_version": adapter.embedding_version,
                    "embedding_model": adapter.embedding_model,
                    "embedding_dimension": adapter.dim,
                },
            },
        ]
    )
    adapter._memory_points["wrong-version"] = {
        "vector": vector,
        "payload": {
            "user_id": "user-1",
            "document_id": "doc-1",
            "embedding_version": "old-version",
            "embedding_model": adapter.embedding_model,
            "embedding_dimension": adapter.dim,
        },
    }

    hits = await adapter.search_points(
        user_id="user-1",
        query_vector=vector,
        top_k=5,
        min_score=0.1,
        document_id="doc-1",
    )

    assert [hit["chunk_id"] for hit in hits] == ["matching"]
    assert hits[0]["score"] == pytest.approx(1.0, abs=1e-6)
    assert len(adapter._memory_points["matching"]["vector"]) == adapter.dim
    assert math.isfinite(hits[0]["score"])


async def _no_client():
    return None


@pytest.mark.asyncio
async def test_upsert_rejects_incorrect_vector_dimension():
    adapter = QdrantAdapter()

    with pytest.raises(ValueError, match="expected"):
        await adapter.upsert_points(
            [{"id": "invalid", "vector": [1.0, 0.0], "payload": {}}]
        )


@pytest.mark.asyncio
async def test_search_uses_query_points_api(monkeypatch):
    adapter = QdrantAdapter()
    monkeypatch.setattr(settings, "APP_ENV", "local")
    vector = unit_vector(adapter.dim)
    result_point = SimpleNamespace(
        id="matching",
        score=0.9,
        payload={"user_id": "user-1", "document_id": "doc-1"},
    )
    expected = SimpleNamespace(points=[result_point])

    class QueryPointsClient:
        async def query_points(self, **kwargs):
            assert kwargs["collection_name"] == adapter.collection_name
            assert kwargs["query"] == vector
            assert kwargs["limit"] == 3
            assert kwargs["score_threshold"] == 0.2
            assert kwargs["with_payload"] is True
            return expected

    async def get_query_points_client():
        return QueryPointsClient()

    monkeypatch.setattr(adapter, "get_client", get_query_points_client)
    hits = await adapter.search_points(
        user_id="user-1",
        query_vector=vector,
        top_k=3,
        min_score=0.2,
    )

    assert hits == [
        {
            "chunk_id": "matching",
            "score": 0.9,
            "payload": {"user_id": "user-1", "document_id": "doc-1"},
        }
    ]
