"""Generate answers using Groq API with extractive fallback."""

from __future__ import annotations

import re

from src.common import get_groq_client, GROQ_MODEL


SYSTEM_PROMPT = """You are a factual assistant for HDFC Mutual Fund queries.
Answer only from the provided chunks.
Maximum 3 sentences.
No investment advice.
No returns or performance numbers.
Never output URLs.
If the chunks list fund managers, list all their names.
If the chunks do not contain the answer, reply exactly: NOT_FOUND

Write the fund name with the plan in brackets, e.g. HDFC Large Cap Fund (Direct Growth). Use simple, grammatically correct English. Use "crore" not "Cr". Write exit load as "1% if sold within 1 year"."""


def _strip_reasoning(text: str) -> str:
    """Remove reasoning blocks and normalize special characters from model output."""
    # Remove <thinking>...</thinking> blocks
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove ```...``` blocks (reasoning model output)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove 【...】 citation markers sometimes used by reasoning models
    text = re.sub(r"【.*?】", "", text)
    # Normalize special spaces: \u202f (narrow no-break space), \u00a0 (no-break space) -> normal space
    text = text.replace("\u202f", " ").replace("\u00a0", " ")
    # Normalize special dashes: \u2011 (non-breaking hyphen), \u2013 (en dash), \u2014 (em dash) -> "-"
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    return text.strip()


def _build_prompt(chunks: list[dict], question: str) -> str:
    """Build the user prompt with chunks and question."""
    context_lines = ["Context chunks:"]
    for i, ch in enumerate(chunks, start=1):
        context_lines.append(f"[{i}] {ch['text']}")
    context = "\n\n".join(context_lines)
    return f"{context}\n\nQuestion: {question}\n\nAnswer:"


def generate_answer(chunks: list[dict], question: str) -> str:
    """Call Groq API to generate answer from chunks. Returns answer or raises on failure."""
    client = get_groq_client()
    if client is None:
        raise RuntimeError("GROQ_API_KEY not set")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_prompt(chunks, question)},
    ]

    # Base params
    base_params = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 800,
    }

    # Add reasoning_effort for gpt-oss models
    if "gpt-oss" in GROQ_MODEL.lower():
        base_params["reasoning_effort"] = "low"

    # Try with reasoning_format="hidden" if supported
    try:
        params = {**base_params, "reasoning_format": "hidden"}
        resp = client.chat.completions.create(**params)
    except TypeError:
        # Fallback if reasoning_format not supported
        resp = client.chat.completions.create(**base_params)

    answer = resp.choices[0].message.content or ""
    answer = _strip_reasoning(answer)

    # Treat empty/whitespace as failure
    if not answer or not answer.strip():
        raise RuntimeError("Groq returned empty response")

    return answer


def extract_answer(chunk_text: str, question: str) -> str:
    """Extractive fallback: best 1-3 sentences from chunk by keyword overlap with question."""
    # Remove "Heading: " prefix if present
    text = re.sub(r"^[^:]+:\s*", "", chunk_text).strip()

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "Information not available in the knowledge base."

    # Score sentences by keyword overlap with question
    question_words = set(re.findall(r"\b\w+\b", question.lower()))
    stopwords = {"the", "a", "an", "is", "of", "in", "for", "to", "and", "or", "what", "how", "much", "many", "who", "which", "when", "where", "why", "my", "your", "his", "her", "its", "our", "their", "this", "that", "these", "those", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "can", "may", "might", "must", "shall"}
    question_keywords = {w for w in question_words if w not in stopwords and len(w) > 2}

    scored = []
    for sent in sentences:
        sent_words = set(re.findall(r"\b\w+\b", sent.lower()))
        overlap = len(question_keywords & sent_words)
        scored.append((overlap, sent))

    # Sort by overlap descending, take top 3
    scored.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [s for _, s in scored[:3]]

    # If no overlap, just take first 3 sentences
    if not top_sentences or all(o == 0 for o, _ in scored[:3]):
        top_sentences = sentences[:3]

    return " ".join(top_sentences)