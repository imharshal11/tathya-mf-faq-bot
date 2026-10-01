# Implementation guide (as built)

How Tathya is implemented today, module by module. Use it to understand — or safely change — one part of the pipeline at a time. The project brief is `problem_statement.md`; the design is `architecture.md`.

**Rules when changing anything**

- Never weaken the four safety layers, never lower `SCORE_THRESHOLD` (0.55) or `NOT_FOUND_OVERRIDE_THRESHOLD` (0.80) to make a test pass, never delete eval rows to make them pass.
- `.env` and `corpus/` are not part of a code change (`.env` is gitignored, `corpus/` is a frozen 27 Sep 2026 snapshot).
- After a change, run the eval (see §12) and fix failures before committing.

---

## 1. Repo layout

```
src/
  common.py       # singletons (Chroma client, ONNX embeddings, Groq client) + thresholds
  ingest.py       # corpus -> heading chunks -> ChromaDB (CLI: python -m src.ingest)
  retrieve.py     # scheme detect, fact headings, heading preference, top-k search
  guardrails.py   # Layer 1: PII, greeting/thanks, advice, returns, live data, plan type, other funds, clarify
  intent.py       # Layer 2: one short Groq call that labels ambiguous questions
  generate.py     # Groq answer prompt + extractive fallback
  api.py          # FastAPI routes, pipeline order, Layer 3 + Layer 4, safety net
web/
  index.html, styles.css, app.js   # Chat / Funds / About UI
tests/
  eval_questions.csv, last_failed.txt
scripts/
  run_eval.py     # evaluation runner
corpus/           # 6 markdown files (5 funds + mf-basics)
data/chroma/      # vector store (gitignored)
```

---

## 2. Ingestion — `src/ingest.py`

Run: `python -m src.ingest` (or `POST /index`). Always a **full rebuild**: the collection is dropped and recreated.

1. Load every `corpus/*.md` and parse the HTML-comment front matter: `scheme_name`, `category`, `source_url`, `fetched_date`.
2. Strip the front matter, split the body by `##` headings. One heading = one chunk, prefixed with its heading ("Expense Ratio: …").
3. The `## FAQs` section is special: each `- Q: … A: …` pair becomes its own chunk with heading `FAQ`.
4. ChromaDB embeds the texts automatically with `ONNXMiniLM_L6_V2` (`all-MiniLM-L6-v2` in ONNX, CPU) and stores them with metadata: `chunk_id`, `scheme_name`, `category`, `source_url`, `fetched_date`, `heading`.

Current corpus: **113 chunks** (Large Cap 20, Flexi Cap 20, ELSS 21, Small Cap 20, Balanced Advantage 20, mf-basics 12).

---

## 3. `POST /chat` pipeline — strict order

Implemented in `src/api.py::post_chat`. Every step must run in this order; a hit at any step returns immediately.

```
PII
 -> identity / greeting / thanks
 -> Layer 1 keyword guardrails
 -> Layer 2 AI intent check (ambiguous questions only)
 -> retrieval (heading preference + fund-name augmentation)
 -> score gate (0.55)
 -> Groq answer
 -> Layer 3 answer check
 -> Layer 4 number check
 -> safety net (0.80)
```

### Step 1 — PII (`guardrails.check_pii`)

Regex patterns for PAN, Aadhaar, account numbers, OTP, email, phone, password. First check in the pipeline. Returns:

- title: "Please don't share personal details."
- answer: "For your safety, never share your PAN, Aadhaar, account number, OTP, email, phone number or password."
- `source_url`: AMFI link, `debug.guardrail: "pii"`.

### Step 2 — Identity / greeting / thanks (`check_identity`, `check_greeting`, `check_thanks`)

Short friendly replies, before retrieval and before any AI call. Greetings and thanks only trigger on messages of ~5 words that name no fund and contain no fund-fact keyword (so "exit load?" is never treated as "hi").

