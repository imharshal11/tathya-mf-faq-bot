"""Input guardrails: PII, advisory intent, returns/performance, live data, plan type, other funds, greetings, clarify."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    triggered: bool
    type: str | None
    title: str | None
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

ADVISORY_KEYWORDS = [
    "shall i buy",
    "shall i invest",
    "shall invest",
    "can i buy",
    "can i invest",
    "should i buy",
    "should i invest",
    "should i start",
    "is it worth",
    "worth buying",
    "good time to invest",
    "good time to buy",
    "buy or not",
    "invest or not",
    "should i put",
    "can i put money",
]

ADVISORY_EXCEPTION_KEYWORDS = [
    "how",
    "sip",
    "lump sum",
    "minimum",
    "via",
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

# Exceptions for live data: prediction questions about NAV should not trigger live_data
LIVE_DATA_EXCEPTIONS = [
    r"will.*nav.*rise",
    r"will.*nav.*go",
    r"nav.*rise",
    r"nav.*go\s+up",
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

IDENTITY_PATTERNS = [
    r"who are you",
    r"what are you",
    r"what is tathya",
    r"how do you work",
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


def check_advisory_keywords(text: str) -> bool:
    """Check for advisory keywords (whole-word, case-insensitive).
    Exception: if question is a factual how-to (contains 'how' as in 'how can i', 'how to', 'how do i')
    combined with 'sip', 'lump sum', 'minimum', or 'via', do NOT trigger."""
    text_lower = text.lower()
    
    # Check for how-to exception: question must be a genuine how-to question
    # (contains "how" as in "how can i", "how to", "how do i") AND one of the other exception keywords
    how_to_patterns = [
        r"\bhow\s+can\s+i\b",
        r"\bhow\s+to\b",
        r"\bhow\s+do\s+i\b",
        r"^how\b",
    ]
    is_how_to = any(re.search(pattern, text_lower) for pattern in how_to_patterns)
    
    if is_how_to:
        for exc in ["sip", "lump sum", "minimum", "via"]:
            if re.search(rf"\b{re.escape(exc)}\b", text_lower):
                return False
    
    # Check advisory keywords
    for keyword in ADVISORY_KEYWORDS:
        # Whole-word match with word boundaries
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            return True
    
    # Also check with "it" and "this fund"
    it_patterns = [
        r"\bcan i buy it\b",
        r"\bcan i invest in it\b",
        r"\bshould i buy it\b",
        r"\bshould i invest in it\b",
        r"\bshall i buy it\b",
        r"\bshall i invest in it\b",
        r"\bis it worth buying it\b",
        r"\bworth buying it\b",
        r"\bbuy or not it\b",
        r"\binvest or not it\b",
        r"\bcan i put money in it\b",
        r"\bshould i put money in it\b",
        r"\bcan i buy this fund\b",
        r"\bcan i invest in this fund\b",
        r"\bshould i buy this fund\b",
        r"\bshould i invest in this fund\b",
        r"\bshall i buy this fund\b",
        r"\bshall i invest in this fund\b",
        r"\bis this fund worth buying\b",
        r"\bworth buying this fund\b",
        r"\bbuy or not this fund\b",
        r"\binvest or not this fund\b",
    ]
    for pattern in it_patterns:
        if re.search(pattern, text_lower):
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
    # Check exceptions first
    for exception in LIVE_DATA_EXCEPTIONS:
        if re.search(exception, text_lower):
            return False
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


def check_identity(text: str) -> bool:
    """Check for identity/help questions. Checked BEFORE retrieval and before any AI check."""
    text_lower = text.lower().strip()
    for pattern in IDENTITY_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def check_greeting(text: str) -> bool:
    """Check for greetings or help requests. Only trigger on short messages (~5 words or fewer) that don't name a fund or ask a fund fact."""
    import re
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
    import re
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
            title="Please don't share personal details.",
            message="For your safety, never share your PAN, Aadhaar, account number, OTP, email, phone number or password.",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # 2. Identity/Help check (BEFORE retrieval and before any AI check)
    if check_identity(question):
        return GuardrailResult(
            triggered=True,
            type="greeting",
            title=None,
            message="Hi! I'm Tathya. Ask me a fact about any of 5 HDFC mutual funds, for example: \"What is the expense ratio of HDFC Large Cap Fund?\"",
            source_url="",
            fetched_date="",
        )

    # 3. Greeting check
    if check_greeting(question):
        return GuardrailResult(
            triggered=True,
            type="greeting",
            title=None,
            message="Hi! I'm Tathya. Ask me a fact about any of 5 HDFC mutual funds, for example: \"What is the expense ratio of HDFC Large Cap Fund?\"",
            source_url="",
            fetched_date="",
        )

    # 4. Thanks check
    if check_thanks(question):
        return GuardrailResult(
            triggered=True,
            type="thanks",
            title=None,
            message="You're welcome! Ask me anything else about the 5 HDFC funds.",
            source_url="",
            fetched_date="",
        )

    # 5. Advisory keywords check (new specific keywords)
    if check_advisory_keywords(question):
        return GuardrailResult(
            triggered=True,
            type="advisory",
            title="I can't give investment advice.",
            message="I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai.",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # 4. Advisory phrases check
    if check_advisory(question):
        return GuardrailResult(
            triggered=True,
            type="advisory",
            title="I can't give investment advice.",
            message="I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai.",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
        )

    # 5. Returns/performance check
    if check_returns(question):
        return GuardrailResult(
            triggered=True,
            type="returns",
            title="I can't share returns or performance.",
            message="Please check the official HDFC factsheet for this information.",
            source_url=HDFC_FACTSHEET_URL,
            fetched_date=TODAY_DATE,
        )

    # 6. Live data check
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
            title=None,
            message="I don't have live data, such as today's NAV. Please check the fund's page for the latest value.",
            source_url=source_url,
            fetched_date=TODAY_DATE,
        )

    # 7. Plan type check
    if check_plan_type(question):
        return GuardrailResult(
            triggered=True,
            type="plan_type",
            title=None,
            message="My information covers only the Direct Plan (Growth option) of these 5 funds.",
            source_url="",
            fetched_date="",
        )

    # 8. Other funds/AMCs check
    if check_other_funds(question):
        return GuardrailResult(
            triggered=True,
            type="out_of_scope",
            title=None,
            message="I can only answer questions about these 5 HDFC funds: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap and Balanced Advantage.",
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
            title=None,
            message="I can help with 5 HDFC funds: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap and Balanced Advantage. Which one would you like to know about? For example: \"What is the AUM of HDFC Large Cap Fund?\"",
            source_url="",
            fetched_date="",
        )

    return GuardrailResult(
        triggered=False,
        type=None,
        title=None,
        message="",
        source_url="",
        fetched_date="",
    )