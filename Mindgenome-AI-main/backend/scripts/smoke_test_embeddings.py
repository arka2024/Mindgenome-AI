from __future__ import annotations

import argparse
import asyncio
import uuid

from app.adapters.qdrant import qdrant_adapter
from app.services.embedding_service import embedding_service


async def main() -> None:
    qdrant_client = await qdrant_adapter.get_client()
    if qdrant_client is None:
        raise RuntimeError(
            "Qdrant is unavailable; refusing to run the embedding smoke test against memory fallback"
        )

    probe_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())
    document_text = "Gradient descent updates model parameters to reduce the loss function."
    inserted = False
    try:
        document_vector = await asyncio.to_thread(
            embedding_service.embed_documents,
            [document_text],
        )
        query_vector = await asyncio.to_thread(
            embedding_service.embed_query,
            "How does gradient descent reduce loss?",
        )
        await qdrant_adapter.upsert_points(
            [
                {
                    "id": probe_id,
                    "vector": document_vector[0],
                    "payload": {
                        "user_id": user_id,
                        "document_id": document_id,
                        "chunk_id": probe_id,
                        "page_start": 1,
                        "page_end": 1,
                        "text": document_text,
                        "embedding_model": embedding_service.model_name,
                        "embedding_version": embedding_service.version,
                        "embedding_dimension": embedding_service.dimension,
                    },
                }
            ]
        )
        inserted = True
        hits = await qdrant_adapter.search_points(
            user_id=user_id,
            query_vector=query_vector,
            top_k=1,
            min_score=0.0,
            document_id=document_id,
        )
        if not hits or hits[0]["chunk_id"] != probe_id:
            raise RuntimeError("The test vector was not returned by the configured Qdrant collection")
        print(
            "Embedding and Qdrant smoke test passed: "
            f"model={embedding_service.model_name}, "
            f"version={embedding_service.version}, "
            f"dimension={embedding_service.dimension}, "
            f"score={hits[0]['score']:.4f}"
        )
    finally:
        if inserted:
            await qdrant_adapter.delete_points([probe_id])
        embedding_service.close()


if __name__ == "__main__":
    argparse.ArgumentParser(
        description="Verify Gemini embeddings and real Qdrant insertion/retrieval."
    ).parse_args()
    asyncio.run(main())
