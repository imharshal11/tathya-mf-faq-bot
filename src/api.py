"""FastAPI app with /chat, /index, /health endpoints."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ingest import chroma_path, load_env, rebuild_index
from src.retrieve import retrieve_chunks
from src.generate import chat_response
from src.guardrails import check_guardrails
from src.rewrite import rewrite_query

load_env()

app = FastAPI(title="Groww RAG Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    history: list[dict] | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]
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

    history = req.history or []

    # Guardrails first
    guardrail = check_guardrails(req.question)
    if guardrail:
        if "advice" in guardrail.lower() or "buy" in guardrail.lower() or "sell" in guardrail.lower():
            reason = "advice"
        else:
            reason = "secret"
        return chat_response(req.question, [], [], False, guardrail=reason)

    # Query rewrite for follow-ups
    rewritten = rewrite_query(req.question, history)
    search_query = rewritten or req.question

    # Retrieve using rewritten (or original) query
    chunks, scores = retrieve_chunks(search_query)
    threshold_passed = len(chunks) > 0

    # Generate response (pass original question to LLM, not rewritten)
    resp = chat_response(
        req.question,
        chunks,
        scores,
        threshold_passed,
        rewritten_query=rewritten,
    )
    return resp