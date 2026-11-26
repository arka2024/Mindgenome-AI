from __future__ import annotations

import hashlib
import math
import threading
import numpy as np
from app.core.config import settings
from app.core.logging import logger

_model = None
_model_lock = threading.Lock()
_encode_lock = threading.Lock()


def _get_sentence_transformer():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _model = SentenceTransformer(settings.EMBEDDING_MODEL)
                    logger.info("sentence_transformer_loaded", model=settings.EMBEDDING_MODEL)
                except Exception as exc:
                    logger.warning("sentence_transformers_not_available_using_fallback", error=str(exc))
                    _model = False
    return _model if _model is not False else None


class EmbeddingService:
    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a normalized vector of size self.dim."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings."""
        if not texts:
            return []

        model = _get_sentence_transformer()
        if model is not None:
            try:
                with _encode_lock:
                    embeddings = model.encode(texts, normalize_embeddings=True)
                return [emb.tolist() for emb in embeddings]
            except Exception as exc:
                logger.error("model_encode_failed_using_deterministic_fallback", error=str(exc))

        # Deterministic fallback vector generation based on sha256 + token distribution
        vectors: list[list[float]] = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            words = text.lower().split()
            if not words:
                words = ["empty"]
            for i, word in enumerate(words):
                h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
                idx = (h + i) % self.dim
                weight = 1.0 / math.sqrt(i + 1)
                vec[idx] += weight
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.tolist())
        return vectors


embedding_service = EmbeddingService(dim=384)
