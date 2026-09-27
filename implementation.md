# Implementation guide (phase-wise)

Use this file to drive Cursor **one phase at a time**. Do not ask it to "build the whole app." After each phase, run the **Done when** checks yourself, then paste the next **Cursor prompt**.

**Always attach:** `problem_statement.md` (source of truth). `architecture.md` follows it.

**Rules for every phase**

- Follow `architecture.md` layout, stack, and API shapes. No LLM APIs, no API keys, no Groww APIs, no auth, no scraping.
- Stay inside this phase's file list. Do not start the next phase's work early.
- After coding, tell Cursor to run the phase verification commands and fix failures before stopping.

---

## How to run a phase

1. Open a new Cursor chat (or `/clear`) so prior phases do not pull in extra scope.
2. Paste the **Cursor prompt** for that phase.
3. `@`-mention `architecture.md` and `implementation.md`.
4. When Cursor finishes, execute **Done when**. Only then start the next phase.

---

## Phase 6 — Corpus (5 HDFC scheme files)

**Goal:** Create 5 curated markdown files in `corpus/`, one per scheme from `problem_statement.md` table.

**Create / fill**

- `corpus/hdfc-large-cap.md` — content from https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
- `corpus/hdfc-flexi-cap.md` — content from https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
- `corpus/hdfc-elss.md` — content from https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
- `corpus/hdfc-small-cap.md` — content from https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth
- `corpus/hdfc-balanced-advantage.md` — content from https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth

**Method:** One-time fetch allowed using `requests` + `BeautifulSoup` to retrieve the 5 pages. Save raw HTML to `corpus/raw_*.html` for reference. Then extract factual sections and write clean markdown. **No runtime scraping** — this is a one-time corpus build step.

