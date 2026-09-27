# Implementation guide (phase-wise)

Use this file to drive Cursor **one phase at a time**. Do not ask it to “build the whole app.” After each phase, run the **Done when** checks yourself, then paste the next **Cursor prompt**.

**Always attach:** `architecture.md` (source of truth). `PRD.md` is context only.

**Rules for every phase**

- Follow `architecture.md` layout, stack, and API shapes. Do not invent Groww APIs, auth, scraping, or a database of users.
- Stay inside this phase’s file list. Do not start the next phase’s UI/debug/rewrite work early.
- Secrets only in `.env`. Never commit API keys.
- After coding, tell Cursor to run the phase verification commands and fix failures before stopping.

---

## How to run a phase

1. Open a new Cursor chat (or `/clear`) so prior phases do not pull in extra scope.
2. Paste the **Cursor prompt** for that phase.
3. `@`-mention `architecture.md` and `implementation.md`.
4. When Cursor finishes, execute **Done when**. Only then start the next phase.

---

## Phase 0 — Project skeleton

**Goal:** Runnable Python project with the folders and config from architecture §4 and §11. No RAG logic yet.

**Create**

- `requirements.txt` — `fastapi`, `uvicorn`, `chromadb`, `openai` (or OpenAI-compatible client), `python-dotenv`, `pypdf` (optional for later), `tiktoken` or a simple char splitter if you skip extra deps
- `.gitignore` — `.env`, `data/`, `__pycache__/`, `.venv/`
- `.env.example` — `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `CHAT_MODEL`, `CHROMA_PATH`, `CORPUS_PATH`, `TOP_K`, `SCORE_THRESHOLD`
- `src/__init__.py`, empty-or-stub `src/api.py` with `GET /health` returning `{ "ok": true, "index_exists": false }`
- `README.md` — venv, install, copy `.env.example` → `.env`, `uvicorn` command only (no product essay)

**Do not**

- Implement ingest, retrieve, generate, or a chat UI
- Add LangChain unless you must; architecture default is plain Python + Chroma

**Done when**

```text
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn src.api:app --reload
```

`GET http://127.0.0.1:8000/health` returns JSON. CORS not required until Phase 3.

### Cursor prompt — Phase 0

```text
Implement Phase 0 only from implementation.md. Read architecture.md sections 3, 4, and 11 first.

Create a Python FastAPI skeleton for Groww RAG Bot:
- requirements.txt, .gitignore, .env.example, src/__init__.py
- src/api.py with GET /health as specified in architecture.md
- README.md with local run steps only

Do not implement ingest, retrieval, LLM, corpus content, or any UI.
Do not add auth, databases, or Groww APIs.
Stop when GET /health works and list the files you created.
```

---

## Phase 1 — Corpus + ingest (PRD M1 / FR-1, FR-7)

**Goal:** Curated markdown in `corpus/`, plus a rebuild of a persisted Chroma collection.

**Create / fill**

- `corpus/` — 4–8 original or clearly attributed notes, enough to answer PRD sample questions at a high level:
  - what Groww is
  - stocks vs mutual funds (generic, educational)
  - product categories (stocks, mutual funds, FDs) at FAQ level
  - explicit **non-coverage** note: no live prices, no account balances, not official support
- `src/ingest.py` — load `.md` from `CORPUS_PATH` → chunk (~500–800 tokens, ~10–15% overlap) → embed → **delete and rebuild** Chroma at `CHROMA_PATH`
- Metadata per architecture §5.4: `chunk_id`, `source_name`, `source_path`, optional `url`, `text`
- CLI: `python -m src.ingest` prints file count, chunk count, persist path
- `POST /index` in `api.py` calls the same rebuild function (no extra behavior)

**Do not**

- Call the chat LLM
- Build a UI
- Scrape groww.in
- Incremental upsert logic

**Done when**

```text
.venv\Scripts\python -m src.ingest
```

