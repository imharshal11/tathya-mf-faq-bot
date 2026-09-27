"""FastAPI app with /chat, /index, /health endpoints. Serves web UI at root."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.ingest import load_env, rebuild_index
from src.retrieve import retrieve_chunks, retrieve_all_funds_fact, is_all_funds_query, get_fact_heading
from src.generate import generate_answer, extract_answer
from src.guardrails import check_guardrails, GuardrailResult
from src.common import get_collection, COLLECTION_NAME


# Safe defaults (env vars override)
TOP_K = int(os.getenv("TOP_K", "6"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.40"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - index is built at Docker build time, just verify it exists
    load_env()
    persist = Path(os.getenv("CHROMA_PATH", "data/chroma"))
    if not (persist.exists() and any(persist.iterdir())):
        print("Index not found at startup, building from corpus...")
        rebuild_index()
        print("Index built.")
    yield
    # Shutdown (nothing needed)


load_env()

app = FastAPI(title="Tathya — HDFC Mutual Fund FAQ Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (web UI) - mounted AFTER API routes so they don't override
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/")
    async def root():
        return FileResponse(WEB_DIR / "index.html")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    source_url: str
    fetched_date: str
    debug: dict


@app.post("/index")
def post_index() -> dict:
    return rebuild_index()


@app.get("/health")
def health() -> dict:
    persist = Path(os.getenv("CHROMA_PATH", "data/chroma"))
    index_exists = persist.exists() and any(persist.iterdir()) if persist.exists() else False
    return {"ok": True, "index_exists": index_exists}


@app.post("/chat", response_model=ChatResponse)
def post_chat(req: ChatRequest) -> ChatResponse:
    # Check if index exists
    persist = Path(os.getenv("CHROMA_PATH", "data/chroma"))
    if not (persist.exists() and any(persist.iterdir())):
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not built. Run POST /index or python -m src.ingest",
        )

    # Guardrails first
    guardrail_result = check_guardrails(req.question)
    if guardrail_result.triggered:
        # For guardrails that don't need a link/date, use empty strings
        source_url = guardrail_result.source_url if guardrail_result.source_url else ""
        fetched_date = guardrail_result.fetched_date if guardrail_result.fetched_date else ""
        return ChatResponse(
            answer=guardrail_result.message,
            source_url=source_url,
            fetched_date=fetched_date,
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": guardrail_result.type,
                "fallback": False,
            },
        )

    # Check for all-funds query (comparison or "all funds")
    if is_all_funds_query(req.question):
        chunks, scores = retrieve_all_funds_fact(req.question)
        if chunks:
            # Build compact list answer from chunks
            fact_heading = get_fact_heading(req.question) or "the requested fact"
            parts = []
            for c in chunks:
                # Extract the value from the chunk text
                text = c["text"]
                import re
                # Different extraction patterns based on fact type
                if fact_heading in ("Expense Ratio", "Exit Load"):
                    # Extract percentage like "1.03%" or "1%"
                    match = re.search(r"(\d+(?:\.\d+)?%)", text)
                    value = match.group(1).strip() if match else ""
                elif fact_heading == "Fund Size (AUM)":
                    # Extract AUM like "39,933.37 crore" or "39,933.37 crore as of ..."
                    match = re.search(r"([\d,]+\.?\d*\s*crore)", text, re.IGNORECASE)
                    if not match:
                        match = re.search(r"([\d,]+\.?\d*)\s*crore", text, re.IGNORECASE)
                    value = match.group(1).strip() if match else ""
                elif fact_heading in ("Minimum SIP", "Minimum First Investment", "Minimum Additional Investment"):
                    # Extract currency amount like "₹500" or "500"
                    match = re.search(r"(₹?\s*[\d,]+)", text)
                    value = match.group(1).strip() if match else ""
                elif fact_heading in ("Benchmark", "Riskometer", "Fund Manager", "Lock-in Period", "Stamp Duty", "Tax Implication"):
                    # Extract the sentence after the heading
                    match = re.search(rf"{re.escape(fact_heading)}:\s*(.+)", text)
                    value = match.group(1).strip() if match else text[:100]
                else:
                    # Generic: extract first percentage/number or first sentence
                    match = re.search(rf"{re.escape(fact_heading)}:\s*(.+)", text)
                    if match:
                        value = match.group(1).strip()[:150]
                    else:
                        value = text[:100]
                short_name = c["scheme_name"].replace("HDFC ", "").replace(" - Direct Growth", "").replace(" - Direct Plan Growth", "").replace("(formerly HDFC Equity Fund)", "").strip()
                if value:
                    parts.append(f"{short_name} {value}")
            answer = f"{fact_heading}: " + ", ".join(parts) + "."
            # Use first fund's source URL
            source_url = chunks[0]["source_url"] if chunks else ""
            fetched_date = chunks[0]["fetched_date"] if chunks else ""
            return ChatResponse(
                answer=answer,
                source_url=source_url,
                fetched_date=fetched_date,
                debug={
                    "threshold_passed": True,
                    "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                    "guardrail": None,
                    "fallback": False,
                    "all_funds": True,
                },
            )

    # Retrieve
    chunks, scores = retrieve_chunks(req.question)
    threshold_passed = len(chunks) > 0

    if not threshold_passed:
        return ChatResponse(
            answer="Not in the knowledge base",
            source_url="",
            fetched_date="",
            debug={
                "threshold_passed": False,
                "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                "guardrail": None,
                "fallback": False,
            },
        )

    # Generate with Groq
    try:
        answer = generate_answer(chunks, req.question)
    except Exception as e:
        # Groq call failed - use extractive fallback
        fallback_answer = extract_answer(chunks[0]["text"], req.question)
        top_chunk = chunks[0]
        return ChatResponse(
            answer=fallback_answer,
            source_url=top_chunk["source_url"],
            fetched_date=top_chunk["fetched_date"],
            debug={
                "threshold_passed": True,
                "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                "guardrail": None,
                "fallback": True,
            },
        )

    # Handle Groq response
    if answer.strip() == "NOT_FOUND":
        # Safety net: if top match score >= 0.70, use extractive fallback
        top_score = scores[0] if scores else 0
        if top_score >= 0.70:
            fallback_answer = extract_answer(chunks[0]["text"], req.question)
            top_chunk = chunks[0]
            return ChatResponse(
                answer=fallback_answer,
                source_url=top_chunk["source_url"],
                fetched_date=top_chunk["fetched_date"],
                debug={
                    "threshold_passed": True,
                    "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                    "guardrail": None,
                    "fallback": True,
                    "not_found_override": True,
                },
            )
        return ChatResponse(
            answer="Not in the knowledge base",
            source_url="",
            fetched_date="",
            debug={
                "threshold_passed": True,
                "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                "guardrail": None,
                "fallback": False,
            },
        )

    # Groq returned an answer - attach metadata from top chunk
    top_chunk = chunks[0]
    return ChatResponse(
        answer=answer,
        source_url=top_chunk["source_url"],
        fetched_date=top_chunk["fetched_date"],
        debug={
            "threshold_passed": True,
            "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
            "guardrail": None,
            "fallback": False,
        },
    )