Each file must include a front-matter comment with `scheme_name`, `category`, `source_url`, `fetched_date` (today's date). Body: include **only sections whose facts are actually present on the page** (e.g., expense ratio, exit load, minimum SIP, ELSS lock-in where applicable, riskometer, benchmark, factsheet/fee page references). Do not invent a "statement download" section if the page doesn't have it. If a page can't be fetched or a field is missing, report it and leave it out. Fallback: if fetching fails, paste raw page text into `corpus/raw_*.txt` and clean manually.

**Do not**

- Write ingestion code
- Scrape at runtime
- Add extra schemes or AMCs
- Invent data not on the page

**Done when**

```text
ls corpus/
# Shows 5 .md files + optional raw_*.html
head -20 corpus/hdfc-large-cap.md
# Shows front-matter + factual content (only sections found on page)
```

### Cursor prompt — Phase 6

```text
Implement Phase 6 only from implementation.md. Read architecture.md sections 3, 4, 5.4, and problem_statement.md §4.

Create 5 markdown files in corpus/ for the 5 HDFC schemes listed in problem_statement.md:
- hdfc-large-cap.md
- hdfc-flexi-cap.md
- hdfc-elss.md
- hdfc-small-cap.md
- hdfc-balanced-advantage.md

One-time fetch allowed with requests + BeautifulSoup. Save raw HTML to corpus/raw_*.html. Extract only factual sections actually present on each page (expense ratio, exit load, minimum SIP, ELSS lock-in if applicable, riskometer, benchmark, factsheet refs). Do NOT require "statement download" in each file. Front-matter: scheme_name, category, source_url, fetched_date. If a page fails or field missing, report and skip — fallback: paste raw text to corpus/raw_*.txt and clean manually.

Do not write any Python code for ingest. Do not implement retrieve, or API.
Stop after listing the 5 files created and showing one file's head.
```

---

## Phase 7 — Chunking + ingest

**Goal:** `src/ingest.py` loads `corpus/`, chunks with overlap, embeds with local all-MiniLM-L6-v2, rebuilds Chroma at `data/chroma/`.

**Create**

- `src/ingest.py` — CLI entry: `python -m src.ingest`
  - Load all `.md` from `CORPUS_PATH`
  - Parse front-matter for `scheme_name`, `category`, `source_url`, `fetched_date`
  - Chunk body text: recursive character splitter (strategy chosen after inspecting Phase 6 corpus; reason documented in README)
  - Embed with `sentence-transformers/all-MiniLM-L6-v2` (local, no API)
  - **Delete and rebuild** Chroma collection at `CHROMA_PATH`
  - Metadata per vector: `chunk_id`, `scheme_name`, `category`, `source_url`, `fetched_date`, `text`
  - Print file count, chunk count, persist path
- `POST /index` in `src/api.py` calls the same rebuild function
- `requirements.txt` additions: `chromadb`, `sentence-transformers`, `python-dotenv`

**Do not**

- Call any LLM
- Build UI
- Incremental upsert logic

**Done when**

```text
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m src.ingest
```

- `data/chroma/` exists and is gitignored
- Re-running ingest succeeds (full rebuild)
- Inspect collection: chunk IDs present, metadata includes scheme_name, category, source_url, fetched_date

### Cursor prompt — Phase 7

```text
Implement Phase 7 only from implementation.md. Read architecture.md sections 3, 4, 5.4, 8, 11, and problem_statement.md.

Build src/ingest.py and wire POST /index:
- Load corpus/*.md, parse front-matter for scheme_name, category, source_url, fetched_date
- Chunk with recursive character splitter (strategy chosen after inspecting Phase 6 corpus; reason in README)
- Embed with sentence-transformers/all-MiniLM-L6-v2 (local)
- Full rebuild Chroma at CHROMA_PATH
- Metadata: chunk_id, scheme_name, category, source_url, fetched_date, text
- CLI: python -m src.ingest prints file count, chunk count, persist path
- POST /index calls same function
- Update requirements.txt

Do not implement retrieve, generate, guardrails, or any frontend.
Do not commit .env or data/chroma.
Stop after ingest runs successfully and summarizes chunk counts per scheme.
```

---

## Phase 8 — Answers + guardrails + chat API

**Goal:** `POST /chat` implements architecture §5.3 and §6. Guardrails first, then retrieve, then Groq generates answer from top chunks. Fallback to extractive ONLY on Groq call failure (error, timeout, missing key). If Groq returns "NOT_FOUND", return "Not in the knowledge base" (no fallback).

**Create**

- `src/guardrails.py`
  - `check_pii(text)` → bool + matched pattern (PAN, Aadhaar, account, OTP, email, phone, password)
  - `check_advisory(text)` → bool (phrases: "should I buy", "should I sell", "should I invest", "which is better", "recommend", "best fund"). Do NOT block plain "buy" or "invest in" (e.g., "minimum amount to invest in HDFC ELSS" must work).
  - `check_returns(text)` → bool (phrases: "returns", "past performance", "how much return", "CAGR", "NAV history"). Do NOT block "growth" (appears in every scheme name).
  - Refusal messages with educational links:
    - Advisory: "I cannot provide investment advice. For investor education, visit AMFI: https://www.mutualfundssahihai.com/en"
    - Returns: "I cannot provide performance data. Refer to the official factsheet: https://www.hdfcfund.com/mutual-funds/factsheets"
    - PII: "Please do not share personal information (PAN, Aadhaar, account numbers, OTP, email, phone, passwords)."
- `src/retrieve.py`
  - `retrieve(query, top_k, threshold)` → list of (chunk_dict, score)
  - Detect scheme in query (keywords: "large cap", "flexi cap", "elss", "small cap", "balanced advantage" — case-insensitive). If found, filter Chroma by `scheme_name` metadata before search.
  - Embed query with same local model
  - Chroma similarity search (with optional where-filter), normalize scores so higher = better
  - Return empty list if best score < threshold
- `src/generate.py`
  - `generate_answer(chunks, question)` → answer string from Groq
    - Build prompt: chunks + question, with rules (answer only from chunks, max 3 sentences, no advice, no returns/performance numbers, never output URLs, reply "NOT_FOUND" if chunks don't contain answer)
    - Call Groq API (`GROQ_API_KEY`, `GROQ_MODEL` from `.env`, temperature 0)
    - Return Groq response or raise on failure
  - `extract_answer(chunk_text, question)` → 1-3 sentences from chunk (fallback heuristic: split into sentences, rank by keyword overlap with question, take top 3)
- `POST /chat` in `src/api.py`
  - Body: `{ "question": "..." }`
  - Pipeline: guardrails → retrieve → score gate → Groq generate → handle response
  - Response handling:
    - Groq returns "NOT_FOUND" → return "Not in the knowledge base" + debug (no fallback)
    - Groq call fails (exception, timeout, missing `GROQ_API_KEY`) → call `extract_answer` on top chunk, attach metadata, set `debug.fallback: true`
    - Groq returns answer → attach `source_url` + `fetched_date` from top chunk metadata
  - Response shape exactly as architecture §10:
    ```json
    {
      "answer": "...",
      "source_url": "...",
      "fetched_date": "...",
      "debug": { "threshold_passed": true, "matches": [...], "guardrail": null, "fallback": false }
    }
    ```
  - Guardrail hit → refusal answer + educational `source_url` + `fetched_date` + `debug.guardrail`
  - Low similarity → "Not in the knowledge base" + `debug.threshold_passed: false` + matches
  - Missing index → 503 with message

**Do not**

- Query rewrite (out of scope)
- Chat UI / debug panel (Phase 9)
- Streaming

**Done when** (with index built)

```text
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What is the expense ratio of HDFC Large Cap Fund?\"}"
# Returns answer + source_url + fetched_date + debug.threshold_passed: true

curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"Should I buy HDFC ELSS?\"}"
# Returns advisory refusal + AMFI link + debug.guardrail: "advisory"

curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What was the return last year?\"}"
# Returns returns refusal + factsheet link + debug.guardrail: "returns"

curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application.json" -d "{\"question\": \"My PAN is ABCDE1234F\"}"
# Returns PII refusal + debug.guardrail: "pii"
```

### Cursor prompt — Phase 8

```text
Implement Phase 8 only from implementation.md. Read architecture.md sections 5.2, 5.3, 6, 7, 8, 9, 10, 12.

Add src/guardrails.py, src/retrieve.py, src/generate.py and POST /chat.
Pipeline order is mandatory: guardrails → retrieve → score gate → Groq generate → handle response.
Guardrails: PII regex, advisory phrases ("should I buy", "should I sell", "should I invest", "which is better", "recommend", "best fund" — NOT plain "buy"/"invest in"), returns phrases ("returns", "past performance", "how much return", "CAGR", "NAV history" — NOT "growth"). Refusals include educational URLs (AMFI: mutualfundssahihai.com/en, HDFC factsheet: hdfcfund.com/mutual-funds/factsheets).
Retrieve: local embeddings, Chroma top-k, score threshold. Detect scheme in query ("large cap", "flexi cap", "elss", "small cap", "balanced advantage") and filter by scheme_name metadata.
Generate: src/generate.py calls Groq (GROQ_API_KEY, GROQ_MODEL from .env, temperature 0) with prompt rules (answer only from chunks, max 3 sentences, no advice, no returns/performance, never output URLs, "NOT_FOUND" if chunks lack answer).
Response handling:
- Groq returns "NOT_FOUND" → return "Not in the knowledge base" + debug (no fallback)
- Groq call fails (exception, timeout, missing GROQ_API_KEY) → extractive fallback (best 1-3 sentences from top chunk by keyword overlap), attach metadata, debug.fallback: true
- Groq returns answer → attach source_url + fetched_date from top chunk metadata
Response JSON must match architecture section 10 exactly (debug.fallback boolean).
Handle missing index, low similarity, guardrails, provider errors as in architecture section 12.

Do not build the web UI, debug panel, or query rewriting.
Do not add any other LLM API calls.
After implementation, run the four example /chat calls above and show outputs.
```

---

## Phase 9 — Chat UI

**Goal:** Browser chat in `web/index.html` calling local API. Welcome line, 3 example questions, disclaimer.

**Create**

- `web/index.html` — single static file (HTML + CSS + JS)
  - Welcome line: "Welcome to the HDFC Mutual Fund FAQ Assistant."
  - Three example questions as clickable chips:
    1. "What is the expense ratio of HDFC Large Cap Fund?"
    2. "What is the ELSS lock-in period?"
    3. "How to download capital gains statement?"
  - Disclaimer: "Facts-only. No investment advice."
  - Chat area: send question → POST /chat → render answer, source link, "Last updated from sources: [date]"
  - Source link opens in new tab
  - Error states: API down, timeout, knowledge base not built
  - CORS enabled on FastAPI for file:// or http://localhost origin
- Update `README.md` with:
  - Setup steps (venv, install, ingest, run API)
  - Scope: HDFC Mutual Fund, 5 schemes (list them)
  - Known limits: corpus from Groww pages not official AMC/SEBI/AMFI; no performance data; no advice

**Do not**

- Debug panel (out of scope)
- Login, routing, component libraries
- Persist chats to disk

**Done when**

- UI + API both running
- Ask "What is the expense ratio of HDFC Large Cap Fund?" → answer + source link + date on screen
- Ask "Should I buy HDFC ELSS?" → refusal + AMFI link
- Kill the API → UI shows error, last user message remains

### Cursor prompt — Phase 9

```text
Implement Phase 9 only from implementation.md. Read architecture.md sections 5.1, 5.2, 12, 13, 14, and problem_statement.md §5.

Build web/index.html (single static file) and enable CORS on FastAPI.
Single-session in-memory chat, no auth.
UI must include: welcome line, 3 example questions (clickable), disclaimer "Facts-only. No investment advice."
Show answer, source link (opens new tab), "Last updated from sources: [date]".
Handle API down, timeout, missing index.
Update README.md with setup steps, scope (HDFC + 5 schemes), known limits.
Do not implement debug panel, routing, user accounts, or extra pages.
Document how to start API and UI in README.md.
```

---

## Phase 10 — Deliverables

**Goal:** Verify all deliverables from `problem_statement.md` §9 exist and work.

**Create / verify**

- Working prototype: API + UI running locally (demo via screen recording or live)
- `SOURCE_LIST.md` — table of 5 URLs with scheme, category, source_url, fetched_date
- `README.md` — updated with setup, scope, known limits (per architecture §13)
- `SAMPLE_QA.md` — 5–10 queries with assistant's answers and links (run through API and capture)
- Disclaimer snippet used in UI (already in `web/index.html`)
- Verify success criteria from `problem_statement.md` §10:
  1. Every answer factually correct and traceable to cited source
  2. Every answer includes one source link and last-updated date
  3. Advisory and PII queries consistently refused
  4. Answers stay within 3 sentences

**Do not**

- Add new features
- Change architecture

**Done when**

```text
# All files exist
ls SOURCE_LIST.md SAMPLE_QA.md README.md web/index.html

# Sample Q&A verified against live API
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What is the exit load of HDFC Small Cap Fund?\"}"
# Check answer ≤ 3 sentences, has source_url, has fetched_date

# Guardrails verified
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What returns can I expect?\"}"
# Returns refusal + factsheet link

# Demo runs end-to-end
```

### Cursor prompt — Phase 10

```text
Implement Phase 10 only from implementation.md. Read architecture.md section 13, problem_statement.md §9 and §10.

Create/verify deliverables:
- SOURCE_LIST.md: table of 5 URLs with scheme, category, source_url, fetched_date
- SAMPLE_QA.md: 5-10 queries run through the live API, capture answer, source_url, fetched_date
- README.md: final version with setup, scope (HDFC + 5 schemes), known limits
- Verify all 4 success criteria from problem_statement.md §10

Do not add new features or change architecture.
Run verification commands and show outputs.
Stop when all deliverables exist and success criteria are met.
```

---

## Phase checklist

| Phase | Deliverable | You should have |
|-------|-------------|-----------------|
| 6 | Corpus | 5 markdown files in `corpus/` |
| 7 | Ingest | `python -m src.ingest` builds Chroma |
| 8 | Chat API | `POST /chat` returns extractive answers + guardrails |
| 9 | UI | `web/index.html` with welcome, 3 examples, disclaimer |
| 10 | Deliverables | SOURCE_LIST.md, SAMPLE_QA.md, README.md, verified success criteria |

---

## If Cursor drifts

Paste this and nothing else:

```text
You went beyond the current phase. Revert or remove anything not listed in that phase of implementation.md. Re-read architecture.md. Do not add features from later phases. No LLM APIs, no API keys, no scraping, no auth.
```