- `data/chroma/` exists and is gitignored
- Re-running ingest succeeds (full rebuild)
- You can inspect collection count (small script or Chroma API in a one-off) and see chunk ids matching filenames

### Cursor prompt — Phase 1

```text
Implement Phase 1 only from implementation.md. Read architecture.md sections 4, 5.4, 8, and 11.

Build corpus/ (original educational markdown, not a site scrape) and src/ingest.py:
- chunk with overlap as in architecture
- persist Chroma under CHROMA_PATH
- rebuild on each run (not incremental)
- metadata: chunk_id, source_name, source_path, optional url, text
- wire POST /index to the same function
- python -m src.ingest must work

Do not implement retrieve, generate, guardrails beyond ingest, or any frontend.
Do not commit .env or data/chroma.
Stop after ingest runs successfully and summarize chunk counts.
```

---

## Phase 2 — Retrieve + generate + chat API (PRD M2 / FR-2–FR-5)

**Goal:** `POST /chat` implements architecture §5.3 and §6. Citations from **retrieved metadata**. Score gate before the LLM.

**Create**

- `src/retrieve.py` — embed query, top-k (`TOP_K` default 4), return chunks + scores (normalize so “higher is better” if Chroma returns distance)
- `src/guardrails.py` — advice / buy-sell; password, OTP, account-number style input; canned refusals (architecture §9 and §12)
- `src/generate.py` — prompt contract architecture §7; LLM only after threshold pass; citations array from retrieved chunks, never model-invented URLs
- `POST /chat` body: `{ "question": "...", "history": [] }` (`history` ignored until Phase 5)
- Response shape **exactly** as architecture §10 (`answer`, `citations`, `debug`)
- Missing index → user-visible message from architecture §12, HTTP 503 or a structured error the UI can later show
- Weak retrieval → `threshold_passed: false`, canned “not in the knowledge base”, `debug.matches` still populated
- Guardrail hit → short refusal, **do not** retrieve as a product FAQ
- API/LLM failures → generic error, no fabricated Groww facts

**Do not**

- Query rewrite (Phase 5)
- Chat UI / debug drawer (Phases 3–4)
- Streaming (optional later)

**Tune** `SCORE_THRESHOLD` against:

- In-corpus: “What is Groww?”
- Out-of-corpus: “What is my portfolio value?” / a live ticker price

**Done when** (with `.env` key set and index built)

```text
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What is Groww?\"}"
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"What is my portfolio value?\"}"
```

First returns a cited answer and `threshold_passed: true`. Second refuses without a fake balance.

### Cursor prompt — Phase 2

```text
Implement Phase 2 only from implementation.md. Read architecture.md sections 5.2, 5.3, 6, 7, 8, 9, 10, and 12.

Add src/retrieve.py, src/guardrails.py, src/generate.py and POST /chat.
Pipeline order is mandatory: guard → retrieve → score gate → generate.
Citations must come from Chroma metadata. Response JSON must match architecture section 10.
Handle missing index, low similarity, guardrails, and provider errors as in architecture section 12.
history may be accepted but ignored.

Do not build the web UI, debug panel, or query rewriting.
Do not add Groww account/market APIs.
After implementation, run two example /chat calls (in-corpus and out-of-corpus) if an API key is present; if not, say what to run.
```

---

## Phase 3 — Chat UI (PRD M3 / FR-6)

**Goal:** Browser chat that calls the local API. Single session in memory. Disclaimer is static.

**Create**

- `web/` — static HTML/JS **or** Vite; pick one and keep it small
- CORS on FastAPI for the UI origin
- Chat: send `question`, render `answer` and `citations` (title, path, chunk id, excerpt)
- Static disclaimer: educational demo, not official Groww support
- Empty/error: API down, timeout, knowledge base not built (from `/chat` or `/health`)
- Optional: button or note to run ingest / `POST /index` (no need for a polished admin)

**Do not**

- Login, routing, component libraries beyond what you need
- Full debug panel (Phase 4) — a collapsed “sources” list is enough
- Persist chats to disk

