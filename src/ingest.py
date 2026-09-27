"""Load corpus markdown, chunk, embed, and fully rebuild the Chroma collection."""

from __future__ import annotations

import os
import re
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import (
    OpenAIEmbeddingFunction,
    SentenceTransformerEmbeddingFunction,
)
from dotenv import load_dotenv

COLLECTION_NAME_DEFAULT = "groww_rag"
# ~625 tokens at ~4 chars/token; ~14% overlap (architecture §8).
CHUNK_SIZE_CHARS = 2500
CHUNK_OVERLAP_CHARS = 350


def load_env() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def corpus_path() -> Path:
    raw = os.getenv("CORPUS_PATH", "corpus")
    path = Path(raw)
    return path if path.is_absolute() else project_root() / path


def chroma_path() -> Path:
    raw = os.getenv("CHROMA_PATH", "data/chroma")
    path = Path(raw)
    return path if path.is_absolute() else project_root() / path


def collection_name() -> str:
    return os.getenv("CHROMA_COLLECTION", COLLECTION_NAME_DEFAULT)


def get_embedding_function():
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
    if api_key:
        kwargs = {"api_key": api_key, "model_name": model}
        if base_url:
            kwargs["api_base"] = base_url
        return OpenAIEmbeddingFunction(**kwargs)
    return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def get_chroma_client() -> chromadb.PersistentClient:
    persist = chroma_path()
    persist.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist))


def _slug(stem: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug or "doc"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def load_markdown_files(root: Path) -> list[tuple[Path, str]]:
    if not root.is_dir():
        raise FileNotFoundError(f"Corpus folder not found: {root}")
    files = sorted(root.glob("*.md"))
    loaded: list[tuple[Path, str]] = []
    for path in files:
        loaded.append((path, path.read_text(encoding="utf-8")))
    return loaded


def rebuild_index() -> dict:
    load_env()
    corpus = corpus_path()
    persist = chroma_path()
    name = collection_name()

    documents = load_markdown_files(corpus)
    ids: list[str] = []
    documents_text: list[str] = []
    metadatas: list[dict] = []

    for path, raw in documents:
        slug = _slug(path.stem)
        source_name = path.stem.replace("-", " ").replace("_", " ").title()
        rel = path.relative_to(project_root()).as_posix()
        for i, chunk in enumerate(chunk_text(raw), start=1):
            chunk_id = f"{slug}-{i:03d}"
            ids.append(chunk_id)
            documents_text.append(chunk)
            metadatas.append(
                {
                    "chunk_id": chunk_id,
                    "source_name": source_name,
                    "source_path": rel,
                    "url": "",
                    "text": chunk,
                }
            )

    client = get_chroma_client()
    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(
        name=name,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    if ids:
        collection.add(ids=ids, documents=documents_text, metadatas=metadatas)

    result = {
        "file_count": len(documents),
        "chunk_count": len(ids),
        "persist_path": str(persist),
        "collection": name,
    }
    return result


def main() -> None:
    result = rebuild_index()
    print(f"files:     {result['file_count']}")
    print(f"chunks:    {result['chunk_count']}")
    print(f"persist:   {result['persist_path']}")
    print(f"collection:{result['collection']}")


if __name__ == "__main__":
    main()
