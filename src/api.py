"""FastAPI app with /chat, /index, /health, /funds endpoints. Serves web UI at root."""

from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.ingest import load_env, rebuild_index
from src.retrieve import retrieve_chunks, retrieve_all_funds_fact, is_all_funds_query, get_fact_heading, ALL_FUNDS, detect_scheme
from src.generate import generate_answer, extract_answer
from src.guardrails import check_guardrails, GuardrailResult, AMFI_URL, HDFC_FACTSHEET_URL, TODAY_DATE
from src.intent import classify_intent
from src.common import get_collection, COLLECTION_NAME, CORPUS_PATH, TOP_K, SCORE_THRESHOLD, NOT_FOUND_OVERRIDE_THRESHOLD


def format_date(date_str: str) -> str:
    """Format ISO date (YYYY-MM-DD) to '27 Sep 2026' format."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str


# Safe defaults (env vars override)
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - index is built at Docker build time, just verify it exists
    load_env()
    persist = Path(os.getenv("CHROMA_PATH", "data/chroma"))
    if not (persist.exists() and any(persist.iterdir())):
        print("Index not found at startup, building from corpus...")
        rebuild_index()
        print("Index built.")
    yield
    # Shutdown (nothing needed)


load_env()

app = FastAPI(title="Tathya — HDFC Mutual Fund FAQ Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (web UI) - mounted AFTER API routes so they don't override
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    # Serve brand assets
    brand_dir = WEB_DIR / "brand"
    if brand_dir.exists():
        app.mount("/brand", StaticFiles(directory=brand_dir), name="brand")
    
    # Serve individual files at root level
    @app.get("/styles.css")
    async def styles_css():
        return FileResponse(WEB_DIR / "styles.css") if (WEB_DIR / "styles.css").exists() else FileResponse(WEB_DIR / "index.html")
    
    @app.get("/app.js")
    async def app_js():
        return FileResponse(WEB_DIR / "app.js") if (WEB_DIR / "app.js").exists() else FileResponse(WEB_DIR / "index.html")
    
    @app.get("/manifest.json")
    async def manifest_json():
        return FileResponse(WEB_DIR / "manifest.json") if (WEB_DIR / "manifest.json").exists() else FileResponse(WEB_DIR / "index.html")

    @app.get("/")
    async def root():
        return FileResponse(WEB_DIR / "index.html")


class ChatRequest(BaseModel):
    question: str
    scheme: str | None = None


class ChatResponse(BaseModel):
    answer: str
    title: str | None = None
    source_url: str
    fetched_date: str
    debug: dict


class FundManager(BaseModel):
    name: str
    since: str


class FundResponse(BaseModel):
    full_name: str
    display_name: str
    short_name: str
    scheme_name: str
    category: str
    source_url: str
    fetched_date: str
    expense_ratio: str
    exit_load: str
    min_sip: str
    lock_in: str | None
    riskometer: str
    benchmark: str
    aum: str
    fund_managers: list[FundManager]


@app.post("/index")
def post_index() -> dict:
    return rebuild_index()


@app.get("/health")
def health() -> dict:
    persist = Path(os.getenv("CHROMA_PATH", "data/chroma"))
    index_exists = persist.exists() and any(persist.iterdir()) if persist.exists() else False
    return {"ok": True, "index_exists": index_exists}


def _parse_fund_file(filepath: Path) -> FundResponse:
    """Parse a single fund corpus file and return FundResponse."""
    content = filepath.read_text(encoding="utf-8")
    
    # Extract front matter
    scheme_name_match = re.search(r"<!--\s*scheme_name:\s*(.+?)\s*-->", content)
    category_match = re.search(r"<!--\s*category:\s*(.+?)\s*-->", content)
    source_url_match = re.search(r"<!--\s*source_url:\s*(.+?)\s*-->", content)
    fetched_date_match = re.search(r"<!--\s*fetched_date:\s*(.+?)\s*-->", content)
    
    scheme_name = scheme_name_match.group(1).strip() if scheme_name_match else ""
    category = category_match.group(1).strip() if category_match else ""
    source_url = source_url_match.group(1).strip() if source_url_match else ""
    fetched_date = fetched_date_match.group(1).strip() if fetched_date_match else ""
    
    # Parse full name and short name
    # scheme_name like "HDFC Large Cap Fund - Direct Growth" -> full_name "HDFC Large Cap Fund", display_name "HDFC Large Cap Fund (Direct Growth)"
    full_name = scheme_name.replace(" - Direct Growth", "").replace(" - Direct Plan Growth", "").replace("(formerly HDFC Equity Fund)", "").strip()
    full_name = " ".join(full_name.split())
    
    display_name = scheme_name.replace(" - Direct Growth", " (Direct Growth)").replace(" - Direct Plan Growth", " (Direct Growth)").replace("(formerly HDFC Equity Fund)", "").strip()
    display_name = " ".join(display_name.split())
    
    # Short name from category
    short_name = category.replace(" (Hybrid)", "")
    
    # Parse sections
    sections = {}
    heading_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(content))
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        sections[heading] = text
    
    # Extract expense ratio
    expense_ratio = ""
    if "Expense Ratio" in sections:
        match = re.search(r"(\d+(?:\.\d+)?%)", sections["Expense Ratio"])
        expense_ratio = match.group(1) if match else ""
    
    # Extract exit load
    exit_load = ""
    if "Exit Load" in sections:
        text = sections["Exit Load"]
        if "nil" in text.lower() or "zero" in text.lower():
            exit_load = "Nil"
        else:
            # Check for "in excess of X% of the investment" pattern (Balanced Advantage)
            excess_match = re.search(r"in excess of\s+(\d+)%\s+of the investment", text, re.IGNORECASE)
            if excess_match:
                percent = excess_match.group(1)
                # Extract the charge percentage and period
                charge_match = re.search(r"(\d+%)\s+will be charged for redemption within\s+(\d+\s+year)", text, re.IGNORECASE)
                if charge_match:
                    charge_pct = charge_match.group(1)
                    period = charge_match.group(2)
                    exit_load = f"For units above {percent}% of the investment, {charge_pct} if sold within {period}"
                else:
                    # Fallback
                    match = re.search(r"(\d+% if .+?)(?:\.|$)", text, re.IGNORECASE)
                    if match:
                        exit_load = match.group(1).strip()
                    else:
                        match = re.search(r"(\d+%.+?)(?:\.|$)", text)
                        exit_load = match.group(1).strip() if match else text[:100]
            else:
                match = re.search(r"(\d+% if .+?)(?:\.|$)", text, re.IGNORECASE)
                if match:
                    exit_load = match.group(1).strip()
                else:
                    # Fallback
                    match = re.search(r"(\d+%.+?)(?:\.|$)", text)
                    exit_load = match.group(1).strip() if match else text[:100]
    
    # Replace "redeemed"/"redemption" with "sold"/"sale" in exit_load output
    exit_load = exit_load.replace("redeemed", "sold").replace("Redeemed", "Sold")
    exit_load = exit_load.replace("redemption", "sale").replace("Redemption", "Sale")
    
    # Extract min SIP
    min_sip = ""
    if "Minimum SIP" in sections:
        match = re.search(r"(₹?\s*[\d,]+)", sections["Minimum SIP"])
        min_sip = match.group(1).strip() if match else ""
    
    # Extract lock-in
    lock_in = None
    if "Lock-in Period" in sections:
        text = sections["Lock-in Period"]
        # Extract only the duration (e.g., "3 years" or "3 year")
        match = re.search(r"(\d+\s+years?)", text, re.IGNORECASE)
        if match:
            lock_in = match.group(1).strip()
        else:
            lock_in = text[:100]
    
    # Extract riskometer
    riskometer = ""
    if "Riskometer" in sections:
        match = re.search(r"risk level of .+? is (.+?)(?:\.|$)", sections["Riskometer"], re.IGNORECASE)
        riskometer = match.group(1).strip() if match else sections["Riskometer"][:100]
    
    # Extract benchmark
    benchmark = ""
    if "Benchmark" in sections:
        match = re.search(r"benchmark of .+? is (.+?)(?:\.|$)", sections["Benchmark"], re.IGNORECASE)
        benchmark = match.group(1).strip() if match else sections["Benchmark"][:100]
    
    # Extract AUM
    aum = ""
    if "Fund Size (AUM)" in sections:
        match = re.search(r"([\d,]+\.?\d*\s*crore)", sections["Fund Size (AUM)"], re.IGNORECASE)
        aum = f"₹{match.group(1).strip()}" if match else ""
    
    # Extract fund managers
    fund_managers = []
    if "Fund Manager" in sections:
        text = sections["Fund Manager"]
        # Pattern: Name (since Month Year) - match only the manager names
        # The text format: "The fund managers of HDFC Large Cap Fund - Direct Growth are Rahul Baijal (since Jul 2022) and Dhruv Muchhal (since Jun 2023)."
        # We want to match "Rahul Baijal" and "Dhruv Muchhal"
        pattern = r"(?:^|[,\sand])([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(since\s+([A-Za-z]+\s+\d{4})\)"
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            since = match.group(2).strip()
            fund_managers.append(FundManager(name=name, since=since))
    
    # Format fetched_date from YYYY-MM-DD to DD Mon YYYY
    formatted_date = fetched_date
    try:
        from datetime import datetime
        dt = datetime.strptime(fetched_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%d %b %Y")
    except:
        pass
    
    return FundResponse(
        full_name=full_name,
        display_name=display_name,
        short_name=short_name,
        scheme_name=scheme_name,
        category=category,
        source_url=source_url,
        fetched_date=formatted_date,
        expense_ratio=expense_ratio,
        exit_load=exit_load,
        min_sip=min_sip,
        lock_in=lock_in,
        riskometer=riskometer,
        benchmark=benchmark,
        aum=aum,
        fund_managers=fund_managers,
    )


@app.get("/funds", response_model=list[FundResponse])
def get_funds() -> list[FundResponse]:
    """Read the 5 corpus files and return per fund details."""
    corpus_dir = Path(CORPUS_PATH)
    fund_files = [
        "hdfc-large-cap.md",
        "hdfc-flexi-cap.md",
        "hdfc-elss.md",
        "hdfc-small-cap.md",
        "hdfc-balanced-advantage.md",
    ]
    funds = []
    for fname in fund_files:
        filepath = corpus_dir / fname
        if filepath.exists():
            funds.append(_parse_fund_file(filepath))
    return funds


@app.post("/chat", response_model=ChatResponse)
def post_chat(req: ChatRequest) -> ChatResponse:
    # Check if index exists
    persist = Path(os.getenv("CHROMA_PATH", "data/chroma"))
    if not (persist.exists() and any(persist.iterdir())):
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not built. Run POST /index or python -m src.ingest",
        )

    # Guardrails first
    # Use validated scheme for guardrails (invalid schemes treated as null)
    validated_scheme = req.scheme if req.scheme in ALL_FUNDS else None
    guardrail_result = check_guardrails(req.question, explicit_scheme=validated_scheme)
    if guardrail_result.triggered:
        # For guardrails that don't need a link/date, use empty strings
        source_url = guardrail_result.source_url if guardrail_result.source_url else ""
        fetched_date = format_date(guardrail_result.fetched_date) if guardrail_result.fetched_date else ""
        return ChatResponse(
            answer=guardrail_result.message,
            title=guardrail_result.title,
            source_url=source_url,
            fetched_date=fetched_date,
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": guardrail_result.type,
                "fallback": False,
            },
        )

    # AI Intent Check (Layer 2) - after keyword guardrails, before retrieval
    # Determine active fund for context
    auto_scheme = detect_scheme(req.question)
    explicit_scheme = req.scheme
    valid_explicit_scheme = explicit_scheme if explicit_scheme in ALL_FUNDS else None
    active_fund = auto_scheme or valid_explicit_scheme

    # Skip AI intent check for clear fact questions:
    # (a) contains a fund-fact keyword, AND (b) no advisory/returns guardrail triggered
    # (since we're here, no keyword guardrail triggered, so just check fund-fact keyword)
    import re
    fund_fact_keywords = [
        "expense ratio", "expense", "ter", "exit load", "sip", "minimum", "lump sum",
        "aum", "fund size", "manager", "managers", "manages", "who runs",
        "risk", "riskometer", "benchmark", "index", "lock-in", "lockin", "lock in",
        "objective", "category", "fund house", "stamp duty",
        "who manages", "what is", "how to", "how can i",
    ]
    text_lower = req.question.lower()
    has_fund_fact_keyword = any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in fund_fact_keywords)

    if has_fund_fact_keyword:
        intent_label = "FACT"
        debug_intent = "skipped"
    else:
        try:
            intent_label = classify_intent(req.question, active_fund)
            debug_intent = intent_label
        except Exception as e:
            # Classifier failed or rate-limited: log error, fall back to keyword result (FACT)
            intent_label = "FACT"
            debug_intent = "error"

    if intent_label == "ADVICE":
        return ChatResponse(
            answer="I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai.",
            title="I can't give investment advice.",
            source_url=AMFI_URL,
            fetched_date=TODAY_DATE,
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": "advisory",
                "fallback": False,
                "intent": intent_label,
            },
        )
    if intent_label == "RETURNS":
        return ChatResponse(
            answer="Please check the official HDFC factsheet for this information.",
            title="I can't share returns or performance.",
            source_url=HDFC_FACTSHEET_URL,
            fetched_date=TODAY_DATE,
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": "returns",
                "fallback": False,
                "intent": intent_label,
            },
        )
    if intent_label == "OFF_TOPIC":
        return ChatResponse(
            answer="I can only answer questions about these 5 HDFC funds: Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap and Balanced Advantage.",
            source_url="",
            fetched_date="",
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": "out_of_scope",
                "fallback": False,
                "intent": intent_label,
            },
        )
    if intent_label == "NONSENSE":
        return ChatResponse(
            answer="I don't have that information yet. Try asking about the expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark or fund managers.",
            source_url="",
            fetched_date="",
            debug={
                "threshold_passed": False,
                "matches": [],
                "guardrail": "not_found",
                "fallback": False,
                "intent": intent_label,
            },
        )
    # FACT -> continue to retrieval

    def _short_name(scheme_name: str) -> str:
        """Extract short fund name from scheme_name (remove plan suffix and 'formerly')."""
        return " ".join(
            scheme_name.replace(" - Direct Growth", "")
            .replace(" - Direct Plan Growth", "")
            .replace("(formerly HDFC Equity Fund)", "")
            .split()
        )

    # Use the already-determined active_fund from intent check
    scheme_name = active_fund

    # Augment retrieval query with fund name ONLY when question contains a fund-fact keyword
    retrieval_question = req.question
    if scheme_name:
        import re
        fund_fact_keywords = [
            "expense ratio", "expense", "ter", "exit load", "sip", "minimum", "lump sum",
            "aum", "fund size", "manager", "managers", "manages", "who runs",
            "risk", "riskometer", "benchmark", "index", "lock-in", "lockin", "lock in",
            "nav", "objective", "category", "fund house", "stamp duty"
        ]
        text_lower = req.question.lower()
        has_fund_fact_keyword = any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in fund_fact_keywords)
        if has_fund_fact_keyword:
            retrieval_question = f"{req.question} {_short_name(scheme_name)}"

    # Check for all-funds query (comparison or "all funds")
    if is_all_funds_query(req.question):
        chunks, scores = retrieve_all_funds_fact(req.question)
        if chunks:
            # Build compact list answer from chunks
            fact_heading = get_fact_heading(req.question) or "the requested fact"
            
            # Check if this is a "lowest" or "highest" query
            is_lowest = "lowest" in req.question.lower()
            is_highest = "highest" in req.question.lower()
            
            parts = []
            for c in chunks:
                # Extract the value from the chunk text
                text = c["text"]
                import re
                # Different extraction patterns based on fact type
                if fact_heading in ("Expense Ratio", "Exit Load"):
                    # Extract percentage like "1.03%" or "1%"
                    match = re.search(r"(\d+(?:\.\d+)?%)", text)
                    value = match.group(1).strip() if match else ""
                elif fact_heading == "Fund Size (AUM)":
                    # Extract AUM like "39,933.37 crore" or "39,933.37 crore as of ..."
                    match = re.search(r"([\d,]+\.?\d*\s*crore)", text, re.IGNORECASE)
                    if not match:
                        match = re.search(r"([\d,]+\.?\d*)\s*crore", text, re.IGNORECASE)
                    value = match.group(1).strip() if match else ""
                elif fact_heading in ("Minimum SIP", "Minimum First Investment", "Minimum Additional Investment"):
                    # Extract currency amount like "₹500" or "500"
                    match = re.search(r"(₹?\s*[\d,]+)", text)
                    value = match.group(1).strip() if match else ""
                elif fact_heading in ("Benchmark", "Riskometer", "Fund Manager", "Lock-in Period", "Stamp Duty", "Tax Implication"):
                    # Extract the sentence after the heading
                    match = re.search(rf"{re.escape(fact_heading)}:\s*(.+)", text)
                    value = match.group(1).strip() if match else text[:100]
                else:
                    # Generic: extract first percentage/number or first sentence
                    match = re.search(rf"{re.escape(fact_heading)}:\s*(.+)", text)
                    if match:
                        value = match.group(1).strip()[:150]
                    else:
                        value = text[:100]
                
                # Use full fund name with plan in brackets
                scheme_name = c["scheme_name"]
                # Clean up display name: replace plan suffix with brackets, remove "formerly HDFC Equity Fund", collapse spaces
                full_name = scheme_name.replace(" - Direct Growth", " (Direct Growth)").replace(" - Direct Plan Growth", " (Direct Growth)").replace("(formerly HDFC Equity Fund)", "")
                # Collapse multiple spaces to single space
                full_name = " ".join(full_name.split())
                
                if value:
                    parts.append((full_name, value))
            
            if is_lowest or is_highest:
                # Sort by value for lowest/highest
                def parse_value(v):
                    # Try to extract numeric value for sorting
                    if "%" in v:
                        return float(v.replace("%", ""))
                    elif "crore" in v.lower():
                        return float(v.replace("crore", "").replace(",", "").strip())
                    elif "₹" in v:
                        return float(v.replace("₹", "").replace(",", "").strip())
                    return 0
                
                # Sort parts by value
                parts_sorted = sorted(parts, key=lambda x: parse_value(x[1]), reverse=is_highest)
                
                # Get the top fund(s) - check for ties
                top_value = parse_value(parts_sorted[0][1])
                top_funds = [p[0] for p in parts_sorted if parse_value(p[1]) == top_value]
                
                if is_lowest:
                    answer = f"{', '.join(top_funds)} has the lowest {fact_heading.lower()} at {top_value}%."
                else:
                    answer = f"{', '.join(top_funds)} has the highest {fact_heading.lower()} at {top_value}%."
                
                # Add others in sorted order (skip the top ones already mentioned)
                others = [f"{name} {val}" for name, val in parts_sorted if parse_value(val) != top_value]
                if others:
                    answer += f" Others: {', '.join(others)}."
            else:
                # Regular all-funds list
                parts_str = [f"{name} {val}" for name, val in parts]
                answer = f"{fact_heading}: " + ", ".join(parts_str) + "."
            
            # Use first fund's source URL
            source_url = chunks[0]["source_url"] if chunks else ""
            fetched_date = format_date(chunks[0]["fetched_date"]) if chunks else ""
            return ChatResponse(
                answer=answer,
                source_url=source_url,
                fetched_date=fetched_date,
                debug={
                    "threshold_passed": True,
                    "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                    "guardrail": None,
                    "fallback": False,
                    "all_funds": True,
                },
            )

    # Retrieve
    chunks, scores = retrieve_chunks(retrieval_question, scheme_name=scheme_name, top_k=1)
    threshold_passed = len(chunks) > 0

    if not threshold_passed:
        return ChatResponse(
            answer="I don't have that information yet. Try asking about the expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark or fund managers.",
            source_url="",
            fetched_date="",
            debug={
                "threshold_passed": False,
                "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                "guardrail": None,
                "fallback": False,
                "intent": debug_intent,
            },
        )

    # Generate with Groq
    try:
        # Pre-process chunk text for exit load questions to normalize phrasing
        processed_chunks = chunks
        if "exit load" in req.question.lower():
            processed_chunks = []
            for ch in chunks:
                text = ch["text"]
                # Remove "will be charged" phrases
                text = text.replace("will be charged for redemption", "if sold")
                text = text.replace("will be charged for sale", "if sold")
                text = text.replace("will be charged if sold", "if sold")
                text = text.replace("will be charged ", "")
                text = text.replace("will be charged", "")
                processed_chunks.append({**ch, "text": text})
        
        answer = generate_answer(processed_chunks, req.question)
    except Exception as e:
        # Groq call failed - use extractive fallback
        fallback_answer = extract_answer(chunks[0]["text"], req.question)
        fallback_answer = fallback_answer.replace("redeemed", "sold").replace("Redeemed", "Sold")
        fallback_answer = fallback_answer.replace("redemption", "sale").replace("Redemption", "Sale")
        fallback_answer = fallback_answer.replace("for sale", "if sold").replace("For sale", "If sold")
        fallback_answer = fallback_answer.replace("will be charged ", "").replace("will be charged", "")
        top_chunk = chunks[0]
        return ChatResponse(
            answer=fallback_answer,
            source_url=top_chunk["source_url"],
            fetched_date=format_date(top_chunk["fetched_date"]),
            debug={
                "threshold_passed": True,
                "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                "guardrail": None,
                "fallback": True,
                "intent": debug_intent,
                "answer_check": "ok",
                "number_check": "ok",
            },
        )

    # Handle Groq response
    if answer.strip() == "NOT_FOUND":
        # Safety net: if top match score >= NOT_FOUND_OVERRIDE_THRESHOLD, use extractive fallback
        top_score = scores[0] if scores else 0
        if top_score >= NOT_FOUND_OVERRIDE_THRESHOLD:
            fallback_answer = extract_answer(chunks[0]["text"], req.question)
            fallback_answer = fallback_answer.replace("redeemed", "sold").replace("Redeemed", "Sold")
            fallback_answer = fallback_answer.replace("redemption", "sale").replace("Redemption", "Sale")
            fallback_answer = fallback_answer.replace("for sale", "if sold").replace("For sale", "If sold")
            fallback_answer = fallback_answer.replace("will be charged ", "").replace("will be charged", "")
            top_chunk = chunks[0]
            return ChatResponse(
                answer=fallback_answer,
                source_url=top_chunk["source_url"],
                fetched_date=format_date(top_chunk["fetched_date"]),
                debug={
                    "threshold_passed": True,
                    "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                    "guardrail": None,
                    "fallback": True,
                    "not_found_override": True,
                    "intent": debug_intent,
                    "answer_check": "ok",
                    "number_check": "ok",
                },
            )
        return ChatResponse(
            answer="I don't have that information yet. Try asking about the expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark or fund managers.",
            source_url="",
            fetched_date="",
            debug={
                "threshold_passed": True,
                "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
                "guardrail": None,
                "fallback": False,
                "intent": debug_intent,
                "answer_check": "ok",
                "number_check": "ok",
            },
        )

    # Groq returned an answer - attach metadata from top chunk
    # Post-process: replace "redeemed"/"redemption" with "sold" for exit load answers
    answer = answer.replace("redeemed", "sold").replace("Redeemed", "Sold")
    answer = answer.replace("redemption", "sale").replace("Redemption", "Sale")
    answer = answer.replace("for sale", "if sold").replace("For sale", "If sold")
    # Remove "will be charged" phrasing
    answer = answer.replace("will be charged ", "")
    answer = answer.replace("will be charged", "")

    # ANSWER CHECK (Layer 3): block advice language in generated answer
    advice_phrases = [
        "you should", "i recommend", "we recommend", "good investment", "worth investing",
        "yes, you can buy", "yes, you can invest", "suitable for you", "consider investing",
        "will rise", "will grow", "good choice", "safe bet"
    ]
    answer_lower = answer.lower()
    answer_check_blocked = any(phrase in answer_lower for phrase in advice_phrases)
    if answer_check_blocked:
        answer = "I share facts only. To learn more about investing, visit AMFI's Mutual Funds Sahi Hai."
        answer_check_status = "blocked"
        title_override = "I can't give investment advice."
    else:
        answer_check_status = "ok"
        title_override = None

    # NUMBER CHECK (Layer 4): verify every number in answer appears in retrieved chunk
    import re
    top_chunk_text = chunks[0]["text"]
    # Normalize both texts for comparison (remove commas, extra spaces)
    def normalize_num(text: str) -> str:
        return re.sub(r"[\s,]+", "", text.lower())

    chunk_norm = normalize_num(top_chunk_text)
    # Find all numbers in answer: percentages, rupee amounts, years, dates
    number_pattern = re.compile(r"(?:\d+(?:,\d+)*(?:\.\d+)?%|₹\s*\d+(?:,\d+)*(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:years?|crore|lakh)|\d{4})")
    numbers_in_answer = number_pattern.findall(answer)
    number_check_fallback = False
    for num in numbers_in_answer:
        num_norm = normalize_num(num)
        if num_norm not in chunk_norm:
            number_check_fallback = True
            break

    if number_check_fallback:
        fallback_answer = extract_answer(chunks[0]["text"], req.question)
        fallback_answer = fallback_answer.replace("redeemed", "sold").replace("Redeemed", "Sold")
        fallback_answer = fallback_answer.replace("redemption", "sale").replace("Redemption", "Sale")
        fallback_answer = fallback_answer.replace("for sale", "if sold").replace("For sale", "If sold")
        fallback_answer = fallback_answer.replace("will be charged ", "").replace("will be charged", "")
        answer = fallback_answer
        number_check_status = "fallback"
    else:
        number_check_status = "ok"

    top_chunk = chunks[0]
    return ChatResponse(
        answer=answer,
        title=title_override,
        source_url=top_chunk["source_url"],
        fetched_date=format_date(top_chunk["fetched_date"]),
        debug={
            "threshold_passed": True,
            "matches": [{"chunk_id": c["chunk_id"], "score": round(s, 4)} for c, s in zip(chunks, scores)],
            "guardrail": None,
            "fallback": False,
            "intent": debug_intent,
            "answer_check": answer_check_status,
            "number_check": number_check_status,
        },
    )