**Done when**

- UI + API both running
- Ask “What is Groww?” → answer + sources on screen
- Ask “What is my portfolio value?” → refusal
- Kill the API → UI shows an error, last user message remains

Verify in the browser: type, submit, citations visible, error path. Screenshot-only is not enough.

### Cursor prompt — Phase 3

```text
Implement Phase 3 only from implementation.md. Read architecture.md sections 5.1, 5.2, and 12.

Build web/ chat UI and enable CORS on the FastAPI app.
Single-session in-memory chat, no auth.
Show answer, citations from the API, and a static educational disclaimer.
Handle API down, timeout, and missing index.
Do not implement the debug panel (scores / threshold_passed drawer) yet.
Do not add routing, user accounts, or extra pages.
Document how to start API and UI in README.md.
```

---

## Phase 4 — Debug panel + demo script (PRD M4 / FR-8)

**Goal:** Teaching surface for class. Sample questions the presenter can click or copy.

**Create**

- Debug drawer/panel: `debug.matches` (chunk id, score), `threshold_passed`, `rewritten_query` (null for now)
- Do **not** show raw embedding vectors
- `web/` or `Docx/demo-questions.md` — 8–10 questions from `PRD.md` §12, labeled in-corpus vs expect-refusal
- Optional click-to-fill chips in the UI
- README: 5–10 minute demo script matching PRD §4 (in-corpus → follow-up → out-of-corpus + open debug)

**Do not**

- Query rewrite
- Analytics, logging SaaS, extra backends

**Done when**

- Presenter can show why an answer was grounded (scores + chunk ids)
- Presenter can show a refusal with `threshold_passed: false` (or guardrail copy)
- Sample question list exists and matches the actual corpus

### Cursor prompt — Phase 4

```text
Implement Phase 4 only from implementation.md. Read architecture.md sections 5.1, 10, and 15, and PRD.md sections 4 and 12.

Add a debug panel to the existing chat UI using the debug object from POST /chat.
Show top-k matches, scores, and threshold_passed. Do not display embedding vectors.
Add 8–10 sample questions aligned with the corpus, including refusal cases.
Update README with a short live-demo script.

Do not add query rewriting, auth, or new APIs except tiny UI helpers.
Keep changes to web/ and README (plus a demo-questions file if useful).
```

---

## Phase 5 — Optional follow-ups (FR-9, FR-10)

**Do this only if** Phase 4 demo follow-ups retrieve the wrong chunks (pronouns like “those funds”).

**Goal:** Send last 2–4 turns; optionally rewrite to a standalone search query **before** retrieve. Put the rewrite string in `debug.rewritten_query`.

**Do not**

- Add sessions server-side, Redis, or user accounts
- Change citation rules or skip the score gate

### Cursor prompt — Phase 5

```text
Implement Phase 5 only from implementation.md. Read architecture.md sections 5.2, 7, and 8 (query rewrite).

Use client-supplied history (last 2–4 turns) on POST /chat.
If the new question is ambiguous, rewrite to a standalone query for retrieval only; generate still sees the user question and context chunks.
Set debug.rewritten_query. Keep the score gate and metadata citations unchanged.
No server-side session store.

Stop after one follow-up example works (e.g. “What is Groww?” then “What products does it offer?”).
```

---

## Phase checklist (presenter)

| Phase | PRD | You should have |
|-------|-----|-----------------|
| 0 | — | `/health` |
| 1 | M1 | `python -m src.ingest` |
| 2 | M2 | `/chat` cited + refusal |
| 3 | M3 | Browser chat + disclaimer |
| 4 | M4 | Debug + sample Qs |
| 5 | FR-9/10 | Follow-ups if needed |

---

## If Cursor drifts

Paste this and nothing else:

```text
You went beyond the current phase. Revert or remove anything not listed in that phase of implementation.md. Re-read architecture.md. Do not add features from later phases.
```
