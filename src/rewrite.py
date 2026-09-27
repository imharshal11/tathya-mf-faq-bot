"""Query rewriting for follow-up questions (FR-10)."""

from __future__ import annotations

import os
import re
from typing import Any

from openai import OpenAI


AMBIGUOUS_PATTERNS = [
    r"\b(those?|these?|that|this|it|they|them|their)\b",
    r"\b(what about|how about|and)\b",
    r"\b(more|other|another)\b",
    r"^\s*(and|but|so|then)\b",
]


def needs_rewrite(question: str, history: list[dict]) -> bool:
    """Check if question likely needs rewriting based on ambiguity markers."""
    if not history:
        return False
    q = question.lower().strip()
    for pat in AMBIGUOUS_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return True
    return False


def build_rewrite_prompt(question: str, history: list[dict]) -> str:
    """Build prompt to rewrite follow-up into standalone query."""
    # Take last 3 turns max
    recent = history[-3:]
    turns = []
    for turn in recent:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            turns.append(f"User: {content}")
        elif role == "assistant":
            turns.append(f"Assistant: {content[:200]}...")

    history_str = "\n".join(turns) if turns else "(no prior context)"

    return f"""Rewrite the follow-up question into a standalone search query that captures the full intent.
Use the conversation history for context. Keep it concise.

History:
{history_str}

Follow-up question: {question}

Standalone query:"""


def rewrite_query(question: str, history: list[dict]) -> str | None:
    """Rewrite ambiguous follow-up into standalone query using LLM."""
    if not needs_rewrite(question, history):
        return None

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")

    if not api_key:
        # Fallback: simple heuristic rewrite - prepend last user question
        last_user = next((t["content"] for t in reversed(history) if t.get("role") == "user"), "")
        if last_user:
            return f"{last_user} {question}"
        return None

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        prompt = build_rewrite_prompt(question, history)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You rewrite follow-up questions into standalone search queries. Output only the rewritten query."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=60,
        )
        rewritten = (resp.choices[0].message.content or "").strip()
        return rewritten if rewritten else None
    except Exception:
        return None