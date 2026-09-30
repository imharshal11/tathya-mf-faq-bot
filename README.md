---
title: Tathya
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Tathya — HDFC Mutual Fund FAQ Assistant

Tathya (Hindi/Sanskrit for "fact") is a facts-only RAG chatbot. Every answer comes with its source.

A Retrieval-Augmented Generation (RAG) chatbot that answers factual questions about 5 HDFC Mutual Fund schemes using only public Groww pages. Every answer includes one source link and a last-updated date. The assistant provides facts only and never gives investment advice.

**Disclaimer:** Facts-only. No investment advice.

## Scope

**AMC:** HDFC Mutual Fund

**Schemes (5):**

| Category | Scheme | Source |
|---|---|---|
| Large Cap | HDFC Large Cap Fund - Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi Cap | HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver Fund - Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| Small Cap | HDFC Small Cap Fund - Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Balanced Advantage (Hybrid) | HDFC Balanced Advantage Fund - Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

**Facts covered per scheme:** expense ratio, exit load, minimum SIP, minimum first and additional investment, lock-in (ELSS), riskometer, benchmark, fund size (AUM), fund managers, fund objective, fund house, stamp duty, tax implication, and factual FAQs.

## Tech Stack

| Component | Choice |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` (ONNX via ChromaDB, runs on CPU without PyTorch) |
| Vector database | ChromaDB (local, cosine similarity) |
| LLM | Groq, `openai/gpt-oss-20b` (temperature 0) |
| Backend | Python, FastAPI |
| Frontend | Single static HTML/JS page |

## Architecture

### Ingestion Pipeline

1. **Load:** The 5 Groww pages were fetched once (`scripts/fetch_corpus.py`) and curated into 5 markdown files in `corpus/`, one per scheme, with front matter: `scheme_name`, `category`, `source_url`, `fetched_date`.
2. **Chunk:** Split by markdown heading, so each chunk holds one fact (see Chunking Strategy).
3. **Embed:** Convert each chunk to a vector with `all-MiniLM-L6-v2`.
4. **Store:** Save vectors with metadata (`chunk_id`, `scheme_name`, `category`, `source_url`, `fetched_date`, `heading`) in ChromaDB at `data/chroma/`. Every ingest is a full rebuild.

### Retrieval Pipeline

1. **Guardrails (run first):**
   - **PII:** PAN, Aadhaar, account numbers, OTP, email, phone, passwords. Refused, not stored. Title: "Please don't share personal details."
   - **Advice:** "should I buy / sell / invest", "which is better", "recommend", "best fund". Refused with an AMFI investor education link. Title: "I can't give investment advice."
   - **Returns / performance:** "returns", "past performance", "how much return", "CAGR", "NAV history". Refused with the official HDFC factsheet link. Title: "I can't share returns or performance."
   - **Live data:** "NAV", "today", "current price", "live", "right now". Refused with fund page link.
   - **Plan type:** "regular plan", "IDCW", "dividend". Clarifies only Direct Plan (Growth option) covered.
   - **Other funds/AMCs:** Other AMCs or HDFC schemes not in the 5. Refused.
   - **Clarify:** Asks scheme-level fact without naming a fund. Asks user to specify.
   - A guardrail hit skips retrieval and the LLM entirely.
2. **Scheme filter:** Detects the fund in the question ("large cap", "flexi cap" / "equity fund", "elss" / "tax saver", "small cap", "balanced advantage" / "baf") and searches only that fund's chunks.
3. **Retrieve:** Embed the question with the same model and fetch the top 6 chunks (`TOP_K=6`).
4. **Score gate:** If the best similarity is below `0.55` (`SCORE_THRESHOLD`), reply "I don't have that information yet. Try asking about the expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark or fund managers."
5. **Generate:** Groq writes a short answer using only the retrieved chunks: max 3 sentences, no advice, no returns, no URLs, or `NOT_FOUND` if the chunks don't contain the answer.
6. **Cite:** Code (not the LLM) attaches `source_url` and `fetched_date` from the top chunk's metadata.
7. **Fallback:** If the Groq call fails (error, timeout, missing key), the best 1-3 sentences from the top chunk are returned instead.
8. **Safety net:** If Groq replies `NOT_FOUND` but the top match scores 0.80 or higher, the fact sentence from that chunk is returned instead, since such a strong match clearly contains the answer.

**Response format:** `{ answer, title, source_url, fetched_date, debug }`

## Chunking Strategy

Each corpus file has one fact per heading (for example, `## Expense Ratio` followed by one sentence). Splitting by heading makes each chunk exactly one retrievable fact, and each FAQ question-answer pair is its own chunk. This keeps retrieval precise and citations exact, so no overlap is needed. Chunks are about 50-300 characters. Each fact sentence repeats the fund name, so a chunk still makes sense on its own. The current corpus has 101 chunks.

