"""Shared singletons: embedding function, Chroma client/collection, Groq client."""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
CORPUS_PATH = os.getenv("CORPUS_PATH", "corpus")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mf_faq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
TOP_K = int(os.getenv("TOP_K", "6"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.55"))
NOT_FOUND_OVERRIDE_THRESHOLD = float(os.getenv("NOT_FOUND_OVERRIDE_THRESHOLD", "0.80"))


_embedding_fn: ONNXMiniLM_L6_V2 | None = None
_chroma_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None
_groq_client: Groq | None = None


def get_embedding_function() -> ONNXMiniLM_L6_V2:
    """Get cached singleton embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = ONNXMiniLM_L6_V2()
    return _embedding_fn


def get_chroma_client() -> chromadb.PersistentClient:
    """Get cached singleton ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PATH, settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_collection() -> chromadb.Collection:
    """Get cached singleton collection (creates if missing)."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        emb_fn = get_embedding_function()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=emb_fn,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def get_groq_client() -> Groq | None:
    """Get cached singleton Groq client (returns None if no API key)."""
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def reset_singletons() -> None:
    """Reset all singletons (for testing)."""
    global _embedding_fn, _chroma_client, _collection, _groq_client
    _embedding_fn = None
    _chroma_client = None
    _collection = None
    _groq_client = None