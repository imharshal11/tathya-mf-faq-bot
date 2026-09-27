"""Build prompt, call LLM, parse answer with citations."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from src.guardrails import refusal_message


SYSTEM_PROMPT = """You are a helpful assistant for Groww educational queries.
Answer only from the provided context.
If context is missing or irrelevant, say the knowledge base does not cover it.
No personalized financial advice; no account actions.
Educational demo, not official Groww support.
Cite sources by source_name / chunk_id that actually appear in context."""


def _build_context(chunks: list[dict]) -> str:
    lines = ["Context chunks:"]
    for i, ch in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] chunk_id={ch['chunk_id']} source={ch['source_name']}\n{ch['text']}"
        )
    return "\n\n".join(lines)


def _call_llm(messages: list[dict[str, str]]) -> str:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def generate_answer(question: str, chunks: list[dict]) -> tuple[str, list[dict]]:
    """Return (answer_text, citations_list)."""
    if not chunks:
        return "That isn't covered in the knowledge base.", []

    context = _build_context(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\n{context}"},
    ]

    try:
        answer = _call_llm(messages)
    except Exception:
        return "Service temporarily unavailable. Please try again.", []

    # Extract citations from chunks that were provided
    citations = []
    for ch in chunks:
        citations.append(
            {
                "chunk_id": ch["chunk_id"],
                "source_name": ch["source_name"],
                "source_path": ch["source_path"],
                "excerpt": ch["text"][:200],
            }
        )

    return answer, citations


def chat_response(
    question: str,
    chunks: list[dict],
    scores: list[float],
    threshold_passed: bool,
    guardrail: str | None = None,
    rewritten_query: str | None = None,
) -> dict[str, Any]:
    """Build the full /chat response object per architecture §10."""
    if guardrail:
        return refusal_message(question, guardrail)

    if not threshold_passed or not chunks:
        return refusal_message(question, "weak_retrieval")

    answer, citations = generate_answer(question, chunks)

    return {
        "answer": answer,
        "citations": citations,
        "debug": {
            "rewritten_query": rewritten_query,
            "threshold_passed": threshold_passed,
            "matches": [
                {"chunk_id": ch["chunk_id"], "score": round(sc, 4)}
                for ch, sc in zip(chunks, scores)
            ],
        },
    }