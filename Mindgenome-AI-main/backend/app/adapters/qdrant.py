from __future__ import annotations

import math
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
        self.collection_name = getattr(settings, "QDRANT_COLLECTION", "mindgenome_chunks")
        self.dim = 384
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
                    # Create payload index for user_id
                    await self._client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name="user_id",
                        field_schema=qmodels.PayloadSchemaType.KEYWORD,
                    )
            except Exception as exc:
                logger.warning("qdrant_client_failed_using_memory_fallback", error=str(exc))
                self._client = None
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
                logger.error("qdrant_upsert_failed_saving_to_memory", error=str(exc))

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
        client = await self.get_client()
        if client is not None and qmodels is not None:
            try:
                must_conditions = [
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=str(user_id)),
                    )
                ]
                if document_id:
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=str(document_id)),
                        )
                    )

                search_result = await client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=qmodels.Filter(must=must_conditions),
                    limit=top_k,
                    score_threshold=min_score,
                )

                return [
                    {
                        "chunk_id": str(r.id),
                        "score": float(r.score),
                        "payload": r.payload,
                    }
                    for r in search_result
                ]
            except Exception as exc:
                logger.error("qdrant_search_failed_falling_back_to_memory", error=str(exc))

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


qdrant_adapter = QdrantAdapter()
