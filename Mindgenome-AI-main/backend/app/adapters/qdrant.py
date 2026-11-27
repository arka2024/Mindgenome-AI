from __future__ import annotations

import math
import re
import uuid
from typing import Any
import numpy as np
from app.core.config import settings
from app.core.logging import logger

try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.http import models as qmodels
except Exception:
    AsyncQdrantClient = None
    qmodels = None


class QdrantAdapter:
    def __init__(self) -> None:
        self.url = getattr(settings, "QDRANT_URL", "http://localhost:6333")
        self.api_key = getattr(settings, "QDRANT_API_KEY", None)
        self.embedding_version = settings.EMBEDDING_VERSION
        self.embedding_model = settings.EMBEDDING_MODEL
        self.collection_name = settings.EMBEDDING_COLLECTION_NAME.strip() or (
            f"{getattr(settings, 'QDRANT_COLLECTION', 'mindgenome_chunks')}_"
            f"{re.sub(r'[^a-zA-Z0-9_-]+', '_', self.embedding_version)}"
        )
        self.dim = settings.EMBEDDING_DIMENSION
        self._client = None
        # In-memory storage fallback for local dev & testing
        self._memory_points: dict[str, dict[str, Any]] = {}

    async def get_client(self):
        if self._client is None and AsyncQdrantClient is not None:
            try:
                self._client = AsyncQdrantClient(
                    url=self.url,
                    api_key=self.api_key if self.api_key else None,
                    timeout=5.0,
                )
                # Verify collection exists
                collections = await self._client.get_collections()
                names = [c.name for c in collections.collections]
                if self.collection_name not in names:
                    await self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=qmodels.VectorParams(
                            size=self.dim,
                            distance=qmodels.Distance.COSINE,
                        ),
                    )
                else:
                    collection_info = await self._client.get_collection(self.collection_name)
                    vector_config = collection_info.config.params.vectors
                    collection_size = getattr(vector_config, "size", None)
                    if collection_size != self.dim:
                        raise RuntimeError(
                            f"Qdrant collection {self.collection_name!r} has dimension "
                            f"{collection_size}, expected {self.dim}"
                        )

                for field_name in (
                    "user_id",
                    "document_id",
                    "embedding_version",
                    "embedding_model",
                ):
                    await self._client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=qmodels.PayloadSchemaType.KEYWORD,
                    )
            except Exception as exc:
                self._client = None
                if settings.is_production:
                    logger.exception(
                        "qdrant_connection_failed",
                        collection=self.collection_name,
                        error=str(exc),
                    )
                    raise RuntimeError(
                        f"Unable to initialize the configured Qdrant collection {self.collection_name!r}"
                    ) from exc
                logger.warning("qdrant_client_failed_using_memory_fallback", error=str(exc))
        return self._client

    async def upsert_points(
        self,
        points: list[dict[str, Any]],
    ) -> None:
        """
        Upsert a list of points.
        Each point dict has: {"id": str, "vector": list[float], "payload": dict}
        """
        if not points:
            return

        for point in points:
            if len(point["vector"]) != self.dim:
                raise ValueError(
                    f"Qdrant vector has dimension {len(point['vector'])}; expected {self.dim}"
                )
            payload = point["payload"]
            if (
                payload.get("embedding_model") != self.embedding_model
                or payload.get("embedding_version") != self.embedding_version
                or payload.get("embedding_dimension") != self.dim
            ):
                raise ValueError("Qdrant point metadata does not match the active embedding configuration")

        client = await self.get_client()
        if client is not None and qmodels is not None:
            try:
                q_points = [
                    qmodels.PointStruct(
                        id=p["id"],
                        vector=p["vector"],
                        payload=p["payload"],
                    )
                    for p in points
                ]
                await client.upsert(
                    collection_name=self.collection_name,
                    points=q_points,
                )
                logger.info("qdrant_points_upserted", count=len(points))
                return
            except Exception as exc:
                if settings.is_production:
                    logger.exception("qdrant_upsert_failed", error=str(exc))
                    raise RuntimeError("Qdrant rejected an embedding batch") from exc
                logger.error("qdrant_upsert_failed_saving_to_memory", error=str(exc))
        elif settings.is_production:
            raise RuntimeError("Qdrant is unavailable; refusing to store production vectors in process memory")

        # Memory fallback
        for p in points:
            self._memory_points[p["id"]] = {
                "vector": np.array(p["vector"], dtype=np.float32),
                "payload": p["payload"],
            }
        logger.info("points_saved_to_memory_fallback", count=len(points))

    async def search_points(
        self,
        user_id: str,
        query_vector: list[float],
        top_k: int = 12,
        min_score: float = 0.35,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for nearest chunks enforcing tenant user_id filter.
        Returns list of {"chunk_id": str, "score": float, "payload": dict}.
        """
        if len(query_vector) != self.dim:
            raise ValueError(
                f"Query vector has dimension {len(query_vector)}; expected {self.dim}"
            )

        client = await self.get_client()
        if client is not None and qmodels is not None:
            try:
                must_conditions = [
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=str(user_id)),
                    ),
                    qmodels.FieldCondition(
                        key="embedding_version",
                        match=qmodels.MatchValue(value=self.embedding_version),
                    ),
                    qmodels.FieldCondition(
                        key="embedding_model",
                        match=qmodels.MatchValue(value=self.embedding_model),
                    ),
                    qmodels.FieldCondition(
                        key="embedding_dimension",
                        match=qmodels.MatchValue(value=self.dim),
                    ),
                ]
                if document_id:
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=str(document_id)),
                        )
                    )

                query_filter = qmodels.Filter(must=must_conditions)
                if hasattr(client, "query_points"):
                    search_result = await client.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        query_filter=query_filter,
                        limit=top_k,
                        score_threshold=min_score,
                        with_payload=True,
                    )
                    points = search_result.points
                else:
                    search_result = await client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        query_filter=query_filter,
                        limit=top_k,
                        score_threshold=min_score,
                    )
                    points = search_result

                return [
                    {
                        "chunk_id": str(r.id),
                        "score": float(r.score),
                        "payload": r.payload,
                    }
                    for r in points
                ]
            except Exception as exc:
                if settings.is_production:
                    logger.exception("qdrant_search_failed", error=str(exc))
                    raise RuntimeError("Qdrant vector search failed") from exc
                logger.error("qdrant_search_failed_falling_back_to_memory", error=str(exc))
        elif settings.is_production:
            raise RuntimeError("Qdrant is unavailable; production semantic search cannot run")

        # In-memory cosine search fallback
        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        results = []
        for pid, data in self._memory_points.items():
            payload = data["payload"]
            # Tenant isolation check
            if str(payload.get("user_id")) != str(user_id):
                continue
            if payload.get("embedding_version") != self.embedding_version:
                continue
            if payload.get("embedding_model") != self.embedding_model:
                continue
            if payload.get("embedding_dimension") != self.dim:
                continue
            if document_id and str(payload.get("document_id")) != str(document_id):
                continue

            v = data["vector"]
            v_norm = np.linalg.norm(v)
            if v_norm > 0:
                v = v / v_norm
            score = float(np.dot(q_vec, v))
            if score >= min_score:
                results.append({"chunk_id": pid, "score": score, "payload": payload})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def delete_by_document(self, user_id: str, document_id: str) -> None:
        """Delete all vectors for a document."""
        client = await self.get_client()
        if client is not None and qmodels is not None:
            try:
                await client.delete(
                    collection_name=self.collection_name,
                    points_selector=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=str(user_id))),
                            qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=str(document_id))),
                        ]
                    ),
                )
            except Exception as exc:
                logger.error("qdrant_delete_failed", error=str(exc))

        # Clean memory fallback
        to_del = [
            pid for pid, data in self._memory_points.items()
            if str(data["payload"].get("user_id")) == str(user_id)
            and str(data["payload"].get("document_id")) == str(document_id)
        ]
        for pid in to_del:
            self._memory_points.pop(pid, None)

    async def delete_points(self, point_ids: list[str]) -> None:
        if not point_ids:
            return

        client = await self.get_client()
        if client is not None and qmodels is not None:
            try:
                await client.delete(
                    collection_name=self.collection_name,
                    points_selector=qmodels.PointIdsList(points=point_ids),
                    wait=True,
                )
            except Exception as exc:
                if settings.is_production:
                    logger.exception("qdrant_stale_point_delete_failed", error=str(exc))
                    raise RuntimeError("Unable to remove stale Qdrant points") from exc
                logger.error("qdrant_stale_point_delete_failed", error=str(exc))
                return
        elif settings.is_production:
            raise RuntimeError("Qdrant is unavailable; cannot safely remove stale vectors")

        for point_id in point_ids:
            self._memory_points.pop(point_id, None)


qdrant_adapter = QdrantAdapter()
