"""Embed query, top-k similarity search with scheme filter, return chunks + scores."""

from __future__ import annotations

import os
import re
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


SCHEME_KEYWORDS = {
    "large cap": "HDFC Large Cap Fund - Direct Growth",
    "flexi cap": "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "equity fund": "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "elss": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "tax saver": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "small cap": "HDFC Small Cap Fund - Direct Growth",
    "balanced advantage": "HDFC Balanced Advantage Fund - Direct Growth",
    "baf": "HDFC Balanced Advantage Fund - Direct Growth",
}


def _normalize_score(score: float) -> float:
    """Chroma returns cosine distance; convert to similarity (higher=better)."""
    return 1.0 - score


def detect_scheme(query: str) -> str | None:
    """Detect scheme from query keywords. Returns scheme_name or None."""
    query_lower = query.lower()
    for keyword, scheme_name in SCHEME_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
            return scheme_name
    return None


def retrieve_chunks(query: str, top_k: int | None = None) -> tuple[list[dict], list[float]]:
    """Return (chunks, scores) for the query. Scores are similarities in [0,1]."""
    load_env()
    k = top_k or int(os.getenv("TOP_K", "6"))
    threshold = float(os.getenv("SCORE_THRESHOLD", "0.35"))

    client = get_chroma_client()
    try:
        coll = client.get_collection(
            name=collection_name(),
            embedding_function=get_embedding_function(),
        )
    except Exception:
        return [], []

    # Detect scheme filter
    scheme_name = detect_scheme(query)
    where_filter = {"scheme_name": scheme_name} if scheme_name else None

    results = coll.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
        where=where_filter,
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
                    "scheme_name": meta.get("scheme_name", ""),
                    "category": meta.get("category", ""),
                    "source_url": meta.get("source_url", ""),
                    "fetched_date": meta.get("fetched_date", ""),
                    "text": meta.get("text", results["documents"][0][i]),
                    "heading": meta.get("heading", ""),
                }
            )
            scores.append(sim)

    return chunks, scores