"""Input guardrails: PII, advisory intent, returns/performance, live data, plan type, other funds, greetings, clarify."""

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
    r"is\s+it\s+good",
    r"is\s+it\s+safe",
    r"\bgood\s+fund\b",
    r"safe\s+to\s+invest",
    r"worth\s+investing",
    r"where\s+should\s+i\s+invest",
    r"where\s+to\s+invest",
    r"which\s+fund\s+should",
    r"\bsuggest\b",
    r"best\s+for",
    r"should\s+i\s+put",
    r"better\s+option",
    r"ignore\s+your\s+rules",
    r"ignore\s+previous",
    r"\bis\b.*\bgood\b",
    r"\bis\b.*\bsafe\b",
]


RETURNS_PHRASES = [
    r"\breturns\b",
    r"past\s+performance",
    r"how\s+much\s+return",
    r"\bcagr\b",
    r"nav\s+history",
    r"\bperformed\b",
    r"\bperformance\b",
    r"how\s+much\s+will\s+i\s+earn",
    r"how\s+much\s+can\s+i\s+earn",
    r"\bprofit\b",
    r"earn\s+in",
    r"gain\s+in",
    r"growth\s+rate",
    r"returns\s+in",
]


LIVE_DATA_PHRASES = [
    r"\bnav\b",
    r"\btoday\b",
    r"current\s+price",
    r"\blive\b",
    r"right\s+now",
]

# Phrases that should NOT trigger returns guardrail (exceptions)
RETURNS_EXCEPTIONS = [
    r"\bperformance\s+benchmark\b",
    r"^benchmark\b",
    r"\bbenchmark\s+(of|for)\b",
]


PLAN_TYPE_PHRASES = [
    r"regular\s+plan",
    r"\bidcw\b",
    r"\bdividend\b",
]


OTHER_AMC_KEYWORDS = [
    "sbi", "icici", "axis", "nippon", "kotak", "mirae", "parag parikh", "uti",
    "aditya birla", "dsp", "quant", "motilal",
]

OTHER_HDFC_SCHEMES = [
    "mid cap", "focused", "index fund", "liquid", "arbitrage", "corporate bond",
    "banking", "psu", "infrastructure", "technology", "pharma", "healthcare",
    "consumption", "esg", "dividend yield",
]


GREETING_PATTERNS = [
    r"^hi\b",
    r"^hello\b",
    r"^hey\b",
    r"^what\s+can\s+you\s+do\b",
    r"^help\b",
]

THANKS_PATTERNS = [
    r"^thanks?\b",
    r"^thank\s+you\b",
    r"^thx\b",
    r"^ok\s+thanks?\b",
]


