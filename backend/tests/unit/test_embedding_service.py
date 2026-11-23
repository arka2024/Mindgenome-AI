from __future__ import annotations

import math
import pytest
from app.services.embedding_service import embedding_service


def test_embedding_dimension_and_norm():
    vec = embedding_service.embed_text("Gradient boosting uses decision trees.")
    assert len(vec) == 384
    norm = math.sqrt(sum(x * x for x in vec))
    assert pytest.approx(norm, 0.01) == 1.0


def test_embedding_batch():
    texts = [
        "First chunk about decision trees.",
        "Second chunk about ensemble learning.",
        "Third chunk about loss functions.",
    ]
    batch = embedding_service.embed_batch(texts)
    assert len(batch) == 3
    for v in batch:
        assert len(v) == 384