## Setup Steps

1. **Create virtual environment:**
```powershell
   python -m venv .venv
```
2. **Install dependencies:**
```powershell
   .\.venv\Scripts\pip install -r requirements.txt
```
3. **Configure environment:**
```powershell
   copy .env.example .env
```
   Edit `.env` and add your `GROQ_API_KEY` (free at https://console.groq.com). Without it, the extractive fallback is used.
4. **Build the knowledge base:**
```powershell
   .\.venv\Scripts\python -m src.ingest
```
5. **Start the backend** (terminal 1):
```powershell
   .\.venv\Scripts\uvicorn src.api:app --reload --port 8000
```
   Endpoints: `GET /health`, `POST /index`, `POST /chat`.
6. **Start the UI** (terminal 2):
```powershell
   cd web; ..\.venv\Scripts\python -m http.server 5173
```
7. Open http://127.0.0.1:5173. For the debug panel (scores, matched chunks), open http://127.0.0.1:5173/?debug=1.

## Example Questions

- What is the expense ratio of HDFC Large Cap Fund?
- What is the lock-in period of HDFC ELSS Tax Saver Fund?
- What is the exit load of HDFC Small Cap Fund?
- Who manages HDFC Balanced Advantage Fund?
- What is the benchmark of HDFC Flexi Cap Fund?

## Deliverables

| File | Contents |
|---|---|
| `README.md` | This file |
| `SOURCE_LIST.md` | The 5 source URLs |
| `SAMPLE_QA.md` | 10 sample queries with actual answers and links |
| `DISCLAIMER.md` | Disclaimer text used in the UI |
| `problem_statement.md` | Project brief |

## Handled Question Types

The assistant handles the following categories of user questions:

| Category | Description | Example |
|---|---|---|
| **Scheme-specific facts** | Expense ratio, exit load, SIP, AUM, manager, lock-in, benchmark, riskometer, etc. for a named fund | "What is the expense ratio of HDFC Large Cap Fund?" |
| **Name variants** | Recognizes common aliases: "HDFC Top 100" → Large Cap, "HDFC Tax Saver" → ELSS, "BAF" → Balanced Advantage | "Who manages BAF?" |
| **All funds / comparison** | Returns a compact list for all 5 funds when asked "all", "each", "lowest", "highest" | "What are the expense ratios of all funds?" |
| **Definitions** | Explains mutual fund concepts from the knowledge base | "What is expense ratio?" |
| **PII protection** | Refuses questions containing PAN, Aadhaar, email, phone, OTP, passwords. Title: "Please don't share personal details." | "My PAN is ABCDE1234F" |
| **Advisory refusal** | Declines investment advice, recommendations, "which is better". Title: "I can't give investment advice." | "Should I buy HDFC Large Cap?" |
| **Returns refusal** | Declines performance/returns questions. Title: "I can't share returns or performance." | "What are the returns of HDFC Small Cap?" |
| **Live data refusal** | Declines NAV/current price queries, directs to fund page | "What is today's NAV of HDFC Flexi Cap?" |
| **Plan type clarification** | Notes that only Direct Plan (Growth option) data is available | "What about the regular plan?" |
| **Out-of-scope funds** | Declines other AMCs or HDFC schemes not in the 5 | "What about SBI Large Cap Fund?" |
| **Greetings / help** | Friendly intro with example questions. Title: none. | "Hi", "What can you do?" |
| **Clarification** | Asks user to specify a fund when a scheme-level fact is asked without naming one. Title: none. | "What is the expense ratio?" |

## Deployment

- **Platform:** Render Free Plan
- **Memory:** 512 MB RAM
- **Behavior:** Service sleeps after 15 minutes of inactivity; ~1 minute wake-up time on first request after sleep
- **Port:** Uses `PORT` environment variable (Render default), fallback to 7860
- **Model:** ONNX embedding model pre-downloaded at build time for fast cold starts

## Known Limits

- **Sources are Groww.in public pages**, not official AMC, SEBI, or AMFI documents.
- **Data is a snapshot from 2026-09-27.** Expense ratio, AUM, and fund managers can change over time.
- **Fund managers were verified manually** against each Groww page, because the automated extraction initially picked up incorrect names.
- **No performance data** (returns, CAGR, NAV history). Such questions are refused with a link to HDFC factsheets.
- **Capital-gains statement download steps are not covered**, since they are not in the 5 source pages.
- **No live data** (current NAV, prices).
- **Covers 5 schemes, Direct Plan (Growth option) only; no live NAV; AMC-level totals not included.**
- **Single-session browser chat**, no chat history saved, no login.
- **Groq free tier has daily rate limits.** If exceeded, answers use the extractive fallback.
- Extra resource for investors: https://investor.sebi.gov.in/iematerial.html