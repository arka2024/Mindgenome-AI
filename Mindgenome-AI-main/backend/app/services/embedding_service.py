from __future__ import annotations

import threading
from typing import Any, Literal

import numpy as np

from app.core.config import settings
from app.core.logging import logger

EmbeddingInputType = Literal["query", "document"]


class EmbeddingService:
    def __init__(
        self,
        model_name: str | None = None,
        version: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.version = version or settings.EMBEDDING_VERSION
        self.dimension = dimension if dimension is not None else settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self._client: Any = None
        self._client_lock = threading.Lock()

        if self.model_name != "gemini-embedding-001":
            raise ValueError(
                "Only gemini-embedding-001 is supported by this embedding service"
            )
        if self.dimension < 1:
            raise ValueError("EMBEDDING_DIMENSION must be at least 1")
        if not self.version.strip():
            raise ValueError("EMBEDDING_VERSION must not be empty")
        if self.batch_size < 1:
            raise ValueError("EMBEDDING_BATCH_SIZE must be at least 1")

    def embed_text(self, text: str) -> list[float]:
        """Backward-compatible query embedding entry point."""
        return self.embed_query(text)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_batch([text], input_type="query")[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_batch(texts, input_type="document")

    def embed_batch(
        self,
        texts: list[str],
        input_type: EmbeddingInputType = "document",
    ) -> list[list[float]]:
        if not texts:
            return []
        if input_type not in ("query", "document"):
            raise ValueError(f"Unsupported embedding input type: {input_type}")

        embeddings = self._embed_gemini(texts, input_type)
        return self._validate_embeddings(embeddings, len(texts))

    def _get_client(self) -> tuple[Any, Any]:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured for embeddings")

        with self._client_lock:
            if self._client is None:
                try:
                    from google import genai
                    from google.genai import types
                except ImportError as exc:
                    logger.exception("gemini_embedding_sdk_missing")
                    raise RuntimeError(
                        "Gemini embeddings require the google-genai package"
                    ) from exc

                self._client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=types.HttpOptions(
                        timeout=settings.GEMINI_TIMEOUT_SECONDS * 1000
                    ),
                )
                self._types = types

            return self._client, self._types

    def _embed_gemini(
        self,
        texts: list[str],
        input_type: EmbeddingInputType,
    ) -> list[list[float]]:
        client, types = self._get_client()
        task_type = "RETRIEVAL_QUERY" if input_type == "query" else "RETRIEVAL_DOCUMENT"
        embeddings: list[list[float]] = []

        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            try:
                response = client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=self.dimension,
                    ),
                )
            except Exception as exc:
                logger.exception(
                    "gemini_embedding_request_failed",
                    model=self.model_name,
                    version=self.version,
                    input_type=input_type,
                    batch_size=len(batch),
                    error=str(exc),
                )
                raise RuntimeError("Gemini embedding API request failed") from exc

            batch_embeddings = getattr(response, "embeddings", None)
            if not batch_embeddings:
                raise RuntimeError("Gemini embedding API returned no embeddings")
            for embedding in batch_embeddings:
                values = getattr(embedding, "values", None)
                if values is None:
                    raise RuntimeError("Gemini embedding API returned an embedding without values")
                embeddings.append(list(values))

        return embeddings

    def _validate_embeddings(
        self,
        embeddings: list[list[float]],
        expected_count: int,
    ) -> list[list[float]]:
        if len(embeddings) != expected_count:
            raise RuntimeError(
                f"Embedding model returned {len(embeddings)} vectors for {expected_count} inputs"
            )

        validated: list[list[float]] = []
        for vector in embeddings:
            if len(vector) != self.dimension:
                raise RuntimeError(
                    f"Embedding model returned dimension {len(vector)}; expected {self.dimension}"
                )
            values = np.asarray(vector, dtype=np.float32)
            if not np.isfinite(values).all():
                raise RuntimeError("Embedding model returned a non-finite vector value")
            norm = float(np.linalg.norm(values))
            if norm == 0:
                raise RuntimeError("Embedding model returned a zero vector")
            normalized = values / norm
            validated.append(normalized.tolist())
        return validated

    def close(self) -> None:
        with self._client_lock:
            if self._client is not None:
                self._client.close()
                self._client = None


embedding_service = EmbeddingService()
