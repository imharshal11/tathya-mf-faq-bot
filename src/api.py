"""FastAPI app with /chat, /index, /health endpoints."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ingest import chroma_path, load_env, rebuild_index
from src.retrieve import retrieve_chunks
from src.generate import generate_answer, extract_answer
from src.guardrails import check_guardrails, GuardrailResult

load_env()

app = FastAPI(title="HDFC Mutual Fund FAQ Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    persist = chroma_path()
    index_exists = persist.exists() and any(persist.iterdir()) if persist.exists() else False
    return {"ok": True, "index_exists": index_exists}


@app.post("/chat", response_model=ChatResponse)
def post_chat(req: ChatRequest) -> ChatResponse:
    # Check if index exists
    persist = chroma_path()
    if not (persist.exists() and any(persist.iterdir())):
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not built. Run POST /index or python -m src.ingest",
        )

    # Guardrails first
    guardrail_result = check_guardrails(req.question)
    if guardrail_result.triggered:
        return ChatResponse(
            answer=guardrail_result.message,
            source_url=guardrail_result.source_url,
            fetched_date=guardrail_result.fetched_date,
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": guardrail_result.type,
                "fallback": False,
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
        # Safety net: if top match score >= 0.80, use extractive fallback
        top_score = scores[0] if scores else 0
        if top_score >= 0.80:
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