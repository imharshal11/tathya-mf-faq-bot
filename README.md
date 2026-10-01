<p align="center">
  <img src="web/brand/wordmark.svg" alt="Tathya" width="220">
</p>

Tathya is a facts-only RAG chatbot that answers questions about 5 HDFC mutual funds — every answer comes with a source link and the date the data was fetched.

**Live demo:** https://tathya-6wiq.onrender.com (free hosting: the first load after ~15 min idle takes about a minute)

**Disclaimer:** Facts-only. No investment advice.

## Features

- **Facts-only answers with source + date.** Every answer cites exactly one source page and shows "Last updated from sources: 27 Sep 2026".
- **Follow-up questions remember the fund.** Select a fund (or send `scheme` with the request) and the next question — "What is the exit load?" — is answered for that fund.
- **Responsive UI (mobile, tablet, desktop).** Bottom nav and full-screen chat on phones, sidebar and panels on desktop, one codebase.
- **Source facts panel.** After an answer, the side panel shows the cited fund's key facts (expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, fund size, managers), an "Open source page" link and the investment disclaimer.
- **Funds page.** Key facts for all 5 funds, each with an **Ask about this fund** button and a link to its source page.
- **About page.** What Tathya does and does not do, the funds covered, all 5 sources with the data date, disclaimer and credits.

## Scope

**AMC:** HDFC Mutual Fund

**Schemes (5), Direct Plan (Growth option) only:**

| Category | Scheme | Source |
|---|---|---|
| Large Cap | HDFC Large Cap Fund - Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi Cap | HDFC Flexi Cap Fund (formerly HDFC Equity Fund) - Direct Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver Fund - Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| Small Cap | HDFC Small Cap Fund - Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Balanced Advantage (Hybrid) | HDFC Balanced Advantage Fund - Direct Growth | https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth |

**Facts covered per scheme:** expense ratio, exit load, minimum SIP, minimum first and additional investment, lock-in (ELSS), riskometer, benchmark, fund size (AUM), fund managers, fund objective, fund house, stamp duty, tax implication, and factual FAQs. Plus a `mf-basics` file for mutual-fund definitions (What is SIP? What is exit load?).

## How safety works

Four layers, in plain words:

**Layer 1 — keyword guardrails** (keyword and pattern checks, no AI involved):

- **PII:** PAN, Aadhaar, account numbers, OTP, email, phone, password → refused, nothing stored. Title: "Please don't share personal details."
- **Advice:** "should I buy / sell / invest", "which is better", "recommend", "best fund" → refused with AMFI's investor education link. Title: "I can't give investment advice."
- **Returns:** "returns", "past performance", "CAGR", "NAV history" → refused with the official HDFC factsheet link. Title: "I can't share returns or performance."
- **Live data:** "NAV", "today", "current price", "live", "right now" → refused with the fund's own page link.
- **Plan type:** "regular plan", "IDCW", "dividend" → clarifies only Direct Plan (Growth option) is covered.
- **Other funds:** other AMCs, or HDFC schemes outside the 5 → refused.

(After PII, identity / greeting / thanks messages get a friendly reply, and a fact question that names no fund asks you to pick one — all still keyword-based.)

**Layer 2 — AI intent check** (only for ambiguous questions): if the question has no clear fund-fact keyword ("expense ratio", "exit load", "SIP", …), one short Groq call labels it FACT / ADVICE / RETURNS / OFF_TOPIC / NONSENSE, and each label gets the matching refusal. Clear fact questions skip this call entirely, which also keeps the app within Groq's free-tier limits. If the call fails, the app falls back to the keyword result.

**Layer 3 — answer check:** after Groq writes the answer, the text is scanned for advice language ("you should", "i recommend", "worth investing", "good choice", …). If any is found, the answer is replaced with the advice refusal.

**Layer 4 — number check:** every number in the answer (percentages, ₹ amounts, years, dates) must also appear in the retrieved source chunk. If one does not, the answer is replaced by the extractive sentence from that source chunk.

