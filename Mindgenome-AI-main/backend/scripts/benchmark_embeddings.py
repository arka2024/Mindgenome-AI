from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from app.services.embedding_service import EmbeddingService


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = []
    with path.open(encoding="utf-8") as dataset:
        for line_number, line in enumerate(dataset, start=1):
            if not line.strip():
                continue
            case = json.loads(line)
            if (
                not isinstance(case.get("query"), str)
                or not isinstance(case.get("candidates"), list)
                or not isinstance(case.get("relevant_indices"), list)
                or not case["candidates"]
            ):
                raise ValueError(f"Invalid benchmark case on line {line_number}")
            if any(index < 0 or index >= len(case["candidates"]) for index in case["relevant_indices"]):
                raise ValueError(f"Relevant candidate index is out of range on line {line_number}")
            cases.append(case)
    if not cases:
        raise ValueError("Benchmark dataset is empty")
    return cases


def evaluate_model(
    model_name: str,
    version: str,
    dimension: int,
    cases: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    if model_name == "gemini-embedding-001":
        service = EmbeddingService(model_name=model_name, version=version, dimension=dimension)
        embed_documents = service.embed_documents
        embed_query = service.embed_query
    else:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Install the evaluation extra with "
                "`pip install -e .[dev]` to benchmark the MiniLM baseline"
            ) from exc

        model = SentenceTransformer(model_name)
        def embed_documents(texts: list[str]) -> list[list[float]]:
            return model.encode(
                texts,
                normalize_embeddings=True,
                truncate_dim=dimension,
                convert_to_numpy=True,
                show_progress_bar=False,
            ).tolist()

        def embed_query(text: str) -> list[float]:
            return model.encode(
                [text],
                normalize_embeddings=True,
                truncate_dim=dimension,
                convert_to_numpy=True,
                show_progress_bar=False,
            )[0].tolist()

        service = None

    recall_hits = 0
    reciprocal_rank_sum = 0.0
    started_at = time.perf_counter()
    try:
        for case in cases:
            candidate_vectors = np.asarray(embed_documents(case["candidates"]))
            query_vector = np.asarray(embed_query(case["query"]))
            scores = candidate_vectors @ query_vector
            ranking = np.argsort(scores)[::-1]
            relevant = set(case["relevant_indices"])
            first_relevant_rank = next(
                (rank for rank, candidate_index in enumerate(ranking, start=1) if candidate_index in relevant),
                None,
            )
            if first_relevant_rank is not None and first_relevant_rank <= top_k:
                recall_hits += 1
            if first_relevant_rank is not None:
                reciprocal_rank_sum += 1.0 / first_relevant_rank
    finally:
        if service is not None:
            service.close()

    return {
        "model": model_name,
        "version": version,
        "dimensions": dimension,
        "recall_at_k": recall_hits / len(cases),
        "mrr": reciprocal_rank_sum / len(cases),
        "elapsed_seconds": round(time.perf_counter() - started_at, 3),
        "queries": len(cases),
        "top_k": top_k,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare MiniLM and Gemini retrieval ranking on a labeled JSONL dataset."
    )
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be at least 1")
    cases = load_cases(args.dataset)
    results = [
        evaluate_model(
            "sentence-transformers/all-MiniLM-L6-v2",
            "minilm_l6_v2",
            384,
            cases,
            args.top_k,
        ),
        evaluate_model(
            "gemini-embedding-001",
            "gemini_embedding_001_v1",
            768,
            cases,
            args.top_k,
        ),
    ]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
