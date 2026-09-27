"""Embed query, top-k similarity search with scheme filter, return chunks + scores."""

from __future__ import annotations

import os
import re

from src.common import get_collection
from src.ingest import load_env


SCHEME_KEYWORDS = {
    "large cap": "HDFC Large Cap Fund - Direct Growth",
    "flexi cap": "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "equity fund": "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "elss": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "tax saver": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "small cap": "HDFC Small Cap Fund - Direct Growth",
    "balanced advantage": "HDFC Balanced Advantage Fund - Direct Growth",
    "baf": "HDFC Balanced Advantage Fund - Direct Growth",
    # Name variants
    "top 100": "HDFC Large Cap Fund - Direct Growth",
    "top100": "HDFC Large Cap Fund - Direct Growth",
    "hdfc top": "HDFC Large Cap Fund - Direct Growth",
    "largecap": "HDFC Large Cap Fund - Direct Growth",
    "large-cap": "HDFC Large Cap Fund - Direct Growth",
    "flexicap": "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "flexi-cap": "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "taxsaver": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "smallcap": "HDFC Small Cap Fund - Direct Growth",
    "small-cap": "HDFC Small Cap Fund - Direct Growth",
    "prudence": "HDFC Balanced Advantage Fund - Direct Growth",
    # Hindi/Hinglish variants
    "lockin": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "lock in": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "kitna": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "lockin kitna": "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
}

ALL_FUNDS = [
    "HDFC Large Cap Fund - Direct Growth",
    "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth",
    "HDFC ELSS Tax Saver Fund - Direct Plan Growth",
    "HDFC Small Cap Fund - Direct Growth",
    "HDFC Balanced Advantage Fund - Direct Growth",
]

FACT_HEADINGS = {
    "expense ratio": "Expense Ratio",
    "expense ratios": "Expense Ratio",
    "exit load": "Exit Load",
    "minimum sip": "Minimum SIP",
    "minimum first investment": "Minimum First Investment",
    "minimum additional investment": "Minimum Additional Investment",
    "sip": "Minimum SIP",
    "aum": "Fund Size (AUM)",
    "fund size": "Fund Size (AUM)",
    "assets under management": "Fund Size (AUM)",
    "benchmark": "Benchmark",
    "riskometer": "Riskometer",
    "risk": "Riskometer",
    "manager": "Fund Manager",
    "manages": "Fund Manager",
    "lock-in": "Lock-in Period",
    "lock in": "Lock-in Period",
    "stamp duty": "Stamp Duty",
    "tax": "Tax Implication",
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


def is_all_funds_query(query: str) -> bool:
    """Check if query asks for all funds or comparison (lowest/highest)."""
    query_lower = query.lower()
    patterns = [
        r"\ball\b", r"\beach\b", r"\bevery\b", r"5\s+funds?",
        r"\blowest\b", r"\bhighest\b", r"\bcompare\b", r"\bcomparison\b",
    ]
    for pattern in patterns:
        if re.search(pattern, query_lower):
            return True
    return False


def is_definitional_query(query: str) -> bool:
    """Check if query asks for definition of a concept."""
    query_lower = query.lower().strip()
    patterns = [
        r"^what\s+is\b",
        r"^what\s+does\b",
        r"^meaning\s+of\b",
        r"^define\b",
        r"^explain\b",
    ]
    for pattern in patterns:
        if re.search(pattern, query_lower):
            return True
    return False


def get_fact_heading(query: str) -> str | None:
    """Extract the fact heading from query (e.g., 'expense ratio' -> 'Expense Ratio')."""
    query_lower = query.lower()
    for keyword, heading in FACT_HEADINGS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
            return heading
    return None


def retrieve_chunks(query: str, top_k: int | None = None, scheme_name: str | None = None) -> tuple[list[dict], list[float]]:
    """Return (chunks, scores) for the query. Scores are similarities in [0,1]."""
    load_env()
    k = top_k or int(os.getenv("TOP_K", "6"))
    threshold = float(os.getenv("SCORE_THRESHOLD", "0.40"))

    try:
        coll = get_collection()
    except Exception:
        return [], []

    # Detect scheme filter (use explicit scheme_name if provided, otherwise auto-detect)
    auto_scheme = detect_scheme(query)
    effective_scheme = scheme_name or auto_scheme
    all_funds_query = is_all_funds_query(query)
    definitional_query = is_definitional_query(query)

    # For definitional queries with no scheme, search mf-basics
    if definitional_query and not effective_scheme and not all_funds_query:
        where_filter = {"scheme_name": "Mutual Fund Basics"}
    # For all-funds queries, we'll fetch per scheme below
    elif all_funds_query:
        where_filter = None
    else:
        where_filter = {"scheme_name": effective_scheme} if effective_scheme else None

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


def retrieve_all_funds_fact(query: str) -> tuple[list[dict], list[float]]:
    """Retrieve a specific fact (e.g., expense ratio) for all 5 funds."""
    load_env()
    threshold = float(os.getenv("SCORE_THRESHOLD", "0.40"))

    try:
        coll = get_collection()
    except Exception:
        return [], []

    fact_heading = get_fact_heading(query)
    if not fact_heading:
        return [], []

    all_chunks = []
    all_scores = []

    for scheme in ALL_FUNDS:
        where_filter = {
            "$and": [
                {"scheme_name": scheme},
                {"heading": fact_heading},
            ]
        }
        results = coll.query(
            query_texts=[query],
            n_results=1,
            include=["documents", "metadatas", "distances"],
            where=where_filter,
        )

        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i]
                dist = results["distances"][0][i]
                sim = _normalize_score(dist)
                if sim >= threshold:
                    all_chunks.append(
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
                    all_scores.append(sim)

    return all_chunks, all_scores