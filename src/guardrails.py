"""Input guardrails: advice, secrets, empty-retrieval policy."""

from __future__ import annotations

import re


ADVICE_PATTERNS = [
    r"\b(should\s+i\s+(buy|sell|invest))\b",
    r"\b(buy|sell)\s+\w+",  # buy/sell [ticker]
    r"\b(recommend|recommendation)\b.*\b(stock|fund|etf)\b",
    r"\bwhat\s+should\s+i\s+do\b",
    r"\bbest\s+(stock|fund|investment)\b",
]

SECRET_PATTERNS = [
    r"\b(password|passwd|pwd)\b",
    r"\b(otp|one[-\s]?time\s+password)\b",
    r"\b(account\s*(number|no|#)?|acct\s*(num|no|#)?)\b",
    r"\b(pan|aadhaar|aadhar)\b",
    r"\b(cvv|cvc)\b",
    r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # 16-digit card-like
]


def check_guardrails(question: str) -> str | None:
    """Return a refusal message if guardrail triggered, else None."""
    q = question.lower()

    # Advice / buy-sell
    for pat in ADVICE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return (
                "I can't give personalized financial advice or buy/sell recommendations. "
                "I can explain how Groww's products work or share general investing education."
            )

    # Secrets / sensitive input
    for pat in SECRET_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return "Please don't share passwords, OTPs, account numbers, or other sensitive info."

    return None


def refusal_message(query: str, reason: str = "guardrail") -> dict:
    """Build a standard refusal response matching /chat shape."""
    base = {
        "answer": "I can't help with that.",
        "citations": [],
        "debug": {
            "rewritten_query": None,
            "threshold_passed": False,
            "matches": [],
            "guardrail": reason,
        },
    }
    if reason == "advice":
        base["answer"] = (
            "I can't give personalized financial advice or buy/sell recommendations. "
            "I can explain Groww's product features or general investing concepts."
        )
    elif reason == "secret":
        base["answer"] = "Please don't share passwords, OTPs, account numbers, or other sensitive info."
    elif reason == "weak_retrieval":
        base["answer"] = "That isn't covered in the knowledge base."
    return base