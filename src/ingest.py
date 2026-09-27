import os
import re
import sys
from pathlib import Path

from src.common import (
    get_chroma_client,
    get_embedding_function,
    get_collection,
    CHROMA_PATH,
    CORPUS_PATH,
    COLLECTION_NAME,
)

# UTF-8 safe console printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FRONT_MATTER_PATTERN = re.compile(r"<!--\s*scheme_name:\s*(.+?)\s*-->")
CATEGORY_PATTERN = re.compile(r"<!--\s*category:\s*(.+?)\s*-->")
SOURCE_URL_PATTERN = re.compile(r"<!--\s*source_url:\s*(.+?)\s*-->")
FETCHED_DATE_PATTERN = re.compile(r"<!--\s*fetched_date:\s*(.+?)\s*-->")

HEADING_PATTERN = re.compile(r"^##\s+(.+)$", re.MULTILINE)
FAQ_PATTERN = re.compile(r"-\s*Q:\s*(.+?)\s*A:\s*(.+?)(?=\n-\s*Q:|\n##|\Z)", re.DOTALL)


def parse_front_matter(content: str) -> dict:
    meta = {}
    m = FRONT_MATTER_PATTERN.search(content)
    if m:
        meta["scheme_name"] = m.group(1).strip()
    m = CATEGORY_PATTERN.search(content)
    if m:
        meta["category"] = m.group(1).strip()
    m = SOURCE_URL_PATTERN.search(content)
    if m:
        meta["source_url"] = m.group(1).strip()
    m = FETCHED_DATE_PATTERN.search(content)
    if m:
        meta["fetched_date"] = m.group(1).strip()
    return meta


def split_by_headings(content: str) -> list[tuple[str, str]]:
    """Split content by ## headings. Returns list of (heading, text)."""
    sections = []
    matches = list(HEADING_PATTERN.finditer(content))
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        if text:
            sections.append((heading, text))
    return sections


def split_faqs(faq_text: str) -> list[tuple[str, str]]:
    """Split FAQ section into individual Q&A pairs. Returns list of (question, answer)."""
    pairs = []
    for match in FAQ_PATTERN.finditer(faq_text):
        q = match.group(1).strip()
        a = match.group(2).strip()
        if q and a:
            pairs.append((q, a))
    return pairs


def chunk_file(filepath: Path) -> list[dict]:
    """Parse one .md file and return list of chunks with metadata."""
    content = filepath.read_text(encoding="utf-8")
    meta = parse_front_matter(content)

    # Remove front matter from content
    body = re.sub(r"<!--.*?-->\n", "", content)
    body = re.sub(r"^# .+\n", "", body).strip()

    chunks = []

    # Split by headings
    sections = split_by_headings(body)
    for heading, text in sections:
        if heading == "FAQs":
            # Split FAQs into individual Q&A chunks
            for q, a in split_faqs(text):
                chunk_text = f"Q: {q}\nA: {a}"
                chunks.append({
                    "text": chunk_text,
                    "heading": "FAQ",
                    "scheme_name": meta.get("scheme_name", ""),
                    "category": meta.get("category", ""),
                    "source_url": meta.get("source_url", ""),
                    "fetched_date": meta.get("fetched_date", ""),
                })
        else:
            chunk_text = f"{heading}: {text}"
            chunks.append({
                "text": chunk_text,
                "heading": heading,
                "scheme_name": meta.get("scheme_name", ""),
                "category": meta.get("category", ""),
                "source_url": meta.get("source_url", ""),
                "fetched_date": meta.get("fetched_date", ""),
            })

    return chunks


def load_env() -> None:
    """Load environment variables from .env file if present."""
    from dotenv import load_dotenv
    load_dotenv()


def rebuild_index() -> dict:
    """Rebuild the Chroma index from corpus files. Called by POST /index."""
    load_env()
    client = get_chroma_client()
    
    # Delete old collection
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    
    # Create collection with embedding function and cosine space
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"}
    )

    # Run the ingestion
    corpus_dir = Path(CORPUS_PATH)
    md_files = list(corpus_dir.glob("*.md"))

    if not md_files:
        return {"status": "error", "message": "No .md files found in corpus/"}

    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")

    all_chunks = []
    chunk_counts = {}

    for md_file in md_files:
        chunks = chunk_file(md_file)
        scheme = chunks[0]["scheme_name"] if chunks else md_file.stem
        chunk_counts[scheme] = len(chunks)
        print(f"  {md_file.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if not all_chunks:
        return {"status": "error", "message": "No chunks generated."}

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Adding chunks to collection (embedding happens automatically)...")

    texts = [c["text"] for c in all_chunks]
    ids = [f"{c['scheme_name'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '')}-{i:03d}" for i, c in enumerate(all_chunks)]
    metadatas = [{
        "chunk_id": ids[i],
        "scheme_name": c["scheme_name"],
        "category": c["category"],
        "source_url": c["source_url"],
        "fetched_date": c["fetched_date"],
        "heading": c["heading"],
    } for i, c in enumerate(all_chunks)]

    # Add in small batches to reduce memory
    BATCH_SIZE = 16
    for i in range(0, len(texts), BATCH_SIZE):
        end = min(i + BATCH_SIZE, len(texts))
        collection.add(ids=ids[i:end], documents=texts[i:end], metadatas=metadatas[i:end])

    print(f"\nIngestion complete. Collection count: {collection.count()}")

    return {
        "status": "ok",
        "chunks": len(all_chunks),
        "chunk_counts": chunk_counts,
        "collection": COLLECTION_NAME,
    }


def ingest():
    """CLI entry point for python -m src.ingest"""
    load_env()
    result = rebuild_index()
    if result.get("status") == "ok":
        print(f"\nIngestion complete. Collection count: {result.get('chunks', 0)}")
        print("\n--- Chunk Details ---")
        collection = get_collection()
        results = collection.get(include=["documents", "metadatas"])
        for i, (doc_id, doc, meta) in enumerate(zip(results["ids"], results["documents"], results["metadatas"])):
            print(f"  {doc_id} | {meta.get('scheme_name', '')} | {doc[:80]}...")


if __name__ == "__main__":
    ingest()