- Identity/greeting → "Hi! I'm Tathya. Ask me a fact about any of 5 HDFC mutual funds…" (`guardrail: "greeting"`).
- Thanks → "You're welcome! Ask me anything else about the 5 HDFC funds." (`guardrail: "thanks"`).

### Step 3 — Layer 1 keyword guardrails (`guardrails.check_guardrails`)

| # | Check | Trigger examples | Reply (`debug.guardrail`) |
|---|-------|------------------|---------------------------|
| 1 | Advice keywords | "shall i buy", "can i invest", "worth buying", "buy or not", "best fund" | Advice refusal + AMFI link (`advisory`) |
| 2 | Advice phrases | "should I buy", "which is better", "recommend", "is it safe" | same as above |
| 3 | Returns | "returns", "past performance", "CAGR", "NAV history", "profit" | Returns refusal + HDFC factsheet link (`returns`) |
| 4 | Live data | "NAV", "today", "current price", "live", "right now" | "I don't have live data…" + fund page link (`live_data`) |
| 5 | Plan type | "regular plan", "IDCW", "dividend" | "…only the Direct Plan (Growth option)…" (`plan_type`) |
| 6 | Other funds | "sbi", "icici", "hdfc mid cap fund", … | "I can only answer questions about these 5 HDFC funds…" (`out_of_scope`) |
| 7 | Clarify | a fact keyword with no fund named ("What is the expense ratio?") | "I can help with 5 HDFC funds… Which one?" (`clarify`) |

Notes:

- **How-to exception:** "How can I invest via SIP in HDFC ELSS?" must *not* trigger the advice check — the keyword check exempts questions containing "how" together with "sip", "lump sum", "minimum" or "via".
- **Benchmark exception:** "benchmark" / "performance benchmark" must not trigger the returns check.
- A guardrail hit skips retrieval, the intent check and Groq entirely.

### Step 4 — Layer 2 AI intent check (`intent.classify_intent`)

Only reached when no keyword guardrail fired.

1. Clear fact questions skip the AI call: if the question contains a fund-fact keyword (expense ratio, exit load, sip, minimum, aum, manager, risk, benchmark, lock-in, …, "what is", "how to"), `intent = "FACT"` and `debug.intent = "skipped"`. This keeps common questions fast and inside Groq free-tier limits.
2. Otherwise one short Groq call (`src/intent.py`, same `GROQ_MODEL`, temperature 0, `max_tokens 60`, `reasoning_effort low`) labels the question:
   - **FACT** → continue to retrieval
   - **ADVICE** → advice refusal (`guardrail: "advisory"`, `debug.intent: "ADVICE"`)
   - **RETURNS** → returns refusal (`guardrail: "returns"`)
   - **OFF_TOPIC** → "I can only answer questions about these 5 HDFC funds…" (`guardrail: "out_of_scope"`)
   - **NONSENSE** → "I don't have that information yet…" (`guardrail: "not_found"`)
3. Keyword fast paths inside `classify_intent` catch what the model often misses (personal tax planning, Hinglish advice, obvious off-topic, gibberish) before the API call.
4. Any error or unknown label falls back to `"FACT"` (`debug.intent: "error"`) — the pipeline never crashes.

