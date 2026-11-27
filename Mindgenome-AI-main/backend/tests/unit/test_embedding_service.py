from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

from app.core.config import settings
from app.services.embedding_service import EmbeddingService


def unit_vector(dimension: int) -> list[float]:
    vector = np.zeros(dimension, dtype=np.float32)
    vector[0] = 1.0
    return vector.tolist()


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def embed_content(self, **kwargs):
        self.calls.append(kwargs)
        texts = kwargs["contents"]
        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(values=unit_vector(kwargs["config"].output_dimensionality))
                for _ in texts
            ]
        )


def test_gemini_embedding_single_and_batch(monkeypatch):
    service = EmbeddingService()
    fake_client = FakeEmbeddingClient()
    service._client = SimpleNamespace(models=fake_client)
    service._types = SimpleNamespace(
        EmbedContentConfig=lambda **kwargs: SimpleNamespace(**kwargs)
    )
    service.batch_size = 1

    single = service.embed_text("Gradient boosting uses decision trees.")
    batch = service.embed_documents(["First chunk.", "Second chunk."])

    assert len(single) == service.dimension
    assert len(batch) == 2
    assert all(len(vector) == service.dimension for vector in batch)
    assert math.sqrt(sum(value * value for value in single)) == pytest.approx(1.0, abs=1e-3)
    assert [call["contents"] for call in fake_client.calls] == [
        ["Gradient boosting uses decision trees."],
        ["First chunk."],
        ["Second chunk."],
    ]
    assert [call["config"].task_type for call in fake_client.calls] == [
        "RETRIEVAL_QUERY",
        "RETRIEVAL_DOCUMENT",
        "RETRIEVAL_DOCUMENT",
    ]


def test_gemini_query_and_document_embeddings_use_same_dimension():
    service = EmbeddingService()
    fake_client = FakeEmbeddingClient()
    service._client = SimpleNamespace(models=fake_client)
    service._types = SimpleNamespace(
        EmbedContentConfig=lambda **kwargs: SimpleNamespace(**kwargs)
    )

    query = service.embed_query("What is gradient boosting?")
    documents = service.embed_documents(["Gradient boosting is an ensemble method."])

    assert len(query) == len(documents[0]) == service.dimension
    assert all(
        call["config"].output_dimensionality == service.dimension
        for call in fake_client.calls
    )


def test_embedding_rejects_mismatched_dimension():
    service = EmbeddingService()
    with pytest.raises(RuntimeError, match="expected"):
        service._validate_embeddings([[0.0, 1.0]], 1)


def test_embedding_rejects_wrong_number_of_vectors():
    service = EmbeddingService()
    with pytest.raises(RuntimeError, match="for 1 inputs"):
        service._validate_embeddings([], 1)


def test_embedding_rejects_non_finite_vector():
    service = EmbeddingService()
    with pytest.raises(RuntimeError, match="non-finite"):
        service._validate_embeddings([[float("nan")] * service.dimension], 1)


def test_embedding_requires_gemini_api_key(monkeypatch):
    service = EmbeddingService()
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        service._get_client()


def test_embedding_rejects_unsupported_model():
    with pytest.raises(ValueError, match="Only gemini-embedding-001"):
        EmbeddingService(model_name="Qwen/Qwen3-Embedding-0.6B")