CLARIFY_FACT_KEYWORDS = [
    "aum", "fund size", "expense ratio", "exit load", "sip", "minimum",
    "benchmark", "riskometer", "risk", "manager", "manages", "lock-in",
    "lock in", "stamp duty", "tax",
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
    # Check exceptions first - if any exception matches, don't trigger returns
    for exception in RETURNS_EXCEPTIONS:
        if re.search(exception, text_lower):
            return False
    for phrase in RETURNS_PHRASES:
        if re.search(phrase, text_lower):
            return True
    return False


def check_live_data(text: str) -> bool:
    """Check for live data requests. Use whole-word matching."""
    text_lower = text.lower()
    for phrase in LIVE_DATA_PHRASES:
        if re.search(phrase, text_lower):
            return True
    return False


def check_plan_type(text: str) -> bool:
    """Check for plan type queries (regular, IDCW, dividend). Use whole-word matching."""
    text_lower = text.lower()
    for phrase in PLAN_TYPE_PHRASES:
        if re.search(phrase, text_lower):
            return True
    return False


def check_other_funds(text: str) -> bool:
    """Check for other AMCs or HDFC schemes not in our 5."""
    text_lower = text.lower()
    for keyword in OTHER_AMC_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            return True
    for scheme in OTHER_HDFC_SCHEMES:
        if re.search(rf"\b{re.escape(scheme)}\b", text_lower):
            return True
    # Also check for "hdfc <name> fund" where name is not our 5
    # This catches things like "hdfc mid cap fund", "hdfc focused fund", etc.
    our_fund_keywords = [
        "large cap", "flexi cap", "equity fund", "elss", "tax saver",
        "small cap", "balanced advantage", "baf", "top 100", "top100",
        "hdfc top", "largecap", "large-cap", "flexicap", "flexi-cap",
        "taxsaver", "smallcap", "small-cap", "prudence",
    ]
    # Check if "hdfc" followed by a fund-like name that's not in our list
    hdfc_match = re.search(r"\bhdfc\s+(.+?)\s+fund\b", text_lower)
    if hdfc_match:
        fund_name = hdfc_match.group(1).strip()
        # Check if this fund name matches any of our known funds
        is_our_fund = False
        for kw in our_fund_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", fund_name):
                is_our_fund = True
                break
        if not is_our_fund:
            return True
    return False


def check_greeting(text: str) -> bool:
    """Check for greetings or help requests. Only trigger on short messages (~5 words or fewer) that don't name a fund or ask a fund fact."""
    text_lower = text.lower().strip()
    words = text_lower.split()
    
    # Check if it's a short message (5 words or fewer)
    if len(words) > 5:
        return False
    
    # Check if it contains a fund name or fund fact keyword - if so, not a greeting
    from src.retrieve import detect_scheme, is_all_funds_query
    scheme_name = detect_scheme(text_lower)
    if scheme_name or is_all_funds_query(text_lower):
        return False
    
    # Check for fund fact keywords
    fact_keywords = ["expense", "aum", "exit load", "sip", "minimum", "benchmark", 
                     "risk", "manager", "lock-in", "lock in", "stamp duty", "tax",
                     "nav", "returns", "performance", "aum", "fund size"]
    for kw in fact_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return False
    
    # Now check greeting patterns
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def check_thanks(text: str) -> bool:
    """Check for thank-you messages. Only trigger on short messages (~5 words or fewer) that don't name a fund or ask a fund fact."""
    text_lower = text.lower().strip()
    words = text_lower.split()
    
    # Check if it's a short message (5 words or fewer)
    if len(words) > 5:
        return False
    
    # Check if it contains a fund name or fund fact keyword - if so, not a thanks
    from src.retrieve import detect_scheme, is_all_funds_query
    scheme_name = detect_scheme(text_lower)
    if scheme_name or is_all_funds_query(text_lower):
        return False
    
    # Check for fund fact keywords
    fact_keywords = ["expense", "aum", "exit load", "sip", "minimum", "benchmark", 
                     "risk", "manager", "lock-in", "lock in", "stamp duty", "tax",
                     "nav", "returns", "performance", "aum", "fund size"]
    for kw in fact_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return False
    
    # Now check thanks patterns
    for pattern in THANKS_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def check_clarify_needed(text: str, scheme_name: str | None) -> bool:
    """Check if question asks a scheme-level fact but no scheme detected."""
    if scheme_name:
        return False
    text_lower = text.lower()
    # Exception: if question says "all", "each", "every", "5 funds", "lowest", "highest"
    exception_patterns = [
        r"\ball\b", r"\beach\b", r"\bevery\b", r"5\s+funds?",
        r"\blowest\b", r"\bhighest\b",
    ]
    for pattern in exception_patterns:
        if re.search(pattern, text_lower):
            return False
    for keyword in CLARIFY_FACT_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            return True
    return False


def check_guardrails(question: str, explicit_scheme: str | None = None) -> GuardrailResult:
    """Run all guardrails in order. Returns GuardrailResult."""
    # 1. PII check
    pii_found, pii_type = check_pii(question)
    if pii_found:
        return GuardrailResult(
            triggered=True,
            type="pii",
            message="Please do not share personal information (PAN, Aadhaar, account numbers, OTP, email, phone, passwords).",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # 2. Advisory check
    if check_advisory(question):
        return GuardrailResult(
            triggered=True,
            type="advisory",
            message="I cannot provide investment advice. For investor education, please visit AMFI's Mutual Funds Sahi Hai.",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # 3. Returns/performance check
    if check_returns(question):
        return GuardrailResult(
            triggered=True,
            type="returns",
            message="I cannot provide performance or returns data. Please refer to the official HDFC factsheet.",
            source_url=HDFC_FACTSHEET_URL,
            fetched_date=TODAY_DATE,
        )

    # 4. Live data check
    if check_live_data(question):
        # Try to detect scheme for link (use explicit if provided)
        from src.retrieve import detect_scheme
        scheme_name = explicit_scheme or detect_scheme(question)
        source_url = HDFC_FACTSHEET_URL
        if scheme_name:
            # Find the source URL from our corpus
            scheme_urls = {
                "HDFC Large Cap Fund - Direct Growth": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
                "HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
                "HDFC ELSS Tax Saver Fund - Direct Plan Growth": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
                "HDFC Small Cap Fund - Direct Growth": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
                "HDFC Balanced Advantage Fund - Direct Growth": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
            }
            source_url = scheme_urls.get(scheme_name, HDFC_FACTSHEET_URL)
        return GuardrailResult(
            triggered=True,
            type="live_data",
            message="I don't have live data such as today's NAV. Please check the scheme page for the latest value.",
            source_url=source_url,
            fetched_date=TODAY_DATE,
        )

    # 5. Plan type check
    if check_plan_type(question):
        return GuardrailResult(
            triggered=True,
            type="plan_type",
            message="My data covers only the Direct Plan - Growth option of these 5 HDFC schemes.",
            source_url="",
            fetched_date="",
        )

    # 6. Other funds/AMCs check
    if check_other_funds(question):
        return GuardrailResult(
            triggered=True,
            type="out_of_scope",
            message="I only cover 5 HDFC Mutual Fund schemes: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, and Balanced Advantage.",
            source_url="",
            fetched_date="",
        )

    # 7. Greeting check
    if check_greeting(question):
        return GuardrailResult(
            triggered=True,
            type="greeting",
            message="Hello! I can answer factual questions about 5 HDFC Mutual Fund schemes (Direct Plan - Growth). For example: 'What is the expense ratio of HDFC Large Cap Fund?' or 'What is the lock-in period of HDFC ELSS Tax Saver Fund?'",
            source_url="",
            fetched_date="",
        )

    # 8. Thanks check
    if check_thanks(question):
        return GuardrailResult(
            triggered=True,
            type="thanks",
            message="You're welcome! Ask me anything else about the 5 HDFC funds.",
            source_url="",
            fetched_date="",
        )

    # 9. Clarify check (no scheme named but asks scheme-level fact)
    from src.retrieve import detect_scheme
    scheme_name = explicit_scheme or detect_scheme(question)
    if check_clarify_needed(question, scheme_name):
        return GuardrailResult(
            triggered=True,
            type="clarify",
            message="I cover 5 HDFC Mutual Fund schemes: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, and Balanced Advantage. Please mention one, for example: 'What is the AUM of HDFC Large Cap Fund?'",
            source_url="",
            fetched_date="",
        )

    return GuardrailResult(
        triggered=False,
        type=None,
        message="",
        source_url="",
        fetched_date="",
    )