The active fund (`auto_detected_scheme` or the request's `scheme`) is included in the prompt so follow-ups like "can I buy it?" are understood.

### Step 5 — Retrieval (`retrieve.retrieve_chunks`)

Before retrieval, `api.py` resolves the **active fund**: a fund detected from the question text, else the request's `scheme` (only if it is one of the 5 valid names).

- **Fund-name augmentation (follow-ups):** if a fund is active *and* the question contains a fund-fact keyword, the fund's short name is appended to the query: `"What is the AUM?"` → `"What is the AUM? HDFC Small Cap Fund"`. Otherwise the question is retrieved exactly as asked.
- **Heading preference:** if the question maps to a fact heading (`get_fact_heading`: "expense ratio" → `Expense Ratio`, "sip" → `Minimum SIP`, …) and a fund is known, search `{scheme_name, heading}` first. If nothing scores ≥ 0.55, fall back to a fund-only search.
- **All-funds queries** ("all", "each", "lowest", "highest", "compare"): `retrieve_all_funds_fact` fetches the same heading from each of the 5 funds (1 chunk each), and `api.py` builds a compact list — including a lowest/highest sort when asked.
- **Definitional queries** ("What is SIP?") with no fund search the `Mutual Fund Basics` scheme (`mf-basics.md`).
- Scores are cosine distances converted to similarity (`1 - distance`); only chunks ≥ `SCORE_THRESHOLD` are returned.

### Step 6 — Score gate (0.55)

No chunk above 0.55 → no LLM call. Reply:

> "I don't have that information yet. Try asking about the expense ratio, exit load, minimum SIP, lock-in period, riskometer, benchmark or fund managers."

with empty `source_url` / `fetched_date` and `debug.threshold_passed: false`.

### Step 7 — Groq answer (`generate.generate_answer`)

The top chunk (plus, for exit-load questions, a light text normalization that removes "will be charged for redemption/sale" phrasing) is sent with the question. System prompt rules (`src/generate.py`):

- answer only from the provided chunk, no external knowledge; max 2 sentences
- no advice; no returns or performance numbers; never output URLs
- fund name with plan in brackets; keep every source condition exactly (e.g. "for units above 15% of the investment")
- answer only the fact asked, using the first (most relevant) chunk
- reply exactly `NOT_FOUND` if the chunk does not contain the answer

Call parameters: `temperature 0`, `max_tokens 800`, `reasoning_effort low` (with a `reasoning_format="hidden"` attempt that falls back if unsupported).

**If the call fails** (error, timeout, missing `GROQ_API_KEY`): `generate.extract_answer` returns the best 1–3 sentences from the top chunk by keyword overlap, wording is normalized the same way, and `debug.fallback: true`.

### Step 8 — Layer 3 answer check (`api.py`)

Scan the generated answer for advice language: "you should", "i recommend", "we recommend", "good investment", "worth investing", "yes, you can buy", "yes, you can invest", "suitable for you", "consider investing", "will rise", "will grow", "good choice", "safe bet".

- Hit → answer replaced by "I share facts only…", `title` becomes "I can't give investment advice.", `debug.answer_check: "blocked"`.
- Clean → `debug.answer_check: "ok"`.

### Step 9 — Layer 4 number check (`api.py`)

Find every number in the answer (percentages, ₹ amounts, "N years/crore/lakh", 4-digit years). Each one must appear in the top chunk's text after normalizing commas and spaces.

- Any number missing → answer replaced by the extractive sentence from the source chunk, `debug.number_check: "fallback"`.
- All present → `debug.number_check: "ok"`.

### Step 10 — Safety net (0.80)

- Groq returned `NOT_FOUND` and top score ≥ `0.80` → return the extractive fact sentence from that chunk with `debug.not_found_override: true` (a match that strong clearly contains the answer).
- Groq returned `NOT_FOUND` below 0.80 → the standard "I don't have that information yet…" reply.

**Finally:** wording normalization ("redeemed" → "sold", "redemption" → "sale") and metadata attach — `source_url` and `fetched_date` come from the top chunk's metadata (formatted "27 Sep 2026"), never from the model.

---

## 4. API contract

| Method | Path | Body / returns |
|--------|------|----------------|
| `POST` | `/chat` | `{ "question": str, "scheme": str\|null }` → `{ answer, title, source_url, fetched_date, debug }` |
| `GET` | `/funds` | key facts for the 5 funds, parsed from `corpus/` (expense ratio, exit load, min SIP, lock-in, riskometer, benchmark, AUM, fund managers, source URL, date) |
| `GET` | `/health` | `{ ok, index_exists }` |
| `POST` | `/index` | full index rebuild |
| `GET` | `/` | the UI |

`scheme` must be one of the 5 full scheme names (the UI sends it); anything else is treated as null. Guardrail replies carry their own `title` (or null) and may have an empty `source_url`.

---

## 5. UI — `web/`

Vanilla HTML/CSS/JS, no build step. FastAPI serves it at `/` together with `/styles.css`, `/app.js` and `/brand/*`.

- **Views:** Chat / Funds / About — top nav pill on tablet & desktop, bottom nav on mobile.
- **Chat:** posts `{question, scheme}` to `/chat`; renders answer, one source link, "Last updated from sources: [date]", guardrail titles, and opens the **Source facts panel** (fund facts from `GET /funds` + "Open source page" + disclaimer).
- **Funds:** cards for all 5 funds from `GET /funds` with key facts, **Ask about this fund** (selects the fund, returns to the composer) and a source link.
- **About:** what Tathya does / does not do, funds covered, sources with data date, disclaimer, credits (LinkedIn / GitHub).
- **Fund memory:** the selected fund is stored in UI state and sent as `scheme` on every `/chat` request, so follow-ups like "What is the exit load?" answer for the right fund.
- Responsive breakpoints: dedicated mobile shell (home / chat / funds screens) vs. desktop workspace (sidebar / chat / source panel).

---

## 6. Evaluation — `tests/` + `scripts/run_eval.py`

`tests/eval_questions.csv` — columns `question, expected_type, must_contain, scheme, must_not_contain`.

- **128 questions**, of which **31 are adversarial** (advice traps, jailbreaks, PII, gibberish, off-topic, look-alike funds) — all passing.
- `expected_type` is matched against `debug.guardrail` (or `not_found` / `answer`), plus optional `must_contain` / `must_not_contain` text checks on `title + answer`.

```powershell
.\.venv\Scripts\python scripts\run_eval.py                     # full run (128)
.\.venv\Scripts\python scripts\run_eval.py --quick             # 2-3 rows per expected type
.\.venv\Scripts\python scripts\run_eval.py --failed            # re-run rows in tests/last_failed.txt
.\.venv\Scripts\python scripts/run_eval.py --only "exit load"  # filter by question text
```

The runner uses FastAPI's `TestClient` (in-process — no server needed), waits ~6s between questions for Groq free-tier limits, retries 429s after 30s, and writes failed row numbers to `tests/last_failed.txt`.

---

## 7. Configuration

`.env` (gitignored, see `.env.example`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `GROQ_API_KEY` | Groq key (required for the LLM steps; extractive fallback without it) | — |
| `GROQ_MODEL` | Groq model | `openai/gpt-oss-20b` |
| `CHROMA_PATH` | Vector store | `data/chroma` |
| `CORPUS_PATH` | Corpus folder | `corpus` |
| `COLLECTION_NAME` | Collection | `mf_faq` |
| `TOP_K` | Retrieval k (the chat route passes 1 explicitly) | `1` |
| `SCORE_THRESHOLD` | Score gate — do not lower | `0.55` |
| `NOT_FOUND_OVERRIDE_THRESHOLD` | Safety net for `NOT_FOUND` — do not lower | `0.80` |

---

## 8. Verifying a change

```powershell
# rebuild the index (only if corpus or chunking changed)
.\.venv\Scripts\python -m src.ingest

# smoke test
.\.venv\Scripts\python scripts\run_eval.py --quick

# full suite — must stay 128/128
.\.venv\Scripts\python scripts\run_eval.py

# manual spot checks (against the running app)
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What is the exit load of HDFC Balanced Advantage Fund?\"}"
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"Should I buy HDFC ELSS?\"}"
curl http://127.0.0.1:8000/funds
```

Expected: the exit-load answer keeps the "units above 15% of the investment" condition; the advice question returns the AMFI refusal with `debug.guardrail: "advisory"`; `/funds` returns all 5 funds.

---

## 9. If something regresses

1. Read `debug` in the response — `guardrail`, `intent`, `answer_check`, `number_check`, `fallback`, `not_found_override` and `matches[].score` say exactly which step fired.
2. Re-run the failing rows: `scripts\run_eval.py --failed`.
3. Fix the check or the prompt — **not** the thresholds, and never by deleting eval rows.
