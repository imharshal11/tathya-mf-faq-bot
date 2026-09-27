"""Embed query, top-k similarity search, return chunks + scores."""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv

from src.ingest import (
    get_chroma_client,
    get_embedding_function,
    collection_name,
    chroma_path,
    load_env,
)


def _normalize_score(score: float) -> float:
    """Chroma returns cosine distance; convert to similarity (higher=better)."""
    return 1.0 - score


def retrieve_chunks(query: str, top_k: int | None = None) -> tuple[list[dict], list[float]]:
    """Return (chunks, scores) for the query. Scores are similarities in [0,1]."""
    load_env()
    k = top_k or int(os.getenv("TOP_K", "4"))
    threshold = float(os.getenv("SCORE_THRESHOLD", "0.3"))

    client = get_chroma_client()
    try:
        collection = client.get_collection(
            name=collection_name(),
            embedding_function=get_embedding_function(),
        )
    except Exception:
        return [], []

    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    if not results["ids"] or not results["ids"][0]:
        return [], []

    chunks = []
    scores = []
    for i, chunk_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        dist = results["distances"][0][i]
        sim = _normalize_score(dist)
        if sim >= threshold:
            chunks.append(
                {
                    "chunk_id": meta.get("chunk_id", chunk_id),
                    "source_name": meta.get("source_name", ""),
                    "source_path": meta.get("source_path", ""),
                    "url": meta.get("url", ""),
                    "text": meta.get("text", results["documents"][0][i]),
                }
            )
            scores.append(sim)

    return chunks, scores