**Thresholds:** retrieval score gate **0.55** — below it the reply is "I don't have that information yet. Try asking about the expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark or fund managers." Safety net **0.80** — if Groq replies `NOT_FOUND` but the top match scores 0.80 or higher, the fact sentence from that chunk is returned instead.

## Evaluation

`tests/eval_questions.csv` holds **128 test questions, including 31 adversarial ones** (advice traps, jailbreak attempts, PII, gibberish, off-topic, look-alike funds) — **all passing**.

```powershell
# full run — all 128 questions (~6s apart because of Groq free-tier rate limits)
.\.venv\Scripts\python scripts\run_eval.py

# quick smoke test — 2-3 questions per expected type
.\.venv\Scripts\python scripts\run_eval.py --quick

# re-run only the rows that failed in the last run
.\.venv\Scripts\python scripts\run_eval.py --failed

# run only the questions containing a phrase
.\.venv\Scripts\python scripts\run_eval.py --only "exit load"
```

Failed row numbers are saved to `tests/last_failed.txt` for `--failed`. The script calls the app in-process (FastAPI `TestClient`), so it does not need the server to be running.

## Architecture

| Component | Choice |
|---|---|
| Backend | Python, FastAPI (`src/api.py`) |
| Vector database | ChromaDB (local, cosine similarity, `data/chroma/`) |
| Embeddings | `all-MiniLM-L6-v2` in ONNX (ChromaDB's built-in `ONNXMiniLM_L6_V2`, runs on CPU, no PyTorch) |
| LLM | Groq, `openai/gpt-oss-20b` (temperature 0) — answers and intent classification |
| Frontend | Vanilla HTML/CSS/JS (`web/index.html`, `web/styles.css`, `web/app.js`), served by FastAPI |

**API**

| Method | Path | Body / role |
|---|---|---|
| `POST` | `/chat` | `{ "question": "...", "scheme": "..." }` — `scheme` is optional and keeps follow-ups on the selected fund |
| `GET` | `/funds` | Key facts for all 5 funds (powers the Funds page and the Source facts panel) |
| `GET` | `/health` | Process up, index exists |
| `POST` | `/index` | Full rebuild of the vector index from `corpus/` |
| `GET` | `/` | The UI itself |

**Request pipeline (current order):**

1. **PII check** — refuse and forget.
2. **Identity / greeting / thanks** — short friendly replies.
3. **Keyword guardrails** — advice, returns, live data, plan type, other funds, clarify.
4. **AI intent check** — one Groq call, only for ambiguous questions.
5. **Retrieval** — heading preference (search the fund's chunk for that fact heading first, fall back to fund-only), and for follow-up questions the active fund name is appended to the query when it contains a fund-fact keyword. All-funds questions ("lowest", "each", "compare") pull the same fact from all 5 funds.
6. **Score gate** — best similarity must be ≥ `0.55` (`SCORE_THRESHOLD`).
7. **Groq** — writes a short answer from the top chunk only.
8. **Answer check** — Layer 3, blocks advice language.
9. **Number check** — Layer 4, every number must be in the source chunk.
10. **Safety net** — `NOT_FOUND` with a top score ≥ `0.80` (`NOT_FOUND_OVERRIDE_THRESHOLD`) returns the source sentence instead.

Code (not the LLM) attaches `source_url` and `fetched_date` from the top chunk's metadata. If the Groq call fails (error, timeout, missing key), the best 1-3 sentences from the top chunk are returned instead.

**Response shape:** `{ answer, title, source_url, fetched_date, debug }`

More detail: [architecture.md](architecture.md) and [implementation.md](implementation.md).

### Ingestion

1. **Load:** the 5 Groww pages were fetched once (`scripts/fetch_corpus.py`) and curated into 5 markdown files in `corpus/` (plus `mf-basics.md`), each with front matter: `scheme_name`, `category`, `source_url`, `fetched_date`.
2. **Chunk:** split by markdown heading, so each chunk holds one fact; each FAQ pair is its own chunk (see Chunking Strategy).
3. **Embed + store:** ChromaDB embeds with `all-MiniLM-L6-v2` (ONNX) and saves vectors with metadata (`chunk_id`, `scheme_name`, `category`, `source_url`, `fetched_date`, `heading`) in `data/chroma/`. Every ingest is a full rebuild.

## Chunking Strategy

Each corpus file has one fact per heading (for example, `## Expense Ratio` followed by one sentence), and each FAQ question-answer pair is its own chunk. Splitting by heading makes every chunk exactly one retrievable fact, so retrieval stays precise and citations exact — no overlap needed. Chunks are about 50-300 characters, and each fact sentence repeats the fund name so a chunk still makes sense on its own. The current corpus has **113 chunks across 6 files** (5 funds + mutual-fund basics).

## Setup

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
5. **Start the app:**
```powershell
   .\.venv\Scripts\uvicorn src.api:app --reload --port 8000
```
6. Open http://127.0.0.1:8000 — the API serves the UI (Chat, Funds, About). Endpoints: `GET /health`, `GET /funds`, `POST /index`, `POST /chat`.

## Example Questions

- What is the expense ratio of HDFC Large Cap Fund?
- What is the lock-in period of HDFC ELSS Tax Saver Fund?
- What is the exit load of HDFC Balanced Advantage Fund?
- Who manages HDFC Balanced Advantage Fund?
- What is the benchmark of HDFC Flexi Cap Fund?

More examples with real answers: [SAMPLE_QA.md](SAMPLE_QA.md).

## Deliverables

| File | Contents |
|---|---|
| `README.md` | This file |
| `SOURCE_LIST.md` | The 5 source URLs |
| `SAMPLE_QA.md` | 10 sample queries with actual answers and links |
| `DISCLAIMER.md` | Disclaimer text used in the UI |
| `problem_statement.md` | Project brief |
| `architecture.md` | Design of the running system |
| `implementation.md` | How the pipeline is implemented, module by module |

## Handled Question Types

| Category | Description | Example |
|---|---|---|
| **Scheme-specific facts** | Expense ratio, exit load, SIP, AUM, manager, lock-in, benchmark, riskometer, etc. for a named fund | "What is the expense ratio of HDFC Large Cap Fund?" |
| **Follow-ups with a selected fund** | The fund chosen in the UI (or sent as `scheme`) answers short follow-ups | `{"question": "What is the AUM?", "scheme": "HDFC Small Cap Fund - Direct Growth"}` |
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

- **Platform:** Render Free Plan — live at https://tathya-6wiq.onrender.com
- **Docker:** `Dockerfile` builds the index and pre-downloads the ONNX embedding model at build time for fast cold starts
- **Port:** uses the `PORT` environment variable (Render default), fallback to 7860
- **Sleep:** the service sleeps after ~15 minutes of inactivity; the first request after that takes about a minute

## Known Limits

- **5 HDFC funds, Direct Plan (Growth option) only** — no other AMCs, no other HDFC schemes, no regular/IDCW plans.
- **Data is a snapshot from 27 Sep 2026** taken from public Groww pages (not official AMC, SEBI or AMFI documents). Expense ratio, AUM and fund managers can change over time.
- **No live NAV, returns or performance.** Such questions are refused with a link to the fund page or the official HDFC factsheet.
- **No capital-gains statement steps** — they are not on the 5 source pages, so they are not covered.
- **Groq free tier has rate limits.** If a call fails or is rate-limited, answers come from the extractive fallback (the source chunk itself); the eval waits ~6s between questions for the same reason.
- **Render free plan sleeps after 15 min idle** — first load after idle takes about a minute.
- **Single-session browser chat**, no login, no saved history.
- Extra resource for investors: https://investor.sebi.gov.in/iematerial.html

## Built by

**Harshal S**

- LinkedIn: https://www.linkedin.com/in/imharshal11
- GitHub: https://github.com/imharshal11
