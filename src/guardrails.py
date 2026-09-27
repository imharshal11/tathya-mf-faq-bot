"""Input guardrails: PII, advisory intent, returns/performance queries."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    triggered: bool
    type: str | None
    message: str
    source_url: str
    fetched_date: str


AMFI_URL = "https://www.mutualfundssahihai.com/en"
HDFC_FACTSHEET_URL = "https://www.hdfcfund.com/mutual-funds/factsheets"
TODAY_DATE = "2026-09-27"


PII_PATTERNS = [
    (r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", "PAN"),
    (r"\b\d{4}\s?\d{4}\s?\d{4}\b", "Aadhaar"),
    (r"\b\d{9,18}\b", "account_number"),
    (r"\b\d{6}\b", "OTP"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
    (r"\b(?:\+91|0)?[6-9]\d{9}\b", "phone"),
    (r"\bpassword\b", "password"),
]


ADVISORY_PHRASES = [
    r"should\s+i\s+buy",
    r"should\s+i\s+sell",
    r"should\s+i\s+invest",
    r"which\s+is\s+better",
    r"\brecommend\b",
    r"\bbest\s+fund\b",
]


RETURNS_PHRASES = [
    r"\breturns\b",
    r"past\s+performance",
    r"how\s+much\s+return",
    r"\bCAGR\b",
    r"NAV\s+history",
]


def check_pii(text: str) -> tuple[bool, str | None]:
    """Check for PII in text. Returns (found, matched_type)."""
    for pattern, ptype in PII_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, ptype
    return False, None


def check_advisory(text: str) -> bool:
    """Check for advisory intent phrases."""
    text_lower = text.lower()
    for phrase in ADVISORY_PHRASES:
        if re.search(phrase, text_lower):
            return True
    return False


def check_returns(text: str) -> bool:
    """Check for returns/performance phrases."""
    text_lower = text.lower()
    for phrase in RETURNS_PHRASES:
        if re.search(phrase, text_lower):
            return True
    return False


def check_guardrails(question: str) -> GuardrailResult:
    """Run all guardrails. Returns GuardrailResult."""
    # PII check
    pii_found, pii_type = check_pii(question)
    if pii_found:
        return GuardrailResult(
            triggered=True,
            type="pii",
            message="Please do not share personal information (PAN, Aadhaar, account numbers, OTP, email, phone, passwords).",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # Advisory check
    if check_advisory(question):
        return GuardrailResult(
            triggered=True,
            type="advisory",
            message="I cannot provide investment advice. For investor education, please visit AMFI's Mutual Funds Sahi Hai.",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # Returns/performance check
    if check_returns(question):
        return GuardrailResult(
            triggered=True,
            type="returns",
            message="I cannot provide performance or returns data. Please refer to the official HDFC factsheet.",
            source_url=HDFC_FACTSHEET_URL,
            fetched_date=TODAY_DATE,
        )

    return GuardrailResult(
        triggered=False,
        type=None,
        message="",
        source_url="",
        fetched_date="",
    )