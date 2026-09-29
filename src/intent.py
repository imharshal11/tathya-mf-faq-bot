"""AI intent classifier using Groq."""

from __future__ import annotations

import time
from src.common import get_groq_client, GROQ_MODEL


INTENT_PROMPT = """Classify the user's question into exactly ONE of these labels:

FACT - asks a factual attribute of one of the 5 HDFC funds (Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage), a factual comparison (e.g. "lowest expense ratio"), or a mutual fund basics definition
ADVICE - should/can/shall I buy or invest; is it good/safe/worth it/suitable; which is better; what should I choose; predictions ("will it go up", "will NAV rise"); personal financial or tax planning ("how much tax will I save", "for my retirement"); role-play or rule-breaking ("pretend you are an advisor", "ignore your rules", "as a friend what would you buy"); Hinglish ("kharidu kya", "invest karu", "accha fund hai")
RETURNS - returns, performance, growth, CAGR, NAV history, "how much did it give/grow"
OFF_TOPIC - not about these 5 HDFC funds or mutual fund basics
NONSENSE - gibberish

If a question mixes a fact and advice, label ADVICE.

Active fund context: {active_fund}

Reply with exactly one label: FACT, ADVICE, RETURNS, OFF_TOPIC, or NONSENSE."""


VALID_LABELS = {"FACT", "ADVICE", "RETURNS", "OFF_TOPIC", "NONSENSE"}


def classify_intent(question: str, active_fund: str | None = None) -> str:
    """Classify question intent using Groq. Returns one of: FACT, ADVICE, RETURNS, OFF_TOPIC, NONSENSE.
    Falls back to 'FACT' on any error."""
    client = get_groq_client()
    if client is None:
        return "FACT"

    fund_context = active_fund or "none specified"
    prompt = INTENT_PROMPT.format(active_fund=fund_context)

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]

    params = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 10,
    }

    if "gpt-oss" in GROQ_MODEL.lower():
        params["reasoning_effort"] = "low"

    try:
        resp = client.chat.completions.create(**params)
        label = (resp.choices[0].message.content or "").strip().upper()
        if label in VALID_LABELS:
            return label
    except Exception:
        pass

    